from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, current_app
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, get_jwt
from .models import User, Course, Chapter, Lesson, Enrollment, Progress
from . import db
from wtforms import Form, StringField, PasswordField, FileField, TextAreaField, IntegerField, SelectField, validators
from werkzeug.utils import secure_filename
import os

main = Blueprint('main', __name__)

# WTForms for registration, file upload, and course management
class RegistrationForm(Form):
    email = StringField('Email', [validators.Length(min=4, max=255), validators.Email()])
    password = PasswordField('Password', [validators.Length(min=6)])
    first_name = StringField('First Name', [validators.Length(min=1, max=50)])
    last_name = StringField('Last Name', [validators.Length(min=1, max=50)])

class UploadForm(Form):
    file = FileField('File')

class CourseForm(Form):
    title = StringField('Title', [validators.Length(min=1, max=255)])
    description = TextAreaField('Description')

class ChapterForm(Form):
    title = StringField('Title', [validators.Length(min=1, max=255)])
    chapter_order = IntegerField('Chapter Order', [validators.NumberRange(min=1)])

class LessonForm(Form):
    title = StringField('Title', [validators.Length(min=1, max=255)])
    lesson_type = SelectField('Lesson Type', choices=[('video', 'Video'), ('document', 'Document'), ('quiz', 'Quiz'), ('other', 'Other')])
    file = FileField('Content File')
    lesson_order = IntegerField('Lesson Order', [validators.NumberRange(min=1)])
    duration = IntegerField('Duration (seconds, optional for videos)', [validators.Optional()])

# Error handler for unauthorized access
@jwt_required()
def handle_unauthorized():
    flash('Please log in to access this page.', 'error')
    return redirect(url_for('main.login'))

@main.route('/')
def index():
    # Check if the user is authenticated
    user = None
    try:
        jwt_data = get_jwt()
        if jwt_data:
            user_email = get_jwt_identity()
            user = User.query.filter_by(email=user_email).first()
    except:
        pass  # User is not authenticated
    return render_template('index.html', user=user)

@main.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm(request.form)
    if request.method == 'POST' and form.validate():
        email = form.email.data
        password = form.password.data
        first_name = form.first_name.data
        last_name = form.last_name.data

        if User.query.filter_by(email=email).first():
            flash('Email already exists', 'error')
            return redirect(url_for('main.register'))

        user = User(email=email, first_name=first_name, last_name=last_name, role="student")
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        flash('Registration successful! Please log in.', 'success')
        return redirect(url_for('main.login'))

    return render_template('register.html', form=form)

@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')

        user = User.query.filter_by(email=email).first()
        if user and user.check_password(password):
            access_token = create_access_token(identity=email)
            response = jsonify({"msg": "Login successful", "access_token": access_token})
            return response, 200
        return jsonify({"msg": "Invalid credentials"}), 401

    return render_template('login.html')

@main.route('/logout')
def logout():
    # For a stateless JWT setup, logout is handled client-side by removing the token
    return render_template('logout.html')

@main.route('/upload', methods=['GET', 'POST'])
@jwt_required()
def upload():
    form = UploadForm(request.form)
    if request.method == 'POST':
        file = request.files.get('file')
        if file:
            filename = secure_filename(file.filename)
            minio_client = current_app.minio_client
            bucket_name = current_app.config.get('MINIO_BUCKET', 'learning_portal')

            if not minio_client.bucket_exists(bucket_name):
                minio_client.make_bucket(bucket_name)

            minio_client.put_object(
                bucket_name,
                filename,
                file.stream,
                length=-1,
                part_size=10*1024*1024
            )
            flash(f'File {filename} uploaded successfully!', 'success')
            return redirect(url_for('main.upload'))

    return render_template('upload.html', form=form)

@main.route('/courses', methods=['GET'])
def list_courses():
    courses = Course.query.filter_by(is_published=True).all()
    return render_template('courses.html', courses=courses)

@main.route('/courses/new', methods=['GET', 'POST'])
@jwt_required()
def create_course():
    current_user_email = get_jwt_identity()
    user = User.query.filter_by(email=current_user_email).first()

    if user.role not in ['teacher', 'admin']:
        flash('Only teachers and admins can create courses.', 'error')
        return redirect(url_for('main.index'))

    form = CourseForm(request.form)
    if request.method == 'POST' and form.validate():
        course = Course(
            title=form.title.data,
            description=form.description.data,
            teacher_id=user.id,
            is_published=True
        )
        db.session.add(course)
        db.session.commit()
        flash('Course created successfully!', 'success')
        return redirect(url_for('main.list_courses'))

    return render_template('course_form.html', form=form)

@main.route('/courses/<int:course_id>/chapters/new', methods=['GET', 'POST'])
@jwt_required()
def create_chapter(course_id):
    current_user_email = get_jwt_identity()
    user = User.query.filter_by(email=current_user_email).first()
    course = Course.query.get_or_404(course_id)

    if user.role not in ['teacher', 'admin'] or course.teacher_id != user.id:
        flash('You do not have permission to add chapters to this course.', 'error')
        return redirect(url_for('main.list_courses'))

    form = ChapterForm(request.form)
    if request.method == 'POST' and form.validate():
        chapter = Chapter(
            title=form.title.data,
            course_id=course_id,
            chapter_order=form.chapter_order.data
        )
        db.session.add(chapter)
        db.session.commit()
        flash('Chapter created successfully!', 'success')
        return redirect(url_for('main.view_course', course_id=course_id))

    return render_template('chapter_form.html', form=form, course=course)

@main.route('/courses/<int:course_id>', methods=['GET'])
def view_course(course_id):
    course = Course.query.get_or_404(course_id)
    return render_template('course_detail.html', course=course)

@main.route('/chapters/<int:chapter_id>/lessons/new', methods=['GET', 'POST'])
@jwt_required()
def create_lesson(chapter_id):
    current_user_email = get_jwt_identity()
    user = User.query.filter_by(email=current_user_email).first()
    chapter = Chapter.query.get_or_404(chapter_id)
    course = chapter.course

    if user.role not in ['teacher', 'admin'] or course.teacher_id != user.id:
        flash('You do not have permission to add lessons to this chapter.', 'error')
        return redirect(url_for('main.view_course', course_id=course.id))

    form = LessonForm(request.form)
    if request.method == 'POST' and form.validate():
        file = request.files.get('file')
        if not file:
            flash('A file is required for the lesson content.', 'error')
            return redirect(url_for('main.create_lesson', chapter_id=chapter_id))

        filename = secure_filename(file.filename)
        minio_client = current_app.minio_client
        bucket_name = current_app.config.get('MINIO_BUCKET', 'learning_portal')

        if not minio_client.bucket_exists(bucket_name):
            minio_client.make_bucket(bucket_name)

        minio_client.put_object(
            bucket_name,
            filename,
            file.stream,
            length=-1,
            part_size=10*1024*1024
        )

        lesson = Lesson(
            title=form.title.data,
            lesson_type=form.lesson_type.data,
            minio_url=f"{bucket_name}/{filename}",
            chapter_id=chapter_id,
            lesson_order=form.lesson_order.data,
            duration=form.duration.data
        )
        db.session.add(lesson)
        db.session.commit()
        flash('Lesson created successfully!', 'success')
        return redirect(url_for('main.view_course', course_id=course.id))

    return render_template('lesson_form.html', form=form, chapter=chapter)

@main.route('/courses/<int:course_id>/enroll', methods=['POST'])
@jwt_required()
def enroll_course(course_id):
    current_user_email = get_jwt_identity()
    user = User.query.filter_by(email=current_user_email).first()
    course = Course.query.get_or_404(course_id)

    if user.role != 'student':
        flash('Only students can enroll in courses.', 'error')
        return redirect(url_for('main.list_courses'))

    if Enrollment.query.filter_by(student_id=user.id, course_id=course_id).first():
        flash('You are already enrolled in this course.', 'error')
        return redirect(url_for('main.list_courses'))

    enrollment = Enrollment(student_id=user.id, course_id=course_id)
    db.session.add(enrollment)
    db.session.commit()
    flash('Successfully enrolled in the course!', 'success')
    return redirect(url_for('main.list_courses'))

@main.route('/lessons/<int:lesson_id>/complete', methods=['POST'])
@jwt_required()
def complete_lesson(lesson_id):
    current_user_email = get_jwt_identity()
    user = User.query.filter_by(email=current_user_email).first()
    lesson = Lesson.query.get_or_404(lesson_id)

    if user.role != 'student':
        flash('Only students can mark lessons as complete.', 'error')
        return redirect(url_for('main.index'))

    enrollment = Enrollment.query.filter_by(student_id=user.id, course_id=lesson.chapter.course_id).first()
    if not enrollment:
        flash('You must be enrolled in the course to mark lessons as complete.', 'error')
        return redirect(url_for('main.list_courses'))

    progress = Progress.query.filter_by(student_id=user.id, lesson_id=lesson_id).first()
    if progress:
        if progress.completed:
            flash('Lesson already marked as complete.', 'info')
        else:
            progress.completed = True
            progress.completed_at = db.func.current_timestamp()
            db.session.commit()
            flash('Lesson marked as complete!', 'success')
    else:
        progress = Progress(student_id=user.id, lesson_id=lesson_id, completed=True)
        db.session.add(progress)
        db.session.commit()
        flash('Lesson marked as complete!', 'success')

    return redirect(url_for('main.view_course', course_id=lesson.chapter.course_id))