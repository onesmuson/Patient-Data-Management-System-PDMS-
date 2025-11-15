import os
from flask import Flask, render_template, redirect, url_for, request, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__, static_folder='static', template_folder='templates')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///pdms.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

login_manager = LoginManager(app)
login_manager.login_view = 'login'

# ---------------------------
# Models
# ---------------------------
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(300), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(150), nullable=False)
    age = db.Column(db.Integer)
    gender = db.Column(db.String(20))
    contact = db.Column(db.String(50))
    address = db.Column(db.String(250))
    condition = db.Column(db.String(500))
    prescribed_drug = db.Column(db.String(250))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Medicine(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150))
    description = db.Column(db.String(250))
    dosage = db.Column(db.String(50))
    quantity = db.Column(db.Integer)

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'))
    patient = db.relationship('Patient', backref='appointments')
    date = db.Column(db.String(50))
    time = db.Column(db.String(50))
    reason = db.Column(db.String(250))

class Bill(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'))
    patient = db.relationship('Patient', backref='bills')
    total_amount = db.Column(db.Float)
    date_issued = db.Column(db.String(20))
    status = db.Column(db.String(50))

class MedicalHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'))
    patient = db.relationship('Patient', backref='histories')
    history = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150))
    email = db.Column(db.String(150))
    message = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# ---------------------------
# Login manager
# ---------------------------
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ---------------------------
# Helper: create DB and default admin
# ---------------------------
with app.app_context():
    db.create_all()
    if not User.query.filter_by(username="admin").first():
        admin = User(username="admin", password=generate_password_hash("admin123", method="sha256"))
        db.session.add(admin)
        db.session.commit()

# ---------------------------
# Routes
# ---------------------------
@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

# Register
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form.get('username').strip()
        password = request.form.get('password')
        if not username or not password:
            flash('Provide username and password', 'danger')
            return redirect(url_for('register'))
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'danger')
            return redirect(url_for('register'))
        hashed = generate_password_hash(password, method='sha256')
        u = User(username=username, password=hashed)
        db.session.add(u)
        db.session.commit()
        flash('Account created. You can now log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

# Login
@app.route('/login', methods=['GET', 'POST'])
def login():
    # if already logged in
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form.get('username').strip()
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash('Logged in successfully', 'success')
            next_page = request.args.get('next')
            return redirect(next_page or url_for('dashboard'))
        flash('Invalid username or password', 'danger')
        return redirect(url_for('login'))
    return render_template('login.html')

# Forgot password (no email) - user supplies username and new password -> shown on screen
@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        username = request.form.get('username').strip()
        new_password = request.form.get('new_password')
        confirm = request.form.get('confirm_password')
        if not username or not new_password:
            flash('Provide username and new password', 'danger')
            return redirect(url_for('forgot_password'))
        if new_password != confirm:
            flash('Passwords do not match', 'danger')
            return redirect(url_for('forgot_password'))
        user = User.query.filter_by(username=username).first()
        if not user:
            flash('Username not found', 'danger')
            return redirect(url_for('forgot_password'))
        user.password = generate_password_hash(new_password, method='sha256')
        db.session.commit()
        # show the success page (as requested: show on screen, not email)
        return render_template('forgot_result.html', username=username, new_password=new_password)
    return render_template('forgot_password.html')

# Logout
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out', 'info')
    return redirect(url_for('login'))

# Dashboard
@app.route('/dashboard')
@login_required
def dashboard():
    total_patients = Patient.query.count()
    total_medicines = Medicine.query.count()
    total_appointments = Appointment.query.count()
    total_bills = Bill.query.count()
    total_messages = Contact.query.count()
    recent_patients = Patient.query.order_by(Patient.created_at.desc()).limit(5).all()
    recent_appointments = Appointment.query.order_by(Appointment.id.desc()).limit(5).all()
    return render_template('dashboard.html',
                           total_patients=total_patients,
                           total_medicines=total_medicines,
                           total_appointments=total_appointments,
                           total_bills=total_bills,
                           total_messages=total_messages,
                           patients=recent_patients,
                           appointments=recent_appointments,
                           username=current_user.username)

# Patients (GET list + POST create)
@app.route('/patients', methods=['GET', 'POST'])
@login_required
def patients():
    if request.method == 'POST':
        try:
            full_name = request.form.get('full_name').strip()
            age = request.form.get('age') or None
            gender = request.form.get('gender') or None
            contact = request.form.get('contact') or None
            address = request.form.get('address') or None
            condition = request.form.get('condition') or None
            prescribed_drug = request.form.get('prescribed_drug') or None

            if not full_name:
                flash('Full name is required', 'danger')
                return redirect(url_for('patients'))

            p = Patient(
                full_name=full_name,
                age=int(age) if age else None,
                gender=gender,
                contact=contact,
                address=address,
                condition=condition,
                prescribed_drug=prescribed_drug
            )
            db.session.add(p)
            db.session.commit()
            flash('Patient added', 'success')
            return redirect(url_for('patients'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error adding patient: {e}', 'danger')
            return redirect(url_for('patients'))
    all_patients = Patient.query.order_by(Patient.id.desc()).all()
    return render_template('patients.html', patients=all_patients)

# Medicines
@app.route('/medicines', methods=['GET', 'POST'])
@login_required
def medicines():
    if request.method == 'POST':
        try:
            m = Medicine(
                name=request.form.get('name'),
                description=request.form.get('description'),
                dosage=request.form.get('dosage'),
                quantity=int(request.form.get('quantity') or 0)
            )
            db.session.add(m)
            db.session.commit()
            flash('Medicine added', 'success')
            return redirect(url_for('medicines'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {e}', 'danger')
            return redirect(url_for('medicines'))
    meds = Medicine.query.all()
    return render_template('medicines.html', medicines=meds)

# Appointments
@app.route('/appointments', methods=['GET', 'POST'])
@login_required
def appointments():
    patients_list = Patient.query.all()
    if request.method == 'POST':
        try:
            a = Appointment(
                patient_id=int(request.form.get('patient_id')),
                date=request.form.get('date'),
                time=request.form.get('time'),
                reason=request.form.get('reason')
            )
            db.session.add(a)
            db.session.commit()
            flash('Appointment added', 'success')
            return redirect(url_for('appointments'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {e}', 'danger')
            return redirect(url_for('appointments'))
    all_apps = Appointment.query.order_by(Appointment.id.desc()).all()
    return render_template('appointments.html', patients=patients_list, appointments=all_apps)

# Billing
@app.route('/billing', methods=['GET', 'POST'])
@login_required
def billing():
    try:
        patients_list = Patient.query.order_by(Patient.full_name).all()
        if request.method == 'POST':
            pid = request.form.get('patient_id')
            amount = request.form.get('total_amount')
            date_issued = request.form.get('date_issued') or datetime.utcnow().strftime('%Y-%m-%d')
            status = request.form.get('status') or 'Pending'
            if not pid or not amount:
                flash('Patient and amount are required', 'danger')
                return redirect(url_for('billing'))
            bill = Bill(patient_id=int(pid), total_amount=float(amount), date_issued=date_issued, status=status)
            db.session.add(bill)
            db.session.commit()
            flash('Bill added successfully', 'success')
            return redirect(url_for('billing'))
        bills = Bill.query.order_by(Bill.id.desc()).all()
        return render_template('billing.html', patients=patients_list, bills=bills)
    except Exception as e:
        db.session.rollback()
        flash('Something went wrong while loading billing data: ' + str(e), 'danger')
        return redirect(url_for('dashboard'))

# Contacts
@app.route('/contacts', methods=['GET', 'POST'])
@login_required
def contacts():
    if request.method == 'POST':
        try:
            c = Contact(name=request.form.get('name'), email=request.form.get('email'), message=request.form.get('message'))
            db.session.add(c)
            db.session.commit()
            flash('Message saved', 'success')
            return redirect(url_for('contacts'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {e}', 'danger')
            return redirect(url_for('contacts'))
    all_msgs = Contact.query.order_by(Contact.id.desc()).all()
    return render_template('contacts.html', messages=all_msgs)

# Medical history (list)
@app.route('/medical_history')
@login_required
def medical_history():
    histories = MedicalHistory.query.order_by(MedicalHistory.created_at.desc()).all()
    return render_template('medical_history.html', histories=histories)

# Add medical history
@app.route('/add_medical_history', methods=['GET', 'POST'])
@login_required
def add_medical_history():
    patients_list = Patient.query.all()
    if request.method == 'POST':
        try:
            mh = MedicalHistory(patient_id=int(request.form.get('patient_id')), history=request.form.get('history'))
            db.session.add(mh)
            db.session.commit()
            flash('Medical history added', 'success')
            return redirect(url_for('medical_history'))
        except Exception as e:
            db.session.rollback()
            flash(f'Error: {e}', 'danger')
            return redirect(url_for('add_medical_history'))
    return render_template('add_medical_history.html', patients=patients_list)

# Reports (placeholder)
@app.route('/reports')
@login_required
def reports():
    return render_template('reports.html')

# Reset password for logged-in users
@app.route('/reset_password', methods=['GET', 'POST'])
@login_required
def reset_password():
    if request.method == 'POST':
        new_password = request.form.get('new_password')
        confirm = request.form.get('confirm_password')
        if not new_password or new_password != confirm:
            flash('Passwords do not match or are empty', 'danger')
            return redirect(url_for('reset_password'))
        current_user.password = generate_password_hash(new_password, method='sha256')
        db.session.commit()
        flash('Password updated successfully', 'success')
        return redirect(url_for('dashboard'))
    return render_template('reset_password.html')

# ---------------------------
# Run
# ---------------------------
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
