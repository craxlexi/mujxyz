import json
import time
import uuid
from copy import deepcopy
import pytest
from fastapi.testclient import TestClient
from cryptography.fernet import Fernet
from app import config
from app.db import db, init
from app.main import app
from app.portal import demo_snapshot, parse_marks_table, PortalUnavailable
from app.changes import save_snapshot, diff
from app.security import encrypt, decrypt, password_hash, password_matches
from app.worker import poll_once, effective_interval, deliver_once

@pytest.fixture(autouse=True)
def database(tmp_path, monkeypatch):
    monkeypatch.setattr(config, 'DB_PATH', str(tmp_path / 'test.db'))
    monkeypatch.setattr(config, 'KEY', Fernet.generate_key().decode())
    monkeypatch.setattr(config, 'VAPID_PRIVATE', '')
    monkeypatch.setattr(config, 'VAPID_PUBLIC', '')
    monkeypatch.setattr(config, 'DEMO_ENABLED', True)
    init()

@pytest.fixture
def client():
    with TestClient(app, headers={'Origin': config.APP_ORIGIN}) as client:
        yield client

def make_user():
    uid = uuid.uuid4().hex
    with db() as conn:
        conn.execute('INSERT INTO users VALUES(?,?,?,?,?,?)', (uid, uid+'@example.com', '', 0, 1, time.time()))
    return uid

def test_baseline_and_deduplication():
    uid = make_user()
    assert save_snapshot(uid, 3, demo_snapshot()) == []
    assert save_snapshot(uid, 3, demo_snapshot(1)) == [{'course':'CSC2102','field':'MTE 2','old':None,'new':'23'}]
    assert save_snapshot(uid, 3, demo_snapshot(1)) == []
    with db() as conn:
        assert conn.execute('SELECT count(*) FROM events').fetchone()[0] == 1

def test_incomplete_results_preserve_snapshot():
    uid = make_user()
    save_snapshot(uid, 3, demo_snapshot())
    broken = demo_snapshot()
    broken['courses'][0]['marks']['MTE 1'] = None
    for value in [broken, dict(demo_snapshot(), complete=False), dict(demo_snapshot(), courses=demo_snapshot()['courses'][:-1])]:
        with pytest.raises(PortalUnavailable):
            save_snapshot(uid, 3, value)
    with db() as conn:
        assert json.loads(conn.execute('SELECT payload FROM snapshots').fetchone()[0]) == demo_snapshot()

def test_semester_baselines():
    uid = make_user()
    save_snapshot(uid, 3, demo_snapshot())
    assert save_snapshot(uid, 4, demo_snapshot(1)) == []

def test_number_format_zero_grades_sgpa():
    before = demo_snapshot()
    after = deepcopy(before)
    after['courses'][0]['marks']['MTE 1'] = '25.00'
    assert diff(before, after) == []
    after['courses'][0]['marks']['CWS'] = '0'
    after['courses'][0]['grade'] = 'A'
    after['official_sgpa'] = '8.9'
    assert {c['field'] for c in diff(before, after)} == {'CWS','Grade','Official SGPA'}

def test_table_and_login_page():
    html = '<table><tr><th>S. No.</th><th>Course Name</th><th>MTE 1</th><th>MTE 2</th></tr><tr><td>1</td><td>DATA STRUCTURES (CSC2101)</td><td>0.00</td><td>-</td></tr></table>'
    assert parse_marks_table(html)[0]['marks'] == {'MTE 1':'0','MTE 2':None}
    for broken in ['<form>Login</form>', html.replace('<td>-</td>','')]:
        with pytest.raises(PortalUnavailable): parse_marks_table(broken)

def test_encryption_and_passwords():
    value = {'password':'a-private-value'}
    encrypted = encrypt(value)
    assert 'a-private-value' not in encrypted and decrypt(encrypted) == value
    hashed = password_hash('long-test-password')
    assert password_matches('long-test-password',hashed)
    assert not password_matches('wrong',hashed)

def test_auth_isolation_csrf_admin(client):
    assert client.get('/api/dashboard').status_code == 401
    assert client.post('/api/auth/demo',json={}).status_code == 200
    first = client.get('/api/dashboard').json()['user']['email']
    assert client.get('/api/admin/settings').status_code == 403
    assert client.post('/api/demo/change',json={},headers={'Origin':'https://evil.example'}).status_code == 403
    client.post('/api/auth/demo',json={})
    assert client.get('/api/dashboard').json()['user']['email'] != first
    assert client.get('/api/dashboard').json()['events'] == []

def test_worker_change_pause(client):
    client.post('/api/auth/demo',json={})
    client.post('/api/demo/change',json={})
    assert poll_once()
    result = client.get('/api/dashboard').json()
    assert result['snapshot']['courses'][0]['marks']['MTE 2'] == '23'
    assert len(result['events']) == 1
    client.patch('/api/account',json={'semester':3,'paused':True})
    client.post('/api/demo/change',json={})
    assert not poll_once()

def test_registration_portal_guard_deletion(client):
    body = {'email':'student@example.com','password':'long-test-password'}
    assert client.post('/api/auth/register',json=body).status_code == 200
    assert client.post('/api/account/connect',json={**body,'semester':3}).status_code == 503
    with db() as conn: assert conn.execute('SELECT count(*) FROM accounts').fetchone()[0] == 0
    client.post('/api/auth/logout',json={})
    assert client.post('/api/auth/login',json=body).status_code == 200
    assert client.request('DELETE','/api/auth/me',json={}).status_code == 200
    assert client.get('/api/dashboard').status_code == 401

def test_validation_redacts_credentials(client):
    r = client.post('/api/auth/login',json={'email':'a','password':'SECRET'})
    assert r.status_code == 422 and 'SECRET' not in r.text

def test_admin_schedule(client):
    client.post('/api/auth/demo',json={})
    with db() as conn: conn.execute('UPDATE users SET is_admin=1')
    body = {'interval_minutes':60,'boost_minutes':10,'boost_hours':1,'paused':False}
    assert client.put('/api/admin/settings',json=body).status_code == 200
    assert client.get('/api/dashboard').json()['polling']['interval_minutes'] == 10
    assert client.put('/api/admin/settings',json={**body,'interval_minutes':5}).status_code == 422

def test_outbox_and_expired_subscription(monkeypatch):
    from pywebpush import WebPushException
    import httpx
    uid = make_user()
    with db() as conn: conn.execute('INSERT INTO subscriptions VALUES(?,?,?)',('sub',uid,'{}'))
    save_snapshot(uid,3,demo_snapshot())
    save_snapshot(uid,3,demo_snapshot(1))
    save_snapshot(uid,3,demo_snapshot(1))
    with db() as conn: assert conn.execute('SELECT count(*) FROM deliveries').fetchone()[0] == 1
    monkeypatch.setattr(config,'VAPID_PRIVATE','configured')
    def gone(**kwargs): raise WebPushException('gone',response=httpx.Response(410))
    monkeypatch.setattr('app.worker.webpush',gone)
    deliver_once()
    with db() as conn: assert conn.execute('SELECT count(*) FROM subscriptions').fetchone()[0] == 0

def test_boost_expiry():
    settings={'boost_minutes':5,'boost_until':100,'interval_minutes':60}
    assert effective_interval(settings,99)==5 and effective_interval(settings,101)==60

def test_disconnected_account_cannot_recreate_snapshot():
    uid = make_user()
    assert save_snapshot(uid,3,demo_snapshot(),require_account=True) == []
    with db() as conn: assert conn.execute('SELECT count(*) FROM snapshots').fetchone()[0] == 0

def test_failed_worker_preserves_baseline_and_backs_off(monkeypatch):
    uid = make_user()
    with db() as conn:
        conn.execute('INSERT INTO accounts(user_id,credentials,semester,next_check) VALUES(?,?,?,?)',(uid,'',3,time.time()-1))
    save_snapshot(uid,3,demo_snapshot())
    def fail(*args): raise PortalUnavailable('invalid portal response')
    monkeypatch.setattr('app.worker.demo_snapshot',fail)
    assert poll_once()
    with db() as conn:
        account = conn.execute('SELECT * FROM accounts').fetchone()
        assert account['failures']==1 and account['next_check']>time.time()
        assert json.loads(conn.execute('SELECT payload FROM snapshots').fetchone()[0]) == demo_snapshot()


def test_live_reconnect_rolls_back_credentials_on_partial_results(client, monkeypatch):
    from app.portal import SLCMClient
    body = {'email': 'synthetic@example.com', 'password': 'synthetic-app-password'}
    client.post('/api/auth/register', json=body)
    monkeypatch.setattr(SLCMClient, 'enabled', True)
    monkeypatch.setattr(SLCMClient, 'fetch', lambda *args: demo_snapshot())
    connect = {'email': 'synthetic@muj.manipal.edu', 'password': 'synthetic-portal-password', 'semester': 3}
    assert client.post('/api/account/connect', json=connect).status_code == 200
    with db() as conn:
        original = dict(conn.execute('SELECT * FROM accounts').fetchone())
    monkeypatch.setattr(SLCMClient, 'fetch', lambda *args: dict(demo_snapshot(), courses=demo_snapshot()['courses'][:-1]))
    assert client.post('/api/account/connect', json={**connect, 'password': 'synthetic-new-password'}).status_code == 502
    with db() as conn:
        assert dict(conn.execute('SELECT * FROM accounts').fetchone()) == original
        assert json.loads(conn.execute('SELECT payload FROM snapshots').fetchone()[0]) == demo_snapshot()


def test_live_authentication_error_is_actionable_and_stores_nothing(client, monkeypatch):
    from app.portal import SLCMClient, PortalAuthenticationError
    client.post('/api/auth/register', json={'email': 'synthetic@example.com', 'password': 'synthetic-app-password'})
    monkeypatch.setattr(SLCMClient, 'enabled', True)

    def rejected(*args): raise PortalAuthenticationError('SLCM sign-in failed; check your credentials on the portal')

    monkeypatch.setattr(SLCMClient, 'fetch', rejected)
    result = client.post('/api/account/connect', json={'email': 'synthetic@muj.manipal.edu', 'password': 'synthetic-private-password', 'semester': 3})
    assert result.status_code == 422 and 'synthetic-private-password' not in result.text
    with db() as conn: assert conn.execute('SELECT count(*) FROM accounts').fetchone()[0] == 0


def test_worker_respects_live_verification_gate(monkeypatch):
    from app.portal import SLCMClient
    uid = make_user()
    with db() as conn:
        conn.execute('UPDATE users SET is_demo=0 WHERE id=?', (uid,))
        conn.execute('INSERT INTO accounts(user_id,credentials,semester,next_check) VALUES(?,?,?,?)', (uid, encrypt({'email': 'synthetic', 'password': 'synthetic'}), 3, time.time() - 1))
    save_snapshot(uid, 3, demo_snapshot())
    monkeypatch.setattr(SLCMClient, 'enabled', False)

    def must_not_fetch(*args): raise AssertionError('Unverified live polling must not send credentials')

    monkeypatch.setattr(SLCMClient, 'fetch', must_not_fetch)
    assert poll_once()
    with db() as conn:
        assert conn.execute('SELECT failures FROM accounts').fetchone()[0] == 1
        assert json.loads(conn.execute('SELECT payload FROM snapshots').fetchone()[0]) == demo_snapshot()
