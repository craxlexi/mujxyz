# MUJ main-building model

`muj-building.blend` is an editable Blender 4.3 project. `muj-building.glb` is a portable 3D export. `build_muj.py` builds the model procedurally from the user's front, angled and aerial photos, supplemented by publicly visible campus galleries. It models the symmetrical wings, front colonnade, circular drum and orange ribbed dome. This is a **stylized architectural approximation**, not a survey-accurate reconstruction; no third-party photo is used as a texture.

The `frames-webp/` directory contains 32 transparent front-to-angle views. They total about 2 MB and drive `../model-turn.html`. The landing prototype keeps text in HTML and uses a scroll-linked canvas only for the building. A static first view is used when reduced motion is requested.

To regenerate from the script:

```sh
blender -b -t 4 --python design-concepts/model/build_muj.py -- --frames
bash design-concepts/model/encode_frames.sh
```

The camera turns 34 degrees. Source PNG renders are ignored by Git; the smaller WebP sequence is committed. Increase render samples and resolution for final production art if this direction is approved.

Additional visual references consulted: [campus aerial gallery](https://collegedunia.com/university/25829-manipal-university-muj-jaipur/gallery) and [administrative block gallery](https://www.collegebatch.com/3598-manipal-university-campus-tour-jaipur). The user's attached photos were the primary reference.
