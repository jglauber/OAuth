from oauth_client.client_management.client_generator import Client

def confirm_write_func():
    client = Client()
    client.name = "Jane Doe"
    client.grant_type = "client_credentials"
    client.resource = 'api_v0.0.1'
    db = 'clientdb'
    host = '127.0.0.1'
    table_name = 'stored_tokens'
    client.generate()
    client.store(db, host, table_name)
    result = client.verify(client._client['client_id'],
                           client._client['client_secret'],
                           client._client['grant_type'],
                           client._client['resource'],
                           db, host, table_name)
    return result

def test_confirm_write():
    # run test with pytest -s
    assert confirm_write_func() == True