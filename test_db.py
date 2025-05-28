from app import create_app, db
from app.model1 import User , Course, Enrollment, Progress, Chapter, Lesson, UserProfile, CourseMetadata, UserRole
from sqlalchemy.sql import text

app = create_app()

def test_db_connection():
    try:
        with app.app_context():
            # Test database connection
            print("Testing database connection... model 1")
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
            expected_tables = ['users', 'courses', 'enrollments', 'progress', 'chapters', 'lessons', 'user_profiles', 'course_metadata']
            missing_tables = [table for table in expected_tables if table not in tables]
            if missing_tables:
                raise Exception(f"Missing tables: {missing_tables}. Please apply the schema using schema.sql.")

            # Check users table structure
            result = db.session.execute(text("SELECT column_name FROM information_schema.columns WHERE table_name = 'users'"))
            columns = [row[0] for row in result]
            print(f"Columns in users table: {columns}")
            expected_columns = ['user_id', 'email', 'password_hash', 'first_name', 'last_name', 'role', 'is_active', 'created_at', 'last_login_at', 'reset_token', 'deleted_at']
            missing_columns = [col for col in expected_columns if col not in columns]
            if missing_columns:
                raise Exception(f"Missing columns in users table: {missing_columns}. Please drop the table and reapply the schema.")

            # Create teacher
            teacher = User.query.filter_by(email="teacher@example.com", deleted_at=None).first()
            if not teacher:
                teacher = User(
                    email="teacher@example.com",
                    role=UserRole.teacher,
                    first_name="Teacher",
                    last_name="One",
                    is_active=True
                )
                teacher.set_password("123456")
                db.session.add(teacher)
                print("Created teacher user.")
            else:
                print(f"Teacher {teacher.email} already exists.")

            # Create student
            student = User.query.filter_by(email="nilalinuxa4n@gmail.com", deleted_at=None).first()
            if not student:
                student = User(
                    email="nilalinuxa4n@gmail.com",
                    role=UserRole.student,
                    first_name="Nilavanan",
                    last_name="S A",
                    is_active=True
                )
                student.set_password("123456")
                db.session.add(student)
                print("Created student user.")
            else:
                print(f"Student {student.email} already exists.")

            # Create test user
            test_user = User.query.filter_by(email="testuser@example.com", deleted_at=None).first()
            if not test_user:
                test_user = User(
                    email="testuser@example.com",
                    role=UserRole.student,
                    first_name="Test",
                    last_name="User",
                    is_active=True
                )
                test_user.set_password("testpassword")
                db.session.add(test_user)
                print("Created test user.")
            else:
                print(f"Test user {test_user.email} already exists.")

            # Create course
            course = Course.query.filter_by(title="Python Basics", deleted_at=None).first()
            if not course:
                course = Course(
                    title="Python Basics",
                    description="Learn Python programming.",
                    is_published=True,
                    teacher_id=teacher.user_id
                )
                db.session.add(course)
                print("Created course.")
            else:
                print(f"Course {course.title} already exists.")

            # Commit to get course_id
            db.session.commit()

            # Create course metadata
            course_metadata = CourseMetadata.query.filter_by(course_id=course.course_id).first()
            if not course_metadata:
                course_metadata = CourseMetadata(
                    course_id=course.course_id,
                    category="Programming",
                    tags=["python", "coding"]
                )
                db.session.add(course_metadata)
                print("Created course metadata.")
            else:
                print(f"Course metadata for course_id {course.course_id} already exists.")

            # Create chapter
            chapter = Chapter.query.filter_by(course_id=course.course_id, title="Introduction to Python").first()
            if not chapter:
                chapter = Chapter(
                    title="Introduction to Python",
                    course_id=course.course_id,
                    chapter_order=1
                )
                db.session.add(chapter)
                print("Created chapter.")
            else:
                print(f"Chapter {chapter.title} already exists.")

            # Create lesson
            lesson = Lesson.query.filter_by(chapter_id=chapter.chapter_id, title="Python Basics Lesson").first()
            if not lesson:
                lesson = Lesson(
                    title="Python Basics Lesson",
                    lesson_type="video",
                    minio_url="learning_portal/python_basics_lesson.mp4",
                    chapter_id=chapter.chapter_id,
                    lesson_order=1,
                    duration=300
                )
                db.session.add(lesson)
                print("Created lesson.")
            else:
                print(f"Lesson {lesson.title} already exists.")

            # Create enrollment
            enrollment = Enrollment.query.filter_by(student_id=student.user_id, course_id=course.course_id).first()
            if not enrollment:
                enrollment = Enrollment(
                    student_id=student.user_id,
                    course_id=course.course_id
                )
                db.session.add(enrollment)
                print("Created enrollment.")
            else:
                print(f"Enrollment for student_id {student.user_id} and course_id {course.course_id} already exists.")

            # Create progress
            progress = Progress.query.filter_by(student_id=student.user_id, course_id=course.course_id).first()
            if not progress:
                progress = Progress(
                    student_id=student.user_id,
                    course_id=course.course_id,
                    completed_percentage=50.0
                )
                db.session.add(progress)
                print("Created progress.")
            else:
                print(f"Progress for student_id {student.user_id} and course_id {course.course_id} already exists.")

            # Create user profile
            profile = UserProfile.query.filter_by(user_id=student.user_id).first()
            if not profile:
                profile = UserProfile(
                    user_id=student.user_id,
                    bio="Student learning Python.",
                    profile_picture_url="learning_portal/student_profile.jpg"
                )
                db.session.add(profile)
                print("Created user profile.")
            else:
                print(f"User profile for user_id {student.user_id} already exists.")

            # Commit all changes
            db.session.commit()

            # Verify inserted data
            print("\nVerifying inserted data:")
            # Users
            users = User.query.filter(User.email.in_(["teacher@example.com", "nilalinuxa4n@gmail.com", "testuser@example.com"]), User.deleted_at == None).all()
            print("Users:")
            for user in users:
                print(f"  ID: {user.user_id}, Email: {user.email}, Role: {user.role}, Name: {user.first_name} {user.last_name}")

            # Courses
            courses = Course.query.filter_by(deleted_at=None).all()
            print("Courses:")
            for course in courses:
                print(f"  ID: {course.course_id}, Title: {course.title}, Teacher ID: {course.teacher_id}")

            # Course Metadata
            course_metadata_records = CourseMetadata.query.all()
            print("Course Metadata:")
            for meta in course_metadata_records:
                print(f"  Course ID: {meta.course_id}, Category: {meta.category}, Tags: {meta.tags}")

            # Chapters
            chapters = Chapter.query.all()
            print("Chapters:")
            for chap in chapters:
                print(f"  ID: {chap.chapter_id}, Title: {chap.title}, Course ID: {chap.course_id}")

            # Lessons
            lessons = Lesson.query.all()
            print("Lessons:")
            for lesson in lessons:
                print(f"  ID: {lesson.lesson_id}, Title: {lesson.title}, Chapter ID: {lesson.chapter_id}")

            # Enrollments
            enrollments = Enrollment.query.all()
            print("Enrollments:")
            for enroll in enrollments:
                print(f"  ID: {enroll.enrollment_id}, Student ID: {enroll.student_id}, Course ID: {enroll.course_id}")

            # Progress
            progress_records = Progress.query.all()
            print("Progress:")
            for prog in progress_records:
                print(f"  ID: {prog.progress_id}, Student ID: {prog.student_id}, Course ID: {prog.course_id}, Percentage: {prog.completed_percentage}")

            # User Profiles
            profiles = UserProfile.query.all()
            print("User Profiles:")
            for prof in profiles:
                print(f"  User ID: {prof.user_id}, Bio: {prof.bio}")

            print("Test data added and verified successfully!")

    except Exception as e:
        print(f"An error occurred: {str(e)}")
        db.session.rollback()

if __name__ == "__main__":
    test_db_connection()



"""
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

"""