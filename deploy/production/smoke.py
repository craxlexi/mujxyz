"""HTTPS deployment checks using one disposable, empty account. No portal credentials."""
import json
import secrets
import uuid
import httpx

origin = 'https://mujheky.lyaxsh.com'
checks = []
email = f'deploy-check-{uuid.uuid4().hex}@example.invalid'
password = secrets.token_urlsafe(32)
created = False

with httpx.Client(base_url=origin, headers={'Origin': origin}, timeout=30) as client:
    try:
        response = client.get('/')
        assert response.status_code == 200
        checks.append('Public landing HTTPS 200')
        for path in ['/api/health', '/sw.js', '/manifest.webmanifest', '/icon.svg']:
            assert client.get(path).status_code == 200, path
            checks.append(f'{path} 200')
        assert client.get('/api/dashboard').status_code == 401
        checks.append('Anonymous workspace denied')
        response = client.post('/api/auth/register', json={'email': email, 'password': password})
        assert response.status_code == 200, f'Registration status {response.status_code}'
        created = True
        cookie = response.headers.get('set-cookie', '').lower()
        assert 'secure' in cookie and 'httponly' in cookie and 'samesite=lax' in cookie
        checks.append('Registration + Secure/HttpOnly/SameSite cookie')
        response = client.get('/api/dashboard')
        assert response.status_code == 200 and response.json()['user']['email'] == email
        assert response.headers.get('cache-control') == 'no-store'
        assert response.json()['push']['configured'] is True
        checks.append('Authenticated proxy + private cache policy + push readiness')
        assert client.get('/api/admin/settings').status_code == 403
        checks.append('Student admin access denied')
        response = client.post('/api/auth/logout', json={}, headers={'Origin': 'https://invalid.example'})
        assert response.status_code == 403
        assert client.get('/api/dashboard').status_code == 200
        checks.append('CSRF rejected without ending session')
        assert client.post('/api/auth/logout', json={}).status_code == 200
        assert client.get('/api/dashboard').status_code == 401
        assert client.post('/api/auth/login', json={'email': email, 'password': password}).status_code == 200
        assert client.get('/api/dashboard').status_code == 200
        checks.append('Logout and login through custom domain')
    finally:
        if created:
            if client.get('/api/dashboard').status_code != 200:
                client.post('/api/auth/login', json={'email': email, 'password': password})
            assert client.request('DELETE', '/api/auth/me', json={}).status_code == 200
            assert client.get('/api/dashboard').status_code == 401
            checks.append('Disposable account removed')

print(json.dumps({'passed': len(checks), 'checks': checks, 'test_account_removed': created}, indent=2))
