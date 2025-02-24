# Welcome to OAuth_Client

A tool written in Python 3.13 to implement OAuth2.0 using the client credentials grant type. This is intended for machine to machine APIs and integrates with a PostgreSQL server for storing client ids and hashed/salted client secrets. Please see requirements.txt for the full list of dependencies.

## Installation

Prior to installing this Python package, PostgreSQL must be installed on the target machine. This README is focused on Linux; however, with appropriate adjustments the program should run on Windows and Mac OS as well.

Install PostgreSQL:  
`sudo apt install postgresql`

Install all
[psycopg build prerequistes](https://www.psycopg.org/docs/install.html#build-prerequisites) including libpq and python3-dev.

PostgreSQL will create a postgres superuser by default. We recommend creating two new users: one user that creates a table for storing client ids and hashed/salted client secrets and one user that has "SELECT" only rights to the table. This can be created as follows:

1. `sudo -s` to switch to root.
2. `su - postgres` to switch to postgres super user.
3. `psql` to launch the postgreSQL cli.
4. `CREATE USER your_admin_username WITH PASSWORD 'your_password';`

    For the admin that will create and maintain the database of client ids and secrets we suggest a user name that is meaningful to the specific user and a strong password.

5. `CREATE USER your_viewer_username WITH PASSWORD 'your_password';`

    For the viewer that will have "SELECT" only privileges, we suggest "auth_client" for the user name and a strong password.

    Create the database that will store the credentials. We suggest using 'clientdb'.

6. `CREATE DATABASE clientdb;`
7. `exit` to exit the psql cli.

8. `su - your-admin-username` to switch to admin user and use the strong password that was created for this admin.

    Create the table to store client credentials. We suggest "stored_tokens".

9. `CREATE TABLE stored_tokens;`
10. `GRANT SELECT ON stored_tokens TO auth_client;` to allow the viewer user access to view the contents of the table.

After all the prerequisites have been met, you can install the package locally, using the following command from the root of the repo.

`pip install -e .`

## Program Structure

The oauth_client package contains three (3) critical components for enabling OAuth.

1. Client creation using client ids and client secrets.
2. An Authorization server that checks that a client is allowed access to the protected resource and grants a json web token (jwt).
3. A Protected Resource Server that verifies that the token is valid and responds with a protected json file.

    For more details, click this link for the full [OAuth2.0 Specification](https://datatracker.ietf.org/doc/html/rfc6749)

## Example Usage

The following examples demonstrate some of the basic capabilities. Please note that it is up to the user to ensure that they maintain good separation of resources. For instance, the Authorization server and Resource server should not reside on the same server. Similarly, the client data should not reside with the resource server.

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

### Create a Signature

This creates assymetric public and private key pairs for the admin. The signature is required for the admin to sign jwt tokens and is stored in a keyring. The private key and public key are both required to sign the jwt; however, only the public key is used to validate that the jwt is authentic. The signature should be stored on the authorization server.

```python
oauth.create_signature()
```

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

### Make Changes to an Existing Client

Client grant type and resource can be modified in the database. In addition, a new client secret can be generated if new_client_secret is set to True.

```python
oauth.update_client(client_id='0083c1b7e3a6ceeac4a4f47bd3a1b501',
                    grant_type='another grant type',
                    resource='another resource',
                    new_client_secret=True)
```

### Request a Token

```python
token = client_request_token('client_credentials',
                             '0083c1b7e3a6ceeac4a4f47bd3a1b501',
                             'PRIVATE-qGSUlXIyQVFB_xfPnHOy6WWGMER5uCgZyaKWgJw-ggQ',
                             'api_v0.0.1',
                             'http://127.0.0.1:5001/token')
```

### Request Protected Resource

This uses the token variable from above:

```python
client_request_resource('http://127.0.0.1:5001/api_v0.0.1',token)
# returns the protected resource as a json string.
# {"about": "This is a protected resource"}
```

## License

MIT

## Authors

John Glauber

## Contact

For any questions, comments, or suggestions please reach out via email to:

<johnbglauber@gmail.com>  
<https://github.com/jglauber/OAuth>
