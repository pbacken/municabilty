agenda = {'date': 'April 4, 2023', 'time': '6:30 PM', 'location': 'Council Chambers', 'sections': [{'number': 1, 'title': 'Call to Order', 'subitems': [{'number': 'A', 'title': 'Pledge of Allegiance and Land Acknowledgement'}, {'number': 'B', 'title': 'Roll Call'}, {'number': 'C', 'title': "Proclamation Recognizing April as Parkinson's Awareness Month"}, {'number': 'D', 'title': 'Proclamation Recognizing April as Fair Housing Month'}]}, {'number': 2, 'title': 'Additions and Corrections to Agenda'}, {'number': 3, 'title': 'Consent Agenda', 'subitems': [{'number': 'A', 'title': 'Approval of City Council Minutes', 'subitems': [{'number': '1', 'title': 'Minutes of the Regular City Council Meeting of March 21, 2023'}]}, {'number': 'B', 'title': 'Approval of City Check Registers'}, {'number': 'C', 'title': 'Licenses', 'subitems': [{'number': '1', 'title': 'General Business Licenses - Fireworks Sales'}]}, {'number': 'D', 'title': 'Bids, Quotes, and Contracts', 'subitems': [{'number': '1', 'title': 'Approve Contract for Brush Pick-Up with Bratt Tree Company'}, {'number': '2', 'title': 'Approve Contract for Gate Valve Repairs with Valley Rich Co., Inc.'}, {'number': '3', 'title': 'Approve Purchase of Replacement Outdoor Hockey Rink Dasher Boards, Steel Components, and Fencing for Scheid Park'}, {'number': '4', 'title': 'Approve Independent Contractor and Court Rental Agreement with Twin City Tennis Camps'}]}, {'number': 'E', 'title': 'Adopt Resolution No. 23-017 Approving Amendment to Compensation and Classification Tables'}, {'number': 'F', 'title': 'Receive and File 2022 Pay Equity Report'}]}, {'number': 4, 'title': 'Public Hearing'}, {'number': 5, 'title': 'Old Business'}, {'number': 6, 'title': 'New Business', 'subitems': [{'number': 'A', 'title': 'Second Consideration of Ordinance No. 761 Amending the 2023 Master Fee Schedule for Items Related to Micromobility Licenses'}, {'number': 'B', 'title': 'Review of Council Calendar'}, {'number': 'C', 'title': 'Mayor and Council Communications', 'subitems': [{'number': '1', 'title': 'Other Committee/Meeting updates'}]}]}, {'number': 7, 'title': 'Adjournment'}]}
mc = {'ca': 'Bill Blonigan', 'ca_2': 'Regan Murphy', '6A': 'Jason Greenberg', '6A_2': 'Aaron Wagner',
     'adj': 'Aaron Wagner', 'adj_2': 'Bill Blonigan'}
ml = [{'Consent Agenda': 'ca'},
    {'Second Consideration of Ordinance No. 761 Amending the 2023 Master Fee Schedule for Items Related to Micromobility Licenses': '6A'},
    {'Review of Council Calendar': '6B'},
    {'Mayor and Council Communications': '6C'},
    {'Adjournment': 'adj'}]


m_date = agenda['date']
m_time = agenda['time']
m_location = agenda['location']

nn = {'Consent Agenda': 'ca',
    'Second Consideration of Ordinance No. 761 Amending the 2023 Master Fee Schedule for Items Related to Micromobility Licenses': '6A',
    'Review of Council Calendar': '6B',
    'Mayor and Council Communications': '6C',
    'Adjournment': 'adj'}

for each_section in agenda['sections']:
    print(str(each_section['number'])+". "+each_section['title'])
    try:
        if each_section['title'] in nn:
            # st = f"{nn[each_section['title']]}"
            # nd = f"{nn[each_section['title']]}_2"
            print(f"First: {mc[nn[each_section['title']]]}")
            print(f"Second: {mc[nn[each_section['title']]+'_2']}")
    except KeyError:
        pass

    if 'subitems' in each_section:
        for each_sub in each_section['subitems']:
            print(each_sub['number']+". "+each_sub['title'])
            try:
                if each_sub['title'] in nn:
                    print(f"First: {mc[nn[each_sub['title']]]}")
                    print(f"Second: {mc[nn[each_sub['title']] + '_2']}")
            except KeyError:
                pass
