"""Exercise the deployed worker on an isolated DB; no real SLCM or push traffic."""
import json
import logging
import os
import resource
import tempfile
import threading
import time
from collections import Counter
from pathlib import Path
from unittest.mock import patch

from cryptography.fernet import Fernet


def main():
    with tempfile.TemporaryDirectory(prefix='mujheky-monitor-probe-') as directory:
        os.environ.update(DATABASE_PATH=str(Path(directory) / 'probe.db'),
                          ENCRYPTION_KEY=Fernet.generate_key().decode(),
                          PORTAL_ENABLED='false', VAPID_PRIVATE_KEY='synthetic', VAPID_PUBLIC_KEY='')
        from app import config, worker
        from app.db import db, init
        from app.portal import SLCMClient, demo_snapshot, PortalUnavailable
        from app.security import encrypt
        from app.changes import save_snapshot
        from pywebpush import WebPushException

        assert Path(config.DB_PATH).resolve().parent == Path(directory).resolve(), 'Production DB must never be used'
        init()
        now = time.time()
        with db() as conn:
            for index in range(400):
                uid = f'probe-{index}'
                conn.execute('INSERT INTO users(id,email,password_hash,created) VALUES(?,?,?,?)',
                             (uid, uid + '@probe.invalid', 'disabled', now))
                conn.execute('INSERT INTO accounts(user_id,credentials,semester,next_check) VALUES(?,?,3,?)',
                             (uid, encrypt({'index': index}), now - 1))
                conn.execute('INSERT INTO subscriptions VALUES(?,?,?)',
                             (uid, uid, json.dumps({'endpoint': f'https://push.invalid/{index}'})))
                save_snapshot(uid, 3, demo_snapshot(), connection=conn)

        lock = threading.Lock()
        fetches, pushes, active_ids = Counter(), Counter(), set()
        active, peak_active, duplicates = 0, 0, 0

        def fetch(client, credentials, semester):
            nonlocal active, peak_active, duplicates
            index = credentials['index']
            with lock:
                duplicates += index in active_ids
                active_ids.add(index)
                active += 1
                peak_active = max(peak_active, active)
                fetches[index] += 1
                attempt = fetches[index]
            try:
                time.sleep(1)  # Assumed upstream latency, not measured SLCM performance.
                if index % 20 == 0 and attempt == 1:
                    raise PortalUnavailable('Synthetic transient portal failure')
                return demo_snapshot(1)
            finally:
                with lock:
                    active -= 1
                    active_ids.remove(index)

        def push(**kwargs):
            index = int(kwargs['subscription_info']['endpoint'].rsplit('/', 1)[1])
            payload = json.loads(kwargs['data'])
            assert payload['url'] == '/app?tab=activity'
            assert 'CSC2102' not in payload['body'] and '23' not in payload['body']
            with lock:
                pushes[index] += 1
                attempt = pushes[index]
            if index % 50 == 0 and attempt == 1:
                raise WebPushException('Synthetic transient push failure')
            time.sleep(.02)

        started = time.monotonic()
        stop = threading.Event()
        retried = False
        first_pass_seconds = None
        completion_seconds = None
        progress = []
        logging.getLogger('pulse.worker').setLevel(logging.ERROR)
        with patch.object(SLCMClient, 'enabled', True), patch.object(SLCMClient, 'fetch', fetch), patch.object(worker, 'webpush', push):
            thread = threading.Thread(target=worker.run_worker, args=(stop,))
            thread.start()
            try:
                while time.monotonic() - started < 420:
                    with db() as conn:
                        successes = conn.execute('SELECT count(*) FROM accounts WHERE last_success IS NOT NULL').fetchone()[0]
                        failures = conn.execute('SELECT count(*) FROM accounts WHERE failures=1').fetchone()[0]
                        leased = conn.execute('SELECT count(*) FROM accounts WHERE lease_until>0').fetchone()[0]
                        delivered = conn.execute('SELECT count(*) FROM deliveries WHERE delivered IS NOT NULL').fetchone()[0]
                        if not retried and successes + failures == 400 and leased == 0:
                            assert successes == 380 and failures == 20
                            failed = conn.execute('SELECT a.next_check,s.payload FROM accounts a JOIN snapshots s ON s.user_id=a.user_id WHERE a.failures=1').fetchall()
                            assert all(row['next_check'] > time.time() and json.loads(row['payload']) == demo_snapshot() for row in failed)
                            first_pass_seconds = round(time.monotonic() - started, 2)
                            # Bring failed synthetic jobs forward; production backoff remains unchanged.
                            conn.execute('UPDATE accounts SET next_check=0 WHERE failures=1')
                            retried = True
                        if successes == 400 and completion_seconds is None:
                            completion_seconds = round(time.monotonic() - started, 2)
                    elapsed = round(time.monotonic() - started, 1)
                    sample = {'elapsed_seconds': elapsed, 'successes': successes,
                              'failed_waiting': failures, 'leased': leased, 'delivered': delivered}
                    progress.append(sample)
                    print(json.dumps(sample), flush=True)
                    if successes == 400 and delivered == 400:
                        break
                    time.sleep(10)
                else:
                    raise AssertionError('Monitoring probe exceeded seven-minute budget')
            finally:
                stop.set()
                thread.join(timeout=10)
                assert not thread.is_alive(), 'Probe worker did not stop'

        with db() as conn:
            assert conn.execute('SELECT count(*) FROM snapshots').fetchone()[0] == 400
            assert conn.execute('SELECT count(*) FROM events').fetchone()[0] == 400
            assert conn.execute('SELECT count(*) FROM deliveries WHERE delivered IS NOT NULL').fetchone()[0] == 400
            assert conn.execute('SELECT count(*) FROM accounts WHERE failures!=0 OR lease_until!=0').fetchone()[0] == 0
            assert all(json.loads(row[0]) == demo_snapshot(1) for row in conn.execute('SELECT payload FROM snapshots'))
            assert conn.execute('PRAGMA quick_check').fetchone()[0] == 'ok'
            assert conn.execute('PRAGMA foreign_key_check').fetchall() == []
            retried_pushes = conn.execute('SELECT count(*) FROM deliveries WHERE attempts=1').fetchone()[0]
            assert retried_pushes == 8
        assert peak_active == 2 and duplicates == 0
        assert len(fetches) == len(pushes) == 400
        assert sum(fetches.values()) == 420 and sum(pushes.values()) == 408
        result = {'kind': 'synthetic-worker-test-not-live-SLCM', 'accounts': 400,
                  'assumed_fetch_latency_seconds': 1, 'poll_concurrency': peak_active,
                  'first_pass_seconds': first_pass_seconds, 'all_snapshots_seconds': completion_seconds,
                  'total_seconds': round(time.monotonic() - started, 2), 'portal_attempts': sum(fetches.values()),
                  'portal_failures_injected': 20, 'portal_retries_forced_due': 20,
                  'events': 400, 'push_attempts': sum(pushes.values()), 'push_failures_retried_naturally': retried_pushes,
                  'delivered': 400, 'overlapping_same_account_checks': duplicates,
                  'peak_rss_mib': round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 1),
                  'all_assertions_passed': True, 'progress': progress}
        Path('/tmp/mujheky-monitoring-results.json').write_text(json.dumps(result, indent=2))
        print('RESULT ' + json.dumps({key: value for key, value in result.items() if key != 'progress'}), flush=True)
    assert not Path(directory).exists(), 'Temporary fixture DB cleanup failed'
    print('Temporary 400-account DB removed; production DB untouched.', flush=True)


if __name__ == '__main__':
    main()
