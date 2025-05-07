from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_jwt_extended import JWTManager
from minio import Minio
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()

# Initialize Flask extensions
db = SQLAlchemy()
migrate = Migrate()
jwt = JWTManager()

def create_app():
    app = Flask(__name__)

    # Load configuration from config.py
    from .config import Config
    app.config.from_object(Config)

    # Optional: verify config loaded
    print("Database connection successful!")
    print(f"MINIO_ACCESS_KEY from env: {app.config['MINIO_ACCESS_KEY']}")
    print(f"MINIO_SECRET_KEY from env: {app.config['MINIO_SECRET_KEY']}")

    # Initialize Flask extensions with the app
    db.init_app(app)
    migrate.init_app(app, db)
    jwt.init_app(app)

    # Initialize MinIO client
    minio_client = Minio(
        app.config["MINIO_URL"],
        access_key=app.config["MINIO_ACCESS_KEY"],
        secret_key=app.config["MINIO_SECRET_KEY"],
        secure=False
    )
    app.minio_client = minio_client

    # Register blueprints (routes)
    from .routes import main
    app.register_blueprint(main)

    # Test database connection
    with app.app_context():
        try:
            db.engine.connect()
            print("Database connection successful!")
        except Exception as e:
            print(f"Error connecting to database: {e}")

    return app
