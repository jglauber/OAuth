import keyring
from jwcrypto import jwk
import secrets

class GenerateKeyPairs:
    def __init__(self, username):
        self.kid = secrets.token_hex(16)
        self.key = jwk.JWK.generate(kty='RSA', size=4096, alg='RSA-OAEP-256', use='enc', kid=self.kid)
        self.private_key = self.key.export_to_pem(private_key=True,password=None).decode('utf-8')
        self.public_key = self.key.export_to_pem().decode('utf-8')
        self.username = username       

    def store_keys(self):
        kid = keyring.get_password(service_name='jwt_signature',username=f"{self.username}_kid")
        pub_key = keyring.get_password(service_name='jwt_signature',username=f"{self.username}_public")
        private_key = keyring.get_password(service_name='jwt_signature',username=f"{self.username}_private")
        if pub_key is None and private_key is None and kid is None:
            print('Username is unique.')
            print('kid, public key, and private key are being stored.\n')

            pub_key = keyring.set_password(service_name='jwt_signature',
                                           username=f"{self.username}_public",
                                           password=self.public_key)
            private_key = keyring.set_password(service_name='jwt_signature',
                                               username=f"{self.username}_private",
                                               password=self.private_key)
            kid = keyring.set_password(service_name='jwt_signature',
                                       username=f"{self.username}_kid",
                                       password=self.kid)
        else:
            print("A kid, public key, and private key already exist for that user.")
            print("To create a new set, be sure to use a unique username.\n")


def retrieve_pub_key(username):
    pub_key = keyring.get_password(service_name='jwt_signature',username=f"{username}_public")
    return pub_key

def retrieve_private_key(username):
    private_key = keyring.get_password(service_name='jwt_signature',username=f"{username}_private")
    return private_key

def retrieve_kid(username):
    kid = keyring.get_password(service_name='jwt_signature',username=f"{username}_kid")
    return kid