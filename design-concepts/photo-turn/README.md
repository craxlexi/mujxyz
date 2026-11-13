# Photographic scroll turn

`../photo-turn.html` scrubs thirteen building cutouts from straight-on to rightward angled. Frames 000 and 012 are the user's earlier front and angled cutouts; 001-011 are generated intermediate angles based on those views. They are image edits, not photographs taken from those camera positions, and some small architectural details can vary between frames.

`frames-png/` holds full-resolution transparent source frames. `frames-webp/` holds the earlier optimized 1600×533 WebP frame sequence. Run `encode_frames.sh` to rebuild those frames. The current page uses the interpolated video in `../video-turn/`.

This is a design prototype, separate from the live SLCM app. Review the actual scroll motion and edge quality before adopting it on the landing page.
