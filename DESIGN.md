# Latest revision — notifications and docking navigation

User direction: remove ambient/full-page gradients. Canvases are flat black; gradients are confined to bounded surfaces (cards, tables, buttons, menus and docked navigation). Original campus colors remain.

Navigation follows the wide-open-to-centered-pill behavior described by [Annnimate Floating Navbar](https://annnimate.com/animations/floating-navbar). Implementation uses a shared passive requestAnimationFrame scroll hook and CSS interpolation, with 110px dock / 45px expand thresholds, a folding wordmark/monogram and reduced-motion handling. Header is fixed; workspace-only reserved space prevents layout movement. Existing destinations, admin gating, profile controls and mobile bottom navigation remain.

Activity now contains a result-change feed and a per-device alert card. Filters derive Marks/Grades from existing change fields. Dates are grouped locally; long updates expand. Permission, installation, secure-context, server-readiness and device-subscription state are distinct. No automatic permission prompt, invented read/unread state or fabricated delivery receipt. Delivery statistics use existing server counts; sent means accepted by push service. Card surfaces carry the warm gradient.

Local push keys are configured in ignored backend/.env using the supplied operator contact. Existing encryption key was preserved. Real browser opt-in and external delivery still require end-to-end verification.

---

# MUJhe ky — unified campus system

## Latest brief: Home and workspace, 14 November 2026

User explicitly superseded the landing protection. One public Home at `/`; authenticated former Home becomes Dashboard at `/app`. Signed-out `/app` redirects to Home's login/signup dialog. Preserve legacy tab slugs, authorization, session cookies, API endpoints, account/admin actions and ten-second polling. Results exposes only Internals and Grades, without a sidebar. Attendance/timetable ingestion remains intact but has no navigation destination.

Stack: existing Next.js 15.5 / React 19 / TypeScript / plain CSS; native view transitions and CSS motion avoid additional application dependencies.

Concept alternatives (originality / fit / feasibility / portability; portability lower is better):
- Campus afterglow: the original Jaipur dome rises through warm stone light while the semester becomes quiet. Signature: layered campus composition with pointer drift and a breathing signal. 4 / 5 / 5 / 2. Selected: ties real campus architecture to relief from refresh fatigue.
- Academic ledger: semester typesetting and a publication index. Signature: assessments arrive along ledger rows. 3 / 5 / 5 / 4. Clear but too portable.
- Chai interval: a semester measured in time away from the portal. Signature: a pause-like chapter transition. 4 / 4 / 3 / 3. Strong voice but would need original photography to carry it honestly.

Concept Card:
- Idea: your campus stays in view while monitoring gets out of the way.
- Metaphor: Jaipur's sandstone afterglow, a quiet campus signal.
- Signature: original-color campus anchored below oversized type; glass signal floats above the architecture. One pointer variable controls campus drift; idle motion breathes slowly.
- Emotion: relief, warmth and belonging.
- Motion verb: settle, float, respond. Primary hover lifts, press compresses; workspace views settle through native transitions.
- Screenshot: original orange dome below “Your semester. Less refresh. More life.”

System: ground #080706 / workspace #000; ink #f1ece5; stone #dfb588; muted #bcb3a9; line #e0bd9029; logo orange #ef965c. Neutral controls with warm glass; no blue table. Shared locally bundled Manrope display/brand and DM Sans UI. Fluid display 57–106px; calm body 14–16px; compact metadata 9–12px. One orange Brand component across Home, workspace, menu context, footer and 404. Radius family: 12px controls, 20–24px glass, rounded avatar shield. Desktop 6vw marketing gutters / 40px workspace gutters; mobile 24px / 20px.

Composition:
- Hero: floating centered nav / left oversized type + CTA / right full-color campus + floating signal / location and scroll cue.
- Story: chapter label / unequal heading + text / three open numbered steps (stacked on mobile).
- Finale: short CTA left / real shared marks table right, with explicitly illustrative records and an interactive sample update; stacked on mobile.
- Dashboard: semester panorama / publication summaries / marks table + activity.
- Results: centered two-option switch / Internals table OR official grades + compact SGPA.
- Profile: identity shield + real name / connection and privacy controls with monitoring primary.

Mobile marks keep course keys at 88px, pin Total on the opposite edge, and reveal full subject names directly beneath the selected row. Horizontal overflow belongs to the table, never the page. New assessment keys are discovered from the marks record; optional empty MTE 2/Re-session stay omitted. Missing is Pending, numeric zero remains valid, totals sum published numeric assessments. ETE support is optional in the existing marks payload; no guessed ETE endpoint or fabricated marks.

Profile extraction accepts explicit StudentName metadata in the already fetched SLCM marks page. Unavailable name yields an honest fallback. Actual live portal markup still needs verification; no credentials or private student data were used for visual QA.

Genericness check: no invented academic stats, testimonials or product screenshots. Original campus assets, Jaipur coordinates and student copy anchor the page. No loader, custom cursor, smooth-scroll dependency or heavy GL. Reduced motion removes decorative movement and page transitions. Weakest accessory removed: redundant sidebar chrome. Earlier phases below are historical and superseded where they conflict.

---

# MUJheky workspace: Phase 1

## Phase 2 authorization and art direction

### Latest user direction

The user subsequently requested the campus building's original colors, a very light gradient based on
its warm stone color, and backdrop blur. “Blue” was explicitly corrected to “blur”: the marks surface
is neutral frosted glass, with no blue tint. Public landing remains untouched.

Home and Results now share one rounded marks table. Course score cards and the Courses/Table toggle
are removed. Total sums available numeric assessments and is labelled as published marks. MTE 2 and
Re-session columns render only when any course has a value, including zero. The user clarified that
Re-session students do not have MTE marks; empty MTE 1 is therefore also omitted for Re-session-only
records. Missing values are Pending, never zero. Official SGPA remains separate and unestimated.

The publication-strip concept below is superseded by this explicit table-only direction. Its signature
is now the academic record itself: precise columns, sticky course identity, calm row feedback and
controlled view transitions. Campus colors, warm ambient light and glass provide the visual identity.

On 14 November 2026 the user approved redesigning the authenticated dashboard too.
The public landing remains protected. Existing API/auth/account/admin/polling contracts remain.
Command palette and Easter eggs are not included in this authorization.

Three directions considered for the expanded brief:

| Direction | Anchor / signature / screenshot | O / fit / feasibility / portability |
| --- | --- | --- |
| Semester ledger (academic material) | One semester contains courses and published assessments. Course focus maps to its actual assessment group in the semester publication strip. A large semester heading sits above a precise unboxed record. | 4 / 5 / 5 / 2 |
| Campus observatory (place) | The provided MUJ cutout anchors a quiet monitoring view. The campus silhouette frames current connection state. A large campus panel is the screenshot. | 3 / 5 / 5 / 3 |
| Check, then leave (process) | Background polling removes repeated manual checking. A handoff from latest check to next scheduled check provides the signature. A status-first dashboard is the screenshot. | 4 / 5 / 4 / 3 |

Choose Semester ledger. Its visual system comes from the product's actual records, not an invented chart.
Borrow only the real campus silhouette as a subdued MUJ anchor.

Idea: One semester, read as a living academic record.
Metaphor: A ledger whose summary and individual records refer to the same source.
Signature: One focusedCourse value connects a course row with its assessment group; pointer and keyboard share it.
Emotion: Clear, quiet, precise, with confident type rather than decorative effects.
Motion verb: Follow the record. A directional arrow steps forward while the matching publication group lifts 3px.
Screenshot: Large Semester 03 heading; unequal publication, course and official-SGPA fields; unboxed course ledger and compact activity column.

The six neutral color roles and existing local typefaces remain. Dashboard display type is 48–80px,
tracking -.065em, line-height 1.02. Record names use DM Sans 16px. Body copy is 15–16px and secondary
UI 11–13px. The intro uses an asymmetric pair; totals use a deliberately unequal data composition;
courses use an index; activity uses a timeline. There are no equal metric cards or per-mark boxes on Home.

Desktop: 12-column logic, 40px outer gutter, 292px monitoring/activity column. Tablet uses 28px gutters;
the course ledger takes full width below 900px. Phone uses 20px gutters, stacked monitoring, a full-width
publication strip, two secondary totals, and course marks beneath each title. The original mobile shell remains.

No new packages. next/image and next/font/local preserve the prior delivery improvements. The workspace
rests still by design: data state, hover, keyboard and press provide life without pretending that a check is running.
Reduced motion keeps content and emphasis, removing movement. Existing campus source image remains unchanged.

Genericness test: remove the boxed marketing hero, three equal statistic cards and nested score boxes.
Expose the real semester number, published/tracked assessment count, official unpublished state and check times.
The publication strip is a data encoding, not a decorative waveform. No invented values or production placeholders.

This section supersedes the earlier Phase 1 stopping boundary below. See Phase 2 review artifacts for results.

## Brief and constraints
Students need a stable place to check academic records and control SLCM monitoring.
Keep the existing Next.js 15 / React 19 / TypeScript stack and Lucide dependency.
Only the authenticated shell, its navigation and workspace design system change.
Public landing composition, API calls, session logic, permissions and polling stay intact.
Dashboard structure and copy are carried forward, not redesigned in this phase.

## Concepts considered
Scores: originality / fit / feasibility / portability (lower portability is better).

| Concept and territory | Anchor | Signature, emotion and screenshot | Scores |
| --- | --- | --- | --- |
| Semester index, academic material | Marks, attendance and timetable are distinct parts of one semester record | Results opens an index rail; calm orientation; selected record beside its context | 4 / 5 / 5 / 2 |
| Campus wayfinding, place | MUJ students move between university services | Destination strip with local signage; familiarity; a route through academic services | 3 / 4 / 5 / 3 |
| Quiet watch, process | Server monitors SLCM while students are away | Monitoring state stays in peripheral chrome; reassurance; quiet status alongside student records | 3 / 5 / 5 / 3 |

Choose Semester index: it directly explains the requested hybrid navigation without inventing content.

## Concept card
Idea: One semester record, with a stable global index and a local academic index.
Metaphor: A student record with its relevant sections close at hand.
Signature: Results introduces a collapsible local rail; phones use a labelled native selector.
Emotion: Calm, precise, immediately oriented.
Motion verb: Settle. Targets step by 1–2px, then settle into graphite surfaces.
Screenshot: White active Results tab above a compact academic rail and unaltered academic content.

## System
Ground #000000; surface #101010; ink #ededed; muted #a1a1a1; line #272727; hover #1c1c1c.
No chromatic accents. Text, controls, statuses and campus image in the workspace are neutral.
Existing locally bundled Manrope headings and DM Sans UI remain; no remote font requests.
The /app layout uses next/font/local for preloads and adjusted fallback metrics.
The existing dashboard campus cutout uses next/image for responsive delivery, with unchanged source and composition.
Heading scale: 29–36px, line-height 1.2, tracking -.035em. UI: 12–15px, line-height 1.5.
Content gutters: 40px desktop, 28px tablet, 20px phone. Header: 72px / 64px phone.
Context: 224px desktop / 200px laptop, 72px collapsed, selector at <=800px.
Global nav switches to labelled bottom destinations at <=700px. Admin remains permission gated.
Radii: 6–8px controls, 10–16px existing content surfaces. Borders, not glow, separate surfaces.
Motion: 160–180ms cubic-bezier(.22,1,.36,1). Still at rest by design: this is a monitoring workspace.
Reduced motion disables transitions and animations. No GSAP, smooth scroll, loaders or WebGL needed.

```
Desktop: [brand / Home Results Activity You (Admin)] [status / profile]
Home:    [breadcrumb                                      refresh]
         [existing dashboard content, full available width]
Results: [local index] [breadcrumb                        refresh]
         [           ] [existing academic content               ]
Phone:   [brand                                         profile]
         [native Results section selector               refresh]
         [existing content                                      ]
         [Home             Results             Activity      You]
```

Genericness test: avoid decorative command inputs, fabricated metrics, dashboard templates and effects.
The academic rail contains only the three existing sections. Profile provides existing settings,
website and sign-out actions. No Phase 2 features, new routes or content placeholders introduced.

## CSS ownership
`globals.css` retains shared primitives. `mujheky.css` and `refinement.css` retain public styling.
Workspace no longer matches `.app-shell`, preventing legacy landing theme rules from affecting it.
`/app/layout.tsx` imports the single `.workspace-root`-scoped `workspace.css` design system.
Workspace overrides have been removed from `refinement.css`; its landing rules remain unchanged.
Workspace never reads or writes the landing theme preference.
Body canvas and browser form color scheme follow the workspace only while it is present.

## Review boundary
Production screenshot fixtures are synthetic, never real academic records. See
`design-concepts/PHASE1_REVIEW.md` for actual verification results and limitations.
Stop at Phase 1. User visual review precedes dashboard redesign.
