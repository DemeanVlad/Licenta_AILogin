### **Descrierea aplicației: Face Recognition Event Manager**

Aplicația **Face Recognition Event Manager** este o platformă web care utilizează recunoașterea facială pentru autentificare și gestionarea evenimentelor. Este construită folosind **Flask** pentru backend, **SQLite** pentru stocarea datelor, și **HTML, CSS, JavaScript** pentru frontend. Aplicația permite utilizatorilor să se înregistreze, să se autentifice și să participe la evenimente, oferind și o interfață de administrare pentru verificarea accesului la evenimente.

---

### **Funcționalități principale**

#### **1. Înregistrare utilizatori**
- Utilizatorii se pot înregistra oferind:
  - Un nume de utilizator unic.
  - O parolă.
  - O fotografie pentru recunoașterea facială.
- Aplicația:
  - Salvează fotografia utilizatorului în directorul uploads.
  - Extrage vectorul facial folosind biblioteca `face_recognition` și îl stochează în baza de date.
  - Hash-uiește parola utilizatorului pentru securitate.

#### **2. Autentificare utilizatori**
- **Autentificare cu recunoaștere facială**:
  - Utilizatorul încarcă o fotografie.
  - Aplicația compară vectorul facial extras din fotografie cu vectorii stocați în baza de date.
  - Dacă există o potrivire, utilizatorul este autentificat.
- **Autentificare cu username și parolă**:
  - Utilizatorul introduce numele de utilizator și parola.
  - Aplicația verifică parola hash-uită din baza de date.
  - Suportă autentificarea pentru utilizatori obișnuiți și administratori.

#### **3. Gestionarea evenimentelor**
- **Vizualizarea evenimentelor disponibile**:
  - Utilizatorii pot vedea o listă de evenimente disponibile și se pot înscrie la acestea.
- **Evenimentele utilizatorului**:
  - Utilizatorii pot vedea evenimentele la care s-au înscris.
- **Adăugarea evenimentelor**:
  - Utilizatorii pot adăuga evenimente la lista lor personală.

#### **4. Interfața de administrare**
- Administratorii pot:
  - Vizualiza toate evenimentele disponibile.
  - Verifica accesul utilizatorilor la evenimente folosind recunoașterea facială.
  - Accesul este verificat prin compararea vectorului facial al utilizatorului cu vectorii stocați pentru evenimentul selectat.

#### **5. Calendar pentru evenimentele utilizatorului**
- Utilizatorii pot vedea evenimentele lor într-un calendar interactiv (implementabil cu FullCalendar).
- Evenimentele sunt afișate în funcție de data lor.

---

### **Structura aplicației**

#### **Backend (Flask)**
- **Rute principale**:
  - `/register`: Înregistrează utilizatorii.
  - `/login`: Autentificare cu recunoaștere facială.
  - `/login_with_credentials`: Autentificare cu username și parolă.
  - `/admin`: Interfața de administrare.
  - `/verify_access`: Verifică accesul utilizatorilor la evenimente.
  - `/get_events`: Returnează lista de evenimente disponibile.
  - `/my_events`: Gestionarea evenimentelor utilizatorului.
  - `/profile`: Vizualizarea profilului utilizatorului.
- **Baza de date**:
  - Tabela `users`:
    - `username`: Nume de utilizator unic.
    - `password`: Parola hash-uită.
    - `face_encoding`: Vectorul facial al utilizatorului.
    - `role`: Rolul utilizatorului (`user` sau `admin`).
  - Tabela `user_events`:
    - `username`: Legătura cu utilizatorul.
    - `event_name`: Numele evenimentului.

#### **Frontend**
- **Pagini HTML**:
  - index.html: Pagina principală pentru autentificare și înregistrare.
  - success.html: Pagina de succes după autentificare.
  - `my_events.html`: Pagina pentru gestionarea evenimentelor utilizatorului.
  - admin.html: Interfața de administrare.
  - `profile.html`: Profilul utilizatorului.
- **CSS**:
  - Stiluri moderne pentru navbar, butoane și secțiuni.
  - Suport pentru layout-uri responsive.
- **JavaScript**:
  - Funcții pentru capturarea imaginilor, gestionarea evenimentelor și interacțiunea cu backend-ul.

---

### **Fluxul aplicației**

1. **Înregistrare**:
   - Utilizatorul completează formularul de înregistrare și încarcă o fotografie.
   - Aplicația salvează datele utilizatorului și vectorul facial în baza de date.

2. **Autentificare**:
   - Utilizatorul se autentifică fie cu recunoaștere facială, fie cu username și parolă.
   - După autentificare, utilizatorul este redirecționat către pagina de succes.

3. **Gestionarea evenimentelor**:
   - Utilizatorul poate vizualiza evenimentele disponibile și se poate înscrie la acestea.
   - Evenimentele utilizatorului sunt afișate într-un calendar interactiv.

4. **Interfața de administrare**:
   - Administratorii pot verifica accesul utilizatorilor la evenimente folosind recunoașterea facială.

---

### **Tehnologii utilizate**

- **Backend**:
  - Flask: Framework pentru gestionarea rutelor și logica aplicației.
  - SQLite: Baza de date pentru stocarea utilizatorilor și evenimentelor.
  - `face_recognition`: Bibliotecă pentru procesarea imaginilor și recunoașterea facială.
  - Werkzeug: Pentru hash-uirea parolelor.

- **Frontend**:
  - HTML, CSS, JavaScript: Pentru interfața utilizatorului.
  - FullCalendar (opțional): Pentru afișarea evenimentelor într-un calendar.

---

### **Posibile îmbunătățiri**

1. **Notificări pentru utilizatori**:
   - Adaugă notificări pentru evenimentele viitoare (de exemplu, prin e-mail sau notificări push).

2. **Suport pentru mai multe limbi**:
   - Adaugă suport pentru traduceri pentru a face aplicația accesibilă unui public mai larg.

3. **Statistici pentru administratori**:
   - Oferă statistici despre utilizatori și evenimente (de exemplu, numărul de participanți la un eveniment).

4. **Integrare cu servicii externe**:
   - Integrează aplicația cu servicii de plată pentru evenimente plătite.

5. **Securitate îmbunătățită**:
   - Adaugă autentificare cu doi factori (2FA) pentru utilizatori.

---

Dacă dorești să implementezi alte funcționalități sau să îmbunătățești aplicația, spune-mi și te voi ajuta! 😊
