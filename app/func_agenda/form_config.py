from flask_wtf import FlaskForm
from flask_login import current_user
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, SelectField, \
    FieldList, FormField, Form, TimeField
from app import app, db
from app.models import User, EntityName, EntityMembers, EntityGroups


def file_list_form_builder(members, meetings_list, meet_default, staff_list, motions_list, member_select_list,
                           consent_list, agenda_time):
    class MemberListForm(FlaskForm):
        pass

    setattr(MemberListForm, 'meet_type', SelectField(choices=meetings_list, label='Meeting Type', default=meet_default))
    setattr(MemberListForm, 'meet_time', TimeField(label='Meeting Start Time', default=agenda_time))

    member_list = []
    for (i, name) in enumerate(members):
        setattr(MemberListForm, name, BooleanField(label=name, default=True))
        member_list.append(name)

    for (i, name) in enumerate(staff_list):
        setattr(MemberListForm, name, BooleanField(label=name))

    for each_1 in motions_list:
        ct = 0
        for jj in each_1:
            for key in jj:
                if ct == 0:
                    ct += 1
                    setattr(MemberListForm, key, SelectField(label='Select 1st', choices=member_select_list))
                else:
                    ct += 1
                    setattr(MemberListForm, key, SelectField(label='Select 2nd', choices=member_select_list))

    # consent list
    for each_item in consent_list:
        ct = 0
        for jj in each_item:
            for key in jj:
                if ct == 0:
                    ct += 1
                    setattr(MemberListForm, key, SelectField(label='Select 1st', choices=member_select_list))
                else:
                    ct += 1
                    setattr(MemberListForm, key, SelectField(label='Select 2nd', choices=member_select_list))

    setattr(MemberListForm, 'submit', SubmitField('Submit'))

    return MemberListForm(), member_list


def get_meeting_list(meet_type):
    meet_default = ""
    meeting_type = db.session.query(EntityGroups).filter(EntityGroups.entity_code == current_user.user_city_code).all()
    for mtypes in meeting_type:
        if mtypes.group_type in meet_type:
            meet_default = mtypes.group_code
    meetings_list = [("", "Choose Meeting Type")] + [(i.group_code, i.group_type) for i in meeting_type]
    return meetings_list, meet_default


def get_member_list(meet_default):
    member_list = db.session.query(EntityMembers).filter(((EntityMembers.entity_code == current_user.user_city_code)
                                                          & (EntityMembers.group_code == meet_default))).all()
    members = []
    member_select_list = ['Select Member', 'NA']
    for member in member_list:
        full_name = f'{member.member_first_name} {member.member_last_name}'
        members.append(full_name)
        member_select_list.append(full_name)

    return members, member_select_list


def get_city_list():
    city_list = db.session.query(EntityGroups).all()
    cities = []
    city_select_list = ['Select City', 'NA']
    for city in city_list:
        city_select_list.append((city['entity_name', city['entity_code']]))

    return city_select_list


def diary_speaker_list(diary):
    diary_speaker_list = []
    for each_line in diary:
        if 'Speaker' in each_line:
            if not each_line[:-2] in diary_speaker_list:
                diary_speaker_list.append(each_line[:-2])

    return diary_speaker_list
