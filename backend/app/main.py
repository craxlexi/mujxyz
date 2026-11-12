import json
import re
import secrets
import sqlite3
import time
import uuid
from contextlib import asynccontextmanager
from urllib.parse import urlparse
from fastapi import FastAPI, Depends, HTTPException, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from . import config
from .db import db, init
from .security import password_hash, password_matches, token_hash, encrypt
from .portal import SLCMClient, demo_snapshot
from .changes import save_snapshot
from .worker import effective_interval

@asynccontextmanager
async def lifespan(app):
    init()
    yield

app = FastAPI(title='MUJ Pulse API', lifespan=lifespan, docs_url=None, redoc_url=None)

@app.exception_handler(RequestValidationError)
async def validation_error(request, exc):
    # Never echo supplied credentials in a validation error response.
    return JSONResponse(status_code=422, content={'detail': 'Invalid input. Check the fields and try again.'})

@app.middleware('http')
async def protect(request: Request, call_next):
    if request.method not in ('GET', 'HEAD', 'OPTIONS'):
        if request.headers.get('origin') != config.APP_ORIGIN:
            return JSONResponse(status_code=403, content={'detail': 'Request origin not allowed'})
        if 'application/json' not in request.headers.get('content-type', ''):
            return JSONResponse(status_code=415, content={'detail': 'JSON required'})
        try:
            body_length = int(request.headers.get('content-length', '0'))
        except ValueError:
            return JSONResponse(status_code=400, content={'detail': 'Invalid content length'})
        if body_length > 20000:
            return JSONResponse(status_code=413, content={'detail': 'Request too large'})
    response = await call_next(request)
    response.headers['Cache-Control'] = 'no-store'
    response.headers['X-Content-Type-Options'] = 'nosniff'
    return response


def limit(request, scope, maximum=30):
    # Client address is supplied by trusted Uvicorn proxy configuration, not arbitrary headers.
    key = f'{scope}:{request.client.host if request.client else "unknown"}'
    now = time.time()
    with db() as conn:
        conn.execute('BEGIN IMMEDIATE')
        row = conn.execute('SELECT * FROM rate_limits WHERE key=?', (key,)).fetchone()
        if row and row['reset'] > now and row['count'] >= maximum:
            raise HTTPException(429, 'Too many attempts; try again in 15 minutes')
        if not row or row['reset'] <= now:
            conn.execute('INSERT OR REPLACE INTO rate_limits VALUES(?,?,?)', (key, 1, now + 900))
        else:
            conn.execute('UPDATE rate_limits SET count=count+1 WHERE key=?', (key,))


def current_user(request: Request):
    with db() as conn:
        user = conn.execute('SELECT u.* FROM users u JOIN sessions s ON u.id=s.user_id WHERE s.token_hash=? AND s.expires>?', (token_hash(request.cookies.get('pulse_session', '')), time.time())).fetchone()
    if not user:
        raise HTTPException(401, 'Please sign in')
    return dict(user)


def admin(user=Depends(current_user)):
    if not user['is_admin']:
        raise HTTPException(403, 'Administrator access required')
    return user


def session(response, user_id):
    token = secrets.token_urlsafe(32)
    with db() as conn:
        conn.execute('INSERT INTO sessions VALUES(?,?,?)', (token_hash(token), user_id, time.time() + 7 * 86400))
    response.set_cookie('pulse_session', token, httponly=True, secure=config.SECURE_COOKIES, samesite='lax', max_age=7 * 86400, path='/')

class AuthInput(BaseModel):
    email: str = Field(min_length=5, max_length=254)
    password: str = Field(min_length=12, max_length=128)

@app.post('/api/auth/register')
def register(body: AuthInput, request: Request, response: Response):
    limit(request, 'register', 10)
    email = body.email.strip().lower()
    if not re.fullmatch(r'[^\s@]+@[^\s@]+\.[^\s@]+', email):
        raise HTTPException(422, 'Enter a valid email address')
    if email == config.ADMIN_EMAIL:
        raise HTTPException(409, 'This address is reserved for operator setup')
    user_id = uuid.uuid4().hex
    try:
        with db() as conn:
            conn.execute('INSERT INTO users(id,email,password_hash,created) VALUES(?,?,?,?)', (user_id, email, password_hash(body.password), time.time()))
    except sqlite3.IntegrityError:
        raise HTTPException(409, 'An account with that email already exists')
    session(response, user_id)
    return {'ok': True}

@app.post('/api/auth/login')
def login(body: AuthInput, request: Request, response: Response):
    limit(request, 'login')
    with db() as conn:
        user = conn.execute('SELECT * FROM users WHERE email=? AND is_demo=0', (body.email.strip().lower(),)).fetchone()
    # Equal-cost password work for unknown identities.
    valid = password_matches(body.password, user['password_hash']) if user else password_matches(body.password, password_hash(secrets.token_urlsafe(20)))
    if not user or not valid:
        raise HTTPException(401, 'Incorrect email or password')
    session(response, user['id'])
    return {'ok': True}

@app.post('/api/auth/demo')
def demo(request: Request, response: Response):
    if not config.DEMO_ENABLED:
        raise HTTPException(404, 'Demo disabled')
    limit(request, 'demo', 20)
    user_id = uuid.uuid4().hex
    with db() as conn:
        conn.execute('INSERT INTO users VALUES(?,?,?,?,?,?)', (user_id, f'demo-{user_id}@example.invalid', '', 0, 1, time.time()))
        conn.execute('INSERT INTO accounts(user_id,credentials,semester,next_check,status) VALUES(?,?,?,?,?)', (user_id, '', 3, time.time() + 3600, 'Monitoring demo data'))
    save_snapshot(user_id, 3, demo_snapshot())
    session(response, user_id)
    return {'ok': True}

@app.post('/api/auth/logout')
def logout(request: Request, response: Response):
    with db() as conn:
        conn.execute('DELETE FROM sessions WHERE token_hash=?', (token_hash(request.cookies.get('pulse_session', '')),))
    response.delete_cookie('pulse_session', path='/')
    return {'ok': True}

@app.get('/api/health')
def health():
    return {'ok': True, 'portal_verified': SLCMClient.enabled}

@app.get('/api/dashboard')
def dashboard(user=Depends(current_user)):
    with db() as conn:
        account = conn.execute('SELECT semester,paused,next_check,last_check,last_success,failures,status FROM accounts WHERE user_id=?', (user['id'],)).fetchone()
        settings = conn.execute('SELECT * FROM settings WHERE id=1').fetchone()
        snapshot = conn.execute('SELECT payload,updated FROM snapshots WHERE user_id=? AND semester=?', (user['id'], account['semester'] if account else 0)).fetchone()
        events = conn.execute('SELECT * FROM events WHERE user_id=? ORDER BY created DESC LIMIT 30', (user['id'],)).fetchall()
        push_count = conn.execute('SELECT count(*) FROM subscriptions WHERE user_id=?', (user['id'],)).fetchone()[0]
        delivery = conn.execute('SELECT sum(d.delivered IS NOT NULL) AS sent,sum(d.delivered IS NULL AND d.attempts<5) AS pending,sum(d.delivered IS NULL AND d.attempts>=5) AS failed FROM deliveries d JOIN events e ON e.id=d.event_id WHERE e.user_id=?', (user['id'],)).fetchone()
    return {'user': {'email': user['email'], 'is_admin': bool(user['is_admin']), 'is_demo': bool(user['is_demo'])}, 'account': dict(account) if account else None,
        'snapshot': json.loads(snapshot['payload']) if snapshot else None, 'snapshot_at': snapshot['updated'] if snapshot else None,
        'events': [{'id': e['id'], 'semester': e['semester'], 'changes': json.loads(e['changes']), 'created': e['created']} for e in events],
        'polling': {'interval_minutes': effective_interval(settings, time.time()), 'paused': bool(settings['paused']), 'boost_until': settings['boost_until']},
        'push': {'configured': bool(config.VAPID_PRIVATE and config.VAPID_PUBLIC), 'public_key': config.VAPID_PUBLIC, 'subscriptions': push_count, 'delivery': dict(delivery)},
        'portal_verified': SLCMClient.enabled}

class ConnectInput(BaseModel):
    email: str = Field(min_length=5, max_length=254)
    password: str = Field(min_length=1, max_length=256)
    semester: int = Field(ge=1, le=12)

@app.post('/api/account/connect')
def connect(body: ConnectInput, user=Depends(current_user)):
    if user['is_demo']:
        raise HTTPException(409, 'Create a real account before connecting SLCM')
    if not SLCMClient.enabled:
        raise HTTPException(503, 'SLCM integration is awaiting verification. Your portal credentials have not been stored or sent.')
    if not config.KEY:
        raise HTTPException(503, 'Credential encryption is not configured')
    credentials = {'email': body.email, 'password': body.password}
    # The verified adapter must enforce finite timeouts and handle expired sessions.
    snapshot = SLCMClient().fetch(credentials, body.semester)
    from .changes import validate_snapshot
    validate_snapshot(snapshot)
    encrypted = encrypt(credentials)
    with db() as conn:
        conn.execute('INSERT INTO accounts(user_id,credentials,semester,next_check) VALUES(?,?,?,?) ON CONFLICT(user_id) DO UPDATE SET credentials=excluded.credentials,semester=excluded.semester,next_check=excluded.next_check,paused=0', (user['id'], encrypted, body.semester, time.time()))
    save_snapshot(user['id'], body.semester, snapshot)
    return {'ok': True}

class AccountInput(BaseModel):
    semester: int = Field(ge=1, le=12)
    paused: bool

@app.patch('/api/account')
def update_account(body: AccountInput, user=Depends(current_user)):
    with db() as conn:
        account = conn.execute('SELECT * FROM accounts WHERE user_id=?', (user['id'],)).fetchone()
        if not account:
            raise HTTPException(404, 'Connect an account first')
        if account['lease_until'] > time.time():
            raise HTTPException(409, 'A check is running; try again shortly')
        conn.execute('UPDATE accounts SET semester=?,paused=?,next_check=? WHERE user_id=?', (body.semester, body.paused, time.time(), user['id']))
    return {'ok': True}

@app.delete('/api/account')
def disconnect(user=Depends(current_user)):
    with db() as conn:
        conn.execute('DELETE FROM accounts WHERE user_id=?', (user['id'],))
        conn.execute('DELETE FROM snapshots WHERE user_id=?', (user['id'],))
        conn.execute('DELETE FROM events WHERE user_id=?', (user['id'],))
        conn.execute('DELETE FROM subscriptions WHERE user_id=?', (user['id'],))
    return {'ok': True}

@app.delete('/api/auth/me')
def delete_user(response: Response, user=Depends(current_user)):
    with db() as conn:
        conn.execute('DELETE FROM users WHERE id=?', (user['id'],))
    response.delete_cookie('pulse_session', path='/')
    return {'ok': True}

@app.post('/api/demo/change')
def demo_change(user=Depends(current_user)):
    if not user['is_demo']:
        raise HTTPException(403, 'Available only in demo mode')
    with db() as conn:
        conn.execute('UPDATE accounts SET demo_revision=demo_revision+1,next_check=? WHERE user_id=?', (time.time(), user['id']))
    return {'ok': True, 'message': 'Demo change queued for the background worker'}

class PushKeys(BaseModel):
    p256dh: str = Field(min_length=50, max_length=200)
    auth: str = Field(min_length=16, max_length=100)

class PushInput(BaseModel):
    endpoint: str = Field(max_length=2048)
    keys: PushKeys

@app.post('/api/push/subscribe')
def subscribe(body: PushInput, user=Depends(current_user)):
    if not config.VAPID_PRIVATE or not config.VAPID_PUBLIC:
        raise HTTPException(503, 'Web push keys have not been configured by the operator')
    try:
        parsed = urlparse(body.endpoint)
        host = parsed.hostname or ''
        port = parsed.port
    except ValueError:
        raise HTTPException(422, 'Invalid push endpoint')
    allowed = host in ('fcm.googleapis.com', 'web.push.apple.com') or any(host.endswith('.' + suffix) for suffix in ('push.services.mozilla.com', 'notify.windows.com', 'notify.live.net'))
    if parsed.scheme != 'https' or parsed.username or parsed.password or port not in (None, 443) or not allowed:
        raise HTTPException(422, 'Unsupported push service endpoint')
    payload = json.dumps(body.model_dump(), sort_keys=True)
    with db() as conn:
        count = conn.execute('SELECT count(*) FROM subscriptions WHERE user_id=?', (user['id'],)).fetchone()[0]
        if count >= 10:
            raise HTTPException(409, 'Device limit reached; disable notifications before re-enabling')
        conn.execute('INSERT OR IGNORE INTO subscriptions VALUES(?,?,?)', (uuid.uuid4().hex, user['id'], payload))
    return {'ok': True}

@app.delete('/api/push/subscribe')
def unsubscribe(user=Depends(current_user)):
    with db() as conn:
        conn.execute('DELETE FROM subscriptions WHERE user_id=?', (user['id'],))
    return {'ok': True}

class SettingsInput(BaseModel):
    interval_minutes: int = Field(ge=5, le=1440)
    boost_minutes: int = Field(ge=5, le=1440)
    boost_hours: int = Field(ge=0, le=168)
    paused: bool

@app.get('/api/admin/settings')
def get_settings(user=Depends(admin)):
    with db() as conn:
        settings = dict(conn.execute('SELECT * FROM settings WHERE id=1').fetchone())
        settings['accounts'] = conn.execute('SELECT count(*) FROM accounts').fetchone()[0]
    return settings

@app.put('/api/admin/settings')
def set_settings(body: SettingsInput, user=Depends(admin)):
    if body.boost_minutes > body.interval_minutes:
        raise HTTPException(422, 'Result-period interval must be no longer than the normal interval')
    now = time.time()
    with db() as conn:
        conn.execute('UPDATE settings SET interval_minutes=?,boost_minutes=?,boost_until=?,paused=? WHERE id=1', (body.interval_minutes, body.boost_minutes, now + body.boost_hours * 3600 if body.boost_hours else 0, body.paused))
        # Apply a shorter schedule without scheduling all accounts at the same instant.
        interval = body.boost_minutes if body.boost_hours else body.interval_minutes
        conn.execute('UPDATE accounts SET next_check=min(next_check, ? + abs(random() % ?))', (now, interval * 60))
    return {'ok': True}
