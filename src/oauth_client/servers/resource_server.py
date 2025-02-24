from flask import Flask, request, jsonify
from oauth_client.servers.auth_server import decode_token, retrieve_pub_key
import json

def create_resource_server(username: str,
                           issuer: str,
                           api_route: str,
                           resource_path: str
                           ):
    app = Flask(__name__)

    @app.route(f'/{api_route}')
    def get():
        if request.method == 'GET' and request.content_type == 'application/json':
            token = request.authorization.token
            result = decode_token(token,retrieve_pub_key(username),api_route,issuer)
            if result:
                with open(resource_path, 'r') as f:
                    data = json.load(f)
                return jsonify(data)
            else:
                return jsonify(
                    {"error":
                        {
                        "message": "(#400) Invalid request.",
                        "type": "invalid_request",
                        "code": 400
                        }
                    }
                )
        else:
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
