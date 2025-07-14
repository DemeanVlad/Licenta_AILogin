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
import random
import smtplib
from datetime import datetime, timedelta

def generate_otp():
    """Generează un cod OTP de 6 cifre."""
    return str(random.randint(100000, 999999))

def send_otp_email(email, otp):
    """Trimite codul OTP prin email."""
    sender_email = "demeanvlad8@gmail.com"
    sender_password = "pbzk fqut ktps eqsw"  # Parola generată pentru aplicație
    subject = "Your OTP Code"
    body = f"Your OTP code is: {otp}. It is valid for 5 minutes."

    message = f"Subject: {subject}\n\n{body}"

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, email, message)
    except Exception as e:
        print("Error sending email:", e)

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

# Încarcă modelul antrenat (
MODEL_PATH = "face_recognition_model.h5"
if os.path.exists(MODEL_PATH):
    model = load_model(MODEL_PATH)
else:
    model = None

# Încarcă class indices 
if os.path.exists("class_indices.json"):
    with open("class_indices.json", "r") as f:
        class_indices = json.load(f)
        class_labels = {v: k for k, v in class_indices.items()}
else:
    class_indices = {}
    class_labels = {}

def init_db():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            email TEXT NOT NULL UNIQUE,
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

# Funcții auxiliare
def preprocess_image(image_path, target_size=(128, 128)):
    img = load_img(image_path, target_size=target_size)
    img_array = img_to_array(img)
    img_array = np.expand_dims(img_array, axis=0)
    return img_array


def hash_password(password):
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt())

def check_password(password, hashed):
    return bcrypt.checkpw(password.encode(), hashed)

def encrypt_face_vector(face_vector):
    face_bytes = json.dumps(face_vector.tolist()).encode()
    encrypted = fernet.encrypt(face_bytes)
    return base64.b64encode(encrypted).decode()

def decrypt_face_vector(encrypted_str):
    encrypted = base64.b64decode(encrypted_str.encode())
    decrypted_bytes = fernet.decrypt(encrypted)
    return np.array(json.loads(decrypted_bytes.decode()))

# Rute
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/register", methods=["POST"])
def register():
    name = request.form.get("name")
    email = request.form.get("email")
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
    hashed_password = bcrypt.hashpw(password.encode(), bcrypt.gensalt())
    encrypted_face_encoding = encrypt_face_vector(face_encoding)

    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO users (username, email, password, face_encoding, role)
            VALUES (?, ?, ?, ?, ?)
        ''', (name, email, hashed_password, encrypted_face_encoding, "user"))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "Registration successful."})
    except sqlite3.IntegrityError:
        return jsonify({"success": False, "message": "Username or email already exists."})

@app.route("/login_with_credentials", methods=["POST"])
def login_with_credentials():
    username = request.form.get("username")
    password = request.form.get("password")
    otp = request.form.get("otp")  # Codul OTP, dacă este trimis

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # Verifică dacă utilizatorul există
    cursor.execute('SELECT password, otp, otp_timestamp, email FROM users WHERE username = ?', (username,))
    result = cursor.fetchone()
    if not result:
        conn.close()
        return jsonify({"success": False, "message": "Invalid username or password."}), 401

    stored_password, stored_otp, otp_timestamp, email = result

    # Dacă OTP-ul este trimis, verifică-l
    if otp:
        if stored_otp != otp:
            conn.close()
            return jsonify({"success": False, "message": "Invalid OTP."}), 400

        # Verifică dacă OTP-ul a expirat (5 minute)
        try:
            otp_time = datetime.strptime(otp_timestamp, "%Y-%m-%d %H:%M:%S.%f")
        except (ValueError, TypeError):
            try:
                otp_time = datetime.strptime(otp_timestamp, "%Y-%m-%d %H:%M:%S")
            except Exception:
                conn.close()
                return jsonify({"success": False, "message": "Invalid OTP timestamp format."}), 400

        if datetime.now() > otp_time + timedelta(minutes=5):
            conn.close()
            return jsonify({"success": False, "message": "OTP expired."}), 400

        # Șterge OTP-ul după utilizare
        cursor.execute('UPDATE users SET otp = NULL, otp_timestamp = NULL WHERE username = ?', (username,))
        conn.commit()
        conn.close()

        # Finalizează autentificarea
        return jsonify({"success": True, "message": "Authentication successful."})

    # Dacă OTP-ul nu este trimis, validează username-ul și parola
    if not bcrypt.checkpw(password.encode(), stored_password):
        conn.close()
        return jsonify({"success": False, "message": "Invalid username or password."}), 401

    # Generează și trimite OTP-ul
    otp = generate_otp()
    otp_timestamp = datetime.now()

    cursor.execute('UPDATE users SET otp = ?, otp_timestamp = ? WHERE username = ?', (otp, otp_timestamp, username))
    conn.commit()
    conn.close()

    send_otp_email(email, otp)

    return jsonify({"success": True, "message": "OTP sent to your email. Please enter it to complete authentication."})

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

@app.route("/success")
def success():
    user_name = request.args.get("user_name")

    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT email FROM users WHERE username = ?', (user_name,))
    result = cursor.fetchone()
    conn.close()

    if result:
        user_email = result[0]
        return render_template("success.html", user_name=user_name, user_email=user_email)
    else:
        return jsonify({"success": False, "message": "User not found."})

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

@app.route("/admin")
def admin_panel():
    return render_template("admin.html")

@app.route("/get_events", methods=["GET"])
def get_events():
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT DISTINCT event_name FROM user_events')
    events = cursor.fetchall()
    conn.close()

    # Returnează evenimentele sub formă de JSON
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
        return jsonify({"success": True, "events": [event[0] for event in events]})

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
    from db import init_db # Importă funcțiile din db.py
    init_db()  # Inițializează baza de date
    app.run(debug=True)