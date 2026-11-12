import sqlite3
from contextlib import contextmanager
from . import config

SCHEMA = '''
CREATE TABLE IF NOT EXISTS users (
 id TEXT PRIMARY KEY, email TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL,
 is_admin INTEGER NOT NULL DEFAULT 0, is_demo INTEGER NOT NULL DEFAULT 0, created REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS sessions (token_hash TEXT PRIMARY KEY, user_id TEXT REFERENCES users(id) ON DELETE CASCADE, expires REAL NOT NULL);
CREATE TABLE IF NOT EXISTS accounts (
 user_id TEXT PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
 credentials TEXT NOT NULL, semester INTEGER NOT NULL, paused INTEGER NOT NULL DEFAULT 0,
 next_check REAL NOT NULL, last_check REAL, last_success REAL, failures INTEGER DEFAULT 0,
 status TEXT NOT NULL DEFAULT 'Waiting for first check', demo_revision INTEGER NOT NULL DEFAULT 0,
 lease_until REAL NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS snapshots (
 user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE, semester INTEGER NOT NULL,
 payload TEXT NOT NULL, updated REAL NOT NULL, PRIMARY KEY(user_id, semester)
);
CREATE TABLE IF NOT EXISTS events (
 id TEXT PRIMARY KEY, user_id TEXT REFERENCES users(id) ON DELETE CASCADE,
 semester INTEGER NOT NULL, changes TEXT NOT NULL, created REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS subscriptions (
 id TEXT PRIMARY KEY, user_id TEXT REFERENCES users(id) ON DELETE CASCADE,
 payload TEXT NOT NULL, UNIQUE(user_id, payload)
);
CREATE TABLE IF NOT EXISTS deliveries (
 id TEXT PRIMARY KEY, event_id TEXT REFERENCES events(id) ON DELETE CASCADE,
 subscription_id TEXT REFERENCES subscriptions(id) ON DELETE CASCADE,
 attempts INTEGER NOT NULL DEFAULT 0, next_attempt REAL NOT NULL,
 delivered REAL, error TEXT, UNIQUE(event_id, subscription_id)
);
CREATE TABLE IF NOT EXISTS settings (
 id INTEGER PRIMARY KEY CHECK(id=1), interval_minutes INTEGER NOT NULL DEFAULT 60,
 boost_minutes INTEGER NOT NULL DEFAULT 10, boost_until REAL NOT NULL DEFAULT 0,
 paused INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS rate_limits (key TEXT PRIMARY KEY, count INTEGER NOT NULL, reset REAL NOT NULL);
INSERT OR IGNORE INTO settings(id) VALUES(1);
'''

@contextmanager
def db():
    config.ensure_data_dir()
    conn = sqlite3.connect(config.DB_PATH, timeout=20)
    conn.row_factory = sqlite3.Row
    conn.execute('PRAGMA foreign_keys=ON')
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init():
    with db() as conn:
        conn.execute('PRAGMA journal_mode=WAL')
        conn.executescript(SCHEMA)
