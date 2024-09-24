from app.models import User, EntityName, EntityMembers, EntityGroups, MeetingAttendance, \
    MeetingInfo, MeetingMotionItems, MeetingMotionVotes
from app import app, db


def get_motion_votes(meet_id):

    votes = db.session.query(EntityMembers, MeetingMotionVotes).filter(
        MeetingMotionVotes.meeting_id == meet_id,).filter(MeetingMotionVotes.member_id == EntityMembers.id).all()

    return votes


def get_attendance_list(meet_id):

    officials_list = db.session.query(EntityMembers, MeetingAttendance).filter(
        MeetingAttendance.meeting_id == meet_id, ).filter(MeetingAttendance.member_id == EntityMembers.id, ).all()

    return officials_list