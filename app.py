import os
import datetime
import cv2
from flask import Flask, jsonify, request, render_template

import face_recognition

app = Flask(__name__)
#create var for register

registered_data = {}


@app.route("/")
def index():
    #now render you html file
    return render_template("index.html")

#post method
@app.route("/register", methods=["POST"])
def register():
    name = request.form.get("name")
    #and get you photo uloads
    photo = request.files['photo']

    #and now save you phoyo to uploads folder
    #when you register process
    uploads_folder = os.path.join(os.getcwd(), "static", "uploads")
    #and if folder uploads not found this system will
    #auto create folder uploads
    if not os.path.exists(uploads_folder):
        os.makedirs(uploads_folder)

    #and save you phoyo image with file name date now
    photo.save(os.path.join(uploads_folder, f'{datetime.date.today()}_{name}.jpg'))

    registered_data[name] = f"{datetime.date.today()}_{name}.jpg"
    #and send success response then page will refresh and login
    response = {"success": True, 'name': name}
    return jsonify(response)

#create login route post
@app.route("/login", methods=["POST"])
def login():  
    photo = request.files['photo']

    #and save you photo login to folder uploads
    uploads_folder = os.path.join(os.getcwd(), "static", "uploads")
    #and create folder if it s not found
    if not os.path.exists(uploads_folder):
        os.makedirs(uploads_folder)

    #and sace file photo login /w ur name
    login_filename = os.path.join(uploads_folder, "login_face.jpg")

    photo.save(login_filename)

    #and thiss process will detect you camrea is there face or not

    login_image = cv2.imread(login_filename)
    gray_image = cv2.cvtColor(login_image, cv2.COLOR_BGR2GRAY)

    #and load you haar cascde file here
    face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + "haarcascade_frontalface_default.xml")
    faces = face_cascade.detectMultiScale(gray_image, scaleFactor=1.1, minNeighbors=5, minSize=(30, 30))

    #and detect if no face in camera
    if len(faces) == 0:
        response = {"success": False}
        return jsonify(response)

    login_image = face_recognition.load_image_file(login_filename)
    #and process andrecognition you face
    #and if photos in folder uploads find domain similarity
    #you imafes tehn login succes
    login_face_encodings = face_recognition.face_encodings(login_image)

    for name, filename in registered_data.items():
        registered_photo = os.path.join(uploads_folder, filename)
        registered_image = face_recognition.load_image_file(registered_photo)

        register_face_encodings = face_recognition.face_encodings(registered_image)
        #and compare your image from loin and reister photo

        if len(register_face_encodings) > 0 and len(login_face_encodings) > 0:
            matches = face_recognition.compare_faces(register_face_encodings, login_face_encodings[0])
            #and see amtch
            print("matches", matches)
            if any(matches):
                response = {"success": True, "name": name}
                return jsonify(response)

        #and if no match found
    response = {"success": False}
    return jsonify(response)

    #and this page will show success page if tou succes login

@app.route("/success")
def success():
    user_name = request.args.get("user_name")
    return render_template("success.html", user_name=user_name)

if __name__ == "__main__":
    app.run(debug=True)