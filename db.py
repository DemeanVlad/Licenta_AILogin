import sqlite3
import bcrypt

def init_db():
    print("Initializing database...")  # Mesaj de debug
    conn = sqlite3.connect('database.db')
    cursor = conn.cursor()
    
    # Crearea tabelelor
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

    # Adăugarea coloanelor pentru OTP (dacă nu există deja)
    try:
        cursor.execute('ALTER TABLE users ADD COLUMN otp TEXT')
    except sqlite3.OperationalError:
        print("Column 'otp' already exists.")

    try:
        cursor.execute('ALTER TABLE users ADD COLUMN otp_timestamp DATETIME')
    except sqlite3.OperationalError:
        print("Column 'otp_timestamp' already exists.")

    conn.commit()
    conn.close()
    print("Database initialized.")  # Mesaj de debug

def create_admin_user():
    """Creează utilizatorul admin dacă nu există deja."""
    with sqlite3.connect('database.db') as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM users WHERE username = 'admin'")
        if cursor.fetchone() is None:
            admin_password = "admin123"
            hashed_password = bcrypt.hashpw(admin_password.encode(), bcrypt.gensalt())
            cursor.execute('''
                INSERT INTO users (username, email, password, face_encoding, role)
                VALUES (?, ?, ?, ?, ?)
            ''', ("admin", "admin@example.com", hashed_password, None, "admin"))
            conn.commit()
            print("Admin user created.")

if __name__ == "__main__":
    init_db()
    create_admin_user()