# EMBER III · 点火 KINDLE: hand-animated in code

![EMBER III](../media/poster3.jpg)

▶ **[Watch it (media/ember3.mp4)](../media/ember3.mp4)** · master on the [v3.0 release](https://github.com/bishpls/ember/releases/tag/v3.0)

A 64-second anime-style episode with **no video models**. Every frame is drawn by JavaScript as a pure function of time, rendered with skia-canvas and piped into ffmpeg. The only generative-model use was three Promare-style **reference** frames (`refs/`), used as a style target the way an art director's boards would be.

It's a retake of the [video-model version](../ep3/) after that one was judged slop. The point was to take motion, timing, composition and consistency back from the model and author them by hand.

## What's in the code
| File | Role |
|---|---|
| `src/engine.js` | Time (150 BPM, 24 fps), easing, keyframe tracks, 2-bone IK, taper/capsule shape tools, cel-shading (hard single shadow), lagged follow-through |
| `src/hero.js` | The heroine: IK puppet with width-profiled limbs, a profile face (lids, iris, brow, mouth), hair mass, a cloak and scarf that trail by *lagged motion history*, and the gun-scythe with its unfold mechanism |
| `src/actor.js` | Sparse pose tracks and a 4-key sprint cycle (contact, down, passing, up) held on twos |
| `src/eye.js` | The extreme close-up anime eye: lids, layered iris, striations, highlights, lashes, snow crystals, fire mode |
| `src/wolf.js` | Void-wolf rig: gallop and leap legs, jagged flickering mane, jaw, cyan eyes |
| `src/fx.js` | Effects animation: Promare triangle fire and fire-blade feathers, ink bursts, smears, speed lines, shockwaves, cel puffs, cracks, muzzle blasts, impact frames |
| `src/bg.js`, `src/scene.js` | Flat layered pines, halftone moon with an eclipse bite, snow fields |
| `src/shots/*.js` | 17 shots, each hand-keyed against the beat map in `STORYBOARD.md` |
| `score.py` | The score on the house synth engine, locked to the same beat map |

Animation principles, applied by hand:
- **Timing and spacing:** drawings held on twos, ones for smears and impacts, and threes for stillness.
- **Anticipation → strike → overshoot → settle:** on every attack.
- **Solved contacts:** wolf leaps are solved backward from where the blade will be on the hit beat.
- **Hit-stop impact frames**, and **delayed kills** where the halves separate and then burst.
- **A rotating-camera ascent**, and one beat of silence before the cut.

## Build
```bash
npm install            # skia-canvas
python ../ep3b/score.py
node render.js --range 0 160 --out out/picture.mp4       # or 4 parallel chunks (~40 s total on an M2 Pro)
node render.js --sheet s07b_spin --n 12                   # contact sheet for any shot
```
