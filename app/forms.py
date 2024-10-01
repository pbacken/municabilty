import sqlalchemy as sa
from app import db
from app.models import User
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, SelectField, \
    FieldList, FormField, Form, HiddenField, IntegerField, DateField
from wtforms.validators import DataRequired, ValidationError, Email, EqualTo, Length, NumberRange
from flask_ckeditor import CKEditorField


class LoginForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Sign In')


class RegistrationForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    email = StringField('Email', validators=[DataRequired(), Email()])
    user_city = StringField('City', validators=[DataRequired()])
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Register')

    def validate_username(self, username):
        user = db.session.scalar(sa.select(User).where(
            User.username == username.data))
        if user is not None:
            raise ValidationError('Please use a different username.')

    def validate_email(self, email):
        user = db.session.scalar(sa.select(User).where(
            User.email == email.data))
        if user is not None:
            raise ValidationError('Please use a different email address.')


class EditProfileForm(FlaskForm):
    username = StringField('Username', validators=[DataRequired()])
    user_city = StringField('City', render_kw={'readonly': True})
    about_me = TextAreaField('About me', validators=[Length(min=0, max=140)])

    submit = SubmitField('Submit')

    def __init__(self, original_username, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_username = original_username

    def validate_username(self, username):
        if username.data != self.original_username:
            user = db.session.scalar(sa.select(User).where(
                User.username == username.data))
            if user is not None:
                raise ValidationError('Please use a different username.')


class ResetPasswordRequestForm(FlaskForm):
    email = StringField('Email', validators=[DataRequired(), Email()])
    submit = SubmitField('Request Password Reset')


class ResetPasswordForm(FlaskForm):
    password = PasswordField('Password', validators=[DataRequired()])
    password2 = PasswordField(
        'Repeat Password', validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField('Request Password Reset')


class MeetingForm(FlaskForm):
    meeting_type = SelectField('Meeting Type', choices=[('council', 'City Council'),
                                                         ('hrc', 'Human Rights Commission'),
                                                         ('plan', 'Planning Commission'),
                                                         ('prf', 'Parks, Rec and Forestry'),
                                                         ('sen', 'Senior Commission'),
                                                         ('sus', 'Sustainability Committee'),
                                                         ('chart', 'Charter Commission')])
    agenda_file = FileField("File",
                            validators=[FileRequired()])

    submit = SubmitField('Create Meeting')


class EditMinutesForm(FlaskForm):
    meeting_type = SelectField('Meeting Type', choices=[('council', 'City Council'),
                                                        ('hrc', 'Human Rights Commission'),
                                                        ('plan', 'Planning Commission'),
                                                        ('prf', 'Parks, Rec and Forestry'),
                                                        ('sen', 'Senior Commission'),
                                                        ('sus', 'Sustainability Committee'),
                                                        ('chart', 'Charter Commission')],
                                                render_kw={'style': 'width: 275px'})

    content = CKEditorField('Content', validators=[DataRequired()])

    submit = SubmitField('Update Minutes')


class DiaryForm(FlaskForm):
    meeting_type_read_only = SelectField('Meeting Type', choices=[('council', 'City Council'),
                                                        ('hrc', 'Human Rights Commission'),
                                                        ('plan', 'Planning Commission'),
                                                        ('prf', 'Parks, Rec and Forestry'),
                                                        ('sen', 'Senior Commission'),
                                                        ('sus', 'Sustainability Committee'),
                                                        ('chart', 'Charter Commission')],

                                          render_kw={'style': 'width: 275px', 'readonly': True})

    diary_content = CKEditorField('Diary Content', render_kw={'readonly': True})


class MembersPresentForm(Form):
    """A form for members"""
    member_meet = BooleanField()


class UpdateAgendaForm(FlaskForm):
    meet_type = SelectField('Meeting Type')
    staff = SelectField('Staff Present', choices=[('council', 'City Council'),
                                                         ('hrc', 'Human Rights Commission'),
                                                         ('plan', 'Planning Commission'),
                                                         ('prf', 'Parks, Rec and Forestry'),
                                                         ('sen', 'Senior Commission'),
                                                         ('sus', 'Sustainability Committee'),
                                                         ('chart', 'Charter Commission')])

    members_present = FieldList(FormField(MembersPresentForm), min_entries=1)


class EntityMemberForm(FlaskForm):
    member_first_name = StringField('First Name', validators=[DataRequired()])
    member_last_name = StringField('Last Name', validators=[DataRequired()])
    title = StringField('Title', validators=[DataRequired()])
    position = StringField('Position', validators=[DataRequired()])

    group_code = SelectField('Group Type', choices=[('council', 'City Council'),
                                                    ('hrc', 'Human Rights Commission'),
                                                    ('plan', 'Planning Commission'),
                                                    ('prf', 'Parks, Rec and Forestry'),
                                                    ('sen', 'Senior Commission'),
                                                    ('sus', 'Sustainability Committee'),
                                                    ('chart', 'Charter Commission'),
                                                    ('staff', 'Staff Member')])

    start_date = DateField('Start Date')
    end_date = DateField('End Date')
    submit = SubmitField('Submit')


class EntityGroupForm(FlaskForm):
    group_type = StringField('Group Name', validators=[DataRequired()])
    group_code = StringField('Group Code', validators=[DataRequired()])

    submit = SubmitField('Add New Member')

