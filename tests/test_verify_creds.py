from oauth_client.client_management.client_generator import Client

def verify_func():
    client = Client()
    client.name = "Jane Doe"
    client.grant_type = "client_credentials"
    client.resource = 'api_v0.0.1'
    db = 'clientdb'
    host = '127.0.0.1'
    table_name = 'stored_tokens'

    # wrong grant_type
    result1 = client.verify('3972a0f2812625acc785a40538259324',
                            'PRIVATE-gVrYR3hqiVgdWWmDonfAlQmwA0UXXxPW4rvrrt0pmes', 
                            'Authorization Code', 'api_v0.0.1',
                            db,host,table_name,True)
    
    # wrong scope
    result2 = client.verify('37e4785f79cfb0246dd10c2c0bb68cd9',
                            'PRIVATE-gVrYR3hqiVgdWWmDonfAlQmwA0UXXxPW4rvrrt0pmes', 
                            'client_credentials', 'apiv0.0.1',
                            db,host,table_name,True)
    
    # wrong client_secret
    result3 = client.verify('37e4785f79cfb0246dd10c2c0bb68cd9',
                            'PRIVATE-wrong', 
                            'client_credentials', 'api_v0.0.1',
                            db,host,table_name,True)
    
    # wrong client_id
    result4 = client.verify('wrong_user',
                            'PRIVATE-gVrYR3hqiVgdWWmDonfAlQmwA0UXXxPW4rvrrt0pmes', 
                            'client_credentials', 'api_v0.0.1',
                            db,host,table_name,True)

    # pass
    result5 = client.verify('37e4785f79cfb0246dd10c2c0bb68cd9',
                            'PRIVATE-gVrYR3hqiVgdWWmDonfAlQmwA0UXXxPW4rvrrt0pmes',
                            'client_credentials', 'api_v0.0.1',
                            db,host,table_name,True)
    return (result1,result2,result3,result4,result5)


def test_verify():
    # run test with pytest -s
    assert verify_func() == (False,False,False,False,True)