from flask import Flask, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
import os

app = Flask(__name__, template_folder='templates')  # explicit templates folder
app.secret_key = 'pdms_secret_key'

# ---------------- DATABASE -------------------
# Use Render PostgreSQL URL from env
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
    password = db.Column(db.String(50), nullable=False)

class Patient(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(100))
    age = db.Column(db.Integer)
    gender = db.Column(db.String(10))
    condition = db.Column(db.String(200))

# ---------------- INIT DB -------------------
with app.app_context():
    db.create_all()
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', password='admin123')
        db.session.add(admin)
        db.session.commit()
        print("Admin created: admin/admin123")

# ---------------- ROUTES --------------------
@app.route('/')
def login():
    return render_template('login.html')

@app.route('/login', methods=['POST'])
def do_login():
    username = request.form['username']
    password = request.form['password']
    user = User.query.filter_by(username=username, password=password).first()
    if user:
        session['username'] = username
        return redirect(url_for('dashboard'))
    return render_template('login.html', error="Invalid login credentials!")

@app.route('/dashboard')
def dashboard():
    if 'username' not in session:
        return redirect(url_for('login'))
    patients = Patient.query.all()
    return render_template('dashboard.html', patients=patients)

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

@app.route('/logout')
def logout():
    session.pop('username', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run()
