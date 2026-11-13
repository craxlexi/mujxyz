# Scroll video study

`muj-turn-alpha.webm` is a 1600×512 transparent VP9 video at 60 fps. It uses the thirteen photographic views in `../photo-turn/frames-png/`, including the user's front and side reference cutouts. Each view is aligned on the dome tip before motion interpolation, so the dome stays in the same screen position during the turn. `build.sh` rebuilds the video with FFmpeg.

Open `../photo-turn.html` to scrub the video with the page scroll. Use `python design-concepts/serve_video.py` from the repository root for local preview; the basic Python HTTP server lacks byte-range support needed for video seeking. The page shows `poster.webp` if video is unavailable or reduced motion is enabled.

Motion interpolation creates a continuous video, but it cannot infer a physically exact camera orbit from photographs. Watch the wings and windows during the middle of the turn before deciding whether the result is suitable for the final landing page.
