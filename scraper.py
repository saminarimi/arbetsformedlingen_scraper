import requests
import re
import json
from pprint import pprint


# read the list of keywords
def read_keywords():
    file = open('keywords.txt', 'r', encoding='utf-8')
    text = file.read()
    file.close()
    return text.strip().split('\n')


# search the site and get all the results for one keyword
def search(keyword):
    print(f'searching keyword : {keyword}')
    max_records = 100

    final_results = []
    for page_number in range(1, 1000000):
        start_index = (page_number - 1) * max_records

        print(f'page : {page_number}')

        headers = {
            'Connection': 'keep-alive',
            'sec-ch-ua': '"Chromium";v="88", "Google Chrome";v="88", ";Not A Brand";v="99"',
            'Accept': 'application/json, text/plain, */*',
            'INT_SYS': 'platsbanken_web_beta',
            'Requesting-Device-Id': 'ce83da79-29fd-4822-97c8-633195b6ce1c',
            'sec-ch-ua-mobile': '?0',
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.182 Safari/537.36',
            'Content-Type': 'application/json',
            'Origin': 'https://arbetsformedlingen.se',
            'Sec-Fetch-Site': 'same-site',
            'Sec-Fetch-Mode': 'cors',
            'Sec-Fetch-Dest': 'empty',
            'Referer': 'https://arbetsformedlingen.se/',
            'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
        }

        data = {
            "filters": [{"type": "freetext", "value": keyword}],
            "fromDate": None,
            "order": "relevance",
            "maxRecords": max_records,
            "startIndex": start_index,
            "toDate": "2021-02-20T02:39:10.021Z",
            "source": "pb"
        }

        response = requests.post('https://platsbanken-api.arbetsformedlingen.se/jobs/v1/search',
                                 headers=headers, json=data)

        '''
        if we need text or html =>  response.text (attribute)
        if we need data in json or dict => response.json() (method)
        '''
        search_data = response.json()

        try:
            for first_data in search_data['ads']:
                final_results.append({
                    'title': first_data['title'],
                    'id': first_data["id"]
                })
        except:
            break
    return final_results


# take an id as input and return the json data for that id
def get_json_data(url_id):
    headers = {
        'Connection': 'keep-alive',
        'sec-ch-ua': '"Chromium";v="88", "Google Chrome";v="88", ";Not A Brand";v="99"',
        'Accept': 'application/json, text/plain, */*',
        'INT_SYS': 'platsbanken_web_beta',
        'Requesting-Device-Id': 'ce83da79-29fd-4822-97c8-633195b6ce1c',
        'sec-ch-ua-mobile': '?0',
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/88.0.4324.182 Safari/537.36',
        'Origin': 'https://arbetsformedlingen.se',
        'Sec-Fetch-Site': 'same-site',
        'Sec-Fetch-Mode': 'cors',
        'Sec-Fetch-Dest': 'empty',
        'Referer': 'https://arbetsformedlingen.se/',
        'Accept-Language': 'en-GB,en-US;q=0.9,en;q=0.8',
    }

    response = requests.get(f'https://platsbanken-api.arbetsformedlingen.se/jobs/v1/job/{url_id}', headers=headers)
    return response.json()


# get emails from given string and return a list of emails
def find_emails_from_text(text):
    # email_regex = r'\w+@[a-zA-Z_]+?\.[a-zA-Z]{2,3}' # online version
    email_regex = r'[a-zA-Z0-9\.\-+_]+@[a-zA-Z0-9\.\-+_]+\.[a-zA-Z]+'  # rose version

    emails = re.findall(email_regex, text)
    return emails


# get phone numbers from given string and return a list of phone numbers
def find_phones_from_text(text):
    # use regex to search for phone numbers in the text and return a list of phone numbers

    # todo: test this regular expression
    phone_number_regex = r'(\+\d{1,2}\s)?\(?\d{3,4}\)?[\s.-]\d{3,4}[\s.-]\d{3,4}'
    phone_numbers = re.findall(phone_number_regex, text)
    return phone_numbers


# get the email, phone numbers and names from a given json data.
# this function will first check if there are email/phone in contacts. if not found, then it will
# get those data from the description.
def get_all_details(id):
    # get the json data for the given id
    json_data = get_json_data(id)

    # first try to get name, email, phone from contacts
    contacts = json_data['contacts']
    persons = []
    for contact in contacts:
        persons.append({
            'email': contact['email'],
            'phone': contact['phoneNumber'],
            'name': str(contact['name']) + str(contact['surname']),
            'description': contact['description']
        })

    # check if any person was found. of not, then get
    # the contacts from the description
    if len(persons) == 0:
        print('No person found in contacts')
        text = json_data['description']
        description_emails = find_emails_from_text(text)
        description_phones = find_phones_from_text(text)
        for mail in description_emails:
            name = get_name_from_email(mail)
            persons.append({
                'email': mail,
                'phone': None,
                'name': name,
                'description': None
            })

    return persons


# take an email as input and return a name
def get_name_from_email(email):
    name = email.split('@')[0]
    client_name = name.split('.')
    for i in range(len(client_name)):
        client_name[i] = client_name[i].capitalize()
    return ' '.join(client_name)


if __name__ == '__main__':
    # read the keywords
    keywords = read_keywords()
    data = {}

    # for each keyword get all the search results
    for keyword in keywords[:1]:
        search_results = search(keyword)

        # TODO(raja): check if any of the search results were already found if the script was run previously
        # TODO(raja): update the cache to save the list of search results

        # for each search result, get the persons
        for search_result in search_results[:21]:
            persons = get_all_details(search_result['id'])

            # save all the results in a single dict
            data[search_result['id']] = {
                'title': search_result['title'],
                'persons': persons
            }
    pprint(data)

    # TODO(raja): finally convert the data into excel file and save it

