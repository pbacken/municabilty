

def process_meeting_data(staff_list, member_list, motion_list, agenda):
    pass


def create_prompt(staff_list, member_list, city, agenda):
    prompt = f"You are the {city} city clerk. " \
             f"Using the agenda Create detailed meeting meetings, including motions and seconds " \
             f"include summary, with pertinent details, from each speaker " \
             f"agenda: {agenda}" \
             "Present at the meeting:" \
             f"Staff: {staff_list}" \
             f"Members: {member_list}" \
             "Include list of all members and staff present, and those absent"
