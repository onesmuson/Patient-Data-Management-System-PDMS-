import os
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import (
    LoginManager,
    UserMixin,
    login_user,
    login_required,
    logout_user,
    current_user,
)
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "your-secret-key")
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get(
    "DATABASE_URL", "sqlite:///pdms.db"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"


# -----------------------
# Models
# -----------------------
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)


class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(150), nullable=False)
    age = db.Column(db.Integer, nullable=True)
    gender = db.Column(db.String(20), nullable=True)
    contact = db.Column(db.String(50), nullable=True)
    address = db.Column(db.String(200), nullable=True)
    condition = db.Column(db.String(200), nullable=True)
    prescribed_drug = db.Column(db.String(200), nullable=True)


class Medicine(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150))
    description = db.Column(db.String(200))
    dosage = db.Column(db.String(50))
    quantity = db.Column(db.Integer)


class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patient.id"))
    patient = db.relationship("Patient", backref="appointments")
    date = db.Column(db.String(20))
    time = db.Column(db.String(20))
    reason = db.Column(db.String(200))


class Bill(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patient.id"))
    patient = db.relationship("Patient", backref="bills")
    total_amount = db.Column(db.Float)
    date_issued = db.Column(db.String(20))
    status = db.Column(db.String(50))


class MedicalHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey("patient.id"))
    patient = db.relationship("Patient", backref="histories")
    history = db.Column(db.String(1000))


# -----------------------
# login loader & template helper
# -----------------------
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# Make current_user available always in templates (avoids Jinja undefined)
@app.context_processor
def inject_user():
    return dict(current_user=current_user)


# -----------------------
# Initialization (create tables, default admin)
# -----------------------
@app.before_first_request
def init_db():
    db.create_all()
    admin_pw = os.environ.get("ADMIN_PASSWORD", "admin123")
    if not User.query.filter_by(username="admin").first():
        admin = User(username="admin", password=generate_password_hash(admin_pw))
        db.session.add(admin)
        db.session.commit()


# -----------------------
# Routes
# -----------------------
@app.route("/")
def index():
    if current_user.is_authenticated:
        return redirect(url_for("dashboard"))
    return redirect(url_for("login"))


# --- Auth ---
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash("Logged in successfully", "success")
            nxt = request.args.get("next")
            return redirect(nxt or url_for("dashboard"))
        flash("Invalid credentials", "danger")
    return render_template("login.html")


@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form.get("username", "").strip()
        password = request.form.get("password", "")
        if not username or not password:
            flash("Provide username and password", "warning")
            return redirect(url_for("register"))
        if User.query.filter_by(username=username).first():
            flash("Username already exists", "danger")
            return redirect(url_for("register"))
        user = User(username=username, password=generate_password_hash(password))
        db.session.add(user)
        db.session.commit()
        flash("Account created — please login", "success")
        return redirect(url_for("login"))
    return render_template("register.html")


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


# --- Dashboard ---
@app.route("/dashboard")
@login_required
def dashboard():
    total_patients = Patient.query.count()
    total_medicines = Medicine.query.count()
    total_appointments = Appointment.query.count()
    total_bills = Bill.query.count()
    recent_patients = Patient.query.order_by(Patient.id.desc()).limit(5).all()
    recent_appointments = (
        Appointment.query.order_by(Appointment.id.desc()).limit(5).all()
    )
    return render_template(
        "dashboard.html",
        total_patients=total_patients,
        total_medicines=total_medicines,
        total_appointments=total_appointments,
        total_bills=total_bills,
        patients=recent_patients,
        appointments=recent_appointments,
    )


# --- Patients (list + create) ---
@app.route("/patients", methods=["GET", "POST"])
@login_required
def patients():
    if request.method == "POST":
        # create new patient
        p = Patient(
            full_name=request.form.get("full_name"),
            age=request.form.get("age") or None,
            gender=request.form.get("gender"),
            contact=request.form.get("contact"),
            address=request.form.get("address"),
            condition=request.form.get("condition"),
            prescribed_drug=request.form.get("prescribed_drug"),
        )
        db.session.add(p)
        db.session.commit()
        flash("Patient added", "success")
        return redirect(url_for("patients"))
    all_patients = Patient.query.order_by(Patient.id.desc()).all()
    return render_template("patients.html", patients=all_patients)


# --- Medicines ---
@app.route("/medicines")
@login_required
def medicines():
    meds = Medicine.query.all()
    return render_template("view_medicines.html", medicines=meds)


@app.route("/add_medicine", methods=["GET", "POST"])
@login_required
def add_medicine():
    if request.method == "POST":
        med = Medicine(
            name=request.form.get("name"),
            description=request.form.get("description"),
            dosage=request.form.get("dosage"),
            quantity=int(request.form.get("quantity") or 0),
        )
        db.session.add(med)
        db.session.commit()
        flash("Medicine added", "success")
        return redirect(url_for("medicines"))
    return render_template("add_medicine.html")


# --- Appointments ---
@app.route("/appointments", methods=["GET", "POST"])
@login_required
def appointments():
    if request.method == "POST":
        ap = Appointment(
            patient_id=int(request.form.get("patient_id")),
            date=request.form.get("date"),
            time=request.form.get("time"),
            reason=request.form.get("reason"),
        )
        db.session.add(ap)
        db.session.commit()
        flash("Appointment saved", "success")
        return redirect(url_for("appointments"))
    patients_list = Patient.query.all()
    all_apps = Appointment.query.order_by(Appointment.id.desc()).all()
    return render_template("appointment.html", patients=patients_list, appointments=all_apps)


# --- Billing (fixed) ---
@app.route("/billing", methods=["GET", "POST"])
@login_required
def billing():
    if request.method == "POST":
        try:
            patient_id = int(request.form.get("patient_id"))
            patient = Patient.query.get(patient_id)
            if not patient:
                flash("Select a valid patient", "danger")
                return redirect(url_for("billing"))
            bill = Bill(
                patient_id=patient.id,
                total_amount=float(request.form.get("total_amount")),
                date_issued=request.form.get("date_issued"),
                status=request.form.get("status"),
            )
            db.session.add(bill)
            db.session.commit()
            flash("Bill added", "success")
            return redirect(url_for("billing"))
        except Exception as e:
            db.session.rollback()
            flash("Error saving bill: " + str(e), "danger")
            return redirect(url_for("billing"))
    patients_list = Patient.query.all()
    bills = Bill.query.order_by(Bill.id.desc()).all()
    return render_template("billing.html", patients=patients_list, bills=bills)


# --- Medical history ---
@app.route("/medical_history", methods=["GET", "POST"])
@login_required
def medical_history():
    if request.method == "POST":
        history = MedicalHistory(
            patient_id=int(request.form.get("patient_id")),
            history=request.form.get("history"),
        )
        db.session.add(history)
        db.session.commit()
        flash("Medical history saved", "success")
        return redirect(url_for("medical_history"))
    patients_list = Patient.query.all()
    histories = MedicalHistory.query.order_by(MedicalHistory.id.desc()).all()
    return render_template(
        "medical_history.html", patients=patients_list, histories=histories
    )


# --- Reports placeholder ---
@app.route("/reports")
@login_required
def reports():
    return render_template("reports.html")


# --- Reset password (logged-in) ---
@app.route("/reset_password", methods=["GET", "POST"])
@login_required
def reset_password():
    if request.method == "POST":
        new_pw = request.form.get("new_password")
        confirm = request.form.get("confirm_password")
        if new_pw != confirm:
            flash("Passwords do not match", "danger")
            return redirect(url_for("reset_password"))
        current_user.password = generate_password_hash(new_pw)
        db.session.commit()
        flash("Password updated", "success")
        return redirect(url_for("dashboard"))
    return render_template("reset_password.html")


# --- Forgot password (unauthenticated, screen-based) ---
@app.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    # WARNING: This changes password immediately without verification.
    if request.method == "POST":
        username = request.form.get("username")
        new_pw = request.form.get("new_password")
        confirm = request.form.get("confirm_password")
        if new_pw != confirm:
            flash("Passwords do not match", "danger")
            return redirect(url_for("forgot_password"))
        user = User.query.filter_by(username=username).first()
        if not user:
            flash("User not found", "warning")
            return redirect(url_for("forgot_password"))
        user.password = generate_password_hash(new_pw)
        db.session.commit()
        flash("Password reset for user. Please login with new password.", "success")
        return redirect(url_for("login"))
    return render_template("forgot_password.html")


# -----------------------
# Run
# -----------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)), debug=True)
