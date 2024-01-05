from base64 import urlsafe_b64encode, urlsafe_b64decode

from cryptography.fernet import Fernet
from django.utils.crypto import get_random_string
from django.utils.text import slugify


def encrypt_token(token: str, key: str) -> str:
    """Encrypt token

    Method responsible for encrypting the token based on a generated private key.

    Args:
        token: (str) - encrypted token
        key (str): - private key
    Returns:
        encrypted token
    """
    f = Fernet(key)
    encrypted_bytes = f.encrypt(token.encode())
    return urlsafe_b64encode(encrypted_bytes).decode()


def decrypt_token(token: str, key: str) -> str:
    """Decrypt token

    Method responsible for decrypting the token based on a generated private key.

    Args:
        token (str): encrypted token
        key (str): private key
    Returns:
        decrypted token

    Raises:
        InvalidToken Error in case the token provided was not encrypted using
        our generated private key.
    """
    f = Fernet(key)
    token_bytes = urlsafe_b64decode(token.encode())
    return f.decrypt(token_bytes).decode()


def generate_private_key() -> str:
    """Generate private key

    Method responsible for generating a private key used at encryption when
    sending tokens in URL's.
    """
    return Fernet.generate_key().decode()


def unique_slugify(string: str) -> str:
    """Slugify

    Method responsible for uniquely slugify a string and return it as slug

    Args:
        string (str): the string to slugify

    Returns:
        str: the slugifyied string
    """
    return slugify(string + get_random_string(5))
