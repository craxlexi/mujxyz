"""Create production-only keys once. Never overwrite existing secrets or databases."""
import base64
import os
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec

target = Path('/opt/mujheky/backend/.env')
if target.exists():
    print('Existing production environment preserved.')
else:
    key = ec.generate_private_key(ec.SECP256R1())
    encode = lambda value: base64.urlsafe_b64encode(value).rstrip(b'=').decode()
    settings = {
        'DATABASE_PATH': '/opt/mujheky/backend/data/pulse.db',
        'ENCRYPTION_KEY': Fernet.generate_key().decode(),
        'APP_ORIGIN': 'https://mujheky.lyaxsh.com',
        'SECURE_COOKIES': 'true',
        'ADMIN_EMAIL': '',
        'VAPID_PRIVATE_KEY': encode(key.private_numbers().private_value.to_bytes(32, 'big')),
        'VAPID_PUBLIC_KEY': encode(key.public_key().public_bytes(serialization.Encoding.X962, serialization.PublicFormat.UncompressedPoint)),
        'VAPID_SUBJECT': 'mailto:contact@lyaxsh.com',
        'DEMO_ENABLED': 'false',
        'PORTAL_ENABLED': 'true',
    }
    with os.fdopen(os.open(target, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600), 'w') as output:
        output.write(''.join(f'{name}={value}\n' for name, value in settings.items()))
    print('Production keys created; no secrets displayed.')
