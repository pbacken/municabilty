from datetime import datetime
from func_agenda import form_config

nested_dict = {'dict1': {'key_A': 'value_A'},
               'dict2': {'key_B': 'value_B'}}

members = {'Bill Blonigan': {'id': 1, 'group_code': 'council', 'entity_code': 'mn1901', 'title': 'Mayor', 'position': 'Mayor'},
           'Regan Murphy': {'id': 2, 'group_code': 'council', 'entity_code': 'mn1901', 'title': 'Council Member', 'position': 'Ward 1'},
           'Jason Greenberg': {'id': 3, 'group_code': 'council', 'entity_code': 'mn1901', 'title': 'Council Member', 'position': 'Ward 2'},
           'Mia Parisian': {'id': 4, 'group_code': 'council', 'entity_code': 'mn1901', 'title': 'Council Member', 'position': 'Ward 3'},
           'Aaron Wagner': {'id': 5, 'group_code': 'council', 'entity_code': 'mn1901', 'title': 'Council Member', 'position': 'Ward 4'}
           }

print(members['Mia Parisian'])
print(members['Mia Parisian']['id'])

# path = f"{app.config['UPLOAD_PATH']}/{current_user.user_city}/json"
file = open("files/Robbinsdale/minutes/rob_cc_022024_diarization.txt", "r")

jj = form_config.diary_speaker_list(file)

print(jj)
exit()

# dd = agenda_parse.get_speaker_list(file)
diary_speaker_list1 = []
for each_line in file:
    if 'Speaker' in each_line:
        if not each_line[:-2] in diary_speaker_list1:
            diary_speaker_list1.append(each_line[:-2])
            print(each_line)

print(diary_speaker_list1)
