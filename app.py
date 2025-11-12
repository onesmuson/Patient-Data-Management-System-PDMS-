from flask import Flask, render_template, request, redirect, url_for, session, flash
from models import db, User, Patient, Medicine, Appointment, Bill, Contact
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your_secret_key'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///pdms.db'
db.init_app(app)

@app.before_first_request
def create_tables():
    db.create_all()
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', password=generate_password_hash('admin123'))
        db.session.add(admin)
        db.session.commit()
        print("Admin created: username='admin', password='admin123'")

# ---------------------- LOGIN ------------------------
@app.route('/', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password, request.form['password']):
            session['user'] = user.username
            return redirect(url_for('dashboard'))
        else:
            flash("Invalid username or password")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

# ---------------------- DASHBOARD ------------------------
@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    return render_template('dashboard.html')

# ---------------------- PATIENTS ------------------------
@app.route('/add_patient', methods=['GET', 'POST'])
def add_patient():
    if request.method == 'POST':
        new_patient = Patient(
            name=request.form['name'],
            age=request.form['age'],
            gender=request.form['gender'],
            contact=request.form['contact'],
            diagnosis=request.form['diagnosis']
        )
        db.session.add(new_patient)
        db.session.commit()
        flash("Patient added successfully!")
        return redirect(url_for('view_patients'))
    return render_template('add_patient.html')

@app.route('/view_patients')
def view_patients():
    patients = Patient.query.all()
    return render_template('view_patients.html', patients=patients)

# ---------------------- MEDICINES ------------------------
@app.route('/add_medicine', methods=['GET', 'POST'])
def add_medicine():
    if request.method == 'POST':
        new_med = Medicine(
            name=request.form['name'],
            category=request.form['category'],
            quantity=request.form['quantity'],
            price=request.form['price']
        )
        db.session.add(new_med)
        db.session.commit()
        flash("Medicine added successfully!")
        return redirect(url_for('view_medicines'))
    return render_template('add_medicine.html')

@app.route('/view_medicines')
def view_medicines():
    medicines = Medicine.query.all()
    return render_template('view_medicines.html', medicines=medicines)

# ---------------------- APPOINTMENT ------------------------
@app.route('/appointment', methods=['GET', 'POST'])
def appointment():
    if request.method == 'POST':
        new_app = Appointment(
            patient_name=request.form['patient_name'],
            doctor_name=request.form['doctor_name'],
            date=request.form['date'],
            time=request.form['time']
        )
        db.session.add(new_app)
        db.session.commit()
        flash("Appointment booked successfully!")
    return render_template('appointment.html')

# ---------------------- BILLING ------------------------
@app.route('/billing', methods=['GET', 'POST'])
def billing():
    if request.method == 'POST':
        new_bill = Bill(
            patient_name=request.form['patient_name'],
            amount=request.form['amount'],
            status=request.form['status']
        )
        db.session.add(new_bill)
        db.session.commit()
        flash("Bill recorded successfully!")
    bills = Bill.query.all()
    return render_template('billing.html', bills=bills)

# ---------------------- CONTACT ------------------------
@app.route('/contacts', methods=['GET', 'POST'])
def contacts():
    if request.method == 'POST':
        new_contact = Contact(
            name=request.form['name'],
            email=request.form['email'],
            message=request.form['message']
        )
        db.session.add(new_contact)
        db.session.commit()
        flash("Message sent successfully!")
    return render_template('contacts.html')

if __name__ == '__main__':
    app.run(debug=True)
