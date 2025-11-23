from app import db
from models import User, Patient, Appointment, Bill, MedicalHistory
from werkzeug.security import generate_password_hash

# Create all tables
db.create_all()

# Create an admin user
admin_username = "admin"
admin_password = generate_password_hash("Admin123!", method='sha256')

if not User.query.filter_by(username=admin_username).first():
    admin = User(username=admin_username, password=admin_password)
    db.session.add(admin)
    db.session.commit()
    print("Admin user created.")
else:
    print("Admin user already exists.")

print("Database initialized successfully.")
