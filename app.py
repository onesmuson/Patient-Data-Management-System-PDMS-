from flask import Flask, render_template, request, redirect, url_for, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, logout_user, login_required, current_user, UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'thisshouldbeasecretkey'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pdms.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"

# ---------------- MODELS ---------------------
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)

class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer)
    gender = db.Column(db.String(10))
    condition = db.Column(db.String(200))
    contact = db.Column(db.String(100))
    address = db.Column(db.String(150))

class Medicine(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(255))
    dosage = db.Column(db.String(100))
    quantity = db.Column(db.Integer)

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'))
    date = db.Column(db.String(50))
    time = db.Column(db.String(50))
    reason = db.Column(db.String(200))
    patient = db.relationship('Patient', backref='appointments')

class Bill(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'))
    total_amount = db.Column(db.Float, nullable=False)
    date_issued = db.Column(db.String(50))
    status = db.Column(db.String(20), default="Unpaid")
    patient = db.relationship('Patient', backref='bills')

class Contact(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100))
    message = db.Column(db.String(300))

class MedicalHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'))
    history = db.Column(db.String(500))
    date_added = db.Column(db.String(50), default=datetime.datetime.now().strftime("%Y-%m-%d"))
    patient = db.relationship('Patient', backref='histories')

# ---------------- LOGIN MANAGER ---------------------
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# ---------------- ROUTES ---------------------
@app.route('/')
@login_required
def index():
    return render_template('dashboard.html')

# --------- LOGIN/LOGOUT ---------
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('index'))
        else:
            flash("Invalid username or password!", "error")
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))

# --------- MEDICINES ---------
@app.route('/add_medicine', methods=['GET', 'POST'])
@login_required
def add_medicine():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        dosage = request.form['dosage']
        quantity = request.form['quantity']
        med = Medicine(name=name, description=description, dosage=dosage, quantity=quantity)
        db.session.add(med)
        db.session.commit()
        flash("Medicine added successfully!", "success")
        return redirect(url_for('view_medicines'))
    return render_template('add_medicine.html')

@app.route('/view_medicines')
@login_required
def view_medicines():
    medicines = Medicine.query.all()
    return render_template('view_medicines.html', medicines=medicines)

# --------- APPOINTMENTS ---------
@app.route('/appointments', methods=['GET', 'POST'])
@login_required
def appointments():
    patients = Patient.query.all()
    if request.method == 'POST':
        patient_id = request.form['patient_id']
        date = request.form['date']
        time = request.form['time']
        reason = request.form['reason']
        appt = Appointment(patient_id=patient_id, date=date, time=time, reason=reason)
        db.session.add(appt)
        db.session.commit()
        flash("Appointment scheduled successfully!", "success")
        return redirect(url_for('appointments'))
    appointments = Appointment.query.all()
    return render_template('appointment.html', appointments=appointments, patients=patients)

# --------- BILLING ---------
@app.route('/billing', methods=['GET', 'POST'])
@login_required
def billing():
    patients = Patient.query.all()
    if request.method == 'POST':
        patient_id = request.form['patient_id']
        total_amount = request.form['total_amount']
        date_issued = request.form['date_issued']
        status = request.form['status']
        bill = Bill(patient_id=patient_id, total_amount=total_amount, date_issued=date_issued, status=status)
        db.session.add(bill)
        db.session.commit()
        flash("Bill added successfully!", "success")
        return redirect(url_for('billing'))
    bills = Bill.query.all()
    return render_template('billing.html', bills=bills, patients=patients)

# --------- CONTACTS ---------
@app.route('/contacts', methods=['GET', 'POST'])
@login_required
def contacts():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        message = request.form['message']
        contact = Contact(name=name, email=email, message=message)
        db.session.add(contact)
        db.session.commit()
        flash("Message sent successfully!", "success")
        return redirect(url_for('contacts'))
    messages = Contact.query.all()
    return render_template('contacts.html', messages=messages)

# --------- PATIENTS ---------
@app.route('/patients', methods=['GET', 'POST'])
@login_required
def patients():
    if request.method == 'POST':
        full_name = request.form['full_name']
        age = request.form['age']
        gender = request.form['gender']
        condition = request.form['condition']
        contact_info = request.form['contact']
        address = request.form['address']
        patient = Patient(full_name=full_name, age=age, gender=gender,
                          condition=condition, contact=contact_info, address=address)
        db.session.add(patient)
        db.session.commit()
        flash("Patient added successfully!", "success")
        return redirect(url_for('patients'))
    patients = Patient.query.all()
    return render_template('patients.html', patients=patients)

# --------- MEDICAL HISTORY ---------
@app.route('/add_medical_history', methods=['GET', 'POST'])
@login_required
def add_medical_history():
    patients = Patient.query.all()
    if request.method == 'POST':
        patient_id = request.form['patient_id']
        history = request.form['history']
        record = MedicalHistory(patient_id=patient_id, history=history)
        db.session.add(record)
        db.session.commit()
        flash("Medical history added successfully!", "success")
        return redirect(url_for('medical_history'))
    return render_template('add_medical_history.html', patients=patients)

@app.route('/medical_history')
@login_required
def medical_history():
    histories = MedicalHistory.query.all()
    return render_template('medical_history.html', histories=histories)

# --------- REPORTS ---------
@app.route('/reports')
@login_required
def reports():
    patients = Patient.query.all()
    return render_template('reports.html', patients=patients)

# ---------------- CREATE DB & DEFAULT ADMIN ---------------------
@app.before_first_request
def create_tables():
    db.create_all()
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', password=generate_password_hash('admin123'))
        db.session.add(admin)
        db.session.commit()
        print("Admin created: username='admin', password='admin123'")

if __name__ == '__main__':
    app.run(debug=True)
