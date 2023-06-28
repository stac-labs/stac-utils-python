import hmac, hashlib
import os, time
import sys

import xmltodict
import requests
import pandas as pd

from insert_leads import insert_hot_lead
from datetime import datetime, date, timedelta

if "BSD_API_SECRET" not in os.environ:
    # Try to load from .env
    from dotenv import load_dotenv

    load_dotenv()

try:
    api_secret = os.environ['BSD_API_SECRET']
    BSD_API_ID = os.environ['BSD_API_ID']
    BSD_URL = os.environ['BSD_URL']
except KeyError:
    sys.exit('Cannot find BSD API Secret')

api_ver = 2  # BSD API ID - always 2
signup_form_id = "115"  # NC Volunteer Form ID from BSD


# Generating the API MAC necessary for the BSD API
def generate_api_mac(time, url, params_str=None):
    root_params = 'api_ver=2&api_id=' + BSD_API_ID \
                  + '&api_ts=' + time

    params = root_params

    if params_str != None:
        params += "&" + params_str

    signing_str = BSD_API_ID + os.linesep \
                  + time + os.linesep \
                  + url + os.linesep \
                  + params

    api_mac = hmac.new(api_secret.encode(), signing_str.encode(), hashlib.sha1).hexdigest()

    print(signing_str)
    print(api_mac)

    return api_mac


# Get volunteer signups from the NC Volunteer Form from the previous day.
# Returns a pandas DataFrame containing sign in data.
def get_volunteer_signups():
    current_time = str(int(time.time()))

    url = '/page/api/signup/get_signups_by_form_id'
    params_str = "signup_form_id=" + signup_form_id

    columns = ['ID', 'First Name', 'Last Name', 'Phone', 'Email', 'Zip', 'VR', 'Canvass', 'Calls', 'Texts',
               'Attend Events', 'Donate', 'Signup Date']
    api_mac = generate_api_mac(current_time, url, params_str)

    params = {
        'api_ver': api_ver,
        'api_id': BSD_API_ID,
        'api_ts': current_time,
        'api_mac': api_mac,
        'signup_form_id': signup_form_id
    }

    today = datetime.now().date()

    resp = requests.get(get_full_url(url), params=params)

    if resp.status_code == requests.codes.ok:
        signup_data = []
        print(resp.text)

        # Response from BSD is an XML structure so we need to parse it
        xml = xmltodict.parse(resp.text, xml_attribs=False)
        signups = xml['api']['stg_signups']['stg_signup']

        for signup in signups:
            s_data = {
                'ID': signup['stg_signup_id'],
                'First Name': signup['firstname'].title() if signup['firstname'].title() else None,
                'Last Name': signup['lastname'].title() if signup['lastname'] else None,
                'Phone': signup['phone'],
                'Email': signup['email'].lower() if signup['email'] else None,
                'Zip': signup['zip'],
                'VR': False,
                'Canvass': False,
                'Calls': False,
                'Texts': False,
                'Attend Events': False,
                'Donate': False,
                'Signup Date': signup['create_dt'].split(" ")[0]
            }

            t = s_data['Signup Date'].split("-")
            d = date(int(t[0]), int(t[1]), int(t[2]))

            yesterday = today - timedelta(days=1)

            if (d == yesterday):
                if 'stg_signup_extra' in signup:
                    su_extra = signup['stg_signup_extra']

                    if 'stg_signup_extra_value' in su_extra:
                        extra_vals = su_extra['stg_signup_extra_value']

                        if isinstance(extra_vals, list):
                            for extra_val in extra_vals:
                                value = extra_val['value_varchar']

                                if (value == 'Help register voters'):
                                    s_data['VR'] = True
                                elif (value == 'Canvass'):
                                    s_data['Canvass'] = True
                                elif (value == 'Make calls'):
                                    s_data['Calls'] = True
                                elif (value == 'Text voters'):
                                    s_data['Texts'] = True
                                elif (value == 'Attend events'):
                                    s_data['Attend Events'] = True
                                elif (value == 'Donate'):
                                    s_data['Donate'] = True
                        else:
                            value = extra_vals['value_varchar']

                            if (value == 'Help register voters'):
                                s_data['VR'] = True
                            elif (value == 'Canvass'):
                                s_data['Canvass'] = True
                            elif (value == 'Make calls'):
                                s_data['Calls'] = True
                            elif (value == 'Text voters'):
                                s_data['Texts'] = True
                            elif (value == 'Attend events'):
                                s_data['Attend Events'] = True
                            elif (value == 'Donate'):
                                s_data['Donate'] = True

                signup_data.append(s_data)

        signup_df = pd.DataFrame(data=signup_data, columns=columns)
        print(signup_df)

        return signup_df
