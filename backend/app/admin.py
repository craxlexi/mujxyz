"""Create the sole configured administrator from the VPS terminal."""
import getpass
import time
import uuid
from . import config
from .db import db, init
from .security import password_hash

if __name__ == '__main__':
    if not config.ADMIN_EMAIL:
        raise SystemExit('Set ADMIN_EMAIL in the environment first')
    password = getpass.getpass('New administrator password (12+ characters): ')
    if len(password) < 12 or password != getpass.getpass('Confirm password: '):
        raise SystemExit('Passwords must match and have at least 12 characters')
    init()
    with db() as conn:
        conn.execute('INSERT INTO users(id,email,password_hash,is_admin,created) VALUES(?,?,?,?,?) ON CONFLICT(email) DO UPDATE SET password_hash=excluded.password_hash,is_admin=1', (uuid.uuid4().hex, config.ADMIN_EMAIL, password_hash(password), 1, time.time()))
        conn.execute('DELETE FROM sessions WHERE user_id IN (SELECT id FROM users WHERE email=?)', (config.ADMIN_EMAIL,))
    print('Administrator provisioned. Sign in through the app.')
