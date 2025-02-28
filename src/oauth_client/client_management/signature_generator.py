import keyring
from jwcrypto import jwk
import secrets
import gc

class GenerateKeyPairs:
    """
    A class to create the jwt signature for use by the resource owner to sign tokens.

    ...

    Attributes
    ----------
    kid
        The randomly generated key id.
    key
        The randomly generated key using the jwcrypto package.
    private_key
        The private key.
    public_key
        The public key.
    username
        The username of the resource owner.
    
    Methods
    -------
    store_keys()
        Stores the kid, public key, and private key in a keyring and \
        deletes the binding and variables from memory.
    """

    def __init__(self, username: str):
        """
        Parameters
        ----------
        username : str
            The username of the resource owner generating the signature.
        """

        self.kid = secrets.token_hex(16)
        self.key = jwk.JWK.generate(kty='RSA', size=4096, alg='RSA-OAEP-256', use='enc', kid=self.kid)
        self.private_key = self.key.export_to_pem(private_key=True,password=None).decode('utf-8')
        self.public_key = self.key.export_to_pem().decode('utf-8')
        self.username = username       

    def store_keys(self):
        """
        A method to store the signature in a keyring.
        """

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
            del self.kid
            del self.private_key
            del self.public_key
            del self.username
            gc.collect()
        else:
            print("A kid, public key, and private key already exist for that user.")
            print("To create a new set, be sure to use a unique username.\n")

def retrieve_pub_key(username: str):
    """
    Retrieve the public key of the signature from the keyring storage.

    Parameters
    ----------
    username : str
        The username of the resource owner that signed the jwt access token.

    Returns
    -------
    string
        The public key.
    """

    pub_key = keyring.get_password(service_name='jwt_signature',username=f"{username}_public")
    return pub_key

def retrieve_private_key(username: str):
    """
    Retrieve the private key of the signature from the keyring storage.

    Parameters
    ----------
    username : str
        The username of the resource owner that signed the jwt access token.

    Returns
    -------
    string
        The private key.
    """

    private_key = keyring.get_password(service_name='jwt_signature',username=f"{username}_private")
    return private_key

def retrieve_kid(username: str):
    """
    Retrieve the key id (kid) of the signature from the keyring storage.

    Parameters
    ----------
    username : str
        The username of the resource owner that signed the jwt access token.

    Returns
    -------
    string
        The key id.
    """

    kid = keyring.get_password(service_name='jwt_signature',username=f"{username}_kid")
    return kid