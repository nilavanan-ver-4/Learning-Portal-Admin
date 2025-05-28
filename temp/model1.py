from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import enum

db = SQLAlchemy()

class UserRole(enum.Enum):
    student = "student"
    teacher = "teacher"
    admin = "admin"

class User(db.Model):
    __tablename__ = 'users'

    user_id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(50))
    last_name = db.Column(db.String(50))
    role = db.Column(db.Enum(UserRole), default=UserRole.student, nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=db.func.now())
    last_login_at = db.Column(db.DateTime)
    reset_token = db.Column(db.String(255))
    deleted_at = db.Column(db.DateTime)

    enrollments = db.relationship("Enrollment", back_populates="student")
    progress = db.relationship("Progress", back_populates="student")
    profile = db.relationship("UserProfile", back_populates="user", uselist=False)
    courses = db.relationship("Course", back_populates="teacher")

    def set_password(self, password):
        from werkzeug.security import generate_password_hash
        self.password_hash = generate_password_hash(password, method='scrypt')

    def check_password(self, password):
        from werkzeug.security import check_password_hash
        return check_password_hash(self.password_hash, password)

    def __repr__(self):
        return f"<User {self.email}>"

class Course(db.Model):
    __tablename__ = 'courses'

    course_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    description = db.Column(db.Text)
    is_published = db.Column(db.Boolean, default=False)
    teacher_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.now())
    updated_at = db.Column(db.DateTime, onupdate=db.func.now())
    deleted_at = db.Column(db.DateTime)

    teacher = db.relationship("User", back_populates="courses")
    enrollments = db.relationship("Enrollment", back_populates="course")
    progress = db.relationship("Progress", back_populates="course", overlaps="enrollments")
    chapters = db.relationship("Chapter", back_populates="course")
    course_metadata = db.relationship("CourseMetadata", back_populates="course", uselist=False)

    def __repr__(self):
        return f"<Course {self.title}>"

class Enrollment(db.Model):
    __tablename__ = 'enrollments'

    enrollment_id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.course_id'), nullable=False)
    enrolled_at = db.Column(db.DateTime, default=db.func.now())

    student = db.relationship("User", back_populates="enrollments")
    course = db.relationship("Course", back_populates="enrollments")

    __table_args__ = (
        db.UniqueConstraint('student_id', 'course_id', name='uix_student_course'),
    )

    def __repr__(self):
        return f"<Enrollment student_id={self.student_id} course_id={self.course_id}>"

class Progress(db.Model):
    __tablename__ = 'progress'

    progress_id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.course_id'), nullable=True)
    lesson_id = db.Column(db.Integer, db.ForeignKey('lessons.lesson_id'), nullable=True)
    completed = db.Column(db.Boolean, default=False)
    completed_percentage = db.Column(db.Float, default=0.0)
    completed_at = db.Column(db.DateTime)

    student = db.relationship("User", back_populates="progress")
    lesson = db.relationship("Lesson", back_populates="progress")
    course = db.relationship("Course", back_populates="progress", overlaps="enrollments")

    __table_args__ = (
        db.UniqueConstraint('student_id', 'lesson_id', name='check_student_lesson_unique'),
        db.UniqueConstraint('student_id', 'course_id', name='check_student_course_progress_unique'),
        db.Index('idx_student_lesson_unique', 'student_id', 'lesson_id', unique=True, postgresql_where=db.text('lesson_id IS NOT NULL')),
        db.Index('idx_student_course_unique', 'student_id', 'course_id', unique=True, postgresql_where=db.text('course_id IS NOT NULL')),
    )

    def __repr__(self):
        return f"<Progress student_id={self.student_id} course_id={self.course_id} lesson_id={self.lesson_id}>"

class Lesson(db.Model):
    __tablename__ = 'lessons'

    lesson_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    lesson_type = db.Column(db.String(50), nullable=False)
    minio_url = db.Column(db.String(255))
    chapter_id = db.Column(db.Integer, db.ForeignKey('chapters.chapter_id'), nullable=False)
    lesson_order = db.Column(db.Integer, nullable=False)
    duration = db.Column(db.Integer)
    created_at = db.Column(db.DateTime, default=db.func.now())
    updated_at = db.Column(db.DateTime, onupdate=db.func.now())

    chapter = db.relationship("Chapter", back_populates="lessons")
    progress = db.relationship("Progress", back_populates="lesson")

    def __repr__(self):
        return f"<Lesson {self.title}>"

class Chapter(db.Model):
    __tablename__ = 'chapters'

    chapter_id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(255), nullable=False)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.course_id'), nullable=False)
    chapter_order = db.Column(db.Integer, nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.now())
    updated_at = db.Column(db.DateTime, onupdate=db.func.now())

    course = db.relationship("Course", back_populates="chapters")
    lessons = db.relationship("Lesson", back_populates="chapter")

    def __repr__(self):
        return f"<Chapter {self.title}>"

class UserProfile(db.Model):
    __tablename__ = 'user_profiles'

    profile_id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    bio = db.Column(db.Text)
    profile_picture_url = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=db.func.now())
    updated_at = db.Column(db.DateTime, onupdate=db.func.now())

    user = db.relationship("User", back_populates="profile")

    def __repr__(self):
        return f"<UserProfile user_id={self.user_id}>"

class CourseMetadata(db.Model):
    __tablename__ = 'course_metadata'

    metadata_id = db.Column(db.Integer, primary_key=True)
    course_id = db.Column(db.Integer, db.ForeignKey('courses.course_id'), nullable=False)
    category = db.Column(db.String(100))
    tags = db.Column(db.JSON)
    created_at = db.Column(db.DateTime, default=db.func.now())
    updated_at = db.Column(db.DateTime, onupdate=db.func.now())

    course = db.relationship("Course", back_populates="course_metadata")

    def __repr__(self):
        return f"<CourseMetadata course_id={self.course_id}>"