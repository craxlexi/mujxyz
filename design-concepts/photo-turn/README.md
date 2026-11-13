# Photographic scroll turn

`../photo-turn.html` scrubs thirteen building cutouts from straight-on to rightward angled. Frames 000 and 012 are the user's earlier front and angled cutouts; 001-011 are generated intermediate angles based on those views. They are image edits, not photographs taken from those camera positions, and some small architectural details can vary between frames.

`frames-png/` holds full-resolution transparent source frames. `frames-webp/` holds optimized 1600×533 WebP frames (about 2 MB total) used by the browser. Run `encode_frames.sh` to rebuild the optimized sequence. The page advances through every angle with brief transitions and always settles on a single frame. The turn takes about half a viewport of scrolling. Reduced-motion settings show a static first view.

This is a design prototype, separate from the live SLCM app. Review the actual scroll motion and edge quality before adopting it on the landing page.
