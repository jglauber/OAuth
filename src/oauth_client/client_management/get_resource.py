import requests

def get_api_content(resource_url,token):
    url = resource_url
    headers = {'Content-Type': 'application/json',
               'Authorization': 'Bearer ' + token}
    r = requests.get(url, headers=headers)
    response = r.json()
    print(response)
    return response
