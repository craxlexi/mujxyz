# Latest: notifications, docking nav and surface-only gradients

- Home and workspace headers are wide/transparent at the top and dock into a centered glass pill after scrolling. `useFloatingNav.ts`, `FloatingBrand.tsx` and `floating-nav.css` own this behavior. Reduced motion changes state instantly. Existing navigation/history, role gating and mobile destinations are preserved.
- Page/hero/section canvases are flat black. Removed ambient radial gradients and orbit decoration; gradients remain inside cards, tables, controls and menus. Original building images/colors remain.
- `NotificationCenter.tsx`, `notifications.css`, `usePushDevice.ts` own Activity presentation and device controls. Existing API polling/history/account behavior remains. Browser support/permission, iOS install, secure context, server keys and saved current-device state are checked independently.
- Added authenticated `POST /api/push/device` status and `DELETE /api/push/device` removal. Existing all-device DELETE remains. Subscribe is idempotent by endpoint at the device limit, deduplicates historical entries and serializes its cap check.
- Push clicks open `/app?tab=activity`; service worker confines targets to the app origin/path and coalesces academic alerts. Lock-screen messages remain private, without marks.
- Local VAPID pair created only because absent; supplied operator contact set in ignored backend/.env. Encryption key unchanged. API and polling/push worker restarted. No external test push sent; real-device delivery remains unverified. Enable in Activity on the desired browser/device.
- Backend suite: 52 passed. Typecheck/build pass. Notification visual review and complete actual test results: `design-concepts/NOTIFICATIONS_REVIEW.md`. Temporary browser QA dependencies live in `.qa-tools`, not application manifests.

Earlier records below are historical where superseded.

---

# Latest redesign — unified Home and workspace

14 November 2026. Latest user request supersedes earlier landing protection and prior navigation decisions below.

- `/` is the only public Home, with one login/signup dialog. Signed-out `/app` redirects there; authenticated `/app` is Dashboard. Existing `tab=home/results/activity/you/admin` links still work. Results uses Internals/Grades with `result=grades` and browser history. Sidebar, Attendance and Timetable navigation were intentionally removed; their backend ingestion remains.
- Shared `Brand.tsx`, root-owned local Manrope/DM Sans fonts, sandstone gradients and floating centered glass navigation. Original-color hero campus remains. Home uses CSS entrance/idle/pointer movement, a real shared marks-table preview with explicitly illustrative values, and an interactive sample update. No demo values enter authenticated records or APIs.
- Profile uses an identity shield and optional `snapshot.student.name`, extracted only from explicit StudentName metadata in the already fetched marks page. Missing identity remains honest fallback. No new endpoint, credentials or portal request added for names. Live name markup is unverified. Monitoring control is primary; existing reconnect, privacy, sign-out, subscription and deletion handlers remain.
- `MarksTable.tsx` discovers assessment keys from data, keeps stable known ordering, preserves conditional MTE 2/Re-session and numeric zero, and sums published numeric marks. Backend accepts optional ETE in the existing marks payload. A separately introduced portal endpoint/table still needs its validated adapter; no endpoint was invented. Mobile pins an 88px course key and Total on opposite edges; names expand beside their row and scroll clear of floating navigation.
- New styling ownership: `brand.css` identity; `home.css` public composition; `workspace.css` shell/primitives; `shell-details.css` result/profile enhancements; `marks-table.css` owns all reusable table behavior; `overview.css` dashboard. No new rules added to `refinement.css`. Public preview reuses the real table component and scoped workspace table styles.
- API/auth/session/authorization, SLCM requests, account/admin actions and ten-second polling retained. Only optional snapshot name/ETE data were added on the backend; no DB schema migration. No application dependency added. Playwright and axe were installed temporarily without manifest/lock changes.

Local hosting: production Next server http://localhost:3000, API 127.0.0.1:8000, background worker. Run `python scripts/run_local.py` for the existing all-in-one development launcher after stopping those services. Local secrets remain ignored; do not copy or print backend/.env.

Final checks: typecheck/build passed; 49 backend tests; 118 browser assertions; zero unexpected browser errors and zero axe violations across ten contexts. Mobile emulation LCP 1436ms, CLS 0.006397. Touch scale0.97, visible keyboard focus, local API proxy and custom 404 verified. Fresh independent review 7.84/10; requested9 target remains unmet. Live SLCM-name markup and physical devices remain unverified.

Verification and visual-review details: `design-concepts/REFRESH_REVIEW.md`; evidence under `design-concepts/refresh/`. Earlier phase records below are historical.

---

# MUJhe ky handoff

## Phase 2 authenticated redesign — latest, 14 November 2026

The user approved Phase 2 for the authenticated dashboard. This supersedes the earlier Phase 1 stopping boundary. The public landing remains protected; no command palette or Easter eggs were authorized.

Home now uses a large semester heading, the original full-color campus cutout, a restrained warm-stone ambient gradient, a blurred monitoring surface, real publication/course/official-SGPA summaries, a marks table and recent activity. The user explicitly corrected “blue” to “blur”: the table is neutral frosted glass, not blue.

`DashboardOverview.tsx` owns overview presentation; `MarksTable.tsx` is shared by Home and Results. Marks are table-only with rounded corners and a published Total. The Courses/Table toggle and score cards were intentionally removed by user request. MTE 2 and Re-session appear only if any course contains a value, including zero. For Re-session-only records, empty MTE 1 is omitted too. The user confirmed these students have no MTE marks. Totals sum available numeric marks; missing marks remain Pending. Official SGPA remains a separate university-published value and is never estimated.

The existing data types moved unchanged into `types.ts`. API/session/auth/admin/account/push functions, background polling and tab/history contracts remain. Native view transitions add short controlled content movement, with a reduced-motion/unsupported-browser fallback. Push-unavailable copy and empty academic views were clarified. Local fonts now use lossless WOFF2 compression; all original mapped characters and original font sources/licenses remain.

Workspace CSS owns the shell and retained secondary-page primitives. `overview.css` owns dashboard composition; `marks-table.css` owns the shared table. No application dependencies were added. Original campus source assets and landing source/styles remain unchanged. See `DESIGN.md` for latest user direction and `design-concepts/PHASE2_REVIEW.md` for verification and limitations.

## Phase 1 application shell — 14 November 2026

Work continues in `fmuj`, copied from the confirmed `muj-pulse-local5/muj-pulse` source without local secrets, databases, virtual environments or generated builds.

`/` keeps the approved public landing. `/app` owns a monochrome dark system through its nested layout and `workspace.css`. Workspace rules were removed from `refinement.css`, which retains landing refinements only. Workspace never reads or writes the landing theme preference.

Global sticky header: Home, Results, Activity, You, and permission-gated Admin. Results alone adds a collapsible contextual rail; at <=800px it becomes a native selector sharing the toolbar with Refresh. At <=700px global destinations use labelled mobile bottom navigation. Profile provides account settings, public website, monitoring status and the existing sign-out action. Escape, focus restoration, outside dismissal and tab navigation are supported.

Existing dashboard composition, academic views and account/admin actions remain. API calls, data types, session handling, SLCM integration, ten-second dashboard refresh and tab/history behavior remain in place. Fonts preload through next/font/local with adjusted fallback metrics. The campus image uses next/image responsive delivery without changing its source or composition. Session loading reserves header and toolbar space.

See `DESIGN.md` and `design-concepts/PHASE1_REVIEW.md` for system, verification, screenshots and limits. Browser fixtures are synthetic and intercepted only in the QA harness; production UI contains no sample records.

Stop at Phase 1 pending the user's visual review. Do not start dashboard redesign, command palette or Easter eggs.

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
