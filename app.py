from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from config import Config
import os

app = Flask(__name__)
app.config.from_object(Config)

db = SQLAlchemy(app)

from models import User, Patient, Appointment, Bill, MedicalHistory

@app.route('/')
def index():
    return redirect(url_for('login'))

@app.route('/login', methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            flash('Logged in successfully!', 'success')
            return redirect(url_for('dashboard'))
        else:
            flash('Invalid username or password', 'danger')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user_id', None)
    flash('Logged out successfully!', 'success')
    return redirect(url_for('login'))

@app.route('/dashboard')
def dashboard():
    patients_count = Patient.query.count()
    appointments_count = Appointment.query.count()
    bills_count = Bill.query.count()
    return render_template('dashboard.html',
                           patients_count=patients_count,
                           appointments_count=appointments_count,
                           bills_count=bills_count)

# CRUD for Patients
@app.route('/patients')
def view_patients():
    patients = Patient.query.all()
    return render_template('view_patients.html', patients=patients)

@app.route('/patients/add', methods=['GET','POST'])
def add_patient():
    if request.method == 'POST':
        name = request.form['name']
        age = request.form['age']
        gender = request.form['gender']
        address = request.form['address']
        patient = Patient(name=name, age=age, gender=gender, address=address)
        db.session.add(patient)
        db.session.commit()
        flash('Patient added successfully!', 'success')
        return redirect(url_for('view_patients'))
    return render_template('add_patient.html')

@app.route('/patients/edit/<int:id>', methods=['GET','POST'])
def edit_patient(id):
    patient = Patient.query.get_or_404(id)
    if request.method == 'POST':
        patient.name = request.form['name']
        patient.age = request.form['age']
        patient.gender = request.form['gender']
        patient.address = request.form['address']
        db.session.commit()
        flash('Patient updated successfully!', 'success')
        return redirect(url_for('view_patients'))
    return render_template('edit_patient.html', patient=patient)

# You can add similar routes for Appointments, Bills, MedicalHistory...

if __name__ == '__main__':
    app.run(debug=True)
