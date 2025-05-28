from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, current_app ,make_response
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, get_jwt
from .models import User, Course, Chapter, Lesson, Enrollment, Progress, UserProfile, CourseMetadata
from . import db
from flask_wtf import FlaskForm  # Updated import
from wtforms import StringField, PasswordField, FileField, TextAreaField, IntegerField, SelectField, validators
from werkzeug.utils import secure_filename
import os

main = Blueprint('main', __name__)

# WTForms for registration, login, file upload, course management, and profile updates
class RegistrationForm(FlaskForm):  # Changed from Form to FlaskForm
    email = StringField('Email', [validators.Length(min=4, max=255), validators.Email()])
    password = PasswordField('Password', [validators.Length(min=6)])
    first_name = StringField('First Name', [validators.Length(min=1, max=50)])
    last_name = StringField('Last Name', [validators.Length(min=1, max=50)])

class LoginForm(FlaskForm):  # Changed from Form to FlaskForm
    email = StringField('Email', [validators.Length(min=4, max=255), validators.Email()])
    password = PasswordField('Password', [validators.Length(min=6)])

class UploadForm(FlaskForm):  # Updated for consistency
    file = FileField('File')

class CourseForm(FlaskForm):  # Updated for consistency
    title = StringField('Title', [validators.Length(min=1, max=255)])
    description = TextAreaField('Description')
    category = StringField('Category', [validators.Length(max=100), validators.Optional()])
    tags = StringField('Tags (comma-separated)', [validators.Optional()])

class ChapterForm(FlaskForm):  # Updated for consistency
    title = StringField('Title', [validators.Length(min=1, max=255)])
    chapter_order = IntegerField('Chapter Order', [validators.NumberRange(min=1)])

class LessonForm(FlaskForm):  # Updated for consistency
    title = StringField('Title', [validators.Length(min=1, max=255)])
    lesson_type = SelectField('Lesson Type', choices=[('video', 'Video'), ('document', 'Document'), ('quiz', 'Quiz'), ('other', 'Other')])
    file = FileField('Content File')
    lesson_order = IntegerField('Lesson Order', [validators.NumberRange(min=1)])
    duration = IntegerField('Duration (seconds, optional for videos)', [validators.Optional(), validators.NumberRange(min=1)])

class ProfileForm(FlaskForm):  # Updated for consistency
    first_name = StringField('First Name', [validators.Length(min=1, max=50)])
    last_name = StringField('Last Name', [validators.Length(min=1, max=50)])
    bio = TextAreaField('Bio', [validators.Optional()])
    profile_picture = FileField('Profile Picture', [validators.Optional()])

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
            user = User.query.filter_by(email=user_email, deleted_at=None).first()  # Added deleted_at filter
            if user:
                if user.role == 'teacher':
                    return redirect(url_for('main.teacher_home'))
                elif user.role == 'student':
                    return redirect(url_for('main.student_home'))
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

        if User.query.filter_by(email=email, deleted_at=None).first():  # Added deleted_at filter
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
    form = LoginForm()
    if request.method == 'POST':
        if form.validate_on_submit():
            email = form.email.data
            password = form.password.data
            user = User.query.filter_by(email=email, deleted_at=None).first()
            if user and user.check_password(password):
                user.last_login_at = db.func.now()
                db.session.commit()
                access_token = create_access_token(identity=email)
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return jsonify({
                        "msg": "Login successful",
                        "access_token": access_token,
                        "role": user.role,
                        "redirect_url": url_for('main.student_home' if user.role == 'student' else 'main.teacher_home' if user.role in ['teacher', 'admin'] else 'main.index')
                    }), 200
                # Non-AJAX fallback: Store token in cookie and redirect
                response = make_response(redirect(url_for('main.student_home' if user.role == 'student' else 'main.teacher_home' if user.role in ['teacher', 'admin'] else 'main.index')))
                response.set_cookie('access_token', access_token, httponly=True, secure=False, samesite='Lax')  # secure=True in production
                flash('Login successful!', 'success')
                return response
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return jsonify({"msg": "Invalid credentials"}), 401
            flash('Invalid credentials', 'error')
            return render_template('login.html', form=form), 401
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return jsonify({"msg": "Invalid form data", "errors": form.errors}), 400
        flash('Invalid form data', 'error')
        return render_template('login.html', form=form), 400
    return render_template('login.html', form=form)

@main.route('/reset_password', methods=['GET'])
def reset_password():
    flash('Password reset functionality is not yet implemented.', 'info')
    return redirect(url_for('main.login'))

@main.route('/logout', methods=['GET'])
def logout():
    response = make_response(render_template('logout.html'))
    response.delete_cookie('access_token')
    flash('Logged out successfully.', 'success')
    return response

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
    courses = Course.query.filter_by(is_published=True, deleted_at=None).all()  # Added deleted_at filter
    return render_template('courses.html', courses=courses)

@main.route('/courses/new', methods=['GET', 'POST'])
@jwt_required()
def create_course():
    current_user_email = get_jwt_identity()
    user = User.query.filter_by(email=current_user_email, deleted_at=None).first()  # Added deleted_at filter

    if user.role not in ['teacher', 'admin']:
        flash('Only teachers and admins can create courses.', 'error')
        return redirect(url_for('main.index'))

    form = CourseForm(request.form)
    if request.method == 'POST' and form.validate():
        course = Course(
            title=form.title.data,
            description=form.description.data,
            teacher_id=user.user_id,
            is_published=True
        )
        db.session.add(course)
        db.session.flush()  # Get course_id for course_metadata
        course_metadata = CourseMetadata(
            course_id=course.course_id,
            category=form.category.data,
            tags=form.tags.data.split(',') if form.tags.data else []
        )
        db.session.add(course_metadata)
        db.session.commit()
        flash('Course created successfully!', 'success')
        return redirect(url_for('main.list_courses'))

    return render_template('course_form.html', form=form)

@main.route('/courses/<int:course_id>/chapters/new', methods=['GET', 'POST'])
@jwt_required()
def create_chapter():
    current_user_email = get_jwt_identity()
    user = User.query.filter_by(email=current_user_email, deleted_at=None).first()  # Added deleted_at filter
    course = Course.query.filter_by(course_id=course_id, deleted_at=None).first() or Course.query.get_or_404(course_id)  # Added deleted_at filter

    if user.role not in ['teacher', 'admin'] or course.teacher_id != user.user_id:
        flash('You do not have permission to add chapters to this course.', 'error')
        return redirect(url_for('main.list_courses'))

    form = ChapterForm(request.form)
    if request.method == 'POST' and form.validate():
        # Check for duplicate chapter_order
        if Chapter.query.filter_by(course_id=course_id, chapter_order=form.chapter_order.data).first():
            flash('Chapter order already exists.', 'error')
            return redirect(url_for('main.create_chapter', course_id=course_id))
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
    course = Course.query.filter_by(course_id=course_id, deleted_at=None).first() or Course.query.get_or_404(course_id)  # Added deleted_at filter
    return render_template('course_detail.html', course=course)

@main.route('/chapters/<int:chapter_id>/lessons/new', methods=['GET', 'POST'])
@jwt_required()
def create_lesson(chapter_id):
    current_user_email = get_jwt_identity()
    user = User.query.filter_by(email=current_user_email, deleted_at=None).first()  # Added deleted_at filter
    chapter = Chapter.query.get_or_404(chapter_id)
    course = chapter.course

    if user.role not in ['teacher', 'admin'] or course.teacher_id != user.user_id:
        flash('You do not have permission to add lessons to this chapter.', 'error')
        return redirect(url_for('main.view_course', course_id=course.course_id))

    form = LessonForm(request.form)
    if request.method == 'POST' and form.validate():
        file = request.files.get('file')
        if not file:
            flash('A file is required for the lesson content.', 'error')
            return redirect(url_for('main.create_lesson', chapter_id=chapter_id))

        # Check for duplicate lesson_order
        if Lesson.query.filter_by(chapter_id=chapter_id, lesson_order=form.lesson_order.data).first():
            flash('Lesson order already exists.', 'error')
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
        return redirect(url_for('main.view_course', course_id=course.course_id))

    return render_template('lesson_form.html', form=form, chapter=chapter)

@main.route('/courses/<int:course_id>/enroll', methods=['POST'])
@jwt_required()
def enroll_course(course_id):
    current_user_email = get_jwt_identity()
    user = User.query.filter_by(email=current_user_email, deleted_at=None).first()  # Added deleted_at filter
    course = Course.query.filter_by(course_id=course_id, deleted_at=None).first() or Course.query.get_or_404(course_id)  # Added deleted_at filter

    if user.role != 'student':
        flash('Only students can enroll in courses.', 'error')
        return redirect(url_for('main.list_courses'))

    if Enrollment.query.filter_by(student_id=user.user_id, course_id=course_id).first():
        flash('You are already enrolled in this course.', 'error')
        return redirect(url_for('main.list_courses'))

    enrollment = Enrollment(student_id=user.user_id, course_id=course_id)
    db.session.add(enrollment)
    db.session.commit()
    flash('Successfully enrolled in the course!', 'success')
    return redirect(url_for('main.list_courses'))

@main.route('/lessons/<int:lesson_id>/complete', methods=['POST'])
@jwt_required()
def complete_lesson(lesson_id):
    current_user_email = get_jwt_identity()
    user = User.query.filter_by(email=current_user_email, deleted_at=None).first()  # Added deleted_at filter
    lesson = Lesson.query.get_or_404(lesson_id)

    if user.role != 'student':
        flash('Only students can mark lessons as complete.', 'error')
        return redirect(url_for('main.index'))

    enrollment = Enrollment.query.filter_by(student_id=user.user_id, course_id=lesson.chapter.course_id).first()
    if not enrollment:
        flash('You must be enrolled in the course to mark lessons as complete.', 'error')
        return redirect(url_for('main.list_courses'))

    progress = Progress.query.filter_by(student_id=user.user_id, lesson_id=lesson_id).first()
    if progress:
        if progress.completed:
            flash('Lesson already marked as complete.', 'info')
        else:
            progress.completed = True
            progress.completed_at = db.func.current_timestamp()
            db.session.commit()
            flash('Lesson marked as complete!', 'success')
    else:
        progress = Progress(student_id=user.user_id, lesson_id=lesson_id, completed=True)
        db.session.add(progress)
        db.session.commit()
        flash('Lesson marked as complete!', 'success')

    return redirect(url_for('main.view_course', course_id=lesson.chapter.course_id))

@main.route('/teacher/home', methods=['GET'])
@jwt_required()
def teacher_home():
    current_user_email = get_jwt_identity()
    user = User.query.filter_by(email=current_user_email, deleted_at=None).first()  # Added deleted_at filter

    if user.role not in ['teacher', 'admin']:
        flash('Access restricted to teachers.', 'error')
        return redirect(url_for('main.index'))

    courses = Course.query.filter_by(teacher_id=user.user_id, deleted_at=None).all()  # Added deleted_at filter
    return render_template('teacher_home.html', user=user, courses=courses)

@main.route('/teacher/profile', methods=['GET', 'POST'])
@jwt_required()
def teacher_profile():
    current_user_email = get_jwt_identity()
    user = User.query.filter_by(email=current_user_email, deleted_at=None).first()  # Added deleted_at filter

    if user.role not in ['teacher', 'admin']:
        flash('Access restricted to teachers.', 'error')
        return redirect(url_for('main.index'))

    profile = user.profile or UserProfile(user_id=user.user_id)  # Create new profile if none exists
    form = ProfileForm(request.form, first_name=user.first_name, last_name=user.last_name, bio=profile.bio)

    if request.method == 'POST' and form.validate():
        user.first_name = form.first_name.data
        user.last_name = form.last_name.data
        profile.bio = form.bio.data
        if 'profile_picture' in request.files:
            file = request.files['profile_picture']
            if file:
                filename = secure_filename(file.filename)
                minio_client = current_app.minio_client
                bucket_name = current_app.config.get('MINIO_BUCKET', 'learning_portal')
                if not minio_client.bucket_exists(bucket_name):
                    minio_client.make_bucket(bucket_name)
                minio_client.put_object(bucket_name, filename, file.stream, length=-1, part_size=10*1024*1024)
                profile.profile_picture_url = f"{bucket_name}/{filename}"
                profile.updated_at = db.func.now()
        if profile not in db.session:
            db.session.add(profile)
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('main.teacher_profile'))

    courses = Course.query.filter_by(teacher_id=user.user_id, deleted_at=None).all()  # Added deleted_at filter
    return render_template('teacher_profile.html', user=user, form=form, courses=courses, profile=profile)

@main.route('/student/home', methods=['GET'])
def student_home():
    # For testing, use a hardcoded user (remove in production)
    user = User.query.filter_by(email='nilalinuxa4n@gmail.com', deleted_at=None).first()
    if not user or user.role != 'student':
        flash('Access denied.', 'error')
        return redirect(url_for('main.index'))
    
    # Get enrolled courses and progress
    enrollments = Enrollment.query.filter_by(student_id=user.user_id).all()
    courses = []
    for enrollment in enrollments:
        course = Course.query.filter_by(id=enrollment.course_id, deleted_at=None).first()
        if course:
            progress = Progress.query.filter_by(
                student_id=user.user_id,
                course_id=course.id
            ).first()
            courses.append({
                'course': course,
                'progress': progress.completed_percentage if progress else 0
            })
    
    return render_template('student_home.html', user=user, courses=courses, user_role=user.role)
@main.route('/student/profile', methods=['GET', 'POST'])
@jwt_required()
def student_profile():
    current_user_email = get_jwt_identity()
    user = User.query.filter_by(email=current_user_email, deleted_at=None).first()  # Added deleted_at filter

    if user.role != 'student':
        flash('Access restricted to students.', 'error')
        return redirect(url_for('main.index'))

    profile = user.profile or UserProfile(user_id=user.user_id)  # Create new profile if none exists
    form = ProfileForm(request.form, first_name=user.first_name, last_name=user.last_name, bio=profile.bio)

    if request.method == 'POST' and form.validate():
        user.first_name = form.first_name.data
        user.last_name = form.last_name.data
        profile.bio = form.bio.data
        if 'profile_picture' in request.files:
            file = request.files['profile_picture']
            if file:
                filename = secure_filename(file.filename)
                minio_client = current_app.minio_client
                bucket_name = current_app.config.get('MINIO_BUCKET', 'learning_portal')
                if not minio_client.bucket_exists(bucket_name):
                    minio_client.make_bucket(bucket_name)
                minio_client.put_object(bucket_name, filename, file.stream, length=-1, part_size=10*1024*1024)
                profile.profile_picture_url = f"{bucket_name}/{filename}"
                profile.updated_at = db.func.now()
        if profile not in db.session:
            db.session.add(profile)
        db.session.commit()
        flash('Profile updated successfully!', 'success')
        return redirect(url_for('main.student_profile'))

    enrollments = Enrollment.query.filter_by(student_id=user.user_id).all()
    return render_template('student_profile.html', user=user, form=form, enrollments=enrollments, profile=profile)