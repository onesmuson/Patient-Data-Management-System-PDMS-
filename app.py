from flask import Flask, render_template, redirect, request, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from datetime import datetime
import random
import string

app = Flask(__name__)
app.config['SECRET_KEY'] = "yoursecretkey"
app.config['SQLALCHEMY_DATABASE_URI'] = "sqlite:///pdms.db"
db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))

class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150))
    age = db.Column(db.Integer)
    condition = db.Column(db.String(300))

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_name = db.Column(db.String(150))
    date = db.Column(db.String(50))

class Bill(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_name = db.Column(db.String(150))
    amount = db.Column(db.Integer)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# =============================
# LOGIN
# =============================
@app.route("/", methods=["GET", "POST"])
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user = User.query.filter_by(username=request.form["username"]).first()
        if user and user.password == request.form["password"]:
            login_user(user)
            return redirect(url_for("dashboard"))
        else:
            flash("Invalid Login Credentials", "danger")

    return render_template("login.html")


# =============================
# REGISTER
# =============================
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = User(username=username, password=password)
        db.session.add(user)
        db.session.commit()

        flash("Account created successfully!", "success")
        return redirect(url_for("login"))

    return render_template("register.html")


# =============================
# FORGOT PASSWORD
# =============================
@app.route("/forgot_password", methods=["GET", "POST"])
def forgot_password():
    if request.method == "POST":
        username = request.form["username"]
        user = User.query.filter_by(username=username).first()

        if not user:
            flash("Username not found", "danger")
            return redirect(url_for("forgot_password"))

        new_password = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        user.password = new_password
        db.session.commit()

        return render_template("forgot_result.html",
                               username=username,
                               new_password=new_password)

    return render_template("forgot_password.html")


# =============================
# DASHBOARD (Updated)
# =============================
@app.route("/dashboard")
@login_required
def dashboard():
    total_patients = Patient.query.count()
    total_appointments = Appointment.query.count()
    total_bills = Bill.query.count()
    today = datetime.now().strftime("%A, %d %B %Y")

    return render_template(
        "dashboard.html",
        username=current_user.username,
        total_patients=total_patients,
        total_appointments=total_appointments,
        total_bills=total_bills,
        today=today
    )


# =============================
# BILLING PAGE
# =============================
@app.route("/billing")
@login_required
def billing():
    bills = Bill.query.all()
    return render_template("billing.html", bills=bills)


# =============================
# APPOINTMENTS PAGE
# =============================
@app.route("/appointments")
@login_required
def appointments():
    appointments = Appointment.query.all()
    return render_template("appointments.html", appointments=appointments)


# =============================
# LOGOUT
# =============================
@app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for("login"))


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
