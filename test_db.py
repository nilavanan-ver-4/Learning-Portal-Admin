from app import create_app, db
from app.models import User
from sqlalchemy.sql import text
import hashlib

app = create_app()

def test_db_connection():
    try:
        with app.app_context():
            # Test database connection
            db.session.execute(text("SELECT 1"))
            print("Database connection successful!")

            # Retrieve and display the database name
            db_name = db.session.execute(text("SELECT current_database()")).scalar()
            print(f"Connected to database: {db_name}")

            # Show the schema search path
            search_path = db.session.execute(text("SHOW search_path")).scalar()
            print(f"Schema search path: {search_path}")

            # Check if the database has any tables
            result = db.session.execute(text("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'"))
            tables = [row[0] for row in result]
            print(f"Tables in database: {tables}")
            if 'users' not in tables:
                # Try a direct query to the users table as a fallback
                try:
                    db.session.execute(text("SELECT 1 FROM users LIMIT 1"))
                    print("Direct query to users table succeeded, but table not found in information_schema. Check schema or permissions.")
                except Exception as e:
                    print(f"Direct query to users table failed: {str(e)}")
                raise Exception("The 'users' table does not exist in the database or is not accessible. Please apply the schema using schema.sql and check permissions.")

            # Check if the users table has the correct structure
            result = db.session.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'users'"))
            columns = [row[0] for row in result]
            print(f"Columns in users table: {columns}")
            if 'user_id' not in columns:
                raise Exception("Column 'user_id' not found in users table. Please drop the table and reapply the database schema.")

            # Check if the test user already exists to avoid duplicate email errors
            existing_user = User.query.filter_by(email="testuser@example.com").first()
            if existing_user:
                print(f"Test user already exists with ID: {existing_user.user_id}")
            else:
                # Create a test user
                password = "testpassword"
                password_hash = hashlib.sha256(password.encode()).hexdigest()  # Simple hashing for demo
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

            # Retrieve and display the test user's data
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
                raise Exception("Failed to retrieve the test user from the database.")

    except Exception as e:
        print(f"An error occurred: {str(e)}")

if __name__ == "__main__":
    test_db_connection()