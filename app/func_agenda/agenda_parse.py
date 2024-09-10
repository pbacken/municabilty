import pdfplumber
import openai
import re
import json
from app import app
from flask_login import current_user
from collections import defaultdict


def agenda_temp():
    agenda = {"meet_type": "City Council Meeting", "date": "September 3, 2024", "time": "7:00 PM", "location": "4100 Lakeview Avenue North, Robbinsdale, MN", "sections": [{"number": 1, "title": "CITY COUNCIL MEETING CALLED TO ORDER"}, {"number": 2, "title": "ROLL CALL", "subitems": [{"number": "A", "title": "Wagner"}, {"number": "B", "title": "Murphy"}, {"number": "C", "title": "Greenberg"}, {"number": "D", "title": "Parisian"}, {"number": "E", "title": "Mayor Blonigan"}]}, {"number": 3, "title": "MICROPHONE CHECK", "subitems": [{"number": "A", "title": "Wagner"}, {"number": "B", "title": "Murphy"}, {"number": "C", "title": "Greenberg"}, {"number": "D", "title": "Parisian"}, {"number": "E", "title": "Mayor Blonigan"}]}, {"number": 4, "title": "OPPORTUNITY FOR THE PUBLIC TO ADDRESS THE CITY COUNCIL ON MATTERS NOT ON THE AGENDA"}, {"number": 5, "title": "APPROVAL OF THE SEPTEMBER 3, 2024 MEETING AGENDA"}, {"number": 6, "title": "CONSENT AGENDA", "subitems": [{"number": "A", "title": "Approve Special City Council Meeting minutes from July 9, 2024"}, {"number": "B", "title": "Receive Parks, Recreation, and Forestry Commission minutes from June 25, 2024"}, {"number": "C", "title": "Deputy Registrar\u2019s Monthly Financial Statements"}, {"number": "D", "title": "Robbinsdale Wine & Spirits\u2019 Monthly Financial Statements"}, {"number": "E", "title": "Quarterly Financial Information for General, Water, Sanitary Sewer, Storm Sewer, and Solid Waste"}, {"number": "F", "title": "Scheduling Public Hearing on October 1, 2024, to Certify the Assessment Roll for Unpaid Administrative Penalties"}, {"number": "G", "title": "Scheduling Public Hearing on October 1, 2024, to Certify the Assessment Roll for Delinquent Utilities"}, {"number": "H", "title": "Scheduling Public Hearing on October 1, 2024, to Certify the Assessment Roll for Emergency Water, Sewer, and Sump Pump Repairs"}, {"number": "I", "title": "Approval of Licenses"}, {"number": "J", "title": "UNCF Walk for Education"}, {"number": "K", "title": "Faith Chapel Event"}]}, {"number": 7, "title": "PRESENTATIONS", "subitems": [{"number": "A", "title": "LMC Legislators of Distinction - Senator Rest, Representative Freiberg"}]}, {"number": 8, "title": "PUBLIC HEARINGS", "subitems": [{"number": "A", "title": "Public Hearing to receive feedback on the Blue Line Light Rail Extension"}]}, {"number": 9, "title": "OLD BUSINESS", "subitems": [{"number": "A", "title": "Consider Consumption and Display Permit for 4130 Lakeland"}]}, {"number": 10, "title": "NEW BUSINESS", "subitems": [{"number": "A", "title": "None"}]}, {"number": 11, "title": "OTHER BUSINESS", "subitems": [{"number": "A", "title": "Voucher Requests Pending Approval for Disbursement"}]}, {"number": 12, "title": "ADMINISTRATIVE REPORTS"}, {"number": 13, "title": "COUNCIL GENERAL COMMUNICATIONS"}, {"number": 14, "title": "ADJOURNMENT"}]}

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

        # print(text_extract)

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
    motion_list = []
    motion_list_2 = []
    ml_sm = {}
    consent_list = []
    consent_list_2 = []
    cl_sm = {}

    master_list = ['approval of the', 'consent agenda', 'public hearing', 'public hearings',
                   'old business', 'new business', 'other business', 'adjournment']

    # meetings_list = [("", "Choose Meeting Type")] + [(i.group_code, i.group_type) for i in meeting_type]
    # motion_list.append('ca')
    # motion_list.append('ca_2')
    # motion_list_2.append([{'ca': 'Consent Agenda', 'ca_2': 'Consent Agenda'}])
    # ml_sm["Consent Agenda"] = ""

    for each_section in agenda['sections']:
        print(each_section['title'].casefold())
        if each_section['title'].casefold() in master_list:
            if 'subitems' in each_section:
                if each_section['title'].casefold() in 'consent agenda':
                    for each_sub in each_section['subitems']:
                        consent_list.append(str(each_section['number']) + str(each_sub['number']))
                        consent_list.append(str(each_section['number']) + str(each_sub['number']+'_2'))
                        consent_list_2.append(
                            [{str(each_section['number']) + str(each_sub['number']): each_sub['title']},
                             {str(each_section['number']) + str(each_sub['number'] + '_2'): each_sub['title']}])
                else:
                    for each_sub in each_section['subitems']:
                        if not each_sub['title'].casefold() == 'none':
                            motion_list.append(str(each_section['number']) + str(each_sub['number']))
                            motion_list.append(str(each_section['number']) + str(each_sub['number']+'_2'))
                            motion_list_2.append([{str(each_section['number']) + str(each_sub['number']): each_sub['title']},
                                                  {str(each_section['number']) + str(each_sub['number']+'_2'): each_sub['title']}])

    motion_list.append('adj')
    motion_list.append('adj_2')
    motion_list_2.append([{'adj': 'Adjournment', 'adj_2': 'Adjournment'}])

    """
    {'Consent Agenda': 'ca',
     'Second Consideration of Ordinance No. 761 Amending the 2023 Master Fee Schedule for Items Related to Micromobility Licenses': '6A',
     'Review of Council Calendar': '6B',
     'Mayor and Council Communications': '6C',
     'Adjournment': 'adj'}
    """
    # print(motion_list_2)
    # print(consent_list_2)
    return motion_list, motion_list_2, consent_list, consent_list_2


def to_pretty_json(value):
    return json.dumps(value, sort_keys=True,
                      indent=4, separators=(',', ': '))
