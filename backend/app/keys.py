from cryptography.fernet import Fernet
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization
import base64

def b64(value):
    return base64.urlsafe_b64encode(value).rstrip(b'=').decode()

if __name__ == '__main__':
    key = ec.generate_private_key(ec.SECP256R1())
    print('Store these locally in backend/.env; do not commit or share them.')
    print('ENCRYPTION_KEY=' + Fernet.generate_key().decode())
    print('VAPID_PRIVATE_KEY=' + b64(key.private_numbers().private_value.to_bytes(32, 'big')))
    print('VAPID_PUBLIC_KEY=' + b64(key.public_key().public_bytes(serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint)))
