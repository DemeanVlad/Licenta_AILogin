import os
import cv2
from flask import Flask, jsonify, request, render_template
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import json
import face_recognition

app = Flask(__name__)

# Funcție pentru inițializarea bazei de date
def init_db():
    # Conectare la baza de date
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()

    # Crearea tabelei `users`
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL,
            face_encoding TEXT
        )
    ''')

    # Crearea tabelei `user_events`
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            event_name TEXT NOT NULL,
            FOREIGN KEY (username) REFERENCES users (username) ON DELETE CASCADE
        )
    ''')

    # Crearea tabelei `saved_events`
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS saved_events (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            event_name TEXT NOT NULL,
            FOREIGN KEY (username) REFERENCES users (username) ON DELETE CASCADE
        )
    ''')

    # Confirmăm modificările și închidem conexiunea
    conn.commit()
    conn.close()

# Inițializăm baza de date la pornirea aplicației
init_db()

@app.route("/")
def index():
    # Renderizăm pagina principală
    return render_template("index.html")

# Ruta pentru înregistrare
@app.route("/register", methods=["POST"])
def register():
    name = request.form.get("name")
    password = request.form.get("password")
    photo = request.files['photo']

    # Salvăm imaginea în folderul uploads
    uploads_folder = os.path.join(os.getcwd(), "static", "uploads")
    if not os.path.exists(uploads_folder):
        os.makedirs(uploads_folder)
    photo_path = os.path.join(uploads_folder, f'{name}.jpg')
    photo.save(photo_path)

    # Extragere vector facial
    image = face_recognition.load_image_file(photo_path)
    face_encodings = face_recognition.face_encodings(image)

    if len(face_encodings) == 0:
        return jsonify({"success": False, "message": "No face detected in the image."})

    face_encoding = face_encodings[0]
    face_encoding_json = json.dumps(face_encoding.tolist())

    # Hash parola
    hashed_password = generate_password_hash(password)

    # Salvăm utilizatorul în baza de date
    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO users (username, password, face_encoding)
            VALUES (?, ?, ?)
        ''', (name, hashed_password, face_encoding_json))
        conn.commit()
        conn.close()
        return jsonify({"success": True, "message": "User registered successfully."})
    except sqlite3.IntegrityError:
        return jsonify({"success": False, "message": "Username already exists."})

# Ruta pentru autentificare cu recunoaștere facială
@app.route("/login", methods=["POST"])
def login():
    photo = request.files['photo']

    # Salvăm imaginea de login
    uploads_folder = os.path.join(os.getcwd(), "static", "uploads")
    if not os.path.exists(uploads_folder):
        os.makedirs(uploads_folder)
    login_path = os.path.join(uploads_folder, "login_face.jpg")
    photo.save(login_path)

    # Extragere vector facial din imaginea de login
    login_image = face_recognition.load_image_file(login_path)
    login_face_encodings = face_recognition.face_encodings(login_image)

    if len(login_face_encodings) == 0:
        return jsonify({"success": False, "message": "No face detected in the image."})

    login_face_encoding = login_face_encodings[0]

    # Comparăm vectorul facial cu utilizatorii din baza de date
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT username, face_encoding FROM users')
    users = cursor.fetchall()

    for username, face_encoding_json in users:
        stored_face_encoding = json.loads(face_encoding_json)
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
    cursor.execute('SELECT password FROM users WHERE username = ?', (username,))
    result = cursor.fetchone()

    if result is None:
        return jsonify({"success": False, "message": "Invalid username or password."})

    stored_password = result[0]
    if check_password_hash(stored_password, password):
        return jsonify({"success": True, "message": "Login successful.", "username": username})
    else:
        return jsonify({"success": False, "message": "Invalid username or password."})

# Ruta pentru pagina de succes
@app.route("/success")
def success():
    user_name = request.args.get("user_name")
    if not user_name:
        return "User not logged in", 400

    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        # Obținem evenimentele utilizatorului
        cursor.execute('SELECT event_name FROM user_events WHERE username = ?', (user_name,))
        events = cursor.fetchall()
        conn.close()

        # Transmitem evenimentele către template
        return render_template(
            "success.html",
            user_name=user_name,
            events=[{"name": event[0]} for event in events]
        )
    except Exception as e:
        return f"An error occurred: {str(e)}", 500

@app.route("/my_events", methods=["POST"])
def post_my_events():
        username = request.form.get("username")  # Obține username-ul din cererea POST
        event_name = request.form.get("event_name")  # Obține numele evenimentului

        # Validarea datelor primite
        if not username or not username.strip():
            return jsonify({"success": False, "message": "Username is required and cannot be empty."}), 400
        if not event_name or not event_name.strip():
            return jsonify({"success": False, "message": "Event name is required and cannot be empty."}), 400

        try:
            conn = sqlite3.connect('database.db')
            cursor = conn.cursor()

            # Verificăm dacă evenimentul există deja pentru utilizator
            cursor.execute('SELECT * FROM user_events WHERE username = ? AND event_name = ?', (username, event_name))
            existing_event = cursor.fetchone()

            if existing_event:
                return jsonify({"success": False, "message": "Event already exists for this user."}), 400

            # Adăugăm evenimentul în baza de date
            cursor.execute('INSERT INTO user_events (username, event_name) VALUES (?, ?)', (username, event_name))
            conn.commit()

            return jsonify({"success": True, "message": "Event added successfully."})
        except sqlite3.Error as e:
            return jsonify({"success": False, "message": f"Database error: {str(e)}"}), 500
        except Exception as e:
            return jsonify({"success": False, "message": f"An unexpected error occurred: {str(e)}"}), 500
        finally:
            conn.close()  # Închidem conexiunea la baza de date în mod sigur

@app.route("/profile", methods=["GET"])
def profile():
    user_name = request.args.get("user_name")
    if not user_name:
        return jsonify({"success": False, "message": "Username is required."}), 400

    # Obținem informațiile utilizatorului din baza de date
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    cursor.execute('SELECT username FROM users WHERE username = ?', (user_name,))
    user = cursor.fetchone()

    if not user:
        return jsonify({"success": False, "message": "User not found."}), 404

    # Obținem evenimentele utilizatorului
    cursor.execute('SELECT event_name FROM user_events WHERE username = ?', (user_name,))
    events = cursor.fetchall()
    conn.close()

    # Transmitem informațiile către template-ul HTML
    return render_template("profile.html", user_name=user_name, events=[event[0] for event in events])

@app.route("/save_event", methods=["POST"])
def save_event():
    data = request.get_json()
    username = data.get("username")
    event_name = data.get("event_name")

    if not username or not event_name:
        return jsonify({"success": False, "message": "Username and event name are required."}), 400

    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        # Verificăm dacă evenimentul este deja salvat
        cursor.execute(
            'SELECT * FROM saved_events WHERE username = ? AND event_name = ?',
            (username, event_name)
        )
        existing_event = cursor.fetchone()
        if existing_event:
            return jsonify({"success": False, "message": "Event already saved."}), 400

        # Salvăm evenimentul
        cursor.execute(
            'INSERT INTO saved_events (username, event_name) VALUES (?, ?)',
            (username, event_name)
        )
        conn.commit()
        return jsonify({"success": True, "message": "Event saved successfully."})
    except sqlite3.Error as e:
        return jsonify({"success": False, "message": f"Database error: {str(e)}"}), 500
    finally:
        conn.close()

# Ruta pentru afișarea evenimentelor salvate
@app.route("/saved_events", methods=["GET"])
def get_saved_events():
    username = request.args.get("user_name")
    if not username:
        return jsonify({"success": False, "message": "Username is required."}), 400

    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        # Preluăm evenimentele salvate
        cursor.execute(
            'SELECT event_name FROM saved_events WHERE username = ?',
            (username,)
        )
        events = cursor.fetchall()
        conn.close()

        # Transmitem evenimentele către template-ul HTML
        return render_template(
            "saved_events.html",
            user_name=username,
            events=[{"name": event[0]} for event in events]
        )
    except sqlite3.Error as e:
        return jsonify({"success": False, "message": f"Database error: {str(e)}"}), 500
    
@app.route("/delete_saved_event", methods=["POST"])
def delete_saved_event():
    username = request.form.get("username")
    event_name = request.form.get("event_name")

    if not username or not event_name:
        return jsonify({"success": False, "message": "Username and event name are required."}), 400

    try:
        conn = sqlite3.connect('database.db')
        cursor = conn.cursor()

        # Ștergem evenimentul
        cursor.execute(
            'DELETE FROM saved_events WHERE username = ? AND event_name = ?',
            (username, event_name)
        )
        conn.commit()
        return jsonify({"success": True, "message": "Event removed successfully."})
    except sqlite3.Error as e:
        return jsonify({"success": False, "message": f"Database error: {str(e)}"}), 500
    finally:
        conn.close()

if __name__ == "__main__":
    app.run(debug=True)