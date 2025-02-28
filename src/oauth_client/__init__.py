#    ____  ___         __  __        _________            __ 
#   / __ \/   | __  __/ /_/ /_      / ____/ (_)__  ____  / /_
#  / / / / /| |/ / / / __/ __ \    / /   / / / _ \/ __ \/ __/
# / /_/ / ___ / /_/ / /_/ / / /   / /___/ / /  __/ / / / /_  
# \____/_/  |_\__,_/\__/_/ /_/____\____/_/_/\___/_/ /_/\__/  
#                           /_____/                          

"""
============
OAuth_Client
============

A package written in Python 3.13 to manage the client credentials OAuth2.0 specification.

Basic Usage
-----------
The following examples demonstrate some of the basic capabilities. Please note that it is up to the user \
to ensure that they maintain good separation of resources. For instance, the Authorization server and \
Resource server should not reside on the same server. Similarly, the client data should not reside with \
the resource server.

...

### Create the OAuth Class

```python
from oauth_client import OAuth, client_request_token, client_request_resource

oauth = OAuth(db_name='clientdb',
              db_host='127.0.0.1',
              db_table_name='stored_tokens',
              db_create_table=False,
              resource_owner_username='admin',
              jwt_issuer='admin',
              jwt_audience='client',
              jwt_subject='client')
```

...

### Create a Signature

This creates assymetric public and private key pairs for the admin. The signature is required for the admin to sign jwt tokens and is stored in a keyring. The private key and public key are both required to sign the jwt; however, only the public key is used to validate that the jwt is authentic. The signature should be stored on the authorization server.

```python
oauth.create_signature()
```

...

### Create a New Authorized Client

*Note* The client secret will be printed locally to the terminal. It will not be retrievable again after. All of the client ids and secrets are for demonstration purposes only. Please do not ever share or store client secrets in plain text.

```python
oauth.add_client(client_name='Jane Doe',
                 grant_type='client_credentials',
                 resource='api_v0.0.1')
# this will print the following to the console:
# {
# "grant_type": "client_credentials",
# "client_id": "0083c1b7e3a6ceeac4a4f47bd3a1b501",
# "client_secret": "PRIVATE-qGSUlXIyQVFB_xfPnHOy6WWGMER5uCgZyaKWgJw-ggQ"
# "resource": "api_v0.0.1"
# }
```

...

### Make Changes to an Existing Client

Client grant type and resource can be modified in the database. In addition, a new client secret can be generated if new_client_secret is set to True.

```python
oauth.update_client(client_id='0083c1b7e3a6ceeac4a4f47bd3a1b501',
                    grant_type='another grant type',
                    resource='another resource',
                    new_client_secret=True)
```

...

### Run the Authorization Server

The authorization server is a Flask server configured with a "/token" route.

```python
app = oauth.auth_server()
app.run(debug=True)
```

The run method of app is appropriate for testing locally. In production, please use a WSGI production server such as [Gunicorn](https://gunicorn.org/)

...

### Request a Token

The Authorization server must be running to request a token.

```python
token = client_request_token('client_credentials',
                             '0083c1b7e3a6ceeac4a4f47bd3a1b501',
                             'PRIVATE-qGSUlXIyQVFB_xfPnHOy6WWGMER5uCgZyaKWgJw-ggQ',
                             'api_v0.0.1',
                             'http://127.0.0.1:5001/token')
```

...

### Run the Resource Server

The resource server is a Flask server. The user can specify two parameters:

1. The default api route ('api_v0.0.1' in the example below).
2. The path and filename of the protected resource. *Note* the protected resource must be a json file.
3. As with the Authorization server, the run method is appropriate for local testing but a production WSGI server should be used in production.

```python
app = oauth.resource_server('api_v0.0.1','protected_resource.json')
app.run(debug=True, port=5001)
```

...

### Request Protected Resource

The Resource Server must be running to request the protected resource.
*Note* The route /api_v0.0.1 is the same route specified when starting the Resource Server.

```python
# This uses the token variable from the initial token request.
client_request_resource('http://127.0.0.1:5001/api_v0.0.1',token)
# returns the protected resource as a json string.
# {"about": "This is a protected resource"}
```

...

Author & License Info
---------------------
:copyright: (c) 2025 by John Glauber.
:email: <johnbglauber@gmail.com>
:license: MIT, see LICENSE for more details.
"""

from oauth_client.oauth import OAuth, client_request_resource, client_request_token

__all__ = ['OAuth','client_request_resource','client_request_token']
