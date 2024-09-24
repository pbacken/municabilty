from app.func_agenda.agenda_parse import openai_agenda, to_pretty_json, agenda_temp, create_motion_list, updated_agenda
from app.func_agenda.form_config import file_list_form_builder, diary_speaker_list
from app.func_agenda.query_func import get_attendance_list


def process_meeting_data(prompt):
    pass


def create_prompt(meet_id):

    original_agenda = agenda_temp()
    agenda = updated_agenda(original_agenda, meet_id)
    officials_list = get_attendance_list(meet_id)

    members_present = ""
    for official in officials_list:
        full_name = f'{official.EntityMembers.title}: {official.EntityMembers.member_first_name} {official.EntityMembers.member_last_name}'
        print(full_name)
        if official.MeetingAttendance.member_present == 'y':
            members_present += f"{full_name} \n"
        else:
            members_present += f"{full_name} (absent) \n"

    prompt = f"You are the city clerk responsible for meeting minutes. \n" \
             f"Using the agenda Create detailed meeting meetings, including motions and seconds \n" \
             f"include summary, with pertinent details, from each speaker \n" \
             f"agenda: {agenda} \n" \
             "Present at the meeting: \n" \
             f"{ members_present} \n" \
             "Include list of all members and staff present, and those absent"

    return prompt
