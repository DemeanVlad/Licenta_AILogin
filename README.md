# Licenta_AILogin
# **Face Recognition Event Manager**

A web application that uses facial recognition for user authentication and allows users to register, log in, and participate in events. Each user can view and manage their selected events.

---

## **Features**

### **1. User Registration**
- Users can register by providing:
  - A username.
  - A password.
  - A photo for facial recognition.
- The app:
  - Hashes and stores the password.
  - Extracts and saves the facial encoding from the uploaded photo.

### **2. User Login**
- **Facial Recognition Login:** Users upload a photo, and the app matches it with stored facial encodings.
- **Username and Password Login:** Users log in with their credentials.

### **3. Event Management**
- **Available Events:** Users can view a list of events and join them.
- **User Events:** Each user can see only the events they have joined.

---

## **Tech Stack**
- **Backend:** Flask, SQLite, Werkzeug.
- **Facial Recognition:** `face_recognition` library.
- **Frontend:** HTML, CSS, JavaScript.

---

## **Database Structure**

### **`users` Table**
- `id`: Primary key.
- `username`: Unique username.
- `password`: Hashed password.
- `face_encoding`: JSON-encoded facial vector.

### **`user_events` Table**
- `id`: Primary key.
- `username`: Linked to the `users` table.
- `event_name`: Name of the event.

------------------------------------------------------------------------------------

delete DB
- image:
  -- cd /Users/demeanvlad8/Desktop/Licenta_Martie/html_facerecogn/static/uploads
  -- ls
  -- rm -rf *
  -- ls
- credentials:
  -- sqlite3 database.db
  -- DELETE FROM users;
  -- DELETE FROM user_events;
  -- SELECT * FROM users;
  -- SELECT * FROM user_events;
  -- .exit
flask run 
