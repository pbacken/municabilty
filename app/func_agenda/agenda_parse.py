import pdfplumber
import openai
import re
import json
from collections import defaultdict


def agenda_temp():
    agenda = {'meet_type': 'City Council Regular Meeting', 'date': 'April 4, 2023', 'time': '6:30 PM',
              'location': 'Council Chambers', 'sections': [
            {'number': 1, 'title': 'Call to Order',
             'subitems': [{'number': 'A', 'title': 'Pledge of Allegiance and Land Acknowledgement'},
                          {'number': 'B', 'title': 'Roll Call'},
                          {'number': 'C', 'title': "Proclamation Recognizing April as Parkinson's Awareness Month"},
                          {'number': 'D', 'title': 'Proclamation Recognizing April as Fair Housing Month'}]},
            {'number': 2, 'title': 'Additions and Corrections to Agenda'}, {'number': 3, 'title': 'Consent Agenda',
                                                                            'subitems': [{'number': 'A',
                                                                                          'title': 'Approval of City Council Minutes',
                                                                                          'subitems': [{'number': '1',
                                                                                                        'title': 'Minutes of the Regular City Council Meeting of March 21, 2023'}]},
                                                                                         {'number': 'B',
                                                                                          'title': 'Approval of City Check Registers'},
                                                                                         {'number': 'C',
                                                                                          'title': 'Licenses',
                                                                                          'subitems': [
                                                                                              {'number': '1',
                                                                                               'title': 'General Business Licenses - Fireworks Sales'}]},
                                                                                         {'number': 'D',
                                                                                          'title': 'Bids, Quotes, and Contracts',
                                                                                          'subitems': [{'number': '1',
                                                                                                        'title': 'Approve Contract for Brush Pick-Up with Bratt Tree Company'},
                                                                                                       {'number': '2',
                                                                                                        'title': 'Approve Contract for Gate Valve Repairs with Valley Rich Co., Inc.'},
                                                                                                       {'number': '3',
                                                                                                        'title': 'Approve Purchase of Replacement Outdoor Hockey Rink Dasher Boards, Steel Components, and Fencing for Scheid Park'},
                                                                                                       {'number': '4',
                                                                                                        'title': 'Approve Independent Contractor and Court Rental Agreement with Twin City Tennis Camps'}]},
                                                                                         {'number': 'E',
                                                                                          'title': 'Adopt Resolution No. 23-017 Approving Amendment to Compensation and Classification Tables'},
                                                                                         {'number': 'F',
                                                                                          'title': 'Receive and File 2022 Pay Equity Report'}]},
            {'number': 4, 'title': 'Public Hearing'}, {'number': 5, 'title': 'Old Business'},
            {'number': 6, 'title': 'New Business', 'subitems': [{'number': 'A',
                                                                 'title': 'Second Consideration of Ordinance No. 761 Amending the 2023 Master Fee Schedule for Items Related to Micromobility Licenses'},
                                                                {'number': 'B', 'title': 'Review of Council Calendar'},
                                                                {'number': 'C',
                                                                 'title': 'Mayor and Council Communications',
                                                                 'subitems': [{'number': '1',
                                                                               'title': 'Other Committee/Meeting updates'}]}]},
            {'number': 7, 'title': 'Adjournment'}]}

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
    with pdfplumber.open("app/files/{}".format(agenda_doc)) as pdf:
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
                        "include date labeled 'date', time labeled 'time', location labeled 'location' " +
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
    # motion_list = []
    motion_list_2 = []
    master_list = ['Old Business', 'New Business', 'Adjournment', 'Public Hearing', 'Regular Agenda', 'Approval Meeting Agenda']

    # meetings_list = [("", "Choose Meeting Type")] + [(i.group_code, i.group_type) for i in meeting_type]
    # motion_list.append('Consent Agenda')
    motion_list_2.append([{'ca': 'Consent Agenda', 'ca_2': 'Consent Agenda'}])

    for each_section in agenda['sections']:
        # print(str(each_section['number']) + ". " + each_section['title'])
        if each_section['title'] in master_list:
            if 'subitems' in each_section:
                for each_sub in each_section['subitems']:
                    motion_list_2.append([{str(each_section['number']) + str(each_sub['number']): each_sub['title']},
                                          {str(each_section['number']) + str(each_sub['number']+'_2'): each_sub['title']}])
                    # motion_list.append(str(each_section['number']) + str(each_sub['number']) + ". " + each_sub['title'])
                    # print(each_sub['number'] + ". " + each_sub['title'])
    # motion_list.append('Adjournment')
    motion_list_2.append([{'adj': 'Adjournment', 'adj_2': 'Adjournment'}])

    return motion_list_2




def to_pretty_json(value):
    return json.dumps(value, sort_keys=True,
                      indent=4, separators=(',', ': '))
