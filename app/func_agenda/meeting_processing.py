import os
from datetime import datetime
from app.func_agenda.agenda_parse import openai_agenda, to_pretty_json, agenda_temp, create_motion_list, updated_agenda
from app.func_agenda.form_config import file_list_form_builder, diary_speaker_list
from app.func_agenda.query_func import get_attendance_list, prompt_save
from app import app, db
import json
from flask_login import current_user
import assemblyai as aai
from app.models import EntityGroups
import uuid


def create_prompt(meet_id, meeting):
    print('Start_prompt')
    # original_agenda = agenda_temp()
    # get agenda

    agenda_path = f"{app.config['UPLOAD_PATH']}/{current_user.user_city}/json/"
    file = open(f"{agenda_path}/{meeting.meeting_agenda}.txt", "r")
    original_agenda = json.load(file)

    # add motion callers to agenda
    motion_agenda = updated_agenda(original_agenda, meet_id)

    officials_list = get_attendance_list(meet_id)
    print(f"Officials: {officials_list}")

    members_present = ""
    for official in officials_list:
        full_name = f'{official.EntityMembers.title}: {official.EntityMembers.member_first_name} {official.EntityMembers.member_last_name}'

        if official.MeetingAttendance.member_present == 'y':
            members_present += f"{full_name} \n"
        else:
            members_present += f"{full_name} (absent) \n"

    prompt = f"You are the city clerk responsible for meeting minutes. \n" \
             f"Using the agenda Create detailed meeting meetings \n" \
             f"include summary, with pertinent details, from each speaker \n" \
             f"agenda: {motion_agenda} \n" \
             "Present at the meeting: \n" \
             f"{ members_present} \n" \
             f"Meeting started at 7:00pm " \
             f"Do not include 'Citizen Participation' agenda item in minutes " \
             "Include list of all members and staff present, and those absent " \
             "Include summary of each speaker for council communications agenda item " \
             "Include who motions and seconds each item "

    prompt_path = f"{app.config['UPLOAD_PATH']}/{current_user.user_city}/prompt"
    promptuuid = uuid.uuid4()
    if not os.path.exists(prompt_path):
        os.makedirs(prompt_path)
    f = open(f"{prompt_path}/{promptuuid}.txt", "w")
    f.write(prompt)
    f.close()
    print("File Written")

    save_prompt = prompt_save(str(promptuuid), meet_id)

    return prompt


def create_minutes(prompt, meeting):

    # create path to file
    # audio_path = f"{app.config['UPLOAD_PATH']}/{current_user.user_city}/audio/{meeting.audio_name}"

    aai.settings.api_key = os.environ['AAI_API_KEY']

    # link to audio file
    audio_url = f"{app.config['UPLOAD_PATH']}/{current_user.user_city}/audio/{meeting.audio_name}"

    # set config for transcription (include speaker labels)
    config = aai.TranscriptionConfig(speaker_labels=True,)

    # transcribe the audio
    print("start transcribe")
    transcript = aai.Transcriber().transcribe(audio_url, config)
    print("end transcribe")

    # summarize the transcription (4000 tokens due to large files)
    print("start summary")
    result = transcript.lemur.task(
        prompt, max_output_size=4000, final_model=aai.LemurModel.claude3_5_sonnet
    )
    print("end summary")

    # Parse transcription for diarization of audio
    text = ""
    for utt in transcript.utterances:
        text += f"Speaker {utt.speaker}:\n{utt.text}\n"
    print("after parse transcribe")

    # Get Meeting Object
    meet_code = ""
    groups = db.session.query(EntityGroups).filter(
        EntityGroups.entity_code == current_user.user_city_code).all()
    for group in groups:
        if group.group_type in meeting.meeting_type:
            meet_code = group.group_code
    if meet_code == "":
        return "error - meeting type not found"
    print('after groups')

    dt = datetime.strptime(meeting.meeting_date, '%B %d, %Y').strftime('%m%d%y')

    # Save diarization and summary
    f = open(f"{app.config['UPLOAD_PATH']}/{current_user.user_city}/minutes/{meeting.meeting_entity}_"
             f"{meet_code}_{dt}_diary.txt", "w")
    f.write(text)
    f.close()
    print('after diary save')

    f = open(f"{app.config['UPLOAD_PATH']}/{current_user.user_city}/minutes/{meeting.meeting_entity}_"
             f"{meet_code}_{dt}_summary.txt", "w")
    f.write(result.response)
    f.close()
    print('after summary save')

    # update meeting object with minutes file name
    meeting.meeting_minutes = f"{meeting.meeting_entity}_{meet_code}_{dt}"
    db.session.commit()

    return result.response

