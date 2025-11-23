import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'this_should_be_random'
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'postgresql://patient_data_management_system_db_4jrj_user:mQpr9rAQvV1pKYBCWhyalT1AB5sad0iM@dpg-d4fibsggjchc73e3r1tg-a.oregon-postgres.render.com/patient_data_management_system_db_4jrj'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
