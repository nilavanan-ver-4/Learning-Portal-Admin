from app import create_app, db
from app.models import User
from sqlalchemy.sql import text
from minio import Minio
from minio.error import S3Error
import hashlib
import io

app = create_app()

def test_db_connection():
    try:
        with app.app_context():
            print("== Testing Database Connection ==")
            db.session.execute(text("SELECT 1"))
            print("Database connection successful!")

            db_name = db.session.execute(text("SELECT current_database()")).scalar()
            print(f"Connected to database: {db_name}")

            search_path = db.session.execute(text("SHOW search_path")).scalar()
            print(f"Schema search path: {search_path}")

            result = db.session.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"))
            tables = [row[0] for row in result]
            print(f"Tables in database: {tables}")
            if 'users' not in tables:
                try:
                    db.session.execute(text("SELECT 1 FROM users LIMIT 1"))
                    print("Direct query to users table succeeded.")
                except Exception as e:
                    print(f"Direct query to users table failed: {str(e)}")
                raise Exception("The 'users' table does not exist or is not accessible.")

            result = db.session.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'users'"))
            columns = [row[0] for row in result]
            print(f"Columns in users table: {columns}")
            if 'user_id' not in columns:
                raise Exception("Missing 'user_id' column in 'users' table.")

            existing_user = User.query.filter_by(email="testuser@example.com").first()
            if existing_user:
                print(f"Test user already exists with ID: {existing_user.user_id}")
            else:
                password = "testpassword"
                password_hash = hashlib.sha256(password.encode()).hexdigest()
                test_user = User(
                    email="testuser@example.com",
                    password_hash=password_hash,
                    role="student",
                    first_name="Test",
                    last_name="User",
                    is_active=True
                )
                db.session.add(test_user)
                db.session.commit()
                print(f"User created with ID: {test_user.user_id}")

            retrieved_user = User.query.filter_by(email="testuser@example.com").first()
            if retrieved_user:
                print("Retrieved user data:")
                print(f"ID: {retrieved_user.user_id}")
                print(f"Email: {retrieved_user.email}")
                print(f"Role: {retrieved_user.role}")
                print(f"First Name: {retrieved_user.first_name}")
                print(f"Last Name: {retrieved_user.last_name}")
                print(f"Is Active: {retrieved_user.is_active}")
                print(f"Created At: {retrieved_user.created_at}")
            else:
                raise Exception("Failed to retrieve the test user.")

    except Exception as e:
        print(f"[DB ERROR] {str(e)}")


def test_minio_connection():
    try:
        with app.app_context():
            print("\n== Testing MinIO Connection ==")
            minio_url = app.config.get("MINIO_URL")
            access_key = app.config.get("MINIO_ACCESS_KEY")
            secret_key = app.config.get("MINIO_SECRET_KEY")

            print(f"Using MINIO_URL: {minio_url}")
            print(f"Using MINIO_ACCESS_KEY: {access_key}")
            print(f"Using MINIO_SECRET_KEY: {secret_key}")

            minio_client = Minio(
                minio_url,
                access_key=access_key,
                secret_key=secret_key,
                secure=False
            )

            bucket_name = "test-bucket"
            file_name = "test-file.txt"
            file_content = "This is a test file for MinIO."

            print("Checking MinIO server accessibility...")
            if minio_client.bucket_exists(bucket_name):
                print(f"Bucket '{bucket_name}' already exists.")
            else:
                minio_client.make_bucket(bucket_name)
                print(f"Bucket '{bucket_name}' created.")

            file_data = io.BytesIO(file_content.encode('utf-8'))
            file_data.seek(0)

            minio_client.put_object(
                bucket_name,
                file_name,
                file_data,
                length=len(file_content),
                content_type="text/plain"
            )
            print(f"File '{file_name}' uploaded.")

            print("Verifying uploaded file...")
            objects = list(minio_client.list_objects(bucket_name))
            if any(obj.object_name == file_name for obj in objects):
                print(f"File '{file_name}' verified in bucket '{bucket_name}'.")
            else:
                print(f"File '{file_name}' not found in bucket '{bucket_name}'.")

            print("Cleaning up...")
            minio_client.remove_object(bucket_name, file_name)
            print(f"File '{file_name}' removed.")
            minio_client.remove_bucket(bucket_name)
            print(f"Bucket '{bucket_name}' removed.")
            print("MinIO test completed.")

    except S3Error as s3_err:
        print(f"[MinIO S3Error] {s3_err}")
    except Exception as err:
        print(f"[MinIO ERROR] {err}")


if __name__ == "__main__":
    test_db_connection()
    test_minio_connection()
