from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# ---------------- MODELS ---------------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), default="staff")  # staff, admin, doctor
    email = db.Column(db.String(100), unique=True)

class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer)
    gender = db.Column(db.String(10))
    condition = db.Column(db.String(200))
    contact = db.Column(db.String(100))
    address = db.Column(db.String(150))
    blood_group = db.Column(db.String(10))
    allergies = db.Column(db.String(200))
    date_registered = db.Column(db.String(50))

class Medicine(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255))
    dosage = db.Column(db.String(100))
    quantity = db.Column(db.Integer)
    price = db.Column(db.Float, default=0.0)
    expiry_date = db.Column(db.String(50))

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'))
    doctor_id = db.Column(db.Integer, db.ForeignKey('user.id'))  # assigned doctor
    date = db.Column(db.String(50))
    time = db.Column(db.String(50))
    reason = db.Column(db.String(200))
    status = db.Column(db.String(20), default="Scheduled")  # Scheduled, Completed, Cancelled
    patient = db.relationship('Patient', backref='appointments')
    doctor = db.relationship('User', backref='appointments')

class Bill(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'))
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointment.id'), nullable=True)
    total_amount = db.Column(db.Float, nullable=False)
    date_issued = db.Column(db.String(50))
    status = db.Column(db.String(20), default="Unpaid")
    patient = db.relationship('Patient', backref='bills')
    appointment = db.relationship('Appointment', backref='bills')

class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100))
    subject = db.Column(db.String(150))
    message = db.Column(db.String(500))
    date_sent = db.Column(db.String(50))
