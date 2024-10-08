import pdfplumber
import openai
import re
import json
from app import app
from flask_login import current_user
from collections import defaultdict
from app.func_agenda.query_func import get_motion_votes


def agenda_temp():
    agenda = {{"meet_type": "City Council Meeting", "date": "March 19, 2024", "time": "7:00 PM", "location": "4100 Lakeview Avenue North, Robbinsdale, MN", "sections": [{"number": 1, "title": "CITY COUNCIL MEETING CALLED TO ORDER"}, {"number": 2, "title": "ROLL CALL", "subitems": [{"number": "A", "title": "Wagner"}, {"number": "B", "title": "Murphy"}, {"number": "C", "title": "Parisian"}, {"number": "D", "title": "Mayor Blonigan"}]}, {"number": 3, "title": "MICROPHONE CHECK", "subitems": [{"number": "A", "title": "Parisian"}, {"number": "B", "title": "Wagner"}, {"number": "C", "title": "Murphy"}, {"number": "D", "title": "Mayor Blonigan"}]}, {"number": 4, "title": "OPPORTUNITY FOR THE PUBLIC TO ADDRESS THE CITY COUNCIL ON MATTERS NOT ON THE AGENDA"}, {"number": 5, "title": "APPROVAL OF THE MARCH 19, 2024 MEETING AGENDA"}, {"number": 6, "title": "CONSENT AGENDA", "subitems": [{"number": "A", "title": "Approve City Council Meeting Minutes of February 6, 2024"}, {"number": "B", "title": "Farmers Market Memorandum of Understanding"}, {"number": "C", "title": "Approval of Credit Card Charges and Payment \u2013 February 2024"}, {"number": "D", "title": "Authorize City Manager to Execute Organized Labor Agreement"}, {"number": "E", "title": "Mobile Food Unit in Robin Center"}, {"number": "F", "title": "DNR No Child Left Inside Grant Acceptance"}, {"number": "G", "title": "Approval of Licenses"}]}, {"number": 7, "title": "PRESENTATIONS", "subitems": [{"number": "A", "title": "Hennepin County District Court Chief Judge Kerry Meyer"}]}, {"number": 8, "title": "PUBLIC HEARINGS", "subitems": [{"number": "A", "title": "None"}]}, {"number": 9, "title": "OLD BUSINESS", "subitems": [{"number": "A", "title": "Authorize City Manager to Execute License Agreement with Birdhouse Restaurant"}, {"number": "B", "title": "Authorize Wicked Wort to expand their current liquor license to include additional space"}]}, {"number": 10, "title": "NEW BUSINESS", "subitems": [{"number": "A", "title": "Authorize City Manager to execute a Professional Services Agreement with Bolton & Menk, Inc"}, {"number": "B", "title": "Consider Support for HF 4182 - Equal Broadband Act"}]}, {"number": 11, "title": "OTHER BUSINESS", "subitems": [{"number": "A", "title": "Voucher Requests Pending Approval for Disbursement"}]}, {"number": 12, "title": "ADMINISTRATIVE REPORTS"}, {"number": 13, "title": "COUNCIL GENERAL COMMUNICATIONS"}, {"number": 14, "title": "ADJOURNMENT"}]}}

    return agenda


def agenda_items(agenda):
    agenda_items = []
    agenda_sub_items = defaultdict(list)
    current_agenda_item = ""
    with pdfplumber.open(agenda) as pdf:
        for page in pdf.pages:
            print(page.page_number)
            text_extract = page.extract_text()
            value = text_extract.split("\n")

            for t in value:

                print(t, re.search(r"\b[a-zA-Z]\w*\.", t.strip()))
                if re.search("^\d+\.$", t[:3].strip()) is not None:
                    if t.find(":") == -1:
                        agenda_items.append(t)
                    else:
                        agenda_items.append(t[:t.find(":")])

                    current_agenda_item = t[:3].strip()
                # Grab items for each section
                if re.search(r"\b[a-zA-Z]\w*\.", t[:3].strip()) is not None:
                    if current_agenda_item != "":
                        print("Here's one!", current_agenda_item)
                        agenda_sub_items[current_agenda_item].append(t)
                if t.find('ADJOURNMENT') != -1:
                    print(agenda_items)
                    print(agenda_sub_items)
                    exit()

    return agenda_items, agenda_sub_items


def openai_agenda(agenda_doc):
    client = openai.OpenAI()

    text_extract = ""
    new_path = f"{app.config['UPLOAD_PATH']}/{current_user.user_city}/{agenda_doc}"
    with pdfplumber.open(new_path.format(agenda_doc)) as pdf:
        for page in pdf.pages:
            # print(page.page_number)
            if page.page_number < 4:
                text_extract += page.extract_text()

        print("PDF read done.")

    completion = client.chat.completions.create(
        model="gpt-4o-mini",
        response_format={"type": "json_object"},
        messages=[
            {"role": "system", "content": "You are a helpful assistant designed to output JSON."},
            {"role": "user",
             "content": "You are a city clerk assistant, create an agenda from the following text. " +
                        "include meeting type labeled 'meet_type' " +
                        "include date formatted Month Date, Year and labeled 'date', time in Standard time and labeled 'time', location labeled 'location' " +
                        "label parent item for main topics as 'sections' " +
                        "label main topics with 'number' and a digit starting at 1. and topics labeled 'title' " +
                        "label subitem section as 'subitems', " +
                        "label subitem topics with 'number' and a letter " +
                        "starting at 'A.'. " +
                        "Text: {}".format(text_extract)},
                ]
    )

    agenda = json.loads(completion.choices[0].message.content)
    # agenda = json.loads(agenda)

    return agenda
    # return str(completion.choices[0].message)[str(agenda).find("content=") + 8:str(agenda).find("role=")].split('/n')


def agenda_form(agenda):
    m_date = agenda['date']
    m_time = agenda['time']
    m_location = agenda['location']

    for each_section in agenda['sections']:
        print(str(each_section['number']) + ". " + each_section['title'])
        if 'subitems' in each_section:
            for each_sub in each_section['subitems']:
                print(each_sub['number'] + ". " + each_sub['title'])


def create_motion_list(agenda):
    motion_list_labels = []
    motion_list_full = []
    ml_sm = {}
    consent_list_labels = []
    consent_list_full = []
    cl_sm = {}

    section_master_list = ['approval of the', 'consent agenda', 'public hearings',
                           'old business', 'new business', 'other business', 'adjournment', 'information only']

    if 'work session' in agenda['meet_type'].casefold():
        print(f"found Work session:  {agenda['meet_type'].casefold()}")
        return motion_list_labels, motion_list_full, consent_list_labels, consent_list_full, ml_sm, cl_sm

    for each_section in agenda['sections']:
        for master in section_master_list:
            if master in each_section['title'].casefold():
                if 'subitems' in each_section:
                    if each_section['title'].casefold() in 'consent agenda':
                        ml_sm_list = []
                        motion_list_labels.append(str(each_section['number']))
                        motion_list_labels.append(str(each_section['number']) + '_2')
                        motion_list_full.append([{str(each_section['number']): each_section['title']},
                                                 {str(each_section['number']) + '_2': each_section[
                                                     'title']}])
                        ml_sm_list.append(f"{each_section['number']}")
                        ml_sm[each_section['title'].casefold()] = ml_sm_list
                        cl_sm_list = []
                        for each_sub in each_section['subitems']:
                            consent_list_labels.append(str(each_section['number']) + str(each_sub['number']))
                            consent_list_labels.append(str(each_section['number']) + str(each_sub['number']+'_2'))
                            consent_list_full.append(
                                [{str(each_section['number']) + str(each_sub['number']): each_sub['title']},
                                 {str(each_section['number']) + str(each_sub['number'] + '_2'): each_sub['title']}])
                            cl_sm_list.append(f"{each_section['number']}{each_sub['number']}")
                        cl_sm[each_section['title'].casefold()] = cl_sm_list
                    else:
                        ml_sm_list = []
                        for each_sub in each_section['subitems']:
                            if not each_sub['title'].casefold() == 'none':
                                motion_list_labels.append(str(each_section['number']) + str(each_sub['number']))
                                motion_list_labels.append(str(each_section['number']) + str(each_sub['number']+'_2'))
                                motion_list_full.append([{str(each_section['number']) + str(each_sub['number']): each_sub['title']},
                                                      {str(each_section['number']) + str(each_sub['number']+'_2'): each_sub['title']}])
                                ml_sm_list.append(f"{each_section['number']}{each_sub['number']}")
                        ml_sm[each_section['title'].casefold()] = ml_sm_list
                else:
                    ml_sm_list = []
                    motion_list_labels.append(str(each_section['number']))
                    motion_list_labels.append(str(each_section['number']) + '_2')
                    motion_list_full.append([{str(each_section['number']): each_section['title']},
                                             {str(each_section['number']) + '_2': each_section[
                                                 'title']}])
                    ml_sm_list.append(f"{each_section['number']}")
                    ml_sm[each_section['title'].casefold()] = ml_sm_list

    return motion_list_labels, motion_list_full, consent_list_labels, consent_list_full, ml_sm, cl_sm


def get_speaker_list(diary):
    for each_line in diary:
        if 'Speaker' in each_line:
            print(each_line)

    return True


def updated_agenda(agenda, meet_id):

    motion_list_labels, motion_list_full, consent_list_labels, consent_list_full, ml_sm, cl_sm = create_motion_list(agenda)

    print(f" ml_sm:  {ml_sm}")
    motion_votes = get_motion_votes(meet_id)
    print(f"motion votes: {motion_votes}")
    mot_call = {}

    for motion in motion_votes:
        full_name = f"{motion.EntityMembers.member_first_name} {motion.EntityMembers.member_last_name}"
        mot_call[motion.MeetingMotionVotes.motion_id] = full_name

    print(f"mot_call: {mot_call}")
    agenda_votes = ""

    for each_section in agenda['sections']:
        # print(f"{each_section['number']}. {each_section['title']}")
        agenda_votes += f"{each_section['number']}. {each_section['title']}"
        if each_section['title'].casefold() in ml_sm:
            # check if consent
            if 'consent' in each_section['title'].casefold():
                print('Found Consent')
                print(f'Consent: ')
                # print(f"Motion by: {mot_call[ml_sm[each_section['title'].casefold()][0]]} "
                      # f"/  Seconded: {mot_call[ml_sm[each_section['title'].casefold()][0] + '_2']}")
                if each_section['title'].casefold() in mot_call:
                    agenda_votes += f"Motion by: {mot_call[ml_sm[each_section['title'].casefold()][0]]} /  Seconded: {mot_call[ml_sm[each_section['title'].casefold()][0] + '_2']}"
            # check if each_section has subitems
            if 'subitems' in each_section:
                for each_sub in each_section['subitems']:
                    # print(f"    {each_sub['number']}. {each_sub['title']}")
                    agenda_votes += f"    {each_sub['number']}. {each_sub['title']}"
                    if each_section['title'].casefold() in ml_sm:
                        for ss in ml_sm[each_section['title'].casefold()]:
                            if ss == f"{each_section['number']}{each_sub['number']}":
                                # print(f"    Motion by: {mot_call[ss]}  /  Seconded: {mot_call[ss + '_2']}")
                                if ss in mot_call:
                                    agenda_votes += f"    (Motion by: {mot_call[ss]}  /  Seconded: {mot_call[ss + '_2']})"
                    if each_section['title'].casefold() in cl_sm:
                        consent_motion_info = ''
                        for ss in cl_sm[each_section['title'].casefold()]:
                            if ss in mot_call:
                                if ss == f"{each_section['number']}{each_sub['number']}":
                                    # print(
                                        #f"    Item pulled. Motion by: {mot_call[ss]}  /  Seconded: {mot_call[ss + '_2']}")
                                    agenda_votes += f"    (Item pulled for discussion. Motion by: {mot_call[ss]}  /  Seconded: {mot_call[ss + '_2']})"
            else:
                if ml_sm[each_section['title'].casefold()]:
                    # print(f"Motion by: {mot_call[ml_sm[each_section['title'].casefold()][0]]} "
                          # f"/  Seconded: {mot_call[ml_sm[each_section['title'].casefold()][0] + '_2']}")
                    for ss in ml_sm[each_section['title'].casefold()]:
                        if ss in mot_call:
                            agenda_votes += f"Motion by: {mot_call[ml_sm[each_section['title'].casefold()][0]]} /  Seconded: {mot_call[ml_sm[each_section['title'].casefold()][0] + '_2']}"

    return agenda_votes


def to_pretty_json(value):
    return json.dumps(value, sort_keys=True,
                      indent=4, separators=(',', ': '))
