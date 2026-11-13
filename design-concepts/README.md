# MUJheky design reference

`concept.html` and the six screenshots preserve the approved visual reference. The working Next.js frontend now uses this direction: warm stone light mode, pitch-black dark mode, orange accents, Space Grotesk display type, and Plus Jakarta Sans interface type.

The live landing page uses exactly two static building cutouts: the front view in the first section and the side view in the second. Both are served from `frontend/public/`. There is no scroll animation, frame sequence, video, or 3D model in the app.

The concept's sample app screen is illustrative. The working dashboard and its SLCM account, results, and notification flows remain in `frontend/app/page.tsx`.

## Signed-in app redesign

The `app-redesign-*.png` files are screenshots of the live Next.js frontend with synthetic course and activity data. They show the compact signed-in Home on desktop and phone in both themes, plus phone views of the course list, Results, Activity, and You. No student account data is present in these captures.

Desktop uses a short top navigation. Phone uses a fixed four-item bottom navigation with safe-area padding. Home places the monitoring status, course counts, latest marks, and recent activity in that order. Course rows and hairline dividers replace the former stat-card grid and sidebar. Tabs update the URL and support browser back.
