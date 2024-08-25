import json

import sqlalchemy as sa
import os
from app import app, db
from app.email import send_password_reset_email
from app.forms import LoginForm, RegistrationForm, EditProfileForm, ResetPasswordRequestForm, \
    ResetPasswordForm, MeetingForm, MembersPresentForm, UpdateAgendaForm
from app.models import User, EntityName, EntityMembers, EntityGroups
from datetime import datetime, timezone
from flask import render_template, flash, redirect, url_for, request, session, copy_current_request_context, abort
from flask_login import current_user, login_user, logout_user, login_required
from urllib.parse import urlsplit
from flask_socketio import SocketIO, emit, disconnect
from flask_wtf.csrf import CSRFError
from threading import Lock
import assemblyai as aai
import threading
from flask_wtf.file import MultipleFileField, FileRequired
from werkzeug.utils import secure_filename
from app.func_agenda.agenda_parse import openai_agenda, to_pretty_json, agenda_temp, create_motion_list
from app.func_agenda.agenda_form_config import file_list_form_builder
import csv
from collections import namedtuple
from wtforms import SubmitField

async_mode = None
socketio = SocketIO(app, async_mode=async_mode)
thread = None
thread_lock = Lock()
aai.settings.api_key = "68b893a3d9d343638b42e03a065b25fb"
app.jinja_env.filters['tojson_pretty'] = to_pretty_json

app.config.update(
    # Flask-Dropzone config:
    DROPZONE_DEFAULT_MESSAGE='<i class="size-48" data-feather="file"></i><br><br>Drag your PDF here<br>Or'
                             '<br>Click to Browse Files',
    DROPZONE_ENABLE_CSRF=True,
    DROPZONE_ALLOWED_FILE_CUSTOM=True,
    DROPZONE_ALLOWED_FILE_TYPE='.pdf',
    DROPZONE_MAX_FILE_SIZE=3,
    # DROPZONE_UPLOAD_ON_CLICK=True,
    # DROPZONE_IN_FORM=True,
    DROPZONE_UPLOAD_ACTION='handle_upload',  # URL or endpoint
    # DROPZONE_REDIRECT_VIEW='completed',
    # DROPZONE_UPLOAD_BTN_ID='submit'
)


def background_thread():
    """Example of how to send server generated events to clients."""
    count = 0


@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.now(timezone.utc)
        db.session.commit()


@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html', title='Home')
    # return render_template('comingsoon.html', title='CivicHub')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user = db.session.scalar(
            sa.select(User).where(User.username == form.username.data))
        if user is None or not user.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user, remember=form.remember_me.data)
        next_page = request.args.get('next')
        if not next_page or urlsplit(next_page).netloc != '':
            next_page = url_for('index')
        return redirect(url_for('index'))
    return render_template('auth-login.html', title='Sign In', form=form)


@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('index'))


@app.route('/user/<username>')
@login_required
def user(username):
    user = db.first_or_404(sa.select(User).where(User.username == username))
    posts = [
        {'author': user, 'body': 'Test post #1'},
        {'author': user, 'body': 'Test post #2'}
    ]
    return render_template('user.html', user=user, posts=posts)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data, user_city=form.user_city.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('auth-register.html', title='Register', form=form)


@app.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    form = EditProfileForm(current_user.username)
    if form.validate_on_submit():
        current_user.username = form.username.data
        current_user.about_me = form.about_me.data
        db.session.commit()
        flash('Your changes have been saved.')
        return redirect(url_for('edit_profile'))
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.about_me.data = current_user.about_me
        form.user_city.data = current_user.user_city
    return render_template('edit_profile.html', title='Edit Profile',
                           form=form)


@app.route('/reset_password_request', methods=['GET', 'POST'])
def reset_password_request():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = ResetPasswordRequestForm()
    if form.validate_on_submit():
        user = db.session.scalar(
            sa.select(User).where(User.email == form.email.data))
        if user:
            send_password_reset_email(user)
        flash('Check your email for the instructions to reset your password')
        return redirect(url_for('login'))
    return render_template('reset_password_request.html',
                           title='Reset Password', form=form)


@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    user = User.verify_reset_password_token(token)
    if not user:
        return redirect(url_for('index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset.')
        return redirect(url_for('login'))
    return render_template('reset_password.html', form=form)


@app.route('/meeting', methods=['GET', 'POST'])
def meeting():
    # agenda_doc = "GV_meeting.pdf"
    # agenda_doc = "meeting.pdf"
    # agenda_doc = "crystal_meeting.pdf"
    agenda_doc = "new_hope_meeting.pdf"
    agenda_text = openai_agenda(agenda_doc)

    return render_template('agenda.html', agenda_text=agenda_text)


@app.errorhandler(413)
def too_large(e):
    return "File is too large", 413


@app.errorhandler(CSRFError)
def csrf_error(e):
    return e.description, 400


@app.route('/create_meeting')
@login_required
def create_meeting_2():
    form = MeetingForm()
    return render_template('meeting2.html', title='Create Meeting', form=form)


@app.route('/create_meeting', methods=['POST'])
@login_required
def create_meeting():

    uploaded_file = request.files['file']
    filename = secure_filename(uploaded_file.filename)
    if filename != '':
        file_ext = os.path.splitext(filename)[1]
        if file_ext not in app.config['UPLOAD_EXTENSIONS']:
            return "Invalid file", 400
    uploaded_file.save(os.path.join(app.config['UPLOAD_PATH'], filename))
    # meeting_type = form.meeting_type.data

    return redirect(url_for('index'))


@app.route('/create_meeting_3', methods=['GET'])
@login_required
def create_meeting_3():
    print(app.config['DROPZONE_DEFAULT_MESSAGE'])

    return render_template('meeting3.html', title='Create Meeting')
    # return render_template('dz_test.html', title='Create Meeting')


@app.route('/upload', methods=['POST'])
def handle_upload():
    print('uploading...')

    f = request.files.get('file')
    filename = secure_filename(f.filename)
    if filename != '':
        f.save(os.path.join(app.config['UPLOAD_PATH'], filename))

    # return '', 204
    return render_template('process-agenda.html', filename=filename)


@app.route('/process-agenda/<filename>')
def process_agenda_function(filename):

    # agenda = openai_agenda(secure_filename(filename))

    agenda = {'meet_type': 'City Council Regular Meeting', 'date': 'April 4, 2023', 'time': '6:30 PM', 'location': 'Council Chambers', 'sections': [
        {'number': 1, 'title': 'Call to Order',
         'subitems': [{'number': 'A', 'title': 'Pledge of Allegiance and Land Acknowledgement'},
                      {'number': 'B', 'title': 'Roll Call'},
                      {'number': 'C', 'title': "Proclamation Recognizing April as Parkinson's Awareness Month"},
                      {'number': 'D', 'title': 'Proclamation Recognizing April as Fair Housing Month'}]},
        {'number': 2, 'title': 'Additions and Corrections to Agenda'}, {'number': 3, 'title': 'Consent Agenda',
                                                                        'subitems': [{'number': 'A',
                                                                                      'title': 'Approval of City Council Minutes',
                                                                                      'subitems': [{'number': '1',
                                                                                                    'title': 'Minutes of the Regular City Council Meeting of March 21, 2023'}]},
                                                                                     {'number': 'B',
                                                                                      'title': 'Approval of City Check Registers'},
                                                                                     {'number': 'C',
                                                                                      'title': 'Licenses', 'subitems': [
                                                                                         {'number': '1',
                                                                                          'title': 'General Business Licenses - Fireworks Sales'}]},
                                                                                     {'number': 'D',
                                                                                      'title': 'Bids, Quotes, and Contracts',
                                                                                      'subitems': [{'number': '1',
                                                                                                    'title': 'Approve Contract for Brush Pick-Up with Bratt Tree Company'},
                                                                                                   {'number': '2',
                                                                                                    'title': 'Approve Contract for Gate Valve Repairs with Valley Rich Co., Inc.'},
                                                                                                   {'number': '3',
                                                                                                    'title': 'Approve Purchase of Replacement Outdoor Hockey Rink Dasher Boards, Steel Components, and Fencing for Scheid Park'},
                                                                                                   {'number': '4',
                                                                                                    'title': 'Approve Independent Contractor and Court Rental Agreement with Twin City Tennis Camps'}]},
                                                                                     {'number': 'E',
                                                                                      'title': 'Adopt Resolution No. 23-017 Approving Amendment to Compensation and Classification Tables'},
                                                                                     {'number': 'F',
                                                                                      'title': 'Receive and File 2022 Pay Equity Report'}]},
        {'number': 4, 'title': 'Public Hearing'}, {'number': 5, 'title': 'Old Business'},
        {'number': 6, 'title': 'New Business', 'subitems': [{'number': 'A',
                                                             'title': 'Second Consideration of Ordinance No. 761 Amending the 2023 Master Fee Schedule for Items Related to Micromobility Licenses'},
                                                            {'number': 'B', 'title': 'Review of Council Calendar'},
                                                            {'number': 'C', 'title': 'Mayor and Council Communications',
                                                             'subitems': [{'number': '1',
                                                                           'title': 'Other Committee/Meeting updates'}]}]},
        {'number': 7, 'title': 'Adjournment'}]}

    # print(agenda)
    return render_template('meeting-config.html', agenda=agenda)


@app.route('/meeting10')
def meeting10():
    # City Council Regular Meeting
    agenda = agenda_temp()
    meet_type = agenda['meet_type']
    meet_default = ""

    # Set Meeting Type Field
    meeting_type = db.session.query(EntityGroups).filter(EntityGroups.entity_code == current_user.user_city_code).all()
    for mtypes in meeting_type:
        if mtypes.group_type in meet_type:
            meet_default = mtypes.group_code
    meetings_list = [("", "Choose Meeting Type")]+[(i.group_code, i.group_type) for i in meeting_type]

    # set members list
    print(f'meet_type: {meet_type}')
    print(f'City Code: {current_user.user_city_code}')

    member_list = db.session.query(EntityMembers).filter(((EntityMembers.entity_code == current_user.user_city_code)
                                                          & (EntityMembers.group_code == meet_default))).all()

    for member in member_list:
        print(f'Member: {member.member_last_name}')
        full_name = f'{member.member_first_name} {member.member_last_name}'
        data = {
            'meet_type': meet_type,
            'member_meet': [
                ('1', 'Bill Bonigan'),
                ('2', 'Regan Murphy'),
                ('3', 'Jason Greenberg'),
                ('4', 'Mia Parisian'),
                ('5', 'Aaron Wagner'),
            ]
        }
        # (member_load(member.id, full_name))
        # member_list_pass.append(member_load(member.id, full_name))
    print(f'Member List: {str(data)}')

    form = UpdateAgendaForm(data=data)
    # form.members_present = member_list_pass
    # form = LargeAgendaForm(meet_type=meet_default, member_list_pass=member_list_pass)
    # form.meet_type.choices = meetings_list

    return render_template('meeting-10.html', agenda=agenda, form=form)


@app.route('/meeting11', methods=['GET', 'POST'])
def meeting11():
    agenda = agenda_temp()
    # Set Meeting Type Field
    meet_type = agenda['meet_type']
    meet_default = ""
    meeting_type = db.session.query(EntityGroups).filter(EntityGroups.entity_code == current_user.user_city_code).all()
    for mtypes in meeting_type:
        if mtypes.group_type in meet_type:
            meet_default = mtypes.group_code
    meetings_list = [("", "Choose Meeting Type")] + [(i.group_code, i.group_type) for i in meeting_type]

    # set members list
    member_list = db.session.query(EntityMembers).filter(((EntityMembers.entity_code == current_user.user_city_code)
                                                          & (EntityMembers.group_code == meet_default))).all()
    members = []
    member_select_list = ['Select Member', 'NA']
    for member in member_list:
        full_name = f'{member.member_first_name} {member.member_last_name}'
        members.append(full_name)
        member_select_list.append(full_name)

    member_list = db.session.query(EntityMembers).filter(((EntityMembers.entity_code == current_user.user_city_code)
                                                          & (EntityMembers.group_code == 'staff'))).all()
    staff = []
    for member in member_list:
        full_name = f'{member.member_first_name} {member.member_last_name}'
        staff.append(full_name)

    motions_list = create_motion_list(agenda)

    form, member_list_var = file_list_form_builder(members, meetings_list, meet_default, staff, motions_list, member_select_list)

    if form.validate_on_submit():
        members_present = []
        staff_present = []
        motion_callers = []
        for var_name in form:
            # print(var_name)
            if not var_name.id == 'submit':
                if 'checked' in str(var_name):
                    if str(var_name.name) in member_list_var:
                        members_present.append(var_name.name)
                    else:
                        staff_present.append(var_name.name)
                if not var_name.data == 'Select Member':
                    motion_callers.append({var_name.name: var_name.data})
                    print(f'Var Name: {var_name.name} / Data: {var_name.data}')


        print(members_present)
        print(staff_present)

    return render_template('meeting12.html', form=form, agenda=agenda, member_list_var=member_list_var,
                           motions_list_var=motions_list, staff_list_var=staff)


@app.route('/test_dict', methods=['GET', 'POST'])
def test_dic():
    agenda = agenda_temp()
    motions_list = create_motion_list(agenda)
    # print(motions_list)

    for each_1 in motions_list:
        # print(each_1)
        ct = 0
        for jj in each_1:
            # for item in jj({i: i for i in range(10)}, 2):
            #     print(item)
            for key in jj:
                print(f'{ct}, {key}')
                if ct == 0:
                    ct += 1
                    print(f'Key1: {key}, {jj[key]}')
                else:
                    ct += 1
                    print(f'Key2: {key}, {jj[key]}')


    return 'Done'


@app.route('/audioR', methods=['GET', 'POST'])
def audio_r():
    return render_template('audioR.html')


@app.route('/audio_r2', methods=['GET', 'POST'])
def audio_r2():
    return render_template('audioR.html')


@socketio.event
def my_event(message):
    session['receive_count'] = session.get('receive_count', 0) + 1
    emit('my_response',
         {'data': message['data'], 'count': session['receive_count']})
    print(message)


@socketio.event
def event_record(message):
    print('Start event_record')
    print(message)

    emit('my_response',
         {'data': 'Start Recording', 'count': '1'})


@socketio.event
def stream_media(message):
    print('Start event_record')
    # print(message)

    transcriber = aai.RealtimeTranscriber(
        on_data=on_data,
        on_error=on_error,
        sample_rate=44_100,
        on_open=on_open,  # optional
        on_close=on_close,  # optional
    )
    # Start the connection
    transcriber.connect()
    print('connect to transcriber')

    transcriber.stream(message)
    print("streaming")

    transcriber.close()
    print('transcribe close')

    emit('my_response', 'audio stream started')

    emit('my_response',
         {'data': 'Start Recording', 'count': '1'})


@socketio.event
def disconnect_request():
    @copy_current_request_context
    def can_disconnect():
        disconnect()

    session['receive_count'] = session.get('receive_count', 0) + 1
    # for this emit we use a callback function
    # when the callback function is invoked we know that the message has been
    # received and it is safe to disconnect
    emit('my_response',
         {'data': 'Disconnected!', 'count': session['receive_count']},
         callback=can_disconnect)


@socketio.event
def connect():
    global thread
    with thread_lock:
        if thread is None:
            thread = socketio.start_background_task(background_thread)
    emit('my_response', {'data': 'Socket Connected', 'count': 0})
    print('socket connected (connect)')


@socketio.on('disconnect')
def test_disconnect():
    print('Client disconnected', request.sid)


def on_open(session_opened: aai.RealtimeSessionOpened):
    # "This function is called when the connection has been established."

    print("Session ID:", session_opened.session_id)


def on_data(transcript: aai.RealtimeTranscript):
    # "This function is called when a new transcript has been received."

    if not transcript.text:
        return

    if isinstance(transcript, aai.RealtimeFinalTranscript):
        print(transcript.text, end="\r\n")
    else:
        print(transcript.text, end="\r")


def on_error(error: aai.RealtimeError):
    # "This function is called when the connection has been closed."

    print("An error occured:", error)


def on_close():
    # "This function is called when the connection has been closed."

    print("Closing Session")


@app.route('/load_data')
def load_data():

    with open('app/files/rob_staff.csv', mode='r') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        line_count = 0

        for row in csv_reader:
            print(row['entity_code'], row['member_last_name'], row['group_code'])

            my_data = EntityMembers(entity_code=row['entity_code'],
                                   group_code=row['group_code'],
                                   member_first_name=row['member_first_name'],
                                   member_last_name=row['member_last_name'],
                                   title=row['title'],
                                   position=row['position']
                                  )

            db.session.add(my_data)
            db.session.commit()
            line_count += 1

    return render_template('data_complete.html', load_file_name='rob_members.csv')


@app.route('/create_motion')
def create_motion():

    agenda = agenda_temp()
    motions_list = create_motion_list(agenda)

    return str(motions_list)
