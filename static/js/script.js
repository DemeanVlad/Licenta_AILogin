let video;
let canvas;
let nameInput;

function init() {
    video = document.getElementById("video");
    canvas = document.getElementById("canvas");
    nameInput = document.getElementById("nameInput");

    navigator.mediaDevices.getUserMedia({ video: true })
        .then(stream => {
            video.srcObject = stream;
        })
        .catch(error => {
            console.log("Error accessing camera:", error);
            alert("Cannot open camera. Please check your device permissions.");
        });
}

function capture() {
    const context = canvas.getContext("2d");
    context.drawImage(video, 0, 0, canvas.width, canvas.height);
    canvas.style.display = "block";
    video.style.display = "none";
    alert("Photo captured successfully!");
}

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
            console.error("Error during registration:", error);
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


function participateInEvent(eventName) {
    const username = document.body.getAttribute("data-username"); // Obține username-ul din atributul data-username

    if (!username) {
        alert("Error: User not logged in.");
        return;
    }

    const formData = new FormData();
    formData.append("username", username); // Adaugă username-ul în FormData
    formData.append("event_name", eventName); // Adaugă numele evenimentului în FormData

    fetch("/my_events", {
        method: "POST",
        body: formData
    })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert(data.message);
                loadUserEvents(); // Reîncarcă lista de evenimente
            } else {
                alert("Error: " + data.message);
            }
        })
        .catch(error => console.error("Error during event participation:", error));
}

function loadUserEvents() {
    const userEventsContainer = document.getElementById("userEvents");
    const username = document.body.getAttribute("data-username"); // Obține username-ul din atributul data-username

    if (!username) {
        userEventsContainer.innerHTML = "<p>Error: User not logged in.</p>";
        return;
    }

    userEventsContainer.innerHTML = "<p>Loading your events...</p>";

    // Trimitem cererea GET către backend pentru a obține evenimentele utilizatorului
    fetch(`/my_events?user_name=${username}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                const events = data.events;
                if (events.length === 0) {
                    userEventsContainer.innerHTML = "<p>No events selected yet.</p>";
                } else {
                    // Afișăm evenimentele în div-ul #userEvents
                    userEventsContainer.innerHTML = events
                        .map(event => `<div class="event-item">${event}</div>`)
                        .join("");
                }
            } else {
                userEventsContainer.innerHTML = `<p>Error: ${data.message}</p>`;
            }
        })
        .catch(error => {
            console.error("Error loading user events:", error);
            userEventsContainer.innerHTML = "<p>Failed to load events. Please try again later.</p>";
        });
}

// Funcție pentru conversia unei imagini DataURI în Blob
function dataURItoBlob(dataURI) {
    const byteString = atob(dataURI.split(",")[1]);
    const mimeString = dataURI.split(",")[0].split(":")[1].split(";")[0];

    const ab = new ArrayBuffer(byteString.length);
    const ia = new Uint8Array(ab);
    for (let i = 0; i < byteString.length; i++) {
        ia[i] = byteString.charCodeAt(i);
    }
    return new Blob([ab], { type: mimeString });
}

function saveEvent(eventName) {
    fetch('/save_event', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
            username: document.body.dataset.username,
            event_name: eventName
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            alert(data.message);
        } else {
            alert(data.message);
        }
    })
    .catch(error => {
        console.error('Error:', error);
        alert('An error occurred while saving the event.');
    });
}

function deleteSavedEvent(eventName) {
    const username = document.body.dataset.username;

    fetch('/delete_saved_event', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, event_name: eventName })
    })
    .then(response => response.json())
    .then(data => {
        alert(data.message);
        location.reload();
    });
}

// Inițializăm camera și încărcăm evenimentele utilizatorului la încărcarea paginii
document.addEventListener("DOMContentLoaded", () => {
    init();
    loadUserEvents();
});