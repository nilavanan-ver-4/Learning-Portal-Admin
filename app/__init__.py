from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from minio import Minio
from dotenv import load_dotenv
import os
import logging

# Load environment variables from .env file
load_dotenv()

# Initialize Flask extensions
db = SQLAlchemy()
migrate = Migrate()
limiter = Limiter(key_func=get_remote_address)  # Initialize Flask-Limiter with in-memory storage

def create_app():
    app = Flask(__name__)

    # Load configuration from config.py
    from .config import Config
    app.config.from_object(Config)

    # Configure logging
    logging.basicConfig(level=logging.INFO)
    app.logger.setLevel(logging.INFO)

    # Verify config loaded
    app.logger.info("Configuration loaded successfully!")
    app.logger.info(f"MINIO_ACCESS_KEY from env: {app.config['MINIO_ACCESS_KEY']}")
    app.logger.info(f"MINIO_SECRET_KEY from env: {app.config['MINIO_SECRET_KEY']}")
    app.logger.info(f"SECRET_KEY from env: {app.config['SECRET_KEY']}")
    app.logger.info(f"SQLALCHEMY_DATABASE_URI: {app.config['SQLALCHEMY_DATABASE_URI']}")

    # Initialize Flask extensions with the app
    db.init_app(app)
    migrate.init_app(app, db)
    limiter.init_app(app)  # Initialize Limiter with the app

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
            app.logger.info("Database connection successful!")
        except Exception as e:
            app.logger.error(f"Error connecting to database: {e}")

    return app