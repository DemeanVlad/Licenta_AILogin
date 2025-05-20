
import os
import bcrypt
from cryptography.fernet import Fernet
import base64
import json
from flask import Flask, jsonify, request, render_template
import sqlite3
import face_recognition

# Încarcă cheia Fernet pentru criptare vector facial
with open("secret.key", "rb") as f:
    fernet = Fernet(f.read())

app = Flask(__name__)

# Funcția pentru inițializarea bazei de date
def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password BLOB NOT NULL,
            face_encoding TEXT,
            role TEXT DEFAULT 'user'
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            event_name TEXT NOT NULL,
            FOREIGN KEY (username) REFERENCES users (username) ON DELETE CASCADE
        )
    ''')
    conn.commit()
    conn.close()

# Funcția pentru crearea utilizatorului admin
def create_admin_user():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = 'admin'")
    if cursor.fetchone() is None:
        admin_password = "admin123"
        hashed_password = bcrypt.hashpw(admin_password.encode(), bcrypt.gensalt())
        cursor.execute('''
            INSERT INTO users (username, password, face_encoding, role)
            VALUES (?, ?, ?, ?)
        ''', ("admin", hashed_password, None, "admin"))
        conn.commit()
    conn.close()

# Funcții pentru gestionarea parolelor și vectorilor faciali
def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt())

def check_password(password, hashed):
    return bcrypt.checkpw(password.encode(), hashed)

def encrypt_face_vector(face_vector):
    face_bytes = json.dumps(face_vector).encode()
    encrypted = fernet.encrypt(face_bytes)
    return base64.b64encode(encrypted).decode()

def decrypt_face_vector(encrypted_str):
    encrypted = base64.b64decode(encrypted_str.encode())
    decrypted_bytes = fernet.decrypt(encrypted)
    return json.loads(decrypted_bytes.decode())

# Ruta principală
@app.route("/")
def index():
    return render_template("index.html")

# Ruta pentru înregistrare
@app.route("/register", methods=["POST"])
def register():
    name = request.form.get("name")
    password = request.form.get("password")
    photo = request.files['photo']

    uploads_folder = os.path.join(os.getcwd(), "static", "uploads")
    if not os.path.exists(uploads_folder):
        os.makedirs(uploads_folder)
    photo_path = os.path.join(uploads_folder, f'{name}.jpg')
    photo.save(photo_path)

    image = face_recognition.load_image_file(photo_path)
    face_encodings = face_recognition.face_encodings(image)

    if len(face_encodings) == 0:
        return jsonify({"success": False, "message": "No face detected in the image."})

    face_encoding = face_encodings[0]
    hashed_password = hash_password(password)
    encrypted_face_encoding = encrypt_face_vector(face_encoding.tolist())

    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM users WHERE username = ?', (name,))
        existing_user = cursor.fetchone()

        if existing_user:
            conn.close()
            return jsonify({"success": False, "message": "Username already exists."})

        cursor.execute('''
            INSERT INTO users (username, password, face_encoding, role)
            VALUES (?, ?, ?, ?)
        ''', (name, hashed_password, encrypted_face_encoding, "user"))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "User registered successfully."})
    except sqlite3.IntegrityError as e:
        return jsonify({"success": False, "message": f"Database error: {str(e)}"})

# Ruta pentru autentificare cu fața
@app.route("/login", methods=["POST"])
def login():
    photo = request.files['photo']

    uploads_folder = os.path.join(os.getcwd(), "static", "uploads")
    if not os.path.exists(uploads_folder):
        os.makedirs(uploads_folder)
    login_path = os.path.join(uploads_folder, "login_face.jpg")
    photo.save(login_path)

    login_image = face_recognition.load_image_file(login_path)
    login_face_encodings = face_recognition.face_encodings(login_image)

    if len(login_face_encodings) == 0:
        return jsonify({"success": False, "message": "No face detected in the image."})

    login_face_encoding = login_face_encodings[0]

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT username, face_encoding FROM users')
    users = cursor.fetchall()
    conn.close()

    for username, face_encoding_json in users:
        if face_encoding_json is None:
            continue

        try:
            stored_face_encoding = decrypt_face_vector(face_encoding_json)
        except Exception:
            continue

        matches = face_recognition.compare_faces([stored_face_encoding], login_face_encoding)
        if any(matches):
            return jsonify({"success": True, "message": "Login successful.", "username": username})

    return jsonify({"success": False, "message": "No matching face found."})

# Ruta pentru autentificare cu username și parolă
@app.route("/login_with_credentials", methods=["POST"])
def login_with_credentials():
    username = request.form.get("username")
    password = request.form.get("password")

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT password, role FROM users WHERE username = ?', (username,))
    result = cursor.fetchone()
    conn.close()

    if result is None:
        return jsonify({"success": False, "message": "Invalid username or password."})

    stored_password, role = result
    if check_password(password, stored_password):
        if role == "admin":
            return jsonify({"success": True, "message": "Admin login successful.", "role": "admin"})
        else:
            return jsonify({"success": True, "message": "User login successful.", "role": "user"})
    else:
        return jsonify({"success": False, "message": "Invalid username or password."})

# Ruta pentru obținerea evenimentelor
@app.route("/get_events", methods=["GET"])
def get_events():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT DISTINCT event_name FROM user_events')
    events = cursor.fetchall()
    conn.close()

    return jsonify({"events": [event[0] for event in events]})

# Ruta pentru adăugarea evenimentelor
@app.route("/my_events", methods=["POST"])
def post_my_events():
    username = request.form.get("username")
    event_name = request.form.get("event_name")

    if not username:
        return jsonify({"success": False, "message": "Username is required."}), 400
    if not event_name:
        return jsonify({"success": False, "message": "Event name is required."}), 400

    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM user_events WHERE username = ? AND event_name = ?', (username, event_name))
        existing_event = cursor.fetchone()

        if existing_event:
            conn.close()
            return jsonify({"success": False, "message": "Event already exists for this user."}), 400

        cursor.execute('INSERT INTO user_events (username, event_name) VALUES (?, ?)', (username, event_name))
        conn.commit()
        conn.close()

        return jsonify({"success": True, "message": "Event added successfully."})
    except Exception as e:
        return jsonify({"success": False, "message": f"An error occurred: {str(e)}"}), 500

if __name__ == "__main__":
    print("Initializing database...")
    init_db()  # Creează tabelele necesare
    create_admin_user()  # Creează utilizatorul admin
    app.run(debug=True)