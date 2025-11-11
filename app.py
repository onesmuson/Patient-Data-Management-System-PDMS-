from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime

app = Flask(__name__, template_folder='templates')
app.secret_key = 'pdms_secret_key'

# ---------------- DATABASE -------------------
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv(
    'DATABASE_URL',
    'sqlite:///pdms.sqlite'  # fallback for local testing
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ---------------- MODELS ---------------------
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)  # hashed

class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100))
    age = db.Column(db.Integer)
    gender = db.Column(db.String(10))
    condition = db.Column(db.String(200))
    medical_histories = db.relationship('MedicalHistory', backref='patient', cascade="all, delete-orphan")

class MedicalHistory(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patient.id'))
    visit_date = db.Column(db.Date)
    diagnosis = db.Column(db.String(200))
    treatment = db.Column(db.String(200))
    notes = db.Column(db.Text)

# ---------------- INIT DB -------------------
with app.app_context():
    db.create_all()
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', password=generate_password_hash('admin123'))
        db.session.add(admin)
        db.session.commit()
        print("Admin created: username='admin', password='admin123'")

# ---------------- ROUTES --------------------
@app.route('/')
def login():
    if 'username' in session:
        return redirect(url_for('dashboard'))
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def do_login():
    username = request.form['username']
    password = request.form['password']
    user = User.query.filter_by(username=username).first()
    if user and check_password_hash(user.password, password):
        session['username'] = username
        return redirect(url_for('dashboard'))
    return render_template('login.html', error="Invalid login credentials!")

# ---------------- Registration -------------------
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if User.query.filter_by(username=username).first():
            error = "Username already exists!"
            return render_template('register.html', error=error)
        hashed_password = generate_password_hash(password)
        new_user = User(username=username, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

# ---------------- Dashboard -------------------
@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    patients = Patient.query.all()
    return render_template('dashboard.html', patients=patients)

# ---------------- Patient -------------------
@app.route('/add_patient', methods=['GET', 'POST'])
def add_patient():
    if 'username' not in session:
        return redirect(url_for('login'))
    if request.method == 'POST':
        name = request.form['name']
        age = request.form['age']
        gender = request.form['gender']
        condition = request.form['condition']
        new_patient = Patient(full_name=name, age=age, gender=gender, condition=condition)
        db.session.add(new_patient)
        db.session.commit()
        return redirect(url_for('dashboard'))
    return render_template('add_patient.html')

@app.route('/view_patients')
def view_patients():
    if 'username' not in session:
        return redirect(url_for('login'))
    patients = Patient.query.all()
    return render_template('view_patients.html', patients=patients)

@app.route('/reports')
def reports():
    if 'username' not in session:
        return redirect(url_for('login'))
    patients = Patient.query.all()
    return render_template('reports.html', patients=patients)

# ---------------- Medical History -------------------
@app.route('/medical_history/<int:patient_id>')
def medical_history(patient_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    patient = Patient.query.get_or_404(patient_id)
    histories = MedicalHistory.query.filter_by(patient_id=patient_id).all()
    return render_template('medical_history.html', patient=patient, histories=histories)

@app.route('/add_medical_history/<int:patient_id>', methods=['GET', 'POST'])
def add_medical_history(patient_id):
    if 'username' not in session:
        return redirect(url_for('login'))
    patient = Patient.query.get_or_404(patient_id)
    if request.method == 'POST':
        visit_date = datetime.strptime(request.form['visit_date'], "%Y-%m-%d")
        diagnosis = request.form['diagnosis']
        treatment = request.form['treatment']
        notes = request.form['notes']
        history = MedicalHistory(
            patient_id=patient_id,
            visit_date=visit_date,
            diagnosis=diagnosis,
            treatment=treatment,
            notes=notes
        )
        db.session.add(history)
        db.session.commit()
        return redirect(url_for('medical_history', patient_id=patient_id))
    return render_template('add_medical_history.html', patient=patient)

# ---------------- Change Password -------------------
@app.route('/change_password', methods=['GET', 'POST'])
def change_password():
    if 'username' not in session:
        return redirect(url_for('login'))

    error = None
    success = None
    user = User.query.filter_by(username=session['username']).first()

    if request.method == 'POST':
        old_password = request.form['old_password']
        new_password = request.form['new_password']

        if not check_password_hash(user.password, old_password):
            error = "Old password is incorrect!"
        else:
            user.password = generate_password_hash(new_password)
            db.session.commit()
            success = "Password updated successfully!"

    return render_template('change_password.html', error=error, success=success)

# ---------------- Logout -------------------
@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

# ---------------- RUN APP -------------------
if __name__ == '__main__':
    app.run(debug=True)
