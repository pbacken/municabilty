agenda = {'meet_type': 'City Council Regular Meeting', 'date': 'April 4, 2023', 'time': '6:30 PM', 'location': 'Council Chambers', 'sections': [
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
                                                                                      'title': 'Licenses', 'subitems': [
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
                                                            {'number': 'C', 'title': 'Mayor and Council Communications',
                                                             'subitems': [{'number': '1',
                                                                           'title': 'Other Committee/Meeting updates'}]}]},
        {'number': 7, 'title': 'Adjournment'}]}


# motion_list = []
motion_list_2 = []
ml_sm = {}
# master_list = ['Old Business', 'New Business', 'Adjournment', 'Public Hearing', 'Regular Agenda', 'Approval Meeting Agenda']

# meetings_list = [("", "Choose Meeting Type")] + [(i.group_code, i.group_type) for i in meeting_type]
# motion_list.append('ca')
# motion_list.append('ca_2')

#motion_list_2.append([{'ca': 'Consent Agenda', 'ca_2': 'Consent Agenda'}])


for each_section in agenda['sections']:
    print(each_section)
    """ 
    if each_section['title'] in master_list:
        if 'subitems' in each_section:
            for each_sub in each_section['subitems']:
                motion_list.append(str(each_section['number']) + str(each_sub['number']))
                motion_list.append(str(each_section['number']) + str(each_sub['number']+'_2'))
                motion_list_2.append([{str(each_section['number']) + str(each_sub['number']): each_sub['title']},
                                      {str(each_section['number']) + str(each_sub['number']+'_2'): each_sub['title']}])


motion_list.append('adj')
motion_list.append('adj_2')
motion_list_2.append([{'adj': 'Adjournment', 'adj_2': 'Adjournment'}])

{'Consent Agenda': 'ca',
 'Second Consideration of Ordinance No. 761 Amending the 2023 Master Fee Schedule for Items Related to Micromobility Licenses': '6A',
 'Review of Council Calendar': '6B',
 'Mayor and Council Communications': '6C',
 'Adjournment': 'adj'}
"""

# return motion_list, motion_list_2