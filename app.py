from flask import Flask, render_template, request, redirect, url_for, flash
from flask_login import LoginManager, login_user, login_required, logout_user, UserMixin, current_user

app = Flask(__name__)
app.secret_key = "supersecretkey"

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# Dummy User class
class User(UserMixin):
    def __init__(self, id):
        self.id = id

# Dummy data
billing_records = []
appointments_list = []

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

@app.route("/")
def home():
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        user = User(username)
        login_user(user)
        return redirect(url_for("dashboard"))
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html",
                           username=current_user.id,
                           billing_count=len(billing_records),
                           appointment_count=len(appointments_list),
                           history_count=0)

@app.route("/billing", methods=["GET", "POST"])
@login_required
def billing():
    if request.method == "POST":
        patient_name = request.form["patient_name"]
        amount = request.form["amount"]
        description = request.form.get("description", "")
        billing_records.append({"id": len(billing_records)+1,
                                "patient_name": patient_name,
                                "amount": amount,
                                "description": description})
        flash("Billing added successfully!", "success")
        return redirect(url_for("billing"))
    return render_template("billing.html", bills=billing_records)

@app.route("/appointments", methods=["GET", "POST"])
@login_required
def appointments():
    if request.method == "POST":
        patient_name = request.form["patient_name"]
        date = request.form["date"]
        time = request.form["time"]
        appointments_list.append({"id": len(appointments_list)+1,
                                  "patient_name": patient_name,
                                  "date": date,
                                  "time": time})
        flash("Appointment added successfully!", "success")
        return redirect(url_for("appointments"))
    return render_template("appointments.html", appointments=appointments_list)

@app.route("/medical_history")
@login_required
def medical_history():
    return render_template("medical_history.html", histories=[])

@app.route("/reports")
@login_required
def reports():
    return render_template("reports.html")

@app.route("/patients")
@login_required
def patients():
    return render_template("patients.html")

@app.route("/reset_password", methods=["GET", "POST"])
@login_required
def reset_password():
    if request.method == "POST":
        flash("Password reset successfully!", "success")
        return redirect(url_for("dashboard"))
    return render_template("reset_password.html")

if __name__ == "__main__":
    app.run(debug=True)
