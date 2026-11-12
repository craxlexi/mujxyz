# MUJ Pulse

A Next.js student dashboard, FastAPI API, and persistent SQLite background worker for MUJ academic-result monitoring. Designed for a Vercel frontend and a small Linux VPS.

**Status:** working demo and monitoring infrastructure. Live SLCM login, semester selection, marks retrieval, and grade retrieval are **not implemented or verified**: this development environment blocks the portal hostname. The live connection form is disabled, and the API refuses to store/send portal credentials. Do not use this as a live result-monitoring service until the integration checklist below is complete.

## Implemented

- Separate app registration/login, salted scrypt password hashes, opaque HttpOnly sessions, origin checks and login throttling.
- Per-student semester, monitoring pause/resume, disconnect, and account deletion.
- Fernet encryption boundary for future portal credentials; no plaintext credential storage or request-body logging.
- One lightweight polling worker with SQLite leases, persisted due dates, jitter, finite retries and backoff. No Redis or browser dependency.
- Validated snapshots, numeric mark comparisons, course/assessment identity, independent semester baselines, change history, grade and official-SGPA change detection. Missing or partial results preserve the last snapshot.
- Transactional event/outbox writes; web push with a service worker, lock-screen messages without marks, delivery retries, and expired-subscription cleanup.
- Administrator-only normal/result-period intervals, expiring result mode and global pause. Admin provisioning requires server-terminal access.
- Isolated synthetic demo accounts and a simulated marks update processed by the actual server worker. Demo accounts expire after 24 hours.

Email, WhatsApp, password reset, verified email ownership, multiple simultaneously monitored semesters, and calculated SGPA are not included. App email is an account identifier; it does not establish ownership of an SLCM account. Production internet signup should wait for email verification/recovery and a verified portal adapter.

## Local development

Requires Python 3.12+ and Node 20.9+.

```bash
python -m venv .venv
.venv/bin/pip install -r backend/requirements.txt
cd frontend
npm ci
```

Run these in three terminals, from the repository root:

```bash
cd backend
../.venv/bin/uvicorn app.main:app --host 0.0.0.0 --port 8000 --no-access-log
```

```bash
cd backend
../.venv/bin/python -m app.worker
```

```bash
cd frontend
npm run dev
```

Open http://localhost:3000 and select **Explore the demo**, then **Simulate a marks update**. The worker picks it up within a few seconds; the dashboard refreshes every ten seconds. That dashboard refresh is only for the visible interface: result checks and notification delivery run on the server even with all browser tabs closed. The first snapshot sends no notification.

The defaults work for the demo without keys. To configure encryption and push, copy `backend/.env.example` to `backend/.env`, generate keys with `cd backend && ../.venv/bin/python -m app.keys`, and place them in that ignored file. Keep the encryption key stable and back it up securely; changing it makes saved portal credentials unreadable. Both backend processes automatically load this ignored `.env` file. Existing process environment settings take precedence. Production systemd also loads it explicitly. Never paste secrets into source, Git, shell arguments, or screenshots.

Tests and frontend build:

```bash
cd backend
../.venv/bin/python -m pytest -q
cd ../frontend
npm run build
```

## Deploy frontend to Vercel

1. Push this repository to your GitHub account and import it into Vercel.
2. Set the project's **Root Directory** to `frontend`; framework preset: Next.js.
3. Set `API_ORIGIN` to your backend's public HTTPS origin, for example `https://api.example.com` (no trailing slash).
4. Deploy. `/api/*` is reverse-proxied by Next.js to the VPS. Session cookies remain on the frontend origin and are HttpOnly; the browser does not need cross-site cookies.
5. Set backend `APP_ORIGIN` to the exact Vercel production URL, with no trailing slash. Preview URLs are deliberately not automatically authorized. Redeploy the frontend after changing `API_ORIGIN`.

No Vercel cron jobs, databases, or paid backend add-ons are required. Confirm your use fits Vercel's current free-plan terms and quotas.

## Deploy backend to a 1 GB Debian/Ubuntu VPS

Do not build Next.js or run Chromium on the VPS. Install Python's venv support, Git, and Caddy using your distribution's supported package instructions. Point a backend hostname at the VPS, and allow inbound TCP 80/443. Do not expose port 8000 publicly.

Example server setup (operator commands, not run automatically):

```bash
sudo useradd --system --home /opt/muj-pulse --shell /usr/sbin/nologin pulse
sudo git clone https://github.com/craxlexi/mujxyz.git /opt/muj-pulse
sudo chown -R pulse:pulse /opt/muj-pulse
sudo -u pulse python3 -m venv /opt/muj-pulse/.venv
sudo -u pulse /opt/muj-pulse/.venv/bin/pip install -r /opt/muj-pulse/backend/requirements.txt
sudo -u pulse mkdir -p /opt/muj-pulse/backend/data
sudo -u pulse cp /opt/muj-pulse/backend/.env.example /opt/muj-pulse/backend/.env
sudo chmod 600 /opt/muj-pulse/backend/.env
```

Generate encryption/push keys locally on that server, then edit its `.env`:

```bash
cd /opt/muj-pulse/backend
sudo -u pulse /opt/muj-pulse/.venv/bin/python -m app.keys
```

Set `DATABASE_PATH=/opt/muj-pulse/backend/data/pulse.db`, `APP_ORIGIN=https://your-project.vercel.app`, `SECURE_COOKIES=true`, your generated keys, your real `VAPID_SUBJECT=mailto:...`, and `ADMIN_EMAIL`. Keep `DEMO_ENABLED=true` only while you want public synthetic demo creation.

Provision the admin from a trusted server terminal. The command loads the ignored backend `.env` file automatically. This uses hidden password input, reserves the configured email against public registration, and never gives admin privileges to the first signup:

```bash
cd /opt/muj-pulse/backend
sudo -u pulse /opt/muj-pulse/.venv/bin/python -m app.admin
```

The command reads the configured `ADMIN_EMAIL` and prompts for a new app password. It does not use your SLCM credentials.

Copy `deploy/muj-pulse-*.service` to `/etc/systemd/system/`. Edit `deploy/Caddyfile` with your backend hostname and install it as `/etc/caddy/Caddyfile`. Validate Caddy's configuration, then:

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now muj-pulse-api muj-pulse-worker
sudo systemctl reload caddy
```

Verify `https://your-backend-host/api/health`. Sign into the app as the provisioned admin to set polling intervals. The two Python services have separate 256 MB memory ceilings; these are limits, **not measured memory requirements**. Keep exactly one worker. SQLite WAL is for a single VPS on a local persistent disk, not network storage.

Web push requires HTTPS (localhost is allowed for development). iPhone users need a supported iOS version and a Home Screen installation. The operator needs outbound HTTPS access to browser push services. VAPID must be configured on both API and worker. Delivery is retried up to five times and is at least once: a crash after sending can cause a duplicate push. Failed deliveries remain visible in the dashboard counts.

## Backups and operation

- Back up SQLite with its online backup API (`sqlite3.Connection.backup`), not by copying an active `.db` while ignoring WAL.
- Keep encrypted backups outside the VPS and back up the encryption key separately. Database backups contain student data.
- Monitor worker restarts, failure counts, disk usage, delivery failures and portal throttling. A failed check must never clear results.
- Use a low-frequency default (60 minutes here). Result-period checking is admin-only and never below five minutes. The worker is serial to limit load; benchmark before increasing concurrency.
- No email fallback is configured. Users without supported push permissions do not receive external alerts until another channel is implemented.

## Finish the live SLCM adapter

`backend/app/portal.py:SLCMClient.enabled` deliberately remains false. Complete these steps before enabling it:

1. Permit `mujslcm.jaipur.manipal.edu` in the development environment's network settings. Inspect the actual public login form and authenticated network flow using a consenting test account entered securely. Do not commit credentials, cookies, student HTML, or screenshots with private data.
2. Confirm allowed automated access, session expiry, CSRF fields, CAPTCHA/OTP behavior and rate limits. Do not bypass authentication challenges.
3. Implement finite-timeout, TLS-verified authentication and semester selection. Prefer HTTP requests; keep redirects constrained to verified university/authentication hosts. Never send credentials to an unverified form action or redirect.
4. Fetch marks at the provided internal-marks page and verify whether data comes from HTML or an authenticated JSON request. The included table parser is based only on the user's screenshot; live markup is unverified.
5. Inspect the grades page, official SGPA, credits, unpublished states, and full/partial response semantics. Do not guess endpoint names or grade-point rules.
6. Add sanitized response fixtures and integration tests for valid/invalid login, expired sessions, empty results, mark corrections, missing rows and grade publication. Validate snapshots before storing credentials or replacing saved results.
7. Enable the adapter only after those checks pass. Then test an external web-push delivery with the website closed and measure memory on the target VPS.

No live portal credential from the conversation is included in this project.
