# MUJhe ky — reference and implementation notes

## Sources and decisions

- User-approved landing screenshot: retain black canvas, orange accents, left-aligned Space Grotesk heading, campus cutout, oversized wordmark and warm-stone light mode. Exactly two campus images, no generated intermediates.
- [Emergent reference](https://riff-app--3n1b1hyj.preview.emergentagent.com/) and the supplied screenshot: use sidebar navigation, a campus overview, compact semester metrics, courses and activity. Do not reproduce unsupported menu destinations, attendance totals, search, or fabricated academic data from the reference.
- [Raycast](https://www.raycast.com/): consulted the official product page for its emphasis on quick access and focused tools. Applied a compact control hierarchy, consistent interaction feedback, and restrained motion. This is an interpretation, not a claim to reproduce Raycast’s exact font or animation implementation.
- [Lucide stroke guidance](https://lucide.dev/guide/react/basics/stroke-width): use actual SVG icons with consistent stroke weight, accessible labels for icon-only buttons, and readable text navigation.
- The Awwwards listing did not load during research. No award claim or inaccessible-site observation informed this implementation.

## Typography and interaction

Dashboard headings use locally bundled Manrope. UI text, course names and numbers use DM Sans with explicit sans-serif fallbacks. Both font licenses are shipped. Course titles are 15–16px; marks 14–15px; supporting labels are secondary. Table row headings do not inherit marketing letter spacing. Pending assessments are explicitly labelled; official unpublished SGPA remains a dash.

Button hover/focus feedback is short and restrained. Initial hero motion is brief, never scroll-dependent. Reduced-motion preference disables transitions and animation. Desktop has one refresh control, and mobile retains navigation with labels and touch targets. The table can scroll within its own container on narrow screens.

## Verification

Real Next.js routes were rendered in Chromium at 1440×1000 and 390×844 with synthetic API fixtures. Checks covered landing independence from authentication, Open app navigation, locally loaded fonts, SVG navigation icons, no page-level horizontal overflow, six course rows in Table view, unavailable attendance messaging, signup dismissal, signed-in signup-link handling, and browser Back. Dark landing/dashboard/table screenshots are saved beside this document. Light theme was also inspected.

These screenshots validate UI with fixtures, not live SLCM attendance/timetable extraction. Earlier marks integration remains unchanged.

Next.js production build and TypeScript validation passed with both `/` and `/app` generated successfully.
