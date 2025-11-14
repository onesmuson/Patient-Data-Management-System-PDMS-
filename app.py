from flask import Flask, render_template, redirect, url_for
from flask_login import LoginManager, login_required, login_user, logout_user, UserMixin

app = Flask(__name__)
app.secret_key = "your_secret_key_here"

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"

# Dummy user class for example
class User(UserMixin):
    def __init__(self, id):
        self.id = id

@login_manager.user_loader
def load_user(user_id):
    return User(user_id)

# ---------------- Routes ----------------

@app.route("/")
def home():
    return redirect(url_for("login"))

@app.route("/login")
def login():
    user = User(id=1)
    login_user(user)
    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))

@app.route("/dashboard")
@login_required
def dashboard():
    return render_template("dashboard.html")

@app.route("/patients")
@login_required
def patients():
    return render_template("patients.html")

@app.route("/billing")
@login_required
def billing():
    bills = [
        {"id": 1, "name": "John Doe", "amount": 100},
        {"id": 2, "name": "Jane Smith", "amount": 200},
    ]
    return render_template("billing.html", bills=bills)

@app.route("/appointments")
@login_required
def appointments():
    appointments = [
        {"id": 1, "patient": "John Doe", "date": "2025-11-20"},
        {"id": 2, "patient": "Jane Smith", "date": "2025-11-22"},
    ]
    return render_template("appointments.html", appointments=appointments)

@app.route("/medical_history")
@login_required
def medical_history():
    return render_template("medical_history.html")

@app.route("/reports")
@login_required
def reports():
    return render_template("reports.html")

@app.route("/reset_password")
@login_required
def reset_password():
    return render_template("reset_password.html")

# ---------------- Run App ----------------
if __name__ == "__main__":
    app.run(debug=True)
