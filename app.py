from flask import Flask, render_template, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hospital.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# ===========================
# MODELS
# ===========================
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(150), unique=True, nullable=False)
    password = db.Column(db.String(150), nullable=False)

class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(150))
    age = db.Column(db.Integer)
    gender = db.Column(db.String(20))
    contact = db.Column(db.String(50))
    address = db.Column(db.String(250))
    condition = db.Column(db.Text)
    prescribed_drug = db.Column(db.String(250))

class Bill(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'))
    total_amount = db.Column(db.Float)
    date_issued = db.Column(db.Date)
    status = db.Column(db.String(50))
    patient = db.relationship('Patient')

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'))
    date = db.Column(db.Date)
    time = db.Column(db.String(50))
    patient = db.relationship('Patient')

class MedicalHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'))
    condition = db.Column(db.Text)
    prescribed_drug = db.Column(db.String(250))
    date = db.Column(db.Date, default=datetime.utcnow)
    patient = db.relationship('Patient')

class Report(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'))
    type = db.Column(db.String(150))
    description = db.Column(db.Text)
    date = db.Column(db.Date, default=datetime.utcnow)
    patient = db.relationship('Patient')


# ===========================
# LOGIN MANAGER
# ===========================
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# ===========================
# ROUTES
# ===========================

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = generate_password_hash(request.form['password'], method='sha256')
        new_user = User(username=username, password=password)
        db.session.add(new_user)
        db.session.commit()
        flash("User registered successfully!")
        return redirect(url_for('login'))
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('dashboard'))
        flash("Invalid username or password")
        return redirect(url_for('login'))
    return render_template('login.html')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('login'))


@app.route('/')
@login_required
def dashboard():
    total_patients = Patient.query.count()
    total_bills = Bill.query.count()
    total_appointments = Appointment.query.count()
    total_medicines = MedicalHistory.query.count()
    recent_patients = Patient.query.order_by(Patient.id.desc()).limit(5).all()
    recent_appointments = Appointment.query.order_by(Appointment.id.desc()).limit(5).all()
    recent_bills = Bill.query.order_by(Bill.id.desc()).limit(5).all()
    recent_reports = Report.query.order_by(Report.id.desc()).limit(5).all()
    return render_template('dashboard.html',
                           total_patients=total_patients,
                           total_bills=total_bills,
                           total_appointments=total_appointments,
                           total_medicines=total_medicines,
                           recent_patients=recent_patients,
                           recent_appointments=recent_appointments,
                           recent_bills=recent_bills,
                           recent_reports=recent_reports)


# ---------------- PATIENTS ----------------
@app.route('/patients', methods=['GET', 'POST'])
@login_required
def patients():
    if request.method == 'POST':
        p = Patient(
            full_name=request.form['full_name'],
            age=request.form['age'],
            gender=request.form['gender'],
            contact=request.form['contact'],
            address=request.form['address'],
            condition=request.form['condition'],
            prescribed_drug=request.form.get('prescribed_drug', '')
        )
        db.session.add(p)
        db.session.commit()
        flash("Patient added successfully!")
        return redirect(url_for('patients'))
    all_patients = Patient.query.all()
    return render_template('patients.html', patients=all_patients)


# ---------------- BILLING ----------------
@app.route('/billing', methods=['GET', 'POST'])
@login_required
def billing():
    if request.method == 'POST':
        patient_id = request.form['patient_id']
        total_amount = request.form['total_amount']
        date_issued = request.form['date_issued']
        status = request.form['status']
        bill = Bill(
            patient_id=patient_id,
            total_amount=total_amount,
            date_issued=datetime.strptime(date_issued, '%Y-%m-%d').date(),
            status=status
        )
        db.session.add(bill)
        db.session.commit()
        flash("Bill added successfully!")
        return redirect(url_for('billing'))
    bills = Bill.query.all()
    patients = Patient.query.all()
    return render_template('billing.html', bills=bills, patients=patients)


# ---------------- APPOINTMENTS ----------------
@app.route('/appointments', methods=['GET', 'POST'])
@login_required
def appointments():
    if request.method == 'POST':
        a = Appointment(
            patient_id=request.form['patient_id'],
            date=datetime.strptime(request.form['date'], '%Y-%m-%d').date(),
            time=request.form['time']
        )
        db.session.add(a)
        db.session.commit()
        flash("Appointment added successfully!")
        return redirect(url_for('appointments'))
    all_patients = Patient.query.all()
    appointments = Appointment.query.all()
    return render_template('appointments.html', patients=all_patients, appointments=appointments)


# ---------------- MEDICAL HISTORY ----------------
@app.route('/medical_history', methods=['GET', 'POST'])
@login_required
def medical_history():
    if request.method == 'POST':
        mh = MedicalHistory(
            patient_id=request.form['patient_id'],
            condition=request.form['condition'],
            prescribed_drug=request.form['prescribed_drug']
        )
        db.session.add(mh)
        db.session.commit()
        flash("Medical history added successfully!")
        return redirect(url_for('medical_history'))
    histories = MedicalHistory.query.all()
    patients = Patient.query.all()
    return render_template('medical_history.html', histories=histories, patients=patients)


# ---------------- REPORTS ----------------
@app.route('/reports', methods=['GET', 'POST'])
@login_required
def reports():
    if request.method == 'POST':
        r = Report(
            patient_id=request.form['patient_id'],
            type=request.form['type'],
            description=request.form['description']
        )
        db.session.add(r)
        db.session.commit()
        flash("Report added successfully!")
        return redirect(url_for('reports'))
    reports = Report.query.all()
    patients = Patient.query.all()
    return render_template('reports.html', reports=reports, patients=patients)


# ---------------- RESET PASSWORD ----------------
@app.route('/reset_password', methods=['GET', 'POST'])
@login_required
def reset_password():
    if request.method == 'POST':
        new_password = generate_password_hash(request.form['new_password'], method='sha256')
        current_user.password = new_password
        db.session.commit()
        flash("Password updated successfully!")
        return redirect(url_for('dashboard'))
    return render_template('reset_password.html')


# ===========================
# RUN APP
# ===========================
if __name__ == '__main__':
    db.create_all()
    app.run(debug=True)
