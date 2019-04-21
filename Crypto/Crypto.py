from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC
from cryptography.hazmat.backends import default_backend
import base64


def generate_key(password):
    password = bytes(password, "utf-8")
    # Salt is equal to password as we want the encryption to be reversible only
    # using the password itself
    kdf = PBKDF2HMAC(algorithm=hashes.SHA256(),
                     length=32,
                     salt=bytes(password),
                     iterations=100000,
                     backend=default_backend())

    return base64.urlsafe_b64encode(kdf.derive(password))


def encrypt(message, key):

    f = Fernet(key)

    return f.encrypt(bytes(message, "utf-8"))


def decrypt(token, key):
    f = Fernet(key)
    return f.decrypt(token)


# my_key = generate_key("1234")

# token = encrypt("password", my_key)

# print(token)

# msg = decrypt(token, my_key)

# print(msg)
