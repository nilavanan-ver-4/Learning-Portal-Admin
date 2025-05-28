import os

class Config:
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "postgresql://learning_user:1234@localhost:5432/learning_portal")
    MINIO_URL = os.environ.get("MINIO_URL", "localhost:9000")  # Update with your MinIO URL
    MINIO_ACCESS_KEY = os.environ.get("MINIO_ACCESS_KEY", "minioadmin")
    MINIO_SECRET_KEY = os.environ.get("MINIO_SECRET_KEY", "minioadmin123")
    SECRET_KEY = os.environ.get("SECRET_KEY", "your_flask_secret_key")
    SESSION_COOKIE_SECURE = os.environ.get("SESSION_COOKIE_SECURE", False)  # Set to False for local development
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 86400 # 1 day in seconds