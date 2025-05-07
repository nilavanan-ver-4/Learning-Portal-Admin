from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, current_app
from flask_jwt_extended import create_access_token, jwt_required
from .models import User
from . import db
from wtforms import Form, StringField, PasswordField, FileField, validators
from werkzeug.utils import secure_filename

main = Blueprint('main', __name__)

# WTForms for registration and file upload
class RegistrationForm(Form):
    email = StringField('Email', [validators.Length(min=4, max=255), validators.Email()])
    password = PasswordField('Password', [validators.Length(min=6)])
    first_name = StringField('First Name', [validators.Length(min=1, max=50)])
    last_name = StringField('Last Name', [validators.Length(min=1, max=50)])

class UploadForm(Form):
    file = FileField('File')

@main.route('/')
def index():
    return render_template('index.html')

@main.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm(request.form)
    if request.method == 'POST' and form.validate():
        email = form.email.data
        password = form.password.data
        first_name = form.first_name.data
        last_name = form.last_name.data

        # Check if user already exists
        if User.query.filter_by(email=email).first():
            flash('Email already exists', 'error')
            return redirect(url_for('main.register'))

        # Create new user
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
            return jsonify(access_token=access_token), 200
        return jsonify({"msg": "Invalid credentials"}), 401

    return render_template('login.html')

@main.route('/upload', methods=['GET', 'POST'])
@jwt_required()
def upload():
    form = UploadForm(request.form)
    if request.method == 'POST':
        file = request.files.get('file')
        if file:
            filename = secure_filename(file.filename)
            # Upload to MinIO using current_app
            minio_client = current_app.minio_client
            bucket_name = "mybucket"

            # Create bucket if it doesn't exist
            if not minio_client.bucket_exists(bucket_name):
                minio_client.make_bucket(bucket_name)

            # Upload file to MinIO
            minio_client.put_object(
                bucket_name,
                filename,
                file.stream,
                length=-1,
                part_size=10*1024*1024  # 10MB part size
            )
            flash(f'File {filename} uploaded successfully!', 'success')
            return redirect(url_for('main.upload'))

    return render_template('upload.html', form=form)