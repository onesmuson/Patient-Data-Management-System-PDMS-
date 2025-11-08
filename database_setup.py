from app import app
from models import db, User

with app.app_context():
    # Create database tables if they don't exist
    db.create_all()

    # Check if admin exists
    if not User.query.filter_by(username='admin').first():
        # Add default admin user
        admin = User(username='admin', password='admin123')
        db.session.add(admin)
        db.session.commit()
        print("Added default admin: username=admin password=admin123")
    else:
        print("Admin user already exists.")
