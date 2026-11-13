# MUJ Pulse handoff

Branch `work` contains the live SLCM integration. On 13 November 2026, the consenting user's browser login and password were confirmed to match the HTTP test. HTTPX returned SLCM's “Invalid Credentials” message, but `curl_cffi` with Chrome impersonation received the authenticated dashboard redirect. The production `SLCMSession` now uses that transport with a fresh CSRF token/cookie, verified TLS, bounded redirects restricted to the SLCM origin, finite timeouts, and response size limits. HTTPX MockTransport remains for synthetic tests.

`backend/verify_slcm.py` passed the complete authenticated connector flow: six semester III courses, grades endpoint, and official GPA endpoint. The GPA was unpublished. No credentials, cookies, or student results are committed. Backend: 42 tests passed. Frontend: TypeScript typecheck passed. `scripts/run_local.py` installs dependencies, creates a private encryption key in ignored `backend/.env` if absent, enables live connection, and starts API, worker, and frontend on localhost. Demo is disabled by default. The dashboard has not been rebuilt.

The user's Windows PC has an extracted copy of an earlier source ZIP. This cloud workspace cannot directly write to that PC. They specifically do not want another ZIP download. Prefer an in-place update path (for example, Git pull or a small updater) when delivering the changes. Do not paste credentials into commands or repository files.

Remaining work: verify real worker polling and external web-push delivery with browser closed; deploy to the user's VPS/Vercel when account access is available. Production signup needs email ownership verification and recovery. See README.md and LOCAL_SETUP.md.
