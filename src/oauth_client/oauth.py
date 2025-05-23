from oauth_client.client_management import Client, remove, create_table, edit_client
from oauth_client.client_management import GenerateKeyPairs
from oauth_client.client_management import Token
from oauth_client.client_management import get_api_content
from oauth_client.servers.auth_server import create_auth_server, CreateToken
from oauth_client.servers.resource_server import create_resource_server
import time

class OAuth:
    """
    OAuth_Client is a tool to help share data between two machines using the \
    OAuth2.0 client credentials process.

    The OAuth Class serves as the primary entrypoint and allows users to:
        * Create and manage clients through a PostgreSQL backend.
        * Generate Resource Owner Signatures
        * Handle the authorization flow
        * Create web tokens for access
        * Serve requests for protected resources

    In general, there should be good separation of these resources as follows:
        1. The PostgreSQL server (established with 2 users: an admin and a viewer)
        2. The Authorization server (with stored signature, access to the PostgreSQL server)
        3. The Resource server (with access to the public key of the stored signature)
    
    Attributes
    ----------
    db_name : str
        The name of the database in PostgreSQL. We suggest "clientdb" but can be any valid string.
    db_host : str
        The host IP address of the PostgreSQL server. For testing, this can be localhost. For production, \
        the server should exist on a dedicated VM likely with a reverse proxy.
    db_table_name : str
        The name of the table to store the client credentials. We suggest "stored_tokens".
    db_create_table : bool
        Create the table to store the client credentials in the PostgreSQL database. Usually this will be \
        False as the table only needs to be generated once and can be generated using the psql cli directly \
        instead of the Python method.
    resource_owner_username : str
        The username for the resource owner that will be signing the token.
    jwt_issuer : str
        The issuer of the jwt token. Likely the same as the resource owner.
    jwt_subject : str
        The user who requested the token (i.e. the authorized client).
    jwt_audience : str
        The recipient for which the token is intended i.e. the resource server.
    
    Methods
    -------
    add_client()
        Adds a new client to the PostgreSQL database.
    remove_client()
        Removes an existing client from the PostgreSQL database.
    update_client()
        Update a client's grant type, resource, or generate a new client secret.
    create_signature()
        Create the resource owner signature for jwt token generation.
    server_create_token()
        Create a new token for the Authorization server to send to the authorized client.
    auth_server()
        Run the authorization server.
    resource_server()
        Run the resource server
    """

    def __init__(self, db_name: str,
                 db_host: str,
                 db_table_name: str,
                 db_create_table: bool = False,
                 resource_owner_username: str = '',
                 jwt_issuer: str = '',
                 jwt_subject: str = '',
                 jwt_audience: str = ''):
        """
        Parameters
        ----------
        db_name : str
            The name of the database in PostgreSQL. We suggest "clientdb" but can be any valid string.
        db_host : str
            The host IP address of the PostgreSQL server. For testing, this can be localhost. For production, \
            the server should exist on a dedicated VM likely with a reverse proxy.
        db_table_name : str
            The name of the table to store the client credentials. We suggest "stored_tokens".
        db_create_table : bool
            Create the table to store the client credentials in the PostgreSQL database. Usually this will be \
            False as the table only needs to be generated once and can be generated using the psql cli directly \
            instead of the Python method.
        resource_owner_username : str
            The username for the resource owner that will be signing the token.
        jwt_issuer : str
            The issuer of the jwt token. Likely the same as the resource owner.
        jwt_subject : str
            The user who requested the token (i.e. the authorized client).
        jwt_audience : str
            The recipient for which the token is intended i.e. the resource server.
        """

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

    def add_client(self, client_name: str, grant_type: str, resource: str) -> None:
        """
        Add a client to the PostgreSQL database.

        Parameters
        ----------
        client_name : str
            The name of the authorized client. *Example* "Jane Doe".
        grant_type : str
            The type of grant. This should be "client credentials" in most cases.
        resource : str
            The resource that the client is allowed to access.
        """

        client = Client(client_name, grant_type, resource)
        client.name = client_name
        client.grant_type = grant_type
        client.resource = resource
        db = self.db_name
        host = self.host
        table_name = self.table_name
        client.generate()
        client.store(db, host, table_name)
    
    def remove_client(self, client_id: str):
        """
        Remove a client from the PostgreSQL database.

        Parameters
        ----------
        client_name : str
            The name of the authorized client. *Example* "Jane Doe".

        Returns
        -------
        literal[True] | None
            True if successfully removed. Otherwise, returns None.
        """

        return remove(self.db_name,self.host,self.table_name,client_id)

    def update_client(self, client_id: str, grant_type: str = None,
                      resource: str = None, new_client_secret: bool = False) -> bool:
        """
        Update a client grant type, resource, or generate a new client secret.

        Parameters
        ----------
        client_name : str
            The name of the authorized client. *Example* "Jane Doe".
        grant_type : str
            The type of grant. This should be "client credentials" in most cases.
        resource : str
            The resource that the client is allowed to access.
        new_client_secret : bool
            If True, generate a new client secret.
        
        Returns
        -------
        bool
            True if sucessful, otherwise False.
        """

        return edit_client(self.db_name,self.host,client_id,grant_type,resource, new_client_secret)
    
    def create_signature(self) -> bool:
        """
        Create a new signature for a resource owner. This can only be done once per username.

        Returns
        -------
        bool
            True if successful, otherwise, False if user already exists.
        """
        if self.username != '':
            kp = GenerateKeyPairs(self.username)
            kp.store_keys()
            return True
        else:
            return False
        
    def server_create_token(self,resource: str):
        """
        Create a new jwt token for use by the Authorization server.

        Parameters
        ----------
        resource : str
            The resource to create the token for.
        
        Returns
        -------
        dict
            A dictionary with the complete token.
        """
        token = CreateToken(self.iss,self.sub,self.aud,self.username,resource)
        token_dict = token.generate_new_token()
        return token_dict
    
    def auth_server(self):
        """
        Create the Authorization Flask server with /token route.

        Returns
        -------
        app
            the Flask app.
        """

        app = create_auth_server(self.db_name,
                                 self.host,
                                 self.table_name,
                                 self.username,
                                 self.iss,
                                 self.sub,
                                 self.aud)
        return app
    
    def resource_server(self, api_route: str, resource_path: str):
        """
        Create the Resource Flask server with designated route and resource path.

        Parameters
        ----------
        api_route: str
            The route to request the protected resource.  
            *Example* "api_v0.0.1"
        resource_path : str
            The relative path of the protected json file.

        Returns
        -------
        app
            the Flask app
        """

        app = create_resource_server(self.username, self.iss, self.aud, api_route, resource_path)
        return app

def client_request_token(grant_type: str,client_id: str, client_secret: str,
                         resource: str, token_request_url: str) -> str:
    """
    A function that allows a client to request the access token.
    
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

    Returns
    -------
    string
        The token as a jwt string.
    """

    token = Token(grant_type,client_id,client_secret,resource,token_request_url)
    token.get_cached_token()
    t = token.expires_on()

    print("expires: {}".format(time.ctime(t)))
    print("now:     {}".format(time.ctime(time.time())))
    print("expired = {}".format(token.expired()))

    return token.string()

def client_request_resource(resource_url: str, token: str) -> str:
    """
    A function that allows a client with valid token to access a protected resource.

    Parameters
    ----------
    resource_url : str
        The fully qualified URL including http/https and api_route for the resource.  
        *Example* http://127.0.0.1/api_v0.0.1
    token : str
        The access token.

    Returns
    -------
    string
        The json string of the protected resource.
    """

    return get_api_content(resource_url,token)
