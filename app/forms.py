from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, TextAreaField, IntegerField, FileField, SelectField
from wtforms.validators import DataRequired, Email, Length, Optional

class RegistrationForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email(), Length(min=4, max=255)])
    password = PasswordField('Password', validators=[DataRequired(), Length(min=6)])
    first_name = StringField('First Name', validators=[DataRequired(), Length(min=1, max=50)])
    last_name = StringField('Last Name', validators=[DataRequired(), Length(min=1, max=50)])

class UploadForm(FlaskForm):
    file = FileField('File', validators=[DataRequired()])

class CourseForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(min=1, max=255)])
    description = TextAreaField('Description', validators=[DataRequired()])

class ChapterForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(min=1, max=255)])
    chapter_order = IntegerField('Chapter Order', validators=[DataRequired()])

class LessonForm(FlaskForm):
    title = StringField('Title', validators=[DataRequired(), Length(min=1, max=255)])
    lesson_type = SelectField('Lesson Type', choices=[('video', 'Video'), ('document', 'Document')], validators=[DataRequired()])
    file = FileField('File', validators=[DataRequired()])
    lesson_order = IntegerField('Lesson Order', validators=[DataRequired()])
    duration = IntegerField('Duration (seconds)', validators=[Optional()])