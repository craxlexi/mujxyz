# MUJhe ky handoff

## Current frontend state — 13 November 2026

This section supersedes the older design notes below. `/` always renders the public landing, including for signed-in users. `/app` owns the existing authenticated workspace and its `?tab=` navigation. Landing CTAs use `/app`; signup uses `/app?auth=register`, which opens signup only when signed out. PWA launch and push clicks target `/app`. Preserve this route separation.

The user approved the original black/orange campus landing composition and the Emergent dashboard reference with Raycast-inspired refinement. Landing uses the side cutout in its hero and front cutout in the second section, with a large two-colour MUJhe ky wordmark. Do not replace this with video, 3D, or a dashboard at `/`. Desktop app uses a sidebar; mobile uses bottom navigation. New locally bundled Manrope headings and DM Sans UI fonts prevent remote-font/fallback failures. Landing retains Space Grotesk and Plus Jakarta Sans. Font licenses accompany files.

The app implementation now lives in `frontend/app/app/page.tsx`; `frontend/app/page.tsx` is only the landing. `refinement.css` is loaded last. Existing API/auth/account/admin actions, marks Courses/Table toggle, Attendance and Timetable views remain wired. No academic data was added to production. Review screenshots use synthetic fixtures, not real student records. See `design-concepts/DESIGN_DECISIONS.md` for reference rationale and validation.

Attendance/timetable fetching was added in commit 437ed79, but has not been verified against a real authenticated account in this workspace. The earlier successful live verification covered marks/grades/GPA only. Keep that distinction in user-facing claims.


Branch `work` contains the live SLCM integration. On 13 November 2026, the consenting user's browser login and password were confirmed to match the HTTP test. HTTPX returned SLCM's “Invalid Credentials” message, but `curl_cffi` with Chrome impersonation received the authenticated dashboard redirect. The production `SLCMSession` now uses that transport with a fresh CSRF token/cookie, verified TLS, bounded redirects restricted to the SLCM origin, finite timeouts, and response size limits. HTTPX MockTransport remains for synthetic tests.

`backend/verify_slcm.py` passed the complete authenticated connector flow: six semester III courses, grades endpoint, and official GPA endpoint. The GPA was unpublished. No credentials, cookies, or student results are committed. Backend: 42 tests passed. Frontend: TypeScript typecheck passed. `scripts/run_local.py` installs dependencies, creates a private encryption key in ignored `backend/.env` if absent, enables live connection, and starts API, worker, and frontend on localhost. Demo is disabled by default. The dashboard has not been rebuilt.

The user's Windows PC has an extracted copy of an earlier source ZIP. This cloud workspace cannot directly write to that PC. They specifically do not want another ZIP download. Prefer an in-place update path (for example, Git pull or a small updater) when delivering the changes. Do not paste credentials into commands or repository files.

Remaining work: verify real worker polling and external web-push delivery with browser closed; deploy to the user's VPS/Vercel when account access is available. Production signup needs email ownership verification and recovery. See README.md and LOCAL_SETUP.md.

Frontend update (13 November 2026): The live Next.js page now uses the MUJheky brand and the approved warm-stone/pitch-black/orange direction. Its signed-out landing has only two static transparent MUJ cutouts: front in the first section, side in the second. The existing authenticated dashboard and SLCM flows remain wired; its shell was restyled to match. Video, multi-frame, and 3D prototypes were removed from the branch. TypeScript and Next production build passed; desktop and phone views, theme switch, auth dialog, and a synthetic signed-in overview were checked in Chromium. Use the in-place updater on Windows and restart `scripts/run_local.py` if it was running.

Signed-in UI update (13 November 2026): Following the user's feedback, the old sidebar and box-heavy Overview were replaced with a compact MUJheky layout. Desktop navigation is across the top; phone navigation uses Home, Results, Activity, and You at the bottom. Home prioritizes the monitoring hero, semester counts, course rows and marks, then recent activity. Results, Activity and You were restyled into the same line-led system. Tabs use `?tab=` and browser history. See `design-concepts/app-redesign-*.png` for synthetic-data captures. The SLCM backend and account actions remain connected. UI/UX Pro Max guidance was consulted for navigation, touch targets, contrast and responsive layout.
