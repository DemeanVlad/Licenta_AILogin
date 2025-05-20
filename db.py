# filepath: /Users/demeanvlad8/Desktop/licenta_20mai_backup/database.py
import sqlite3

def init_db():
    """Creează baza de date și tabelele necesare."""
    with sqlite3.connect('database.db') as conn:
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
        print("Database and tables created successfully.")

def create_admin_user():
    """Creează utilizatorul admin dacă nu există deja."""
    with sqlite3.connect('database.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = 'admin'")
        if cursor.fetchone() is None:
            import bcrypt
            admin_password = "admin123"
            hashed_password = bcrypt.hashpw(admin_password.encode(), bcrypt.gensalt())
            cursor.execute('''
                INSERT INTO users (username, password, face_encoding, role)
                VALUES (?, ?, ?, ?)
            ''', ("admin", hashed_password, None, "admin"))
            conn.commit()
            print("Admin user created.")