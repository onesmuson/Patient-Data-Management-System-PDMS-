import os

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "your_secret_key_here")
    
    # PostgreSQL database (Render)
    SQLALCHEMY_DATABASE_URI = os.getenv(
        "DATABASE_URL",
        "postgresql://patient_data_management_system_db_4jrj_user:"
        "mQpr9rAQvV1pKYBCWhyalT1AB5sad0iM@dpg-d4fibsggjchc73e3r1tg-a.oregon-postgres.render.com/"
        "patient_data_management_system_db_4jrj"
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
