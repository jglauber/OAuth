from flask import Flask, request, jsonify
from oauth_client.client_management.client_generator import Client
from oauth_client.client_management.signature_generator import retrieve_kid, retrieve_private_key, retrieve_pub_key
import jwt
import time


def create_auth_server(db: str,
                       host: str,
                       table_name: str,
                       username: str,
                       issuer: str,
                       subject: str,
                       audience: str):
    app = Flask(__name__)

    @app.route('/token', methods=['POST','GET'])
    def generate_token():
        if request.content_type == 'application/x-www-form-urlencoded':
            body = request.form
            client = Client()
            client_test = client.verify(body['client_id'], body['client_secret'],
                                        body['grant_type'], body['resource'],
                                        db, host, table_name, pgpass=True)
            if client_test:
                RESOURCE = body['resource']
                token = CreateToken(issuer, subject, audience, username, RESOURCE)
                token_dict = token.generate_new_token()
                return jsonify(token_dict)
            else:
                return jsonify({"error":
                    {
                    "message": "(#400) Invalid client.",
                    "type": "invalid_client",
                    "code": 400
                    }
                })
        if request.method == 'GET':
            return jsonify(
                {"error":
                    {
                    "message": "(#400) Invalid request.",
                    "type": "invalid_request",
                    "code": 400
                    }
                }
            )
    return app

"""
invalid_request
    The request is missing a required parameter, includes an
    unsupported parameter value (other than grant type),
    repeats a parameter, includes multiple credentials,
    utilizes more than one mechanism for authenticating the
    client, or is otherwise malformed.

invalid_client
    Client authentication failed (e.g., unknown client, no
    client authentication included, or unsupported
    authentication method).  The authorization server MAY
    return an HTTP 401 (Unauthorized) status code to indicate
    which HTTP authentication schemes are supported.  If the
    client attempted to authenticate via the "Authorization"
    request header field, the authorization server MUST
    respond with an HTTP 401 (Unauthorized) status code and
    include the "WWW-Authenticate" response header field
    matching the authentication scheme used by the client.

invalid_grant
    The provided authorization grant (e.g., authorization
    code, resource owner credentials) or refresh token is
    invalid, expired, revoked, does not match the redirection
    URI used in the authorization request, or was issued to
    another client.

unauthorized_client
    The authenticated client is not authorized to use this
    authorization grant type.

unsupported_grant_type
    The authorization grant type is not supported by the
    authorization server.

"""

class CreateToken:
    def __init__(self, iss, sub, aud, username, resource):
        self.iss = iss
        self.sub = sub
        self.aud = aud
        self.kid = retrieve_kid(username)
        self.private_key = retrieve_private_key(username)
        self.public_key = retrieve_pub_key(username)
        self.resource = resource
        self.payload = {"iss": self.iss,
                "sub": self.sub,
                "aud": self.aud}
        self.additional_headers = {"kid": self.kid}

    def generate_new_token(self):
        iat = time.time()
        exp = iat + 3600
        payload = self.payload
        payload['iat'] = iat
        payload['exp'] = exp       
        encoded_jwt = jwt.encode(payload,self.private_key, headers=self.additional_headers, algorithm='RS256')
        
        token_dict = {"token_type": "Bearer",
                      "expires_on": exp,
                      "not_before": exp,
                      "resource": self.resource,
                      "access_token": encoded_jwt}
        
        return token_dict
    
def decode_token(token,public_key,aud,iss):
    try:
        jwt.decode(token,public_key, algorithms=['RS256'],audience=aud, issuer=iss)
        print("Token is valid.")
    except jwt.ExpiredSignatureError:
        print("Token has expired.")
        return None
    except jwt.InvalidSignatureError:
        print("Invalid signature.")
        return None
    except jwt.DecodeError:
        print("Token could not be decoded.")
        return None
    return True