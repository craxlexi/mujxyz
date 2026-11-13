"""Run exactly one worker process. SQLite leases recover abandoned account jobs."""
import json
import logging
import random
import time
from pywebpush import webpush, WebPushException
from . import config
from .db import db, init
from .security import decrypt
from .portal import SLCMClient, PortalUnavailable, demo_snapshot
from .changes import save_snapshot

log = logging.getLogger('pulse.worker')


def effective_interval(settings, now):
    return settings['boost_minutes'] if settings['boost_until'] > now else settings['interval_minutes']


def poll_once():
    now = time.time()
    with db() as conn:
        conn.execute('BEGIN IMMEDIATE')
        settings = conn.execute('SELECT * FROM settings WHERE id=1').fetchone()
        if settings['paused']:
            return False
        account = conn.execute('SELECT a.*,u.is_demo FROM accounts a JOIN users u ON u.id=a.user_id WHERE a.paused=0 AND a.next_check<=? AND a.lease_until<? ORDER BY a.next_check LIMIT 1', (now, now)).fetchone()
        if not account:
            return False
        conn.execute('UPDATE accounts SET lease_until=? WHERE user_id=?', (now + 180, account['user_id']))
    try:
        if not account['is_demo'] and not SLCMClient.enabled:
            raise PortalUnavailable('Live polling is awaiting verification')
        snapshot = demo_snapshot(account['demo_revision']) if account['is_demo'] else SLCMClient().fetch(decrypt(account['credentials']), account['semester'])
        save_snapshot(account['user_id'], account['semester'], snapshot, require_account=True)
        with db() as conn:
            conn.execute('UPDATE accounts SET last_check=?,last_success=?,failures=0,status=?,next_check=?,lease_until=0 WHERE user_id=?', (now, now, 'Monitoring', now + effective_interval(settings, now) * 60 + random.uniform(0, 15), account['user_id']))
    except Exception:
        # Do not log portal bodies, credentials, or exception strings.
        failures = account['failures'] + 1
        with db() as conn:
            conn.execute('UPDATE accounts SET last_check=?,failures=?,status=?,next_check=?,lease_until=0 WHERE user_id=?', (now, failures, 'Check failed; saved results preserved', now + min(21600, max(effective_interval(settings, now) * 60, 60 * 2 ** min(failures, 8))) + random.uniform(0, 30), account['user_id']))
        log.warning('Portal check failed; retry scheduled')
    return True


def deliver_once():
    if not config.VAPID_PRIVATE:
        return
    now = time.time()
    with db() as conn:
        rows = conn.execute('SELECT d.id,s.id AS sub_id,s.payload FROM deliveries d JOIN subscriptions s ON s.id=d.subscription_id WHERE d.delivered IS NULL AND d.attempts<5 AND d.next_attempt<=? LIMIT 10', (now,)).fetchall()
    for row in rows:
        try:
            webpush(subscription_info=json.loads(row['payload']), data=json.dumps({'title': 'Your academic results changed', 'body': 'Open MUJhe ky to see updated marks, grades or SGPA.', 'url': '/app'}), vapid_private_key=config.VAPID_PRIVATE, vapid_claims={'sub': config.VAPID_SUBJECT}, timeout=15)
            with db() as conn:
                conn.execute('UPDATE deliveries SET delivered=?,error=NULL WHERE id=?', (time.time(), row['id']))
        except WebPushException as exc:
            status = exc.response.status_code if exc.response is not None else None
            with db() as conn:
                if status in (404, 410):
                    conn.execute('DELETE FROM subscriptions WHERE id=?', (row['sub_id'],))
                else:
                    conn.execute("UPDATE deliveries SET attempts=attempts+1,next_attempt=? + 60 * (1 << attempts),error='Push delivery failed' WHERE id=?", (time.time(), row['id']))
        except Exception:
            with db() as conn:
                conn.execute("UPDATE deliveries SET attempts=attempts+1,next_attempt=? + 60 * (1 << attempts),error='Push configuration or delivery error' WHERE id=?", (time.time(), row['id']))


def cleanup():
    with db() as conn:
        now = time.time()
        conn.execute('DELETE FROM sessions WHERE expires<?', (now,))
        conn.execute('DELETE FROM users WHERE is_demo=1 AND created<?', (now - 86400,))
        conn.execute('DELETE FROM rate_limits WHERE reset<?', (now,))

if __name__ == '__main__':
    logging.basicConfig(level=logging.INFO)
    init()
    last_cleanup = 0
    while True:
        try:
            worked = poll_once()
            deliver_once()
            if time.time() - last_cleanup > 3600:
                cleanup()
                last_cleanup = time.time()
            if not worked:
                time.sleep(2)
        except Exception:
            log.error('Worker cycle failed; retrying')
            time.sleep(5)
