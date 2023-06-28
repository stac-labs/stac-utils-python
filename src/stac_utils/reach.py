import logging
import os, sys
import json
import pandas as pd
import requests

from datetime import date, timedelta
from io import StringIO

from stac_utils.google import auth_bq, run_query

logger = logging.getLogger(__name__)
logging.basicConfig(level = logging.INFO)

if 'REACH_API_USER' not in os.environ:
    # Try to load from .env
    from dotenv import load_dotenv
    state = 'local'
    load_dotenv()

try:
    reach_keys = os.environ['REACH_API_USER']
except KeyError:
    sys.exit('Reach API keys environment variable not set, cannot run report')

query_base = 'SELECT myv_van_id FROM '

def get_api_headers():
    auth_info = {
        'username': os.environ['REACH_API_USER'],
        'password': os.environ['REACH_API_PASSWORD']
        }
    r = requests.post('https://api.reach.vote/oauth/token', data = auth_info)
    access_token = {
        'Authorization': 'Bearer ' + json.loads(r.text)['access_token']
        }
    return access_token

def update_people_to_tag(row, van_ids, tag_id, api_call_headers, remove=False):
    if remove is True:
        payload = {
            'people': [
                {'person_id': x, 'person_id_type': 'Voterfile VAN ID', 'action': 'removed'} for x in van_ids
            ]
        }
    else:
        payload = {
            'people': [
                {'person_id': x, 'person_id_type': 'Voterfile VAN ID'} for x in van_ids
            ]
        }
    r = requests.put(
        'https://api.reach.vote/api/v1/tags/' + tag_id,
        data = json.dumps(payload),
        headers = api_call_headers
    )
    if r.status_code == 401:
        api_call_headers = get_api_headers(row)
        r = requests.put(
            'https://api.reach.vote/api/v1/tags/' + tag_id,
            data = json.dumps(payload),
            headers = api_call_headers
        )
    return r

def bq_to_reach(table_name, tag_name):
    client = auth_bq()

    query_string = query_base + ' ' + table_name
    voters = run_query(client, query_string).myv_van_id.to_list()

    print(voters)

    api_call_headers = get_api_headers()
    r = requests.get(
        'https://api.reach.vote/api/v1/tags',
        headers = api_call_headers
        )
    all_tags = json.loads(r.text)['tags']

    print(all_tags)

    id = [x['id'] for x in all_tags if x['name'] == tag_name][0]

    print(id)

    if len(voters) > 0:
        batches = [voters[i * 1000:(i + 1) * 1000] for i in range((len(voters) + 1000 - 1) // 1000)]
        for batch in batches:
            put = update_people_to_tag(
                batch,
                id,
                api_call_headers
            )
            logger.info('Updating Voters with Tag: ' + tag_name)