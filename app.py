import os
from datetime import datetime
from flask import Flask, render_template, redirect, url_for, request, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

# =======================
# App Initialization
# =======================
app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'your_default_secret_key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL', 'sqlite:///pdms.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

# =======================
# MODELS
# =======================
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)
    security_question = db.Column(db.String(200))
    security_answer = db.Column(db.String(150))

class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(150), nullable=False)
    age = db.Column(db.Integer)
    gender = db.Column(db.String(20))
    contact = db.Column(db.String(50))
    address = db.Column(db.String(200))
    condition = db.Column(db.String(200))
    prescribed_drug = db.Column(db.String(200))
    doctor_name = db.Column(db.String(100))
    date_registered = db.Column(db.DateTime, default=datetime.utcnow)

class Medicine(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150))
    description = db.Column(db.String(200))
    dosage = db.Column(db.String(50))
    quantity = db.Column(db.Integer)

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'))
    patient = db.relationship('Patient', backref='appointments')
    date = db.Column(db.String(20))
    time = db.Column(db.String(20))
    reason = db.Column(db.String(200))

class Bill(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'))
    patient = db.relationship('Patient', backref='bills')
    total_amount = db.Column(db.Float)
    date_issued = db.Column(db.String(20))
    status = db.Column(db.String(50))
    payment_method = db.Column(db.String(50))
    description = db.Column(db.String(200))

class MedicalHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'))
    patient = db.relationship('Patient')
    history = db.Column(db.String(500))

class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(150))
    email = db.Column(db.String(150))
    message = db.Column(db.String(500))

# =======================
# LOGIN MANAGER
# =======================
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# =======================
# CREATE TABLES & ADMIN
# =======================
with app.app_context():
    db.create_all()
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin',
                     password=generate_password_hash('admin123', method='sha256'),
                     security_question='Default Question',
                     security_answer='admin')
        db.session.add(admin)
        db.session.commit()

# =======================
# DASHBOARD
# =======================
@app.route('/', endpoint='dashboard')
@login_required
def dashboard():
    stats = {
        'total_patients': Patient.query.count(),
        'total_medicines': Medicine.query.count(),
        'total_appointments': Appointment.query.count(),
        'total_bills': Bill.query.count(),
        'total_messages': Contact.query.count()
    }
    recent_patients = Patient.query.order_by(Patient.id.desc()).limit(5).all()
    recent_appointments = Appointment.query.order_by(Appointment.id.desc()).limit(5).all()
    return render_template('dashboard.html',
                           **stats,
                           patients=recent_patients,
                           appointments=recent_appointments,
                           username=current_user.username)

# =======================
# AUTH ROUTES
# =======================
@app.route('/login', methods=['GET', 'POST'], endpoint='login')
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password, request.form['password']):
            login_user(user)
            flash('Logged in successfully!', 'success')
            return redirect(url_for('dashboard'))
        flash('Invalid username or password.', 'error')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'], endpoint='register')
def register():
    if request.method == 'POST':
        if User.query.filter_by(username=request.form['username']).first():
            flash('Username already exists.', 'error')
            return redirect(url_for('register'))
        hashed_pw = generate_password_hash(request.form['password'], method='sha256')
        db.session.add(User(
            username=request.form['username'],
            password=hashed_pw,
            security_question=request.form['security_question'],
            security_answer=request.form['security_answer'].lower()
        ))
        db.session.commit()
        flash('Account created! Please login.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout', endpoint='logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('login'))

# =======================
# FORGOT PASSWORD
# =======================
@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        username = request.form['username']
        answer = request.form['security_answer'].lower()
        new_pass = request.form['new_password']
        user = User.query.filter_by(username=username).first()
        if user and user.security_answer == answer:
            user.password = generate_password_hash(new_pass, method='sha256')
            db.session.commit()
            flash('Password reset successfully! You can now login.', 'success')
            return redirect(url_for('login'))
        else:
            flash('Incorrect details provided.', 'error')
    return render_template('forgot_password.html')

# =======================
# PATIENTS CRUD
# =======================
@app.route('/patients', methods=['GET', 'POST'], endpoint='patients')
@login_required
def patients():
    if request.method == 'POST':
        new_patient = Patient(
            full_name=request.form['full_name'],
            age=request.form['age'],
            gender=request.form['gender'],
            contact=request.form['contact'],
            address=request.form['address'],
            condition=request.form['condition'],
            prescribed_drug=request.form['prescribed_drug'],
            doctor_name=request.form['doctor_name']
        )
        db.session.add(new_patient)
        db.session.commit()
        flash('Patient added successfully!', 'success')
        return redirect(url_for('patients'))
    all_patients = Patient.query.all()
    return render_template('patients.html', patients=all_patients)

# =======================
# BILLING FIXED
# =======================
@app.route('/billing', methods=['GET', 'POST'], endpoint='billing')
@login_required
def billing():
    patients_list = Patient.query.all()
    if request.method == 'POST':
        try:
            bill = Bill(
                patient_id=request.form['patient_id'],
                total_amount=request.form['total_amount'],
                date_issued=request.form['date_issued'],
                status=request.form['status'],
                payment_method=request.form['payment_method'],
                description=request.form['description']
            )
            db.session.add(bill)
            db.session.commit()
            flash('Bill added successfully!', 'success')
        except Exception as e:
            flash(f'Error adding bill: {e}', 'error')
        return redirect(url_for('billing'))
    all_bills = Bill.query.order_by(Bill.id.desc()).all()
    return render_template('billing.html', patients=patients_list, bills=all_bills)

# =======================
# REPORTS
# =======================
@app.route('/reports', endpoint='reports')
@login_required
def reports():
    return render_template('reports.html')

# =======================
# MAIN
# =======================
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=10000, debug=True)
