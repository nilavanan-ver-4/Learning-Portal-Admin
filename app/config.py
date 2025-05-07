import os

class Config:
    SQLALCHEMY_DATABASE_URI = os.environ.get("DATABASE_URL", "postgresql://learning_user:1234@localhost:5432/Learning_portal")
    MINIO_URL = os.environ.get("MINIO_URL", "minio_url")
    MINIO_ACCESS_KEY = os.environ.get("MINIO_ACCESS_KEY", "minio_access_key")
    MINIO_SECRET_KEY = os.environ.get("MINIO_SECRET_KEY", "minio_secret_key")
    SECRET_KEY = os.environ.get("SECRET_KEY", "your_secret_key")
    JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY", "your-jwt-secret-key")
