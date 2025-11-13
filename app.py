from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# ================== Configuration ==================
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hospital.db'
app.config['SECRET_KEY'] = os.environ.get("SECRET_KEY", "fallback_secret_key")

db = SQLAlchemy(app)

# ================== Database Models ==================
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(200), nullable=False)
    age = db.Column(db.Integer)
    gender = db.Column(db.String(50))
    contact = db.Column(db.String(50))
    address = db.Column(db.String(200))
    condition = db.Column(db.String(200))
    prescribed_drug = db.Column(db.String(200))

class Medicine(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    stock = db.Column(db.Integer)

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'))
    date = db.Column(db.String(50))
    time = db.Column(db.String(50))
    patient = db.relationship('Patient')

class Bill(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'))
    total_amount = db.Column(db.Float)
    date_issued = db.Column(db.String(50))
    status = db.Column(db.String(50))
    patient = db.relationship('Patient')

# ================== Routes ==================
@app.route('/')
def home():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    return redirect(url_for('dashboard'))

# ---------- Register ----------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = generate_password_hash(request.form['password'])
        user = User(username=username, email=email, password=password)
        db.session.add(user)
        db.session.commit()
        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

# ---------- Login ----------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            flash('Welcome back!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid email or password.', 'danger')
    return render_template('login.html')

# ---------- Logout ----------
@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('You have logged out successfully.', 'info')
    return redirect(url_for('login'))

# ---------- Forgot Password ----------
@app.route('/forgot_password', methods=['GET', 'POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form['email']
        user = User.query.filter_by(email=email).first()
        if not user:
            flash('No user found with that email.', 'danger')
            return redirect(url_for('forgot_password'))
        # In a real app, send email link — for now, redirect to reset page
        session['reset_email'] = email
        flash('Proceed to reset your password.', 'info')
        return redirect(url_for('reset_password'))
    return render_template('forgot_password.html')

@app.route('/reset_password', methods=['GET', 'POST'])
def reset_password():
    if 'reset_email' not in session:
        return redirect(url_for('forgot_password'))
    if request.method == 'POST':
        new_password = generate_password_hash(request.form['password'])
        user = User.query.filter_by(email=session['reset_email']).first()
        if user:
            user.password = new_password
            db.session.commit()
            flash('Password updated successfully! Please log in.', 'success')
            session.pop('reset_email', None)
            return redirect(url_for('login'))
    return render_template('reset_password.html')

# ---------- Dashboard ----------
@app.route('/dashboard')
def dashboard():
    total_patients = Patient.query.count()
    total_medicines = Medicine.query.count()
    total_appointments = Appointment.query.count()
    total_bills = Bill.query.count()

    patients = Patient.query.order_by(Patient.id.desc()).limit(5).all()
    appointments = Appointment.query.order_by(Appointment.id.desc()).limit(5).all()

    return render_template('dashboard.html',
                           total_patients=total_patients,
                           total_medicines=total_medicines,
                           total_appointments=total_appointments,
                           total_bills=total_bills,
                           patients=patients,
                           appointments=appointments)

# ---------- Patients ----------
@app.route('/patients', methods=['GET', 'POST'])
def patients():
    if request.method == 'POST':
        new_patient = Patient(
            full_name=request.form['full_name'],
            age=request.form['age'],
            gender=request.form['gender'],
            contact=request.form['contact'],
            address=request.form['address'],
            condition=request.form['condition'],
            prescribed_drug=request.form['prescribed_drug']
        )
        db.session.add(new_patient)
        db.session.commit()
        flash('Patient added successfully!', 'success')
        return redirect(url_for('patients'))
    all_patients = Patient.query.all()
    return render_template('patients.html', patients=all_patients)

# ---------- Billing ----------
@app.route('/billing', methods=['GET', 'POST'])
def billing():
    if request.method == 'POST':
        try:
            patient_id = request.form['patient_id']
            total_amount = float(request.form['total_amount'])
            date_issued = request.form['date_issued']
            status = request.form['status']

            new_bill = Bill(patient_id=patient_id, total_amount=total_amount,
                            date_issued=date_issued, status=status)
            db.session.add(new_bill)
            db.session.commit()
            flash('Bill added successfully!', 'success')
            return redirect(url_for('billing'))
        except Exception as e:
            db.session.rollback()
            flash(f"Error adding bill: {str(e)}", 'danger')
    patients = Patient.query.all()
    bills = Bill.query.all()
    return render_template('billing.html', patients=patients, bills=bills)

# ================== Main Entry ==================
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=5000)
