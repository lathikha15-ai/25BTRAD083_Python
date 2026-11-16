# CarePoint – Hospital Appointment Management System

An intermediate-level academic web application built with Python Flask, SQLite, HTML and CSS.

## Features
- Patient registration and login with hashed passwords
- Search active doctors by doctor name or specialization
- Doctor directory with specialization, working days and consultation fee
- Appointment booking with validation of future date, doctor's working day and clinic hours (9 AM–5 PM)
- Prevents booking an already occupied doctor/date/time slot
- Patient appointment history and cancellation
- Patient appointment rescheduling with the same availability and duplicate-slot validation
- Admin dashboard with patient, active doctor and booked appointment counts
- Admin can add doctors and activate/deactivate doctor profiles

## Requirements
- Python 3.10+
- VS Code recommended

## Run on Windows
Open this folder in VS Code, then Terminal > New Terminal:

```powershell
py -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5000` in your browser.

If PowerShell blocks activation, run this in the current terminal and activate again:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

## Demo admin login
- Email: `admin@hospital.com`
- Password: `Admin@123`

Change the demo password and Flask SECRET_KEY before deployment. The demo admin account is created automatically on first run.

## Database
SQLite database file: `hospital.db` (created automatically inside this project folder).

Tables:
- `users`: patient and administrator accounts
- `doctors`: doctor profile, specialization, working days, fee and active status
- `appointments`: patient, doctor, date, time, reason and booking status

## Test checklist
1. Open the homepage and view the active doctor directory.
2. Search by a doctor name, e.g. `Ananya`, and by specialization, e.g. `Cardiology`.
3. Register a patient and log in.
4. Book on a working day for the selected doctor, within 9 AM–5 PM.
5. Try a non-working day and confirm the application rejects it.
6. Try a time outside clinic hours and confirm it is rejected.
7. Try to book the same doctor/date/time twice; the second booking should be rejected.
8. Reschedule a booked appointment to a valid free slot.
9. Try rescheduling to a non-working day or an occupied slot; both should be rejected.
10. Cancel an appointment and confirm the status changes to Cancelled.
11. Log in as admin, add a doctor, and deactivate/reactivate a doctor.

## Team division (5 members)
1. Patient management: registration, login and patient dashboard
2. Doctor management: doctor directory, search and admin doctor management
3. Appointment management: booking, rescheduling, cancellation and validation
4. Database management: schema, SQL queries, data integrity and test cases
5. Integration and interface: Flask integration, HTML/CSS, admin dashboard, README and GitHub coordination

All members should understand the complete workflow and make meaningful contributions/commits. Follow the instructor's requirements for each member's GitHub repository.

## GitHub upload
Create a repository on GitHub. Do not initialize it with another README if this folder already contains one.

From this project folder, run:

```powershell
git init
git add .
git commit -m "Hospital appointment system with search and rescheduling"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/hospital-appointment-management-system.git
git push -u origin main
```

Replace `YOUR-USERNAME` with your GitHub username. If Git reports that a remote named `origin` already exists, use `git remote set-url origin https://github.com/YOUR-USERNAME/hospital-appointment-management-system.git`.

## Academic prototype notice
This project is for learning and demonstration only. Do not use real patient data. Before production use, it would require stronger security (including CSRF protection), robust concurrent booking protection, audit logging, privacy controls and deployment hardening.


## Deploy on Render (public demo)
1. Push this project folder to a GitHub repository.
2. In Render, create a **New Web Service** and connect that GitHub repository.
3. Set **Build Command** to `pip install -r requirements.txt`.
4. Set **Start Command** to `gunicorn app:app --bind 0.0.0.0:$PORT`.
5. Add an environment variable named `SECRET_KEY` with a long random value.
6. Deploy. Render will provide a public `https://...onrender.com` URL.

**Demo database note:** This project uses SQLite. On Render's free web service, local files are not persistent across service restarts/redeploys, so newly registered patients and appointments may reset. Use only dummy data for the academic demo. For durable records, configure persistent storage or migrate to a managed database before relying on it.

**Security note:** This is an academic prototype, not suitable for real patient information or production healthcare use.
