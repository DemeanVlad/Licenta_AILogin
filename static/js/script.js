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
    const name = document.getElementById("nameInput").value;
    const email = document.getElementById("emailInput").value;
    const password = document.getElementById("passwordInput").value;
    const photo = dataURItoBlob(canvas.toDataURL());

    if (!name || !email || !password || !photo) {
        alert("All fields are required.");
        return;
    }

    const formData = new FormData();
    formData.append("name", name);
    formData.append("email", email);
    formData.append("password", password);
    formData.append("photo", photo, `${name}.jpg`);

    fetch("/register", {
        method: "POST",
        body: formData
    })
        .then(response => response.json())
        .then(data => {
            const messageDiv = document.getElementById("registerMessage");
            if (data.success) {
                messageDiv.innerHTML = `<p style="color: green;">${data.message}</p>`;
                document.getElementById("nameInput").value = "";
                document.getElementById("emailInput").value = "";
                document.getElementById("passwordInput").value = "";
                canvas.style.display = "none";
                video.style.display = "block";
            } else {
                messageDiv.innerHTML = `<p style="color: red;">${data.message}</p>`;
            }
        })
        .catch(error => {
            console.error("Error during registration:", error);
            alert("An error occurred. Please try again.");
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
    const password = document.getElementById("loginPasswordInput").value;
    const otp = document.getElementById("otpInput").value; // OTP-ul, dacă este completat

    if (!username || !password) {
        alert("Please enter both username and password.");
        return;
    }

    const formData = new FormData();
    formData.append("username", username);
    formData.append("password", password);
    if (otp) {
        formData.append("otp", otp); // Adaugă OTP-ul dacă este completat
    }

    fetch("/login_with_credentials", {
        method: "POST",
        body: formData
    })
        .then(response => response.json())
        .then(data => {
            if (data.success && data.message === "OTP sent to your email. Please enter it to complete authentication.") {
                alert("OTP sent to your email. Please check your inbox.");
                document.getElementById("otpSection").style.display = "block"; // Afișează câmpul OTP
            } else if (data.success) {
                alert("Authentication successful!");
                window.location.href = "/success?user_name=" + username;
            } else {
                alert(data.message);
            }
        })
        .catch(error => {
            console.error("Error during login:", error);
            alert("An error occurred. Please try again.");
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
    const eventSelect = document.getElementById("eventSelect");
    const username = document.body.getAttribute("data-username");

    if (!username) {
        console.error("Error: User not logged in.");
        return;
    }

    fetch(`/my_events?user_name=${username}`)
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                eventSelect.innerHTML = "";
                const events = data.events;

                if (events.length === 0) {
                    const option = document.createElement("option");
                    option.text = "No events available";
                    option.disabled = true;
                    eventSelect.add(option);
                } else {
                    events.forEach(event => {
                        const option = document.createElement("option");
                        option.value = event;
                        option.text = event;
                        eventSelect.add(option);
                    });
                }
            } else {
                console.error("Error loading events:", data.message);
            }
        })
        .catch(error => {
            console.error("Error loading user events:", error);
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

function loadEvents() {
    console.log("Loading events..."); // Debugging
    fetch("/get_events")
        .then(response => response.json())
        .then(data => {
            console.log("Events received:", data.events); // Debugging
            const eventSelect = document.getElementById("eventSelect");
            eventSelect.innerHTML = ""; // Golește dropdown-ul

            if (data.events.length === 0) {
                const option = document.createElement("option");
                option.text = "No events available";
                option.disabled = true;
                eventSelect.add(option);
            } else {
                data.events.forEach(event => {
                    const option = document.createElement("option");
                    option.value = event;
                    option.text = event;
                    eventSelect.add(option);
                });
            }
        })
        .catch(error => console.error("Error loading events:", error));
}

function verifyAccess(eventName) {
    const canvas = document.getElementById("canvas");
    const context = canvas.getContext("2d");
    context.drawImage(video, 0, 0, canvas.width, canvas.height);
    const photo = dataURItoBlob(canvas.toDataURL());

    if (!photo) {
        alert("Photo is required.");
        return;
    }

    const formData = new FormData();
    formData.append("event_name", eventName);
    formData.append("photo", photo);

    fetch("/verify_access", {
        method: "POST",
        body: formData
    })
        .then(response => response.json())
        .then(data => {
            const resultDiv = document.getElementById("verificationResult");
            if (data.success) {
                resultDiv.innerHTML = `<p style="color: green;">${data.message}</p>`;
            } else {
                resultDiv.innerHTML = `<p style="color: red;">${data.message}</p>`;
            }
        })
        .catch(error => {
            console.error("Error during access verification:", error);
        });
}

document.addEventListener("DOMContentLoaded", () => {
    init(); // Inițializează camera
    loadEvents(); // Încarcă lista de evenimente pentru admin

    // Apelează `loadUserEvents` doar dacă elementul există
    if (document.getElementById("userEvents")) {
        loadUserEvents();
    }

    // Adaugă event listener pentru formularul de login
    const loginForm = document.getElementById("login-form");
    if (loginForm) {
        loginForm.addEventListener("submit", async function (event) {
            event.preventDefault();

            const formData = new FormData(this);
            const response = await fetch("/login_with_credentials", {
                method: "POST",
                body: formData,
            });

            const result = await response.json();
            if (result.success && result.message === "OTP sent to your email. Please enter it to complete authentication.") {
                alert("OTP sent to your email. Please check your inbox.");
                document.getElementById("otp-section").style.display = "block";
            } else if (result.success) {
                alert("Authentication successful!");
                window.location.href = "/success";
            } else {
                alert(result.message);
            }
        });
    } else {
        console.error("Login form not found in DOM.");
    }
});