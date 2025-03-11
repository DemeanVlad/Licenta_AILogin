let video;
let canvas;
let nameInput;
let emailInput;
let passwordInput;

function init(){
    //and now if you run it will open instant camera
    video = document.getElementById("video");
    canvas = document.getElementById("canvas");
    nameInput = document.getElementById("nameInput");
    emailInput = document.getElementById("emailInput");
    passwordInput = document.getElementById("passwordInput");

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
function register(){
    const name = nameInput.value;
    const email = emailInput.value;
    const password = passwordInput.value;
    const photo = dataURItoBlob(canvas.toDataURL());

    if(!name || !email || !password || !photo){
        alert("All fields are required");
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
    .then(data =>{
        if(data.success){
            alert("Registration successful");
            window.location.href = "/";
        }else{
            alert("Registration failed");
        }
    })
    .catch(error => {
        console.log("error", error);
    });
}

function login(){
    const email = emailInput.value;
    const password = passwordInput.value;
    const context = canvas.getContext("2d");
    context.drawImage(video, 0, 0, canvas.width, canvas.height);
    const photo = dataURItoBlob(canvas.toDataURL());

    if(!email || !password || !photo){
        alert("All fields are required");
        return;
    }
    const formData = new FormData();
    formData.append("email", email);
    formData.append("password", password);
    formData.append("photo", photo, "login.jpg");

    fetch("/login", {
        method: "POST",
        body: formData
    })
    .then(response => response.json())
    .then(data =>{
        console.log(data);
        if(data.success){
            alert("Login successful");
            window.location.href = "/success?user_name=" + nameInput.value;
        }else{
            alert("Login failed");
        }
    }).catch(error =>{
        console.log("error", error);
    });
}

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