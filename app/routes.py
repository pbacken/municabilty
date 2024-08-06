import sqlalchemy as sa
from app import app, db
from app.email import send_password_reset_email
from app.forms import LoginForm, RegistrationForm, EditProfileForm, ResetPasswordRequestForm, ResetPasswordForm
from app.models import User
from datetime import datetime, timezone
from flask import render_template, flash, redirect, url_for, request, session, copy_current_request_context
from flask_login import current_user, login_user, logout_user, login_required
from urllib.parse import urlsplit
from flask_socketio import SocketIO, emit, disconnect
from threading import Lock
import assemblyai as aai
import json
from app.func_agenda.agenda_parse import openai_agenda, to_pretty_json

async_mode = None
socketio = SocketIO(app, async_mode=async_mode)
thread = None
thread_lock = Lock()
aai.settings.api_key = "68b893a3d9d343638b42e03a065b25fb"
app.jinja_env.filters['tojson_pretty'] = to_pretty_json


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
@login_required
def index():
    user = {'username': 'Sonny'}
    return render_template('index.html', title='Home')


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
    return render_template('login.html', title='Sign In', form=form)


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
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('Congratulations, you are now a registered user!')
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


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
