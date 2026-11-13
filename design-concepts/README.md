# MUJheky visual direction — first review

Open `concept.html` in a browser and use the bottom-right controls to switch between landing/app and light/dark. The six PNGs are review captures at desktop and phone sizes.

This is a static design study. Course names, marks and sync time on the app screen are labeled samples. It is not connected to SLCM and does not replace the working frontend.

## Direction

- Brand: MUJheky (working name), with oversized orange type layered over a transparent MUJ building cutout.
- Light: warm stone `#cec6ba`, near-black `#11100e`, dome orange `#d83e0b`.
- Dark: pitch black `#000000`, warm white `#f5f0e8`, brighter orange `#f4511e`.
- Type: Space Grotesk for display; Plus Jakarta Sans for readable UI text.
- Landing: editorial hero inspired by the supplied goat reference, focused on one clear action.
- App: phone-first Home, Results, Activity, You; quick view of semester, last SLCM check, course marks, and official SGPA state.

The generated building cutout is a draft derived from the supplied MUJ photo. Refine edges and verify building details before production use. Keep the oversized art on marketing surfaces; functional result pages should prioritize data.

## Scroll turn study

Open `scroll-prototype.html` and scroll. The front and side cutouts are staged in a sticky hero while the copy changes. This is a two-image perspective/crossfade test, not a true 3D rotation. The middle of the transition shows duplicate architecture because the supplied views have different geometry and camera positions.

For a convincing continuous turn, model the recognizable building in Blender from reference views, then render a short orbit as optimized WebP/AVIF frames. A scroll-linked canvas can scrub those frames while the text and background remain ordinary HTML/CSS. This is likely more predictable on Android than shipping an interactive WebGL scene. Include a static view for reduced-motion users and slower devices.

## 3D turn study

Open `model-turn.html` and scroll. This version uses a true 3D model rather than blending two photographs. The editable Blender file and portable GLB are in `model/`; the page scrubs 32 optimized renders from front to an angled view. The building is a stylized first pass based on the supplied photos, so review its architectural fidelity before using it as final art.
