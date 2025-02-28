import requests

def get_api_content(resource_url: str, token: str):
    """
    Retrieve the content of the protected resource.

    Parameters
    ----------
    resource_url : str
        The full url including http/https and /token path to\
        access and request the protected resource.
    token : str
        The jwt token string used to access the api content.

    Returns
    -------
    string
        The json encoded response.
    """
    url = resource_url
    headers = {'Content-Type': 'application/json',
               'Authorization': 'Bearer ' + token}
    r = requests.get(url, headers=headers)
    response = r.json()
    return response
