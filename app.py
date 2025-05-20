import os
import bcrypt
from cryptography.fernet import Fernet
import base64
import json
from flask import Flask, jsonify, request, render_template, redirect, url_for
import sqlite3
import face_recognition
from tensorflow.keras.models import load_model
from tensorflow.keras.preprocessing.image import img_to_array, load_img
import numpy as np

# Verifică dacă secret.key există, altfel generează unul nou
if not os.path.exists("secret.key"):
    print("Secret key not found. Generating a new one...")
    key = Fernet.generate_key()
    with open("secret.key", "wb") as f:
        f.write(key)

# Încarcă cheia Fernet pentru criptare vector facial
with open("secret.key", "rb") as f:
    fernet = Fernet(f.read())

app = Flask(__name__, static_folder='static')

# Încarcă modelul antrenat (dacă este necesar)
MODEL_PATH = "face_recognition_model.h5"
if os.path.exists(MODEL_PATH):
    model = load_model(MODEL_PATH)
else:
    model = None

# Încarcă class indices (dacă este necesar)
if os.path.exists("class_indices.json"):
    with open("class_indices.json", "r") as f:
        class_indices = json.load(f)
        class_labels = {v: k for k, v in class_indices.items()}
else:
    class_indices = {}
    class_labels = {}

# Funcții auxiliare
def preprocess_image(image_path, target_size=(128, 128)):
    img = load_img(image_path, target_size=target_size)
    img_array = img_to_array(img)
    img_array = np.expand_dims(img_array, axis=0)
    return img_array

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

# Rute
@app.route("/")
def index():
    return render_template("index.html")

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
        cursor.execute('''
            INSERT INTO users (username, password, face_encoding, role)
            VALUES (?, ?, ?, ?)
        ''', (name, hashed_password, encrypted_face_encoding, "user"))
        conn.commit()
        conn.close()
        return redirect(url_for("success", user_name=name))
    except sqlite3.IntegrityError:
        return jsonify({"success": False, "message": "Username already exists."})

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
            continue  # Dacă nu poate decripta, treci peste

        matches = face_recognition.compare_faces([stored_face_encoding], login_face_encoding)
        if any(matches):
            return jsonify({"success": True, "message": "Login successful.", "username": username})

    return jsonify({"success": False, "message": "No matching face found."})

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

@app.route("/success")
def success():
    user_name = request.args.get("user_name")
    return render_template("success.html", user_name=user_name)

@app.route("/profile", methods=["GET"])
def profile():
    user_name = request.args.get("user_name")
    if not user_name:
        return jsonify({"success": False, "message": "Username is required."}), 400

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT username FROM users WHERE username = ?', (user_name,))
    user = cursor.fetchone()

    if not user:
        return jsonify({"success": False, "message": "User not found."}), 404

    cursor.execute('SELECT event_name FROM user_events WHERE username = ?', (user_name,))
    events = cursor.fetchall()
    conn.close()

    return render_template("profile.html", user_name=user_name, events=[event[0] for event in events])

@app.route("/get_my_events", methods=["GET"])
def get_events():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT DISTINCT event_name FROM user_events')
    events = cursor.fetchall()
    conn.close()

    return jsonify({"events": [event[0] for event in events]})

@app.route("/my_events", methods=["GET", "POST"])
def my_events():
    if request.method == "GET":
        username = request.args.get("user_name")
        if not username:
            return jsonify({"success": False, "message": "Username is required."}), 400

        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('SELECT event_name FROM user_events WHERE username = ?', (username,))
        events = cursor.fetchall()
        conn.close()

        return render_template("my_events.html", user_name=username, events=[event[0] for event in events])

    elif request.method == "POST":
        username = request.form.get("username")
        event_name = request.form.get("event_name")

        if not username or not event_name:
            return jsonify({"success": False, "message": "Username and event name are required."}), 400

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
@app.route("/admin")
def admin_panel():
    return render_template("admin.html")

@app.route("/verify_access", methods=["POST"])
def verify_access():
    event_name = request.form.get("event_name")
    photo = request.files['photo']

    # Salvăm imaginea temporar
    uploads_folder = os.path.join(os.getcwd(), "static", "uploads")
    if not os.path.exists(uploads_folder):
        os.makedirs(uploads_folder)
    temp_photo_path = os.path.join(uploads_folder, "temp_access.jpg")
    photo.save(temp_photo_path)

    # Extragere vector facial din imaginea încărcată
    image = face_recognition.load_image_file(temp_photo_path)
    face_encodings = face_recognition.face_encodings(image)

    if len(face_encodings) == 0:
        return jsonify({"success": False, "message": "No face detected in the image."})

    face_encoding = face_encodings[0]

    # Verificăm utilizatorii care au bilete pentru eveniment
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''
        SELECT u.username, u.face_encoding
        FROM users u
        JOIN user_events ue ON u.username = ue.username
        WHERE ue.event_name = ?
    ''', (event_name,))
    attendees = cursor.fetchall()
    conn.close()

    for username, face_encoding_json in attendees:
        stored_face_encoding = decrypt_face_vector(face_encoding_json)
        matches = face_recognition.compare_faces([stored_face_encoding], face_encoding)
        if any(matches):
            return jsonify({"success": True, "message": f"Access granted for {username}."})

    return jsonify({"success": False, "message": "Access denied. No matching face found for this event."})

if __name__ == "__main__":
    init_db()
    create_admin_user()
    app.run(debug=True)