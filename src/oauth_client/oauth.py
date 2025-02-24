from oauth_client.client_management.client_generator import Client, remove, create_table, edit_client
from oauth_client.client_management.signature_generator import GenerateKeyPairs
from oauth_client.client_management.get_token import Token
from oauth_client.client_management.get_resource import get_api_content
from oauth_client.servers.auth_server import create_auth_server, CreateToken
from oauth_client.servers.resource_server import create_resource_server
import time

class OAuth:
    def __init__(self, db_name: str,
                 db_host: str,
                 db_table_name: str,
                 db_create_table: bool = False,
                 resource_owner_username: str = '',
                 jwt_issuer: str = '',
                 jwt_subject: str = '',
                 jwt_audience: str = ''):
        self.db_name = db_name
        self.host = db_host
        self.table_name = db_table_name
        self.create_table = db_create_table
        self.username = resource_owner_username
        self.iss = jwt_issuer
        self.sub = jwt_subject
        self.aud = jwt_audience
        if self.create_table:
            print("Creating new table if it doesn't already exist")
            create_table(self.db_name, self.host, self.table_name)

    def add_client(self, client_name, grant_type, resource):
        client = Client(client_name, grant_type, resource)
        client.name = client_name
        client.grant_type = grant_type
        client.resource = resource
        db = self.db_name
        host = self.host
        table_name = self.table_name
        client.generate()
        client.store(db, host, table_name)
    
    def remove_client(self, client_id):
        return remove(self.db_name,self.host,self.table_name,client_id)

    def update_client(self, client_id: str, grant_type: str = None,
                      resource: str = None, new_client_secret: bool = False):
        return edit_client(self.db_name,self.host,client_id,grant_type,resource, new_client_secret)
    
    def create_signature(self):
        if self.username != '':
            kp = GenerateKeyPairs(self.username)
            kp.store_keys()
            return True
        else:
            return False
        
    def server_create_token(self,resource):
        token = CreateToken(self.iss,self.sub,self.aud,self.username,resource)
        token_dict = token.generate_new_token()
        return token_dict
    
    def auth_server(self):
        app = create_auth_server(self.db_name,
                                 self.host,
                                 self.table_name,
                                 self.username,
                                 self.iss,
                                 self.sub,
                                 self.aud)
        return app
    
    def resource_server(self, api_route, resource_path):
        app = create_resource_server(self.username, self.iss, api_route, resource_path)
        return app

def client_request_token(grant_type,client_id,client_secret,resource,token_request_url):
    token = Token(grant_type,client_id,client_secret,resource,token_request_url)
    token.get_cached_token()
    t = token.expires_on()

    print("expires: {}".format(time.ctime(t)))
    print("now:     {}".format(time.ctime(time.time())))
    print("expired = {}".format(token.expired()))

    return token.string()

def client_request_resource(resource_url,token):
    return get_api_content(resource_url,token)
