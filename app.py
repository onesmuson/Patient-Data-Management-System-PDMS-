from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

# ---------------------------
# App Configuration
# ---------------------------
app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pdms.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# ---------------------------
# Database Models
# ---------------------------
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

class Billing(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_name = db.Column(db.String(150), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.String(250))

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_name = db.Column(db.String(150), nullable=False)
    date = db.Column(db.String(50), nullable=False)
    time = db.Column(db.String(50), nullable=False)

class MedicalHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_name = db.Column(db.String(150), nullable=False)
    history = db.Column(db.Text, nullable=False)

# ---------------------------
# User Loader
# ---------------------------
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ---------------------------
# Routes
# ---------------------------

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))


# ---------------------------
# Login
# ---------------------------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'danger')
            return redirect(url_for('login'))

    return render_template('login.html')


# ---------------------------
# Logout
# ---------------------------
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


# ---------------------------
# Dashboard
# ---------------------------
@app.route('/dashboard')
@login_required
def dashboard():
    billing_count = Billing.query.count()
    appointment_count = Appointment.query.count()
    history_count = MedicalHistory.query.count()
    return render_template(
        'dashboard.html',
        billing_count=billing_count,
        appointment_count=appointment_count,
        history_count=history_count,
        username=current_user.username
    )


# ---------------------------
# Billing Route
# ---------------------------
@app.route('/billing', methods=['GET', 'POST'])
@login_required
def billing():
    try:
        if request.method == 'POST':
            patient_name = request.form.get('patient_name')
            amount = request.form.get('amount')
            description = request.form.get('description')

            if not amount:
                flash("Amount is required.", "danger")
                return redirect(url_for('billing'))

            new_bill = Billing(
                patient_name=patient_name,
                amount=float(amount),
                description=description
            )
            db.session.add(new_bill)
            db.session.commit()
            flash('Billing added successfully!', 'success')
            return redirect(url_for('billing'))

        bills = Billing.query.all()
        return render_template('billing.html', bills=bills)

    except Exception as e:
        return f"Billing Error: {e}", 500


# ---------------------------
# Reset Password (No Email)
# ---------------------------
@app.route('/reset_password', methods=['GET', 'POST'])
@login_required
def reset_password():
    if request.method == 'POST':
        new_password = request.form.get('new_password')
        confirm_password = request.form.get('confirm_password')

        if new_password != confirm_password:
            flash('Passwords do not match!', 'danger')
            return redirect(url_for('reset_password'))

        current_user.password = generate_password_hash(new_password, method='sha256')
        db.session.commit()

        flash('Password updated successfully!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('reset_password.html')


# ---------------------------
# Appointments
# ---------------------------
@app.route('/appointments')
@login_required
def appointments():
    appointments = Appointment.query.all()
    return render_template('appointments.html', appointments=appointments)


# ---------------------------
# Medical History
# ---------------------------
@app.route('/medical_history')
@login_required
def medical_history():
    histories = MedicalHistory.query.all()
    return render_template('medical_history.html', histories=histories)


# ---------------------------
# Reports
# ---------------------------
@app.route('/reports')
@login_required
def reports():
    return render_template('reports.html')


# ---------------------------
# Create Database + Default Admin
# ---------------------------
with app.app_context():
    db.create_all()

    if not User.query.filter_by(username="admin").first():
        admin = User(
            username="admin",
            password=generate_password_hash("admin123", method="sha256")
        )
        db.session.add(admin)
        db.session.commit()


# ---------------------------
# Run App
# ---------------------------
if __name__ == '__main__':
    app.run(debug=True)
