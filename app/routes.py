import assemblyai as aai
import csv
import html2text
import json
import os
import sqlalchemy as sa
import uuid

from sqlalchemy.exc import SQLAlchemyError

from app import app, db
from app.email import send_password_reset_email
from app.forms import LoginForm, RegistrationForm, EditProfileForm, ResetPasswordRequestForm, \
    ResetPasswordForm, MeetingForm, EditMinutesForm, DiaryForm, EntityMemberForm, EntityGroupForm
from app.models import User, EntityName, EntityMembers, EntityGroups, MeetingAttendance, MeetingInfo, \
    MeetingMotionItems, MeetingMotionVotes
from datetime import datetime, timezone
from io import BytesIO
from flask import render_template, flash, redirect, url_for, request, send_file
from flask_login import current_user, login_user, logout_user, login_required
from flask_socketio import SocketIO, emit, disconnect
from flask_wtf.csrf import CSRFError
from threading import Lock
from urllib.parse import urlsplit
from werkzeug.utils import secure_filename

from app.func_agenda.agenda_parse import openai_agenda, to_pretty_json, create_motion_list, updated_agenda
from app.func_agenda.form_config import file_list_form_builder, diary_speaker_list
from app.func_agenda.meeting_processing import create_prompt, create_minutes


async_mode = None
socketio = SocketIO(app, async_mode=async_mode)
thread = None
thread_lock = Lock()
aai.settings.api_key = "68b893a3d9d343638b42e03a065b25fb"
app.jinja_env.filters['tojson_pretty'] = to_pretty_json

app.config.update(
    # Flask-Dropzone config:
    DROPZONE_DEFAULT_MESSAGE='<i class="size-48" data-feather="file"></i><br><br>Drag your File Here<br>Or'
                             '<br>Click to Browse',
    DROPZONE_ENABLE_CSRF=True,
    DROPZONE_ALLOWED_FILE_CUSTOM=True,
    DROPZONE_ALLOWED_FILE_TYPE='.pdf, .mp3, .m4a, .mp4',
    DROPZONE_MAX_FILE_SIZE=9000,
)


responses = [{''}]


@app.before_request
def before_request():
    if current_user.is_authenticated:
        current_user.last_seen = datetime.now(timezone.utc)
        db.session.commit()


@app.route('/test_io')
def test_io():
    return render_template('test_io.html', resps=responses)


@app.route('/')
@app.route('/index')
def index():
    return render_template('index.html', title='Home')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    form = LoginForm()
    if form.validate_on_submit():
        user_var = db.session.scalar(
            sa.select(User).where(User.username == form.username.data))
        if user_var is None or not user_var.check_password(form.password.data):
            flash('Invalid username or password')
            return redirect(url_for('login'))
        login_user(user_var, remember=form.remember_me.data)
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
    user_obj = db.first_or_404(sa.select(User).where(User.username == username))
    posts = [
        {'author': user_obj, 'body': 'Test post #1'},
        {'author': user_obj, 'body': 'Test post #2'}
    ]
    return render_template('user.html', user=user_obj, posts=posts)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    city_list = db.session.query(EntityName).all()
    city_select_list = [('na', 'Choose City')]
    city_select_dict = {}
    for i in city_list:
        city_select_list.append((i.entity_code, i.entity_name.title()))
        city_select_dict[i.entity_code] = i.entity_name
    form = RegistrationForm()
    form.user_city.choices = city_select_list
    if form.validate_on_submit():
        user_reg = User(username=form.username.data,  # type: ignore[call-arg]
                        email=form.email.data,  # type: ignore[call-arg]
                        user_city=city_select_dict[form.user_city.data],  # type: ignore[call-arg]
                        user_city_code=form.user_city.data)  # type: ignore[call-arg]

        user_reg.set_password(form.password.data)
        db.session.add(user_reg)
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
        user_var = db.session.scalar(
            sa.select(User).where(User.email == form.email.data))
        if user_var:
            send_password_reset_email(user_var)
        flash('Check your email for the instructions to reset your password')
        return redirect(url_for('login'))
    return render_template('reset_password_request.html',
                           title='Reset Password', form=form)


@app.route('/reset_password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    user_var = User.verify_reset_password_token(token)
    if not user_var:
        return redirect(url_for('index'))
    form = ResetPasswordForm()
    if form.validate_on_submit():
        user_var.set_password(form.password.data)
        db.session.commit()
        flash('Your password has been reset.')
        return redirect(url_for('login'))
    return render_template('reset_password.html', form=form)


@app.errorhandler(413)
def too_large(e):
    return f"File is too large: {e.description}", 413


@app.errorhandler(CSRFError)
def csrf_error(e):
    return e.description, 400


@app.route('/create_meeting_old')
@login_required
def create_meeting_2():
    form = MeetingForm()
    return render_template('meeting.html', title='Create Meeting', form=form)


@app.route('/upload_audio/<meet_id>', methods=['GET'])
@login_required
def upload_audio(meet_id):

    return render_template('upload_audio.html', title='Upload Audio', meet_id=meet_id)


@app.route('/create_meeting', methods=['GET'])
@login_required
def create_meeting():

    return render_template('meeting.html', title='Create Meeting')


@app.route('/upload', methods=['POST'])
@login_required
def handle_upload():
    print('uploading...')

    f = request.files.get('file')
    filename = secure_filename(f.filename)
    new_path = f"{app.config['UPLOAD_PATH']}/{current_user.user_city}"

    if filename != '':
        if not os.path.exists(new_path):
            os.makedirs(new_path)
        f.save(os.path.join(new_path, filename))

    return render_template("index.html")


@app.route('/upload_audio_file/<meet_id>', methods=['POST'])
@login_required
def handle_upload_audio_file(meet_id):
    print('uploading audio...')

    f = request.files.get('file')
    filename = secure_filename(f.filename)
    new_path = f"{app.config['UPLOAD_PATH']}/{current_user.user_city}/audio"

    print(f"Meet ID: {meet_id} / Filename: {filename}")
    audio_file = db.session.query(MeetingInfo).filter((MeetingInfo.id == meet_id) &
                                                      (MeetingInfo.audio_name == secure_filename(filename))).all()

    # audio_file = db.session.query(MeetingInfo).filter(MeetingInfo.id == new_meet_id).first()
    print(f"Audio File: {audio_file}")
    # print(f"Audio Name: {audio_file.audio_name}")

    if not audio_file:
        print("audio_file name not found")
        if filename != '':
            if not os.path.exists(new_path):
                os.makedirs(new_path)
            f.save(os.path.join(new_path, filename))

        # update database
        meeting = MeetingInfo.query.get(meet_id)
        meeting.audio_name = filename
        db.session.commit()
    else:
        print("audio_file found")
        pass

    return render_template('list_meeting.html', filename=filename)


@app.route('/process_agenda/<filename>')
@login_required
def process_agenda_function(filename):
    new_path = f"{app.config['UPLOAD_PATH']}/{current_user.user_city}/json"

    meeting = db.session.query(MeetingInfo).filter(MeetingInfo.agenda_name == secure_filename(filename)).first()
    if meeting is not None:
        meet_id = meeting.id
        jsonuuid = meeting.meeting_agenda
    else:
        print("Not Found")
        jsonuuid = uuid.uuid4()
        # agenda = agenda_temp()
        agenda = openai_agenda(secure_filename(filename))

        print('agenda done')

        if not os.path.exists(new_path):
            os.makedirs(new_path)
        f = open(f"{new_path}/{jsonuuid}.txt", "w")
        f.write(json.dumps(agenda))
        f.close()

        meeting = MeetingInfo(agenda_name=secure_filename(filename), meeting_agenda=str(jsonuuid),
                              meeting_entity=current_user.user_city_code)
        db.session.add(meeting)
        db.session.commit()
        meet_id = meeting.id

    return redirect(url_for('meeting_process', agenda_id=jsonuuid, meet_id=meet_id))


@app.route('/meeting_process/<agenda_id>/<meet_id>', methods=['GET', 'POST'])
@login_required
def meeting_process(agenda_id, meet_id):
    path = f"{app.config['UPLOAD_PATH']}/{current_user.user_city}/json"
    file = open(f"{path}/{agenda_id}.txt", "r")
    agenda = json.load(file)

    # Set Meeting Type Field
    meet_type = agenda['meet_type']
    meet_default = ""

    # update meeting info to database
    meeting = MeetingInfo.query.get(meet_id)
    meeting.meeting_type = meet_type
    meeting.meeting_date = agenda['date']
    meeting.meeting_time = agenda['time']
    meeting.meeting_agenda = agenda_id
    meeting.meeting_entity = current_user.user_city_code

    db.session.commit()

    # get meeting types
    meeting_type = db.session.query(EntityGroups).filter(EntityGroups.entity_code == current_user.user_city_code).all()
    for mtypes in meeting_type:
        if mtypes.group_type in meet_type:
            meet_default = mtypes.group_code
    meetings_list = [("", "Choose Meeting Type")] + [(i.group_code, i.group_type) for i in meeting_type]

    # get members list
    member_list = db.session.query(EntityMembers).filter(((EntityMembers.entity_code == current_user.user_city_code)
                                                          & (EntityMembers.group_code == meet_default))).all()
    members = []
    member_select_list = ['Select Member', 'NA']
    staff_select_list = []
    member_dict = {}
    staff_dict = {}
    for member in member_list:
        full_name = f'{member.member_first_name} {member.member_last_name}'

        member_dict[full_name] = {
                                  'id': member.id,
                                  'group_code': member.group_code,
                                  'entity_code': member.entity_code,
                                  'title': member.title,
                                  'position': member.position
                                  }

        # title_name = f'{member.title} {member.member_last_name}'
        members.append(full_name)
        member_select_list.append(full_name)

        # member_titles.append(title_name)

    member_list = db.session.query(EntityMembers).filter(((EntityMembers.entity_code == current_user.user_city_code)
                                                          & (EntityMembers.group_code == 'staff'))).all()

    for member in member_list:
        full_name = f'{member.member_first_name} {member.member_last_name}'
        staff_select_list.append(full_name)
        staff_dict[full_name] = {
            'id': member.id,
            'group_code': member.group_code,
            'entity_code': member.entity_code,
            'title': member.title,
            'position': member.position
        }
    "5:00 PM"
    jj = datetime.strptime(agenda['time'], '%I:%M %p')
    print(f'Time: {jj}')

    # print(f"Staff Select List: {staff_select_list}")
    # print(f"Member Select List: {member_select_list}")
    motion_list_labels, motion_list_full, consent_list_labels, consent_list_full, ml_sm, cl_sm = \
        create_motion_list(agenda)
    form, member_list_var = file_list_form_builder(members, meetings_list, meet_default, staff_select_list,
                                                   motion_list_full, member_select_list, consent_list_full,
                                                   agenda_time=jj)

    print(f"Motion List Labels: {motion_list_labels}")
    print(f"Motion List Full: {motion_list_full}")
    print(f"ml_sm: {ml_sm}")

    motion = db.session.query(MeetingMotionItems).filter(MeetingMotionItems.meeting_id == meet_id).first()
    if motion is not None:
        # meeting motions saved already
        pass
    else:
        # save the meeting motions
        motion_save = []
        for each_motion in ml_sm:
            if not ml_sm[each_motion]:
                motion_code = ""
            else:
                motion_code = ml_sm[each_motion][0]

            motion_save.append(MeetingMotionItems(entity_code=current_user.user_city_code,
                                                  meeting_id=meet_id,
                                                  motion_title=each_motion,
                                                  agenda_item=motion_code))

        db.session.bulk_save_objects(motion_save)
        db.session.commit()

    # after submit
    if form.validate_on_submit():
        print("After Submit")
        members_list = []
        staff_present = []
        motion_callers = {}
        member_attendance_save = []
        motion_approve = []

        for var_name in form:
            if not var_name.id == 'submit':
                if 'checked' in str(var_name):
                    if str(var_name.name) in member_list_var:
                        members_list.append(var_name.name)
                        member_attendance_save.append(MeetingAttendance(
                            entity_code=current_user.user_city_code,
                            meeting_id=meet_id,
                            member_id=member_dict[var_name.name]['id'],
                            member_type=member_dict[var_name.name]['group_code'],
                            member_present='y'))
                    else:
                        staff_present.append(var_name.name)
                        member_attendance_save.append(MeetingAttendance(
                            entity_code=current_user.user_city_code,
                            meeting_id=meet_id,
                            member_id=staff_dict[var_name.name]['id'],
                            member_type=staff_dict[var_name.name]['group_code'],
                            member_present='y'))

                else:
                    if str(var_name.name) in member_list_var:
                        members_list.append(f"{var_name.name} (absent)")
                        member_attendance_save.append(MeetingAttendance(
                            entity_code=current_user.user_city_code,
                            meeting_id=meet_id,
                            member_id=member_dict[var_name.name]['id'],
                            member_type=member_dict[var_name.name]['group_code'],
                            member_present='n'))
                if var_name.name in motion_list_labels or var_name.name in consent_list_labels:
                    if not var_name.data == 'Select Member' or var_name.data == 'NA':
                        motion_callers[var_name.id] = var_name.data
                        motion_approve.append(MeetingMotionVotes(entity_code=current_user.user_city_code,
                                                                 meeting_id=meet_id,
                                                                 member_id=member_dict[var_name.data]['id'],
                                                                 motion_id=var_name.id))

        db.session.bulk_save_objects(member_attendance_save)
        db.session.bulk_save_objects(motion_approve)
        db.session.commit()
        print(f"Motion Callers: {motion_callers}")

        return redirect(url_for('meeting_list_page'))
        # return render_template('list_meeting.html')

    return render_template('meeting12.html', form=form, agenda=agenda, member_list_var=member_list_var,
                           motions_list_var=motion_list_full, staff_list_var=staff_select_list, agenda_id=agenda_id,
                           consent_list_var=consent_list_full, meet_id=meet_id)


@app.route('/review_minutes/<meet_id>', methods=['GET', 'POST'])
@login_required
def review_minutes(meet_id):
    meeting = db.session.query(MeetingInfo).filter(MeetingInfo.id == meet_id).first()
    # agenda_path = f"{app.config['UPLOAD_PATH']}/{current_user.user_city}/json"
    minutes_path = f"{app.config['UPLOAD_PATH']}/{current_user.user_city}/minutes"

    minutes_file = open(f"{minutes_path}/{meeting.meeting_minutes}_summary.txt", "r")
    diary_file = open(f"{minutes_path}/{meeting.meeting_minutes}_diary.txt", "r")
    # minutes_file = open(f"{minutes_path}/rob_cc_022024_summary.txt", "r")
    # diary_file = open(f"{minutes_path}/rob_cc_022024_diarization.txt", "r")

    form = EditMinutesForm()

    # after submit
    if form.validate_on_submit():
        # print(form.content.data)
        new_minutes = html2text.html2text(form.content.data).replace("\\", '')
        f = open(f"{minutes_path}/{meeting.meeting_minutes}_summary.txt", "w")
        f.write(new_minutes)
        f.close()

        return redirect(url_for('meeting_list_page'))

    form.content.data = minutes_file.read().replace('\n', '<br />')

    # Diary Form
    var_meet_default = ""
    if 'Council' in meeting.meeting_type:
        var_meet_default = 'council'
    elif 'Sustain' in meeting.meeting_type:
        var_meet_default = 'sus'

    diary_form = DiaryForm(meeting_type_read_only='council')

    diary_form.diary_content.data = diary_file.read().replace('\n', '<br />')

    # For Future use, updating diarization names (Speaker 1, Speaker 2, etc
    officials_list = db.session.query(EntityMembers, MeetingAttendance).filter(
        MeetingAttendance.id == '1', ).filter(MeetingAttendance.member_id == EntityMembers.id, ).filter(
        MeetingAttendance.member_present == 'y').all()

    for official in officials_list:
        full_name = f'{official.EntityMembers.member_first_name} {official.EntityMembers.member_last_name}'
        print(full_name)

    # return render_template('preview_edit.html', form=form)
    return render_template('button_test.html', form=form, diary_form=diary_form, meet_id=meet_id)


@socketio.on('download_minutes_task', namespace='/download_minutes')
def run_lengthy_task(data):
    try:
        # form = EditMinutesForm()
        meeting = db.session.query(MeetingInfo).filter(MeetingInfo.id == data['meet_id']).first()
        minutes_path = f"{app.config['UPLOAD_PATH']}/{current_user.user_city}/minutes"

        # print(form.content.data)
        # file_name = f"{meeting.meeting_date}_minutes.txt"
        new_minutes = html2text.html2text(data['data']).replace("\\", '')
        f = open(f"{minutes_path}/{meeting.meeting_minutes}_summary.txt", "w")
        f.write(new_minutes)
        f.close()

        emit('task_done', {'data': 'Task complete', 'url': url_for('review_minutes_download', meet_id=meeting.id)})
        disconnect()

    except Exception as ex:
        print(ex)


@app.route('/review_minutes/download/<meet_id>', methods=['GET', 'POST'])
@login_required
def review_minutes_download(meet_id):
    # form = EditMinutesForm()
    meeting = db.session.query(MeetingInfo).filter(MeetingInfo.id == meet_id).first()
    minutes_path = f"{app.config['UPLOAD_PATH']}/{current_user.user_city}/minutes"

    # if form.validate_on_submit():

    # print(request.data)
    # for var_name in form:
    #    print(var_name.id)
    #    print(var_name)

    # print(form.content.data)
    file_name = secure_filename(f"{meeting.meeting_date}_minutes.txt")
    # new_minutes = html2text.html2text(form.content.data).replace("\\", '')
    # f = open(f"{minutes_path}/{meeting.meeting_minutes}_summary.txt", "w")
    # f.write(new_minutes)
    # f.close()

    new_minutes = open(f"{minutes_path}/{meeting.meeting_minutes}_summary.txt", "rb")

    byte_obj = BytesIO()
    byte_obj.write(new_minutes.read())
    byte_obj.seek(0)

    # return redirect(url_for('review_minutes', meet_id=meet_id))
    return send_file(byte_obj, download_name=file_name, as_attachment=True)

    # return redirect(url_for('review_minutes', meet_id=meet_id))


@app.route('/review_minutes/download_old/<meet_id>', methods=['GET', 'POST'])
@login_required
def review_minutes_download_old(meet_id):
    form = EditMinutesForm()
    meeting = db.session.query(MeetingInfo).filter(MeetingInfo.id == meet_id).first()
    minutes_path = f"{app.config['UPLOAD_PATH']}/{current_user.user_city}/minutes"

    if form.validate_on_submit():
        # print(form.content.data)
        file_name = f"{meeting.meeting_date}_minutes.txt"
        new_minutes = html2text.html2text(form.content.data).replace("\\", '')
        f = open(f"{minutes_path}/{meeting.meeting_minutes}_summary.txt", "w")
        f.write(new_minutes)
        f.close()

        byte_obj = BytesIO()
        byte_obj.write(new_minutes)
        byte_obj.seek(0)

        return send_file(byte_obj, download_name=file_name, as_attachment=True)

    return redirect(url_for('review_minutes', meet_id=meet_id))


@app.route('/preview_edit_diary/<meet_id>', methods=['GET', 'POST'])
@login_required
def preview_edit_diary(meet_id):
    # agenda_path = f"{app.config['UPLOAD_PATH']}/{current_user.user_city}/json"
    minutes_path = f"{app.config['UPLOAD_PATH']}/{current_user.user_city}/minutes"
    file = open(f"{minutes_path}/rob_cc_022024_diarization.txt", "r")

    officials_list = db.session.query(EntityMembers, MeetingAttendance).\
        filter(MeetingAttendance.id == '1',).\
        filter(MeetingAttendance.member_id == EntityMembers.id,).\
        filter(MeetingAttendance.member_present == 'y').all()

    for official in officials_list:

        full_name = f'{official.EntityMembers.member_first_name} {official.EntityMembers.member_last_name}'
        print(full_name)

    jj = diary_speaker_list(file)
    print(jj)
    file.seek(0)
    list_diary = []

    for line in file:
        try:
            list_diary.append(f"{line} {next(file)}")
        except StopIteration as e:
            break

    return render_template('preview_edit_diary.html', diary=list_diary)


@app.route('/create_minutes/<meet_id>')
@login_required
def process_audio(meet_id):
    # Get Meeting Object
    meeting = MeetingInfo.query.get(meet_id)
    print("get meeting object")

    # Create Prompt
    prompt = create_prompt(meet_id, meeting)
    print("create prompt done")
    print(prompt)

    # process Minutes
    print('processing minutes')
    minutes = create_minutes(prompt, meeting)
    print(f"minutes: { minutes }")

    return redirect(url_for('meeting_list_page'))
    # return render_template('list_meeting.html')


@app.route('/meeting_list')
@login_required
def meeting_list_page():

    # get all meetings
    meeting_list = db.session.query(MeetingInfo).\
        filter((MeetingInfo.meeting_entity == current_user.user_city_code)).all()

    # print(f"{meeting.id} / {meeting.meeting_type} / {meeting.meeting_date} / {meeting.meeting_agenda}")

    return render_template('list_meeting.html', meeting_list=meeting_list)


@app.route('/people_list', methods=['GET', 'POST'])
@login_required
def people_list_page():

    form = EntityMemberForm()

    # get all people
    people_list = db.session.query(EntityMembers, EntityGroups).\
        filter(EntityMembers.entity_code == current_user.user_city_code).\
        filter(EntityGroups.group_code == EntityMembers.group_code).all()

    # after submit
    if form.validate_on_submit():
        print(f"form: {form}")
        print("After Submit")
        member = EntityMembers(group_code=form.group_code.data, member_first_name=form.member_first_name.data,
                               member_last_name=form.member_last_name.data, entity_code=current_user.user_city_code,
                               title=form.title.data, position=form.position.data)

        # validate new member
        # user.set_password(form.password.data)
        db.session.add(member)
        db.session.commit()
        return redirect(url_for('people_list_page'))

    return render_template('list_people.html', people_list=people_list, form=form)


@app.route('/member/<member_id>')
@login_required
def view_member(member_id):

    form = EntityMemberForm()
    member = db.session.query(EntityMembers, EntityGroups). \
        filter(EntityMembers.id == member_id). \
        filter(EntityGroups.group_code == EntityMembers.group_code).first()
    start_date = ''
    end_date = ''

    if member.EntityMembers.start_date:
        start_date = member.EntityMembers.start_date.strftime('%B %d, %Y')
    if member.EntityMembers.end_date:
        end_date = member.EntityMembers.end_date.strftime('%B %d, %Y')
    return render_template('page_member.html', form=form, member=member, start_date=start_date, end_date=end_date)


@app.route('/member/edit/<member_id>', methods=['GET', 'POST'])
@login_required
def edit_member(member_id):
    member = EntityMembers.query.get(member_id)
    form = EntityMemberForm()

    if form.validate_on_submit():
        print('validate')
        print(f"Member: {form.member_first_name.data}")
        print(f"Date: {form.start_date.data}")
        member.member_first_name = form.member_first_name.data
        member.member_last_name = form.member_last_name.data
        member.group_code = form.group_code.data
        member.title = form.title.data
        member.position = form.position.data
        member.start_date = form.start_date.data
        member.end_date = form.end_date.data
        # update database
        db.session.add(member)
        try:
            db.session.commit()
        except SQLAlchemyError as e:
            error = str(e.__dict__['orig'])
            print(error)

        print('after save')

        return redirect(url_for('view_member', member_id=member_id))

    # TODO: Only add members in office/position by date
    start_date = ''
    end_date = ''
    if member.start_date:
        start_date = member.start_date.strftime('%B %d, %Y')
        print(start_date)
    if member.end_date:
        end_date = member.end_date.strftime('%B %d, %Y')

    form.member_first_name.data = member.member_first_name
    form.member_last_name.data = member.member_last_name
    form.group_code.data = member.group_code
    form.title.data = member.title
    form.position.data = member.position
    form.end_date.data = member.end_date
    form.start_date.data = member.start_date

    first_name = member.member_first_name
    last_name = member.member_last_name
    member_title = member.title

    return render_template('edit_member.html', form=form, first_name=first_name, last_name=last_name,
                           member_title=member_title)


@app.route('/group_list', methods=['GET', 'POST'])
@login_required
def group_list_page():

    form = EntityGroupForm()

    # get all meetings
    group_list = db.session.query(EntityGroups).filter(EntityGroups.entity_code == current_user.user_city_code).all()

    if form.validate_on_submit():
        group = EntityGroups(group_type=form.group_type.data, group_code=form.group_code.data,
                             entity_code=current_user.user_city_code)
        db.session.add(group)
        db.session.commit()
        return redirect(url_for('group_list_page'))

    return render_template('list_group.html', city_group_list=group_list, form=form)


@app.route('/group/<group_id>')
@login_required
def view_group(group_id):
    form = EntityGroupForm()
    group = EntityGroups.query.get(group_id)

    return render_template('page_group.html', form=form, group=group)


@app.route('/group/edit/<group_id>', methods=['GET', 'POST'])
@login_required
def edit_group(group_id):
    group = EntityGroups.query.get(group_id)
    form = EntityGroupForm()

    if form.validate_on_submit():
        group.group_type = form.group_type.data
        group.group_code = form.group_code.data
        db.session.add(group)
        db.session.commit()

        return redirect(url_for('view_group', group_id=group_id))

    form.group_type.data = group.group_type
    form.group_code.data = group.group_code

    return render_template('edit_group.html', form=form)


@app.route('/meeting_page/<meet_id>')
@login_required
def meeting_page(meet_id):

    form = MeetingForm()
    meeting = MeetingInfo.query.get(meet_id)

    path = f"{app.config['UPLOAD_PATH']}/{current_user.user_city}/json"
    file = open(f"{path}/{meeting.meeting_agenda}.txt", "r")
    agenda = json.load(file)

    return render_template('page_meeting.html', meeting=meeting, form=form, agenda=agenda)


@app.route('/attendance_list')
@login_required
def attendance_list():

    # get all meetings
    attend_list = db.session.query(MeetingAttendance).\
        filter(MeetingAttendance.entity_code == current_user.user_city_code).all()

    # for people in people_list:
    #    print(f"{people.id} / {people.meeting_type} / {meeting.meeting_date} / {meeting.meeting_agenda}")

    return render_template('list_group.html', attend_list=attend_list)


@app.route('/test_dict/<meet_id>', methods=['GET', 'POST'])
@login_required
def test_dic(meet_id):
    meeting = db.session.query(MeetingInfo).filter(MeetingInfo.id == meet_id).all()
    path = f"{app.config['UPLOAD_PATH']}/{current_user.user_city}/json"
    file = open(f"{path}/{meeting.meeting_agenda}.txt", "r")
    agenda = json.load(file)

    jj = updated_agenda(agenda, meet_id)

    return jj


@app.route('/test_stuff/<meet_id>')
@login_required
def test_stuff(meet_id):

    print(f"Meet ID: {meet_id}")
    city_select_list = db.session.query(EntityName).all()
    for city in city_select_list:
        print(f"Name: {city.entity_name} / code: {city.entity_code}")

    # Get Meeting Object
    # meeting_info = MeetingInfo.query.get(meet_id)

    # meeting = db.session.query(MeetingInfo).filter(MeetingInfo.id == meet_id).first()
    # path = f"{app.config['UPLOAD_PATH']}/{current_user.user_city}/json"
    # file = open(f"{path}/{meeting.meeting_agenda}.txt", "r")
    # agenda = json.load(file)

    # ua = updated_agenda_test(agenda, meet_id)
    # ua = updated_agenda_2(agenda, meet_id)

    # prompt = create_prompt(meet_id, meeting)

    return 'done'


@app.route('/load_data')
@login_required
def load_data():

    with open('app/files/groups.csv', mode='r') as csv_file:
        csv_reader = csv.DictReader(csv_file)
        line_count = 0

        for row in csv_reader:
            my_data = EntityGroups(group_type=row['group_type'],
                                   group_code=row['group_code'],
                                   entity_code=f"mn1901")

            db.session.add(my_data)
            db.session.commit()
            line_count += 1

    return render_template('data_complete.html', load_file_name='rob_members.csv')
