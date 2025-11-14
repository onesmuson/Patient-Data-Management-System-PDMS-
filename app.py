from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your-secret-key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pdms.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# -------------------------------------------------
# DATABASE MODELS
# -------------------------------------------------
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(150), nullable=False)
    age = db.Column(db.String(10), nullable=False)
    gender = db.Column(db.String(50), nullable=False)
    contact = db.Column(db.String(150), nullable=False)
    address = db.Column(db.String(250), nullable=False)
    condition = db.Column(db.String(250), nullable=False)
    prescribed_drug = db.Column(db.String(250))

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

# -------------------------------------------------
# USER LOADER
# -------------------------------------------------
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# -------------------------------------------------
# ROUTES
# -------------------------------------------------

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

# ---------------------- LOGIN ----------------------
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
            flash("Invalid username or password", "danger")
            return redirect(url_for('login'))

    return render_template('login.html')

# ---------------------- REGISTER ----------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get("username")
        password = request.form.get("password")

        if User.query.filter_by(username=username).first():
            flash("Username already exists", "danger")
            return redirect(url_for('register'))

        hashed = generate_password_hash(password, method='sha256')
        new_user = User(username=username, password=hashed)
        db.session.add(new_user)
        db.session.commit()
        flash("Registration Successful! Please log in.", "success")
        return redirect(url_for('login'))

    return render_template('register.html')

# ---------------------- LOGOUT ----------------------
@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# ---------------------- DASHBOARD ----------------------
@app.route('/dashboard')
@login_required
def dashboard():
    # counts
    patient_count = Patient.query.count()
    billing_count = Billing.query.count()
    appointment_count = Appointment.query.count()
    history_count = MedicalHistory.query.count()

    return render_template(
        'dashboard.html',
        welcome=current_user.username,
        patient_count=patient_count,
        billing_count=billing_count,
        appointment_count=appointment_count,
        history_count=history_count
    )

# ---------------------- PATIENTS ----------------------
@app.route('/patients', methods=['GET', 'POST'])
@login_required
def patients():
    if request.method == 'POST':
        full_name = request.form.get('full_name')
        age = request.form.get('age')
        gender = request.form.get('gender')
        contact = request.form.get('contact')
        address = request.form.get('address')
        condition = request.form.get('condition')
        drug = request.form.get('prescribed_drug')

        new_patient = Patient(
            full_name=full_name,
            age=age,
            gender=gender,
            contact=contact,
            address=address,
            condition=condition,
            prescribed_drug=drug
        )
        db.session.add(new_patient)
        db.session.commit()
        flash("New patient added successfully!", "success")
        return redirect(url_for('patients'))

    patients = Patient.query.all()
    return render_template('patients.html', patients=patients)

# ---------------------- BILLING ----------------------
@app.route('/billing', methods=['GET', 'POST'])
@login_required
def billing():
    try:
        if request.method == 'POST':
            patient_name = request.form.get('patient_name')
            amount = float(request.form.get('amount'))
            description = request.form.get('description')

            new_bill = Billing(
                patient_name=patient_name,
                amount=amount,
                description=description
            )
            db.session.add(new_bill)
            db.session.commit()

            flash("Billing record added!", "success")
            return redirect(url_for('billing'))

        bills = Billing.query.all()
        return render_template('billing.html', bills=bills)

    except Exception as e:
        return f"Billing Error: {str(e)}"

# ---------------------- RESET PASSWORD ----------------------
@app.route('/reset_password', methods=['GET', 'POST'])
@login_required
def reset_password():
    if request.method == 'POST':
        new = request.form.get('new_password')
        confirm = request.form.get('confirm_password')

        if new != confirm:
            flash('Passwords do not match', 'danger')
            return redirect(url_for('reset_password'))

        current_user.password = generate_password_hash(new, method='sha256')
        db.session.commit()
        flash('Password updated successfully!', 'success')
        return redirect(url_for('dashboard'))

    return render_template('reset_password.html')

# ---------------------- APPOINTMENTS ----------------------
@app.route('/appointments')
@login_required
def appointments():
    ap = Appointment.query.all()
    return render_template('appointments.html', appointments=ap)

# ---------------------- MEDICAL HISTORY ----------------------
@app.route('/medical_history')
@login_required
def medical_history():
    histories = MedicalHistory.query.all()
    return render_template('medical_history.html', histories=histories)

# ---------------------- REPORTS ----------------------
@app.route('/reports')
@login_required
def reports():
    return render_template('reports.html')

# -------------------------------------------------
# CREATE DB + DEFAULT ADMIN
# -------------------------------------------------
with app.app_context():
    db.create_all()

    # create admin if missing
    if not User.query.filter_by(username="admin").first():
        admin = User(username="admin", password=generate_password_hash("admin123", method="sha256"))
        db.session.add(admin)
        db.session.commit()

# -------------------------------------------------
# RUN APP
# -------------------------------------------------
if __name__ == '__main__':
    app.run(debug=True)
