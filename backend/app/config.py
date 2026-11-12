import os
from pathlib import Path
from dotenv import load_dotenv

# Production environment variables take precedence over the ignored local file.
load_dotenv(Path(__file__).resolve().parents[1] / '.env', override=False)

DB_PATH = os.getenv('DATABASE_PATH', './data/pulse.db')
APP_ORIGIN = os.getenv('APP_ORIGIN', 'http://localhost:3000').rstrip('/')
SECURE_COOKIES = os.getenv('SECURE_COOKIES', 'false').lower() == 'true'
DEMO_ENABLED = os.getenv('DEMO_ENABLED', 'true').lower() == 'true'
KEY = os.getenv('ENCRYPTION_KEY', '')
ADMIN_EMAIL = os.getenv('ADMIN_EMAIL', '').lower()
VAPID_PUBLIC = os.getenv('VAPID_PUBLIC_KEY', '')
VAPID_PRIVATE = os.getenv('VAPID_PRIVATE_KEY', '')
VAPID_SUBJECT = os.getenv('VAPID_SUBJECT', 'mailto:admin@example.com')

def ensure_data_dir():
    Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
