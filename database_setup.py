from app import app
from models import db, User

with app.app_context():
    db.create_all()
    if not User.query.filter_by(username='admin').first():
        admin = User(username='admin', password='admin123')
        db.session.add(admin)
        db.session.commit()
        print("Added default admin: username=admin password=admin123")
    else:
        print("Admin user already exists.")
