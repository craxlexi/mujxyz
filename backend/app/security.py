import base64
import hashlib
import hmac
import json
import secrets
from cryptography.fernet import Fernet
from . import config

def password_hash(password: str) -> str:
    salt = secrets.token_bytes(16)
    value = hashlib.scrypt(password.encode(), salt=salt, n=16384, r=8, p=1)
    return base64.b64encode(salt + value).decode()

def password_matches(password: str, stored: str) -> bool:
    try:
        raw = base64.b64decode(stored)
        value = hashlib.scrypt(password.encode(), salt=raw[:16], n=16384, r=8, p=1)
        return hmac.compare_digest(value, raw[16:])
    except (ValueError, TypeError):
        return False

def token_hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()

def encrypt(value: dict) -> str:
    if not config.KEY:
        raise ValueError('ENCRYPTION_KEY is required before connecting a portal account')
    return Fernet(config.KEY.encode()).encrypt(json.dumps(value).encode()).decode()

def decrypt(value: str) -> dict:
    return json.loads(Fernet(config.KEY.encode()).decrypt(value.encode()))
