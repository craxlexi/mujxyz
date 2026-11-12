# Continue MUJ Pulse

## Immediate next step

Verify outbound HTTPS access to https://mujslcm.jaipur.manipal.edu/ in a NEW task using the republished `mujxyz` cloud environment. The user added this hostname to its allowed domains. The original task still had enforced revision 1 with no additional hosts and received proxy CONNECT 403 after that change.

Do not rebuild the existing app. Complete its live SLCM connector.

## Existing project

- Next.js frontend: `frontend/`, configured for Vercel with `/api/*` proxied to `API_ORIGIN`.
- FastAPI + SQLite backend: `backend/app/`.
- Persistent serial polling and push-outbox worker: `python -m app.worker`.
- VPS deployment: `deploy/` systemd units and Caddy config. Target is the user's existing 1 GB VPS.
- Setup, limitations, security and deployment details: `README.md`.
- Fifteen backend tests passed; frontend production build passed; automated Chromium tests covered demo changes processed by the server worker, grades, history, monitoring pause/resume and mobile navigation.
- Only synthetic demo data was used. No portal credentials, personal marks, cookies, encryption keys or databases are committed.
- Nothing is deployed to the user's Vercel account or VPS yet.

## Outstanding work

1. Inspect the actual login form, session/CSRF behavior and semester-selection flow. The user authorized connecting their own portal account, but credentials must be entered securely; do not ask them to paste another password into chat.
2. Implement `backend/app/portal.py:SLCMClient`, which deliberately has `enabled=False` and currently raises an explicit unavailable error. Its table parser is based on the user's screenshot, not inspected live markup.
3. Inspect the authenticated internal marks page at `/Student/Academic/InternalMarkForStudent`. Discover the actual grades endpoint; do not invent one. Include official SGPA when published.
4. Reuse sessions as appropriate; finite timeouts and verified TLS are required. Do not bypass CAPTCHA/OTP. Keep login responses, cookies and student data out of source and logs.
5. Add sanitized portal fixtures and verification for login failures, expired sessions, incomplete results, corrections and grade publication. Enable live connection only after verification.
6. Configure VAPID and test delivery while the website is closed. Push infrastructure is implemented, but no external push was verified. Email and WhatsApp are not implemented.
7. Deploy the frontend to Vercel and backend/worker to the VPS once the required account/server access is available. A localhost URL in a cloud task is not a public deployment.

## Product decisions

Admin controls x-minute polling, including a shorter interval during result periods with expiry. Students select their semester. First fetch establishes a baseline; later changes produce events and notifications. Missing/partial responses must preserve prior results. Credentials use reversible encryption only for portal automation; app passwords are salted hashes. Push lock-screen content does not expose marks. Do not calculate SGPA without verified university rules; use published official SGPA first.
