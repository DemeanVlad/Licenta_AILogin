let video;
let canvas;
let nameInput;

function init(){
    //and now if you run it will open instant camera
    video = document.getElementById("video");
    canvas = document.getElementById("canvas");
    nameInput = document.getElementById("nameInput");

    //open webcam access
    navigator.mediaDevices.getUserMedia({video:true})
        .then(stream =>{
            video.srcObject = stream;
        })
        .catch(error =>{
            console.log("error camera", error);
            alert("cannot open camera");
        });
}

function capture(){
    const context = canvas.getContext("2d");
    context.drawImage(video, 0, 0, canvas.width, canvas.height);
    canvas.style.display = "block";
    video.style.display = "none";
}

//and create register function
function register() {
    const name = nameInput.value;
    const password = prompt("Enter your password:");
    const photo = dataURItoBlob(canvas.toDataURL());

    if (!name || !password || !photo) {
        alert("Name, password, and photo are required.");
        return;
    }

    const formData = new FormData();
    formData.append("name", name);
    formData.append("password", password);
    formData.append("photo", photo, `${name}.jpg`);

    fetch("/register", {
        method: "POST",
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert("Registration successful!");
        } else {
            alert(data.message);
        }
    })
    .catch(error => {
        console.error("Error:", error);
    });
}

function login() {
    const context = canvas.getContext("2d");
    context.drawImage(video, 0, 0, canvas.width, canvas.height);
    const photo = dataURItoBlob(canvas.toDataURL());

    if (!photo) {
        alert("Photo is required.");
        return;
    }

    const formData = new FormData();
    formData.append("photo", photo, "login.jpg");

    fetch("/login", {
        method: "POST",
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert(`Welcome, ${data.username}!`);
            window.location.href = "/success?user_name=" + data.username;
        } else {
            alert(data.message);
        }
    })
    .catch(error => {
        console.error("Error:", error);
    });
}
// Afișează formularul de login cu username și parolă
function showLoginForm() {
    document.getElementById("loginForm").style.display = "block";
}

// Ascunde formularul de login
function hideLoginForm() {
    document.getElementById("loginForm").style.display = "none";
}

// Funcția pentru autentificare cu username și parolă
function loginWithCredentials() {
    const username = document.getElementById("usernameInput").value;
    const password = document.getElementById("passwordInput").value;

    if (!username || !password) {
        alert("Please enter both username and password.");
        return;
    }

    const formData = new FormData();
    formData.append("username", username);
    formData.append("password", password);

    fetch("/login_with_credentials", {
        method: "POST",
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert(`Welcome, ${data.username}!`);
            window.location.href = "/success?user_name=" + data.username;
        } else {
            alert(data.message);
        }
    })
    .catch(error => {
        console.error("Error:", error);
    });
}

// Funcția pentru a participa la un eveniment
function participateInEvent(eventName) {
    const formData = new FormData();
    formData.append("username", userName); // Folosește variabila `userName` definită în JavaScript
    formData.append("event_name", eventName);

    fetch("/add_event", {
        method: "POST",
        body: formData
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert(data.message);
            loadUserEvents(); // Reîncarcă evenimentele utilizatorului
        } else {
            alert("Error: " + data.message);
        }
    })
    .catch(error => console.error("Error:", error));
}

// Funcția pentru a încărca evenimentele utilizatorului
function loadUserEvents() {
    fetch(`/get_user_events?username=${userName}`)
        .then(response => response.json())
        .then(data => {
            const userEventsDiv = document.getElementById("userEvents");
            userEventsDiv.innerHTML = ""; // Golește lista curentă

            if (data.success) {
                if (data.events.length === 0) {
                    userEventsDiv.innerHTML = "<p>You haven't participated in any events yet.</p>";
                } else {
                    data.events.forEach(event => {
                        const eventElement = document.createElement("div");
                        eventElement.className = "user-event";
                        eventElement.textContent = event;
                        userEventsDiv.appendChild(eventElement);
                    });
                }
            } else {
                alert("Error: " + data.message);
            }
        })
        .catch(error => console.error("Error:", error));
}

// Încarcă evenimentele utilizatorului la încărcarea paginii
document.addEventListener("DOMContentLoaded", loadUserEvents);

function dataURItoBlob(dataURI){
    const byteString = atob(dataURI.split(",")[1]);
    const mimeString = dataURI.split(",")[0].split(":")[1].split(";")[0];

    const ab = new ArrayBuffer(byteString.length);
    const ia = new Uint8Array(ab);
    for(let i = 0; i < byteString.length; i++){
        ia[i] = byteString.charCodeAt(i);
    }
    return new Blob([ab], {type: mimeString});
}

init();