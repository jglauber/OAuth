import requests
from oauth_client.servers.auth_server import decode_token
from oauth_client.client_management.signature_generator import retrieve_pub_key

def generate_token():
    url = 'http://127.0.0.1:5000/token'
    headers = {'Content-Type': 'application/x-www-form-urlencoded'}
    data = {'grant_type': 'client_credentials',
        'client_id': '37e4785f79cfb0246dd10c2c0bb68cd9',
        'client_secret': 'PRIVATE-gVrYR3hqiVgdWWmDonfAlQmwA0UXXxPW4rvrrt0pmes',
        'resource': 'api_v0.0.1'}
    r = requests.post(url, data=data, headers=headers)
    response = dict(r.json())

    return decode_token(response['access_token'],retrieve_pub_key('jglauber'),'api_v0.0.1','jglauber')

def test_generate_token():
    assert generate_token() == True
    