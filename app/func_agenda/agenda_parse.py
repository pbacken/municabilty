import pdfplumber
import openai
import re
import json
from collections import defaultdict


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
    with pdfplumber.open("app/audio/{}".format(agenda_doc)) as pdf:
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
    print(agenda)
    # agenda = json.loads(agenda)

    return agenda
    # return str(completion.choices[0].message)[str(agenda).find("content=") + 8:str(agenda).find("role=")].split('/n')


def to_pretty_json(value):
    return json.dumps(value, sort_keys=True,
                      indent=4, separators=(',', ': '))
