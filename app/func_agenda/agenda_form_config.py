from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField, SelectField, \
    FieldList, FormField, Form


def file_list_form_builder(members, meetings_list, meet_default, staff_list, motions_list, member_select_list):
    class MemberListForm(FlaskForm):
        pass

    setattr(MemberListForm, 'meet_type', SelectField(choices=meetings_list, label='Meeting Type', default=meet_default))

    member_list = []
    for (i, name) in enumerate(members):
        setattr(MemberListForm, name, BooleanField(label=name, default=True))
        member_list.append(name)

    for (i, name) in enumerate(staff_list):
        setattr(MemberListForm, name, BooleanField(label=name))

    print(motions_list)
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

    setattr(MemberListForm, 'submit', SubmitField('Submit'))

    return MemberListForm(), member_list


