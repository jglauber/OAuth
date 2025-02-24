import json
import time
import requests
import keyring

class Token:
    def __init__(self, grant_type, client_id, client_secret, resource, token_request_url):
        self.values = ''
        self.grant_type = grant_type
        self.client_id = client_id
        self.resource = resource
        self.token_request_url = token_request_url
        keyring.set_password('client_secret',self.client_id,client_secret)

    def expires_on(self):
        s = self.values.get("expires_on", "")
        if s == "":
            return 0
        try:
            return int(s)
        except Exception:
            return 0
    
    def expired(self):
        return (self.expires_on() - time.time()) < 0
    
    def string(self):
        return self.values.get("access_token", None)
    
    def type(self):
        return self.values.get("token_type", None)

    def save(self):
        with open("token.json", "w") as f:
            f.write(json.dumps(self.values, indent=4))
            f.close()
    
    def json(self):
        return json.dumps(self.values, indent=4)


    def get_cached_token(self):
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

    def get_new_token(self):
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