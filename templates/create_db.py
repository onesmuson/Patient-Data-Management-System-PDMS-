from app import db, User
from werkzeug.security import generate_password_hash

# Create all tables
db.create_all()
print("✅ Database tables created successfully!")

# Check if admin user already exists
admin_username = "admin"
admin_password = "admin123"  # Change this password to something secure

if not User.query.filter_by(username=admin_username).first():
    admin_user = User(
        username=admin_username,
        password=generate_password_hash(admin_password)
    )
    db.session.add(admin_user)
    db.session.commit()
    print(f"✅ Admin user '{admin_username}' created successfully with password '{admin_password}'")
else:
    print(f"ℹ️ Admin user '{admin_username}' already exists")
