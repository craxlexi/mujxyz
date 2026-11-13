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

## Photographic scroll turn

Open `photo-turn.html` using `python design-concepts/serve_video.py` from the repository root, then scroll. The current study uses a transparent video moving from the supplied front view to the supplied side view, with the dome pinned in place. The video is scrubbed by page scroll. It offers light and dark themes and a static view for reduced-motion users.

The video interpolates eleven generated intermediate angles between the two cutouts. Architectural details can shift during the turn, so review the motion on a phone before using it as final landing art. The source frames remain in `photo-turn/`; the video and build script are in `video-turn/`.

`scroll-prototype.html` preserves the earlier two-image study for comparison.

## 3D turn study

`model-turn.html` and `model/` preserve the stylized 3D experiment. It was set aside because its look did not match the photographic direction.
