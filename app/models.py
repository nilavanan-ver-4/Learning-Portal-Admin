from app import db  # Import db from app/__init__.py
from sqlalchemy.sql import func
from werkzeug.security import generate_password_hash, check_password_hash

class User(db.Model):
    __tablename__ = 'users'

    user_id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, server_default=func.now())
    last_login_at = db.Column(db.DateTime)  # Added for tracking last login
    reset_token = db.Column(db.String(255))  # Added for password reset
    deleted_at = db.Column(db.DateTime)  # Added for soft deletes

    # Relationships
    courses = db.relationship("Course", back_populates="teacher")
    enrollments = db.relationship("Enrollment", back_populates="student")
    progress = db.relationship("Progress", back_populates="student")
    profile = db.relationship("UserProfile", back_populates="user", uselist=False)  # Added for user profile

    __table_args__ = (
        db.CheckConstraint("role IN ('admin', 'teacher', 'student')", name='check_role'),
    )

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.email}>"

class UserProfile(db.Model):
    __tablename__ = 'user_profiles'

    profile_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False, unique=True)
    bio = db.Column(db.Text)  # Optional bio
    profile_picture_url = db.Column(db.Text)  # URL for profile picture (MinIO)
    created_at = db.Column(db.DateTime, server_default=func.now())
    updated_at = db.Column(db.DateTime)  # Track profile updates

    # Relationship
    user = db.relationship("User", back_populates="profile")

    def __repr__(self):
        return f"<UserProfile user_id={self.user_id}>"

class Course(db.Model):
    __tablename__ = 'courses'

    course_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    created_at = db.Column(db.DateTime, server_default=func.now())
    is_published = db.Column(db.Boolean, default=False)
    deleted_at = db.Column(db.DateTime)  # Added for soft deletes

    # Relationships
    teacher = db.relationship("User", back_populates="courses")
    chapters = db.relationship("Chapter", back_populates="course", cascade="all, delete")
    enrollments = db.relationship("Enrollment", back_populates="course")
    course_metadata = db.relationship("CourseMetadata", back_populates="course")  # Changed from metadata to course_metadata

    def __repr__(self):
        return f"<Course {self.title}>"

class CourseMetadata(db.Model):
    __tablename__ = 'course_metadata'

    metadata_id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.course_id'), nullable=False)
    category = db.Column(db.String(100))  # Course category
    tags = db.Column(db.ARRAY(db.Text))  # Array of tags
    created_at = db.Column(db.DateTime, server_default=func.now())

    # Relationship
    course = db.relationship("Course", back_populates="course_metadata")  # Changed to match course_metadata

    def __repr__(self):
        return f"<CourseMetadata course_id={self.course_id}>"

class Chapter(db.Model):
    __tablename__ = 'chapters'

    chapter_id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.course_id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    chapter_order = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, server_default=func.now())

    # Relationships
    course = db.relationship("Course", back_populates="chapters")
    lessons = db.relationship("Lesson", back_populates="chapter", cascade="all, delete")

    __table_args__ = (
        db.UniqueConstraint('course_id', 'chapter_order', name='unique_chapter_order'),  # Added for unique chapter order
    )

    def __repr__(self):
        return f"<Chapter {self.title}>"

class Lesson(db.Model):
    __tablename__ = 'lessons'

    lesson_id = db.Column(db.Integer, primary_key=True)
    chapter_id = db.Column(db.Integer, db.ForeignKey('chapters.chapter_id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    lesson_type = db.Column(db.String(50), nullable=False)
    minio_url = db.Column(db.Text, nullable=False)  # Changed to Text
    lesson_order = db.Column(db.Integer, nullable=False)
    duration = db.Column(db.Integer)  # CHECK constraint handled in schema
    created_at = db.Column(db.DateTime, server_default=func.now())

    # Relationships
    chapter = db.relationship("Chapter", back_populates="lessons")
    progress = db.relationship("Progress", back_populates="lesson")

    __table_args__ = (
        db.CheckConstraint("lesson_type IN ('video', 'document', 'quiz', 'other')", name='check_lesson_type'),
        db.UniqueConstraint('chapter_id', 'lesson_order', name='unique_lesson_order'),  # Added for unique lesson order
        db.CheckConstraint("duration > 0", name='check_duration'),  # Added for positive duration
    )

    def __repr__(self):
        return f"<Lesson {self.title}>"

class Enrollment(db.Model):
    __tablename__ = 'enrollments'

    enrollment_id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.course_id'), nullable=False)
    enrolled_at = db.Column(db.DateTime, server_default=func.now())

    # Relationships
    student = db.relationship("User", back_populates="enrollments")
    course = db.relationship("Course", back_populates="enrollments")

    __table_args__ = (
        db.UniqueConstraint('student_id', 'course_id', name='check_student_course_unique'),
    )

    def __repr__(self):
        return f"<Enrollment student_id={self.student_id} course_id={self.course_id}>"

class Progress(db.Model):
    __tablename__ = 'progress'

    progress_id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    lesson_id = db.Column(db.Integer, db.ForeignKey('lessons.lesson_id'), nullable=False)
    completed = db.Column(db.Boolean, default=False)
    completed_at = db.Column(db.DateTime)

    # Relationships
    student = db.relationship("User", back_populates="progress")
    lesson = db.relationship("Lesson", back_populates="progress")

    __table_args__ = (
        db.UniqueConstraint('student_id', 'lesson_id', name='check_student_lesson_unique'),
    )

    def __repr__(self):
        return f"<Progress student_id={self.student_id} lesson_id={self.lesson_id}>"