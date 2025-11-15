import os
from datetime import datetime
from flask import Flask, render_template, redirect, url_for, request, flash, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user, AnonymousUserMixin
from werkzeug.security import generate_password_hash, check_password_hash

# ---------------------------
# App Configuration
# ---------------------------
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'super-secret-key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///pdms.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'danger'

# ---------------------------
# Models
# ---------------------------
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(150), nullable=False)
    age = db.Column(db.Integer)
    gender = db.Column(db.String(20))
    contact = db.Column(db.String(50))
    address = db.Column(db.String(300))
    condition = db.Column(db.String(300))
    prescribed_drug = db.Column(db.String(200))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Medicine(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150))
    description = db.Column(db.String(300))
    dosage = db.Column(db.String(50))
    quantity = db.Column(db.Integer)

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'))
    patient = db.relationship('Patient', backref='appointments')
    date = db.Column(db.String(50))
    time = db.Column(db.String(50))
    reason = db.Column(db.String(300))

class Bill(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'))
    patient = db.relationship('Patient', backref='bills')
    total_amount = db.Column(db.Float)
    date_issued = db.Column(db.String(50))
    status = db.Column(db.String(50), default='Pending')

class MedicalHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'))
    patient = db.relationship('Patient', backref='histories')
    history = db.Column(db.String(1000))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150))
    email = db.Column(db.String(150))
    message = db.Column(db.String(1000))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

# ---------------------------
# User loader
# ---------------------------
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ---------------------------
# Create DB & default admin
# ---------------------------
with app.app_context():
    db.create_all()
    # Create default admin if not exists
    admin_username = os.environ.get('ADMIN_USERNAME', 'admin')
    admin_password = os.environ.get('ADMIN_PASSWORD', 'admin123')
    if not User.query.filter_by(username=admin_username).first():
        user = User(username=admin_username, password=generate_password_hash(admin_password, method='sha256'))
        db.session.add(user)
        db.session.commit()

# ---------------------------
# Routes
# ---------------------------

@app.route('/')
def home():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

# ----- Register -----
@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form.get('username').strip()
        password = request.form.get('password')
        confirm = request.form.get('confirm_password')
        if not username or not password:
            flash('Please fill username and password', 'danger')
            return redirect(url_for('register'))
        if password != confirm:
            flash('Passwords do not match', 'danger')
            return redirect(url_for('register'))
        if User.query.filter_by(username=username).first():
            flash('Username already exists', 'danger')
            return redirect(url_for('register'))
        new_user = User(username=username, password=generate_password_hash(password, method='sha256'))
        db.session.add(new_user)
        db.session.commit()
        flash('Account created. Please login.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

# ----- Login -----
@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form.get('username').strip()
        password = request.form.get('password')
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            flash(f'Welcome back, {user.username}!', 'success')
            nxt = request.args.get('next')
            return redirect(nxt or url_for('dashboard'))
        flash('Invalid username or password', 'danger')
        return redirect(url_for('login'))
    return render_template('login.html')

# ----- Forgot password (screen-based) -----
@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    # Does not email: user supplies username and new password to reset (screen-based)
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        username = request.form.get('username').strip()
        new_password = request.form.get('new_password')
        confirm = request.form.get('confirm_password')
        if not username or not new_password:
            flash('Please fill both fields.', 'danger')
            return redirect(url_for('forgot_password'))
        if new_password != confirm:
            flash('Passwords do not match.', 'danger')
            return redirect(url_for('forgot_password'))
        user = User.query.filter_by(username=username).first()
        if not user:
            flash('No user with that username.', 'danger')
            return redirect(url_for('forgot_password'))
        user.password = generate_password_hash(new_password, method='sha256')
        db.session.commit()
        flash('Password reset successful. You can now login.', 'success')
        return redirect(url_for('login'))
    return render_template('forgot_password.html')

# ----- Logout -----
@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('login'))

# ----- Dashboard -----
@app.route('/dashboard')
@login_required
def dashboard():
    stats = {
        'total_patients': Patient.query.count(),
        'total_medicines': Medicine.query.count(),
        'total_appointments': Appointment.query.count(),
        'total_bills': Bill.query.count(),
        'total_messages': Contact.query.count()
    }
    recent_patients = Patient.query.order_by(Patient.created_at.desc()).limit(5).all()
    recent_appointments = Appointment.query.order_by(Appointment.id.desc()).limit(5).all()
    welcome = f"Welcome {current_user.username} — Manage patients, appointments and billing from this dashboard."
    return render_template('dashboard.html',
                           stats=stats,
                           patients=recent_patients,
                           appointments=recent_appointments,
                           welcome=welcome)

# ----- Patients (GET to view, POST to add) -----
@app.route('/patients', methods=['GET', 'POST'])
@login_required
def patients():
    if request.method == 'POST':
        full_name = request.form.get('full_name').strip()
        age = request.form.get('age') or None
        gender = request.form.get('gender')
        contact = request.form.get('contact')
        address = request.form.get('address')
        condition = request.form.get('condition')
        prescribed_drug = request.form.get('prescribed_drug')
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
        flash('Patient added successfully', 'success')
        return redirect(url_for('patients'))
    all_patients = Patient.query.order_by(Patient.id.desc()).all()
    return render_template('patients.html', patients=all_patients)

# ----- Patient details -----
@app.route('/patient/<int:patient_id>')
@login_required
def patient_details(patient_id):
    p = Patient.query.get_or_404(patient_id)
    return render_template('patient_details.html', patient=p)

# ----- Medicines -----
@app.route('/medicines', methods=['GET', 'POST'])
@login_required
def medicines():
    if request.method == 'POST':
        name = request.form.get('name')
        description = request.form.get('description')
        dosage = request.form.get('dosage')
        quantity = request.form.get('quantity') or 0
        med = Medicine(name=name, description=description, dosage=dosage, quantity=int(quantity))
        db.session.add(med)
        db.session.commit()
        flash('Medicine added', 'success')
        return redirect(url_for('medicines'))
    meds = Medicine.query.all()
    return render_template('medicines.html', medicines=meds)

# ----- Appointments (create & list) -----
@app.route('/appointments', methods=['GET', 'POST'])
@login_required
def appointments():
    patients_list = Patient.query.all()
    if request.method == 'POST':
        patient_id = int(request.form.get('patient_id'))
        date = request.form.get('date')
        time = request.form.get('time')
        reason = request.form.get('reason')
        ap = Appointment(patient_id=patient_id, date=date, time=time, reason=reason)
        db.session.add(ap)
        db.session.commit()
        flash('Appointment added', 'success')
        return redirect(url_for('appointments'))
    all_apps = Appointment.query.order_by(Appointment.id.desc()).all()
    return render_template('appointments.html', patients=patients_list, appointments=all_apps)

# ----- Billing -----
@app.route('/billing', methods=['GET', 'POST'])
@login_required
def billing():
    try:
        patients_list = Patient.query.all()
        if request.method == 'POST':
            patient_id = request.form.get('patient_id')
            total_amount = request.form.get('total_amount')
            date_issued = request.form.get('date_issued') or datetime.utcnow().strftime('%Y-%m-%d')
            status = request.form.get('status') or 'Pending'

            if not patient_id or not total_amount:
                flash('Please select a patient and enter the amount', 'danger')
                return redirect(url_for('billing'))

            patient = Patient.query.get(int(patient_id))
            if not patient:
                flash('Invalid patient selection', 'danger')
                return redirect(url_for('billing'))

            bill = Bill(patient_id=patient.id,
                        total_amount=float(total_amount),
                        date_issued=date_issued,
                        status=status)
            db.session.add(bill)
            db.session.commit()
            flash('Bill added successfully', 'success')
            return redirect(url_for('billing'))

        bills = Bill.query.order_by(Bill.id.desc()).all()
        return render_template('billing.html', patients=patients_list, bills=bills)
    except Exception as e:
        # Print to logs and show an error page
        app.logger.exception("Billing error")
        flash('Something went wrong with billing. See logs.', 'danger')
        return render_template('error.html', message='Billing internal error'), 500

# ----- Contacts -----
@app.route('/contacts', methods=['GET', 'POST'])
@login_required
def contacts():
    if request.method == 'POST':
        name = request.form.get('name')
        email = request.form.get('email')
        message = request.form.get('message')
        c = Contact(name=name, email=email, message=message)
        db.session.add(c)
        db.session.commit()
        flash('Message received', 'success')
        return redirect(url_for('contacts'))
    msgs = Contact.query.order_by(Contact.created_at.desc()).all()
    return render_template('contacts.html', messages=msgs)

# ----- Medical History -----
@app.route('/medical_history', methods=['GET', 'POST'])
@login_required
def medical_history():
    if request.method == 'POST':
        patient_id = int(request.form.get('patient_id'))
        history_text = request.form.get('history')
        mh = MedicalHistory(patient_id=patient_id, history=history_text)
        db.session.add(mh)
        db.session.commit()
        flash('Medical history added', 'success')
        return redirect(url_for('medical_history'))
    histories = MedicalHistory.query.order_by(MedicalHistory.created_at.desc()).all()
    patients_list = Patient.query.all()
    return render_template('medical_history.html', histories=histories, patients=patients_list)

# ----- Reports (placeholder) -----
@app.route('/reports')
@login_required
def reports():
    # simple placeholder reports
    r = [
        {"title": "Patient Growth", "summary": f"Total patients: {Patient.query.count()}"},
        {"title": "Billing Summary", "summary": f"Total bills: {Bill.query.count()}"}
    ]
    return render_template('reports.html', reports=r)

# ----- Reset password (logged-in) -----
@app.route('/reset_password', methods=['GET', 'POST'])
@login_required
def reset_password():
    if request.method == 'POST':
        old = request.form.get('old_password')
        new = request.form.get('new_password')
        confirm = request.form.get('confirm_password')
        if not check_password_hash(current_user.password, old):
            flash('Old password incorrect', 'danger')
            return redirect(url_for('reset_password'))
        if new != confirm:
            flash('Passwords do not match', 'danger')
            return redirect(url_for('reset_password'))
        current_user.password = generate_password_hash(new, method='sha256')
        db.session.commit()
        flash('Password changed successfully', 'success')
        return redirect(url_for('dashboard'))
    return render_template('reset_password.html')

# ----- Error handler -----
@app.errorhandler(404)
def not_found(e):
    return render_template('error.html', message='Page not found'), 404

@app.errorhandler(500)
def internal_err(e):
    return render_template('error.html', message='Internal server error'), 500

# ---------------------------
# Run App
# ---------------------------
if __name__ == '__main__':
    # For local dev; in production use gunicorn
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=True)
