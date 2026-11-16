from datetime import datetime, date
from functools import wraps
import sqlite3
import os

from flask import Flask, render_template, request, redirect, url_for, flash, session, g
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "local-development-key-change-before-deployment")
DATABASE = "hospital.db"

# The database is stored in this project folder, not in the current terminal folder.
BASE_DIR = __import__("os").path.dirname(__file__)
DATABASE_PATH = __import__("os").path.join(BASE_DIR, DATABASE)


def get_db():
    if "db" not in g:
        g.db = sqlite3.connect(DATABASE_PATH)
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


@app.teardown_appcontext
def close_db(error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = sqlite3.connect(DATABASE_PATH)
    db.execute("PRAGMA foreign_keys = ON")
    db.executescript("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        email TEXT NOT NULL UNIQUE,
        password_hash TEXT NOT NULL,
        phone TEXT NOT NULL,
        role TEXT NOT NULL DEFAULT 'patient'
    );

    CREATE TABLE IF NOT EXISTS doctors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        specialization TEXT NOT NULL,
        available_days TEXT NOT NULL,
        consultation_fee REAL NOT NULL DEFAULT 0,
        active INTEGER NOT NULL DEFAULT 1
    );

    CREATE TABLE IF NOT EXISTS appointments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        patient_id INTEGER NOT NULL,
        doctor_id INTEGER NOT NULL,
        appointment_date TEXT NOT NULL,
        appointment_time TEXT NOT NULL,
        reason TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'Booked',
        created_at TEXT NOT NULL,
        FOREIGN KEY(patient_id) REFERENCES users(id),
        FOREIGN KEY(doctor_id) REFERENCES doctors(id)
    );
    """)

    admin = db.execute(
        "SELECT id FROM users WHERE email = ?", ("admin@hospital.com",)
    ).fetchone()
    if not admin:
        db.execute(
            """INSERT INTO users (name,email,password_hash,phone,role)
               VALUES (?,?,?,?,?)""",
            ("Hospital Admin", "admin@hospital.com",
             generate_password_hash("Admin@123"), "0000000000", "admin")
        )

    count = db.execute("SELECT COUNT(*) FROM doctors").fetchone()[0]
    if count == 0:
        db.executemany(
            """INSERT INTO doctors
               (name,specialization,available_days,consultation_fee)
               VALUES (?,?,?,?)""",
            [
                ("Dr. Ananya Rao", "General Medicine", "Mon, Tue, Wed, Fri", 400),
                ("Dr. Kiran Kumar", "Cardiology", "Tue, Thu, Sat", 700),
                ("Dr. Meera Shah", "Dermatology", "Mon, Wed, Fri", 500),
                ("Dr. Arjun Nair", "Pediatrics", "Mon, Tue, Thu, Sat", 450),
            ]
        )
    db.commit()
    db.close()


# Initialize the SQLite schema when the module is imported as well as when
# run directly. This is required by WSGI servers such as Gunicorn.
init_db()


def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "user_id" not in session:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped


def admin_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if session.get("role") != "admin":
            flash("Admin access is required.", "danger")
            return redirect(url_for("index"))
        return view(*args, **kwargs)
    return wrapped


def validate_appointment_slot(doctor, appointment_date, appointment_time):
    """Return an error message, or None when the selected slot passes validation."""
    try:
        selected_date = date.fromisoformat(appointment_date)
        selected_time = datetime.strptime(appointment_time, "%H:%M").time()
    except (TypeError, ValueError):
        return "Please enter a valid appointment date and time."

    if selected_date < date.today():
        return "Appointment date cannot be in the past."

    allowed_days = {
        day.strip()[:3].title()
        for day in doctor["available_days"].split(",")
        if day.strip()
    }
    if selected_date.strftime("%a") not in allowed_days:
        return "This doctor is not available on the selected day."

    opening_time = datetime.strptime("09:00", "%H:%M").time()
    closing_time = datetime.strptime("17:00", "%H:%M").time()
    if not opening_time <= selected_time <= closing_time:
        return "Appointments are available only between 9:00 AM and 5:00 PM."

    return None


def slot_is_taken(db, doctor_id, appointment_date, appointment_time, exclude_id=None):
    query = """
        SELECT id FROM appointments
        WHERE doctor_id = ?
          AND appointment_date = ?
          AND appointment_time = ?
          AND status = 'Booked'
    """
    params = [doctor_id, appointment_date, appointment_time]
    if exclude_id is not None:
        query += " AND id != ?"
        params.append(exclude_id)
    return db.execute(query, params).fetchone() is not None


@app.route("/")
def index():
    search = request.args.get("q", "").strip()
    db = get_db()
    if search:
        doctors = db.execute("""
            SELECT * FROM doctors
            WHERE active = 1
              AND (name LIKE ? OR specialization LIKE ?)
            ORDER BY name
        """, (f"%{search}%", f"%{search}%")).fetchall()
    else:
        doctors = db.execute(
            "SELECT * FROM doctors WHERE active=1 ORDER BY name"
        ).fetchall()
    return render_template("index.html", doctors=doctors, search=search)


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        phone = request.form.get("phone", "").strip()
        password = request.form.get("password", "")
        if not all([name, email, phone, password]):
            flash("Please complete every field.", "danger")
            return render_template("register.html")
        if len(password) < 6:
            flash("Password must contain at least 6 characters.", "danger")
            return render_template("register.html")
        try:
            db = get_db()
            db.execute(
                """INSERT INTO users (name,email,password_hash,phone)
                   VALUES (?,?,?,?)""",
                (name, email, generate_password_hash(password), phone)
            )
            db.commit()
            flash("Registration successful. Please log in.", "success")
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            flash("That email address is already registered.", "danger")
    return render_template("register.html")


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")
        user = get_db().execute(
            "SELECT * FROM users WHERE email=?", (email,)
        ).fetchone()
        if user and check_password_hash(user["password_hash"], password):
            session.clear()
            session["user_id"] = user["id"]
            session["name"] = user["name"]
            session["role"] = user["role"]
            flash(f"Welcome, {user['name']}!", "success")
            return redirect(
                url_for("admin_dashboard") if user["role"] == "admin"
                else url_for("patient_dashboard")
            )
        flash("Invalid email or password.", "danger")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("index"))


@app.route("/patient")
@login_required
def patient_dashboard():
    if session.get("role") != "patient":
        return redirect(url_for("admin_dashboard"))
    appointments = get_db().execute("""
        SELECT a.*, d.name AS doctor_name, d.specialization
        FROM appointments a
        JOIN doctors d ON a.doctor_id=d.id
        WHERE a.patient_id=?
        ORDER BY a.appointment_date DESC, a.appointment_time DESC
    """, (session["user_id"],)).fetchall()
    return render_template("patient_dashboard.html", appointments=appointments)


@app.route("/book", methods=["GET", "POST"])
@login_required
def book_appointment():
    if session.get("role") != "patient":
        return redirect(url_for("admin_dashboard"))

    db = get_db()
    doctors = db.execute(
        "SELECT * FROM doctors WHERE active=1 ORDER BY name"
    ).fetchall()

    if request.method == "POST":
        doctor_id = request.form.get("doctor_id", type=int)
        appt_date = request.form.get("appointment_date", "")
        appt_time = request.form.get("appointment_time", "")
        reason = request.form.get("reason", "").strip()

        doctor = db.execute(
            "SELECT * FROM doctors WHERE id=? AND active=1", (doctor_id,)
        ).fetchone() if doctor_id else None

        if not doctor or not reason:
            flash("Please select an active doctor and enter a reason.", "danger")
        else:
            error = validate_appointment_slot(doctor, appt_date, appt_time)
            if error:
                flash(error, "danger")
            elif slot_is_taken(db, doctor_id, appt_date, appt_time):
                flash("This doctor already has an appointment at that date and time.", "danger")
            else:
                db.execute("""
                    INSERT INTO appointments
                    (patient_id,doctor_id,appointment_date,appointment_time,
                     reason,status,created_at)
                    VALUES (?,?,?,?,?,'Booked',?)
                """, (
                    session["user_id"], doctor_id, appt_date, appt_time,
                    reason, datetime.now().isoformat(timespec="seconds")
                ))
                db.commit()
                flash("Appointment booked successfully.", "success")
                return redirect(url_for("patient_dashboard"))

    return render_template(
        "book.html", doctors=doctors, today=date.today().isoformat()
    )


@app.route("/reschedule/<int:appointment_id>", methods=["POST"])
@login_required
def reschedule_appointment(appointment_id):
    if session.get("role") != "patient":
        return redirect(url_for("admin_dashboard"))

    db = get_db()
    appointment = db.execute("""
        SELECT * FROM appointments
        WHERE id=? AND patient_id=? AND status='Booked'
    """, (appointment_id, session["user_id"])).fetchone()

    if not appointment:
        flash("Appointment not found or it cannot be rescheduled.", "danger")
        return redirect(url_for("patient_dashboard"))

    new_date = request.form.get("appointment_date", "")
    new_time = request.form.get("appointment_time", "")
    doctor = db.execute(
        "SELECT * FROM doctors WHERE id=? AND active=1",
        (appointment["doctor_id"],)
    ).fetchone()

    if not doctor:
        flash("This doctor is currently unavailable. Contact the hospital.", "danger")
        return redirect(url_for("patient_dashboard"))

    error = validate_appointment_slot(doctor, new_date, new_time)
    if error:
        flash(error, "danger")
        return redirect(url_for("patient_dashboard"))

    if slot_is_taken(
        db, appointment["doctor_id"], new_date, new_time,
        exclude_id=appointment_id
    ):
        flash("The selected slot is already booked. Choose another time.", "danger")
        return redirect(url_for("patient_dashboard"))

    db.execute("""
        UPDATE appointments
        SET appointment_date=?, appointment_time=?
        WHERE id=? AND patient_id=? AND status='Booked'
    """, (new_date, new_time, appointment_id, session["user_id"]))
    db.commit()
    flash("Appointment rescheduled successfully.", "success")
    return redirect(url_for("patient_dashboard"))


@app.route("/cancel/<int:appointment_id>", methods=["POST"])
@login_required
def cancel_appointment(appointment_id):
    db = get_db()
    if session.get("role") == "admin":
        db.execute(
            "UPDATE appointments SET status='Cancelled' WHERE id=? AND status='Booked'",
            (appointment_id,)
        )
    else:
        db.execute("""
            UPDATE appointments SET status='Cancelled'
            WHERE id=? AND patient_id=? AND status='Booked'
        """, (appointment_id, session["user_id"]))
    db.commit()
    flash("Appointment cancelled if it was eligible for cancellation.", "info")
    return redirect(
        url_for("admin_dashboard") if session.get("role") == "admin"
        else url_for("patient_dashboard")
    )


@app.route("/admin")
@login_required
@admin_required
def admin_dashboard():
    db = get_db()
    patients = db.execute(
        "SELECT COUNT(*) FROM users WHERE role='patient'"
    ).fetchone()[0]
    doctors = db.execute(
        "SELECT COUNT(*) FROM doctors WHERE active=1"
    ).fetchone()[0]
    booked = db.execute(
        "SELECT COUNT(*) FROM appointments WHERE status='Booked'"
    ).fetchone()[0]
    appointments = db.execute("""
        SELECT a.*, u.name AS patient_name,
               d.name AS doctor_name, d.specialization
        FROM appointments a
        JOIN users u ON a.patient_id=u.id
        JOIN doctors d ON a.doctor_id=d.id
        ORDER BY a.appointment_date DESC, a.appointment_time DESC
    """).fetchall()
    doctor_list = db.execute(
        "SELECT * FROM doctors ORDER BY active DESC, name"
    ).fetchall()
    return render_template(
        "admin_dashboard.html", patients=patients, doctors=doctors,
        booked=booked, appointments=appointments, doctor_list=doctor_list
    )


@app.route("/admin/doctors", methods=["POST"])
@login_required
@admin_required
def add_doctor():
    name = request.form.get("name", "").strip()
    specialization = request.form.get("specialization", "").strip()
    days = request.form.get("available_days", "").strip()
    fee = request.form.get("consultation_fee", type=float)

    if not name or not specialization or not days or fee is None or fee < 0:
        flash("Enter valid doctor details.", "danger")
    else:
        get_db().execute("""
            INSERT INTO doctors
            (name,specialization,available_days,consultation_fee)
            VALUES (?,?,?,?)
        """, (name, specialization, days, fee))
        get_db().commit()
        flash("Doctor added successfully.", "success")
    return redirect(url_for("admin_dashboard"))


@app.route("/admin/doctors/<int:doctor_id>/toggle", methods=["POST"])
@login_required
@admin_required
def toggle_doctor(doctor_id):
    db = get_db()
    db.execute(
        "UPDATE doctors SET active=CASE active WHEN 1 THEN 0 ELSE 1 END WHERE id=?",
        (doctor_id,)
    )
    db.commit()
    flash("Doctor availability updated.", "info")
    return redirect(url_for("admin_dashboard"))


@app.errorhandler(404)
def not_found(error):
    return render_template("404.html"), 404


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=False)
