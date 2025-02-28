import json
import time
import requests
import keyring

class Token:
    """
    A class to handle token requests to the authorization server.

    ...

    Attributes
    ----------
    values : str
        The stored token.
    grant_type : str
        The type of grant that has been given to a client.
    client_id : str
        The client id issued to a client.
    client_secret : str
        The client secret issued to a client.
    resource : str
        The resource a client is authorized to access.

    Methods
    -------
    expires_on()
        Returns a unix integer time.
    expired()
        Returns True if expired and False if not expired.
    string()
        Returns the access token jwt string.
    type()
        Returns the type of token which is identical to the grant type.
    save()
        Saves a token.json file at the root of the directory.
    json()
        Convert the token to a json string.
    get_cached_token()
        Retrieve the token if it exists as a token.json file. If not, \
        run get_new_token() method. 
    get_new_token()
        A method to get a new token via an HTTP post reqeust.
    """

    def __init__(self, grant_type: str, client_id: str, client_secret: str, resource: str, token_request_url: str):
        """
        Parameters
        ----------
        grant_type : str
            The type of grant that has been given to a client.
        client_id : str
            The client id issued to a client.
        client_secret : str
            The client secret issued to a client.
        resource : str
            The resource a client is authorized to access.
        token_request_url : str
            The URL of the authorization server that issues the token.
        """

        self.values = ''
        self.grant_type = grant_type
        self.client_id = client_id
        self.resource = resource
        self.token_request_url = token_request_url
        keyring.set_password('client_secret',self.client_id,client_secret)

    def expires_on(self) -> int:
        """
        Returns the integer unix date of expiration of the token.

        Returns
        -------
        int
            The unix date as an integer.
        """
        s = self.values.get("expires_on", "")
        if s == "":
            return 0
        try:
            return int(s)
        except Exception:
            return 0
    
    def expired(self) -> bool:
        """
        Check if the token is expired.

        Returns
        -------
        bool
            Returns True if token is expired, otherwise returns False.
        """

        return (self.expires_on() - time.time()) < 0
    
    def string(self) -> str:
        """
        Get the string representation of the token.

        Returns
        -------
        string
            The token as a jwt string.
        """

        return self.values.get("access_token", None)
    
    def type(self) -> str:
        """
        Get the grant type.

        Returns
        -------
        string
            The grant type as a string.
        """

        return self.values.get("token_type", None)

    def save(self) -> None:
        """
        Save the token as a json file.
        """

        with open("token.json", "w") as f:
            f.write(json.dumps(self.values, indent=4))
            f.close()
    
    def json(self) -> str:
        """
        Get the json string of the token.

        Returns
        -------
        string
            The json token.
        """

        return json.dumps(self.values, indent=4)


    def get_cached_token(self) -> None:
        """
        Retrieve the saved token and if not present, request a new token.
        """

        try:
            print("grabbing a token from cache if it exists")
            with open('token.json') as f:
                token_object = json.load(f)
            self.values = token_object
            if self.expired():
                print("token is expired.")
                self.get_new_token()
                self.save()
            else:
                self.values = token_object
        except FileNotFoundError:
            print("no cached token. Getting a new one.")
            self.get_new_token()
            self.save()
            return None

    def get_new_token(self) -> str:
        """
        Retrieve a new token.

        Returns
        -------
        json
            A json string representation of the token.
        """

        print("getting new token...")
        url = self.token_request_url
        headers = {'grant_type': {self.grant_type},
                   'client_id': {self.client_id},
                   'client_secret': {keyring.get_password('client_secret',self.client_id)},
                   'resource': {self.resource}}
        response = requests.post(url, headers)
        granted_token = response.json()
        self.values = granted_token
        return granted_token