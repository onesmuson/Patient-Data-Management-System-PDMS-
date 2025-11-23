import os

class Config:
    # Secret key for sessions
    SECRET_KEY = os.getenv("SECRET_KEY", "change_this_in_production")

    # Read DATABASE_URL (Render/Postgres). Render often provides DATABASE_URL.
    # SQLAlchemy needs dialect+driver in newer versions (postgresql+psycopg).
    database_url = os.getenv("DATABASE_URL")

    if database_url:
        # Normalize common "postgres://" prefix to SQLAlchemy driver form.
        if database_url.startswith("postgres://"):
            # use the new psycopg driver
            database_url = database_url.replace("postgres://", "postgresql+psycopg://", 1)
        SQLALCHEMY_DATABASE_URI = database_url
    else:
        # Local fallback for development — sqlite file in project folder
        SQLALCHEMY_DATABASE_URI = "sqlite:///patient_app.db"

    SQLALCHEMY_TRACK_MODIFICATIONS = False
