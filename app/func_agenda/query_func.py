from app.models import User, EntityName, EntityMembers, EntityGroups, MeetingAttendance, \
    MeetingInfo, MeetingMotionItems, MeetingMotionVotes, PromptInfo
from app import app, db


def get_motion_votes(meet_id):

    votes = db.session.query(EntityMembers, MeetingMotionVotes).filter(
        MeetingMotionVotes.meeting_id == meet_id,).filter(MeetingMotionVotes.member_id == EntityMembers.id).all()

    return votes


def get_attendance_list(meet_id):

    officials_list = db.session.query(EntityMembers, MeetingAttendance).filter(
        MeetingAttendance.meeting_id == meet_id, ).filter(MeetingAttendance.member_id == EntityMembers.id, ).all()
    print(f"db return officials: {officials_list}")

    return officials_list


def prompt_save(prompt, meet_id):

    prompt_obj = PromptInfo(meeting_id=meet_id, prompt_file=prompt)
    db.session.add(prompt_obj)
    db.session.commit()
    # meet_id = meeting.id

    return prompt_obj.id