from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

# ---------- User Table ----------
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)


# ---------- Patient Table ----------
class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer)
    gender = db.Column(db.String(10))
    contact = db.Column(db.String(20))
    address = db.Column(db.String(200))
    medical_history = db.Column(db.Text)


# ---------- Medicine Table ----------
class Medicine(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255))
    quantity = db.Column(db.Integer, default=0)
    price = db.Column(db.Float, default=0.0)


# ---------- Appointment Table ----------
class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'))
    date = db.Column(db.String(50))
    time = db.Column(db.String(50))
    doctor = db.Column(db.String(100))
    reason = db.Column(db.String(255))
    patient = db.relationship('Patient', backref='appointments')


# ---------- Billing Table ----------
class Billing(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'))
    amount = db.Column(db.Float, default=0.0)
    status = db.Column(db.String(20), default='Unpaid')
    patient = db.relationship('Patient', backref='bills')


# ---------- Contact Table ----------
class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(100))
    phone = db.Column(db.String(50))
    message = db.Column(db.Text)
