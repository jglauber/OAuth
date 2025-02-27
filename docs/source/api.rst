API
===

The following documentation describes the classes and functions available for use. \
The documentation is divided into three groups: 
1. The OAuth class which is the public API
2. The client management API
3. The server API

1. OAuth
--------
The OAuth class is the primary user interface for the oauth_client package.

**The OAuth Class**
   .. autoclass:: oauth_client.OAuth

There are also two client facing functions that allow the client to request a token and \
with that token to request a protected resource.

**Request a Token**
   .. autofunction:: oauth_client.client_request_token

**Request a Protected Resource**
   .. autofunction:: oauth_client.client_request_resource

2. Client management
--------------------
Client management classes and functions provide lower level funcionality \
upon which the OAuth class depends. The documentation that follows allows \
developers and users more control over the public API.

**The Client Management Module**
   .. automodule:: oauth_client.client_management
      :members:

3. Servers
----------
The Server functions allow the OAuth class to create an Authorization \
server and a Resource Server. These should always live on two distinct \
machines.

**Authorization Server**
   .. automodule:: oauth_client.servers.auth_server
      :members:

**Resource Server**
   .. automodule:: oauth_client.servers.resource_server
      :members:


   