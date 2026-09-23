# EMBER II · ASH

![EMBER II](../media/poster2.jpg)

▶ **[Watch it (media/ember2.mp4)](../media/ember2.mp4)** · full-quality master on the [Releases page](https://github.com/bishpls/ember/releases)

A 52-second 3D sequel to [EMBER](../README.md), built entirely from code. Blender is driven headless from Python: the characters, forest, choreography, cameras, physics, score and grade are all generated, and there are no hand-made assets.

The brief was a grittier fight, closer to physics realism while keeping the energy. That meant momentum is conserved, single decisive strikes replace flurries, she takes hits and has to recover, and her recoil shots cost her ground.

## Pipeline

| File | Role |
|---|---|
| `tl.py` | Master timeline: 120 BPM at 24 fps, so a beat is exactly 12 frames. Cue times and speed-ramp time-warp. |
| `kin.py` | Pure-Python 3D kinematics: IK biped with a gun-scythe on a tiltable swing plane, and a procedural quadruped gait. |
| `ch.py` | Choreography engine: sparse keyframe tracks, ballistic arcs in warped time, a footstep planner with planted feet, foot locks, a rigid-body tumble sim with ground contacts, wolf scripts, event list and shot list. |
| `act1.py` `act2.py` `act3.py` | The film: every pose, contact, physics hand-off and camera. |
| `blib.py` | Blender library: procedural meshes (hero, weapon, wolves, recursive bare trees), materials, fog volume, moon. |
| `build.py` | Builds the `.blend`: per-frame keys, one camera per shot cut by timeline markers (so motion blur never smears across a cut), cloth cloak, dissolve shaders, particle FX from the event list. |
| `score.py` | Score and sound design, synthesized by reusing the 2D film's engine. SFX are placed from the same event list the visuals use. |
| `post.py` | Grade, bloom, vignette, grain and title card. |

## Choreography notes

- **Contacts are solved, not placed.** Every wolf leap is a ballistic arc solved backward from where the blade tip, shaft or foot will be at the hit frame.
- **Momentum decides outcomes.**
  - After the first cut, the wolf keeps its leap velocity and tumbles past her.
  - The tackle transfers momentum by mass ratio (70 kg into 55 kg), which throws her into a back-roll.
  - The leg hook turns a wolf's own speed into a faceplant.
  - The alpha's sweep crash continues along its lunge.
- **Feet stay planted.** A footstep planner and foot locks keep feet fixed while the body moves over them. Recoil shots slide her back through the snow with plough sprays.
- **She rides the alpha.** During the ride, her root is attached to the alpha's body frame, so she inherits its rear.
- **The cloak is Blender cloth**, pinned at the shoulders with body colliders and a wind field, and the roar gusts it.

## Build and render

Eevee needs GPU access (Metal). On macOS 13 the Eevee raytracing shaders crash the Metal compiler, so raytracing is disabled.

```bash
python score.py                                                             # -> out/ember2.wav
blender -b --factory-startup --python build.py -- --anim --pct 100 --samples 32 --out fin
python post.py fin finp a
ffmpeg -framerate 24 -i finp/p%04d.png -i out/ember2.wav -c:v libx264 -crf 17 -pix_fmt yuv420p -c:a aac -b:a 320k -shortest out/ember2_final.mp4
```

For quick iteration, use `build.py -- --frames 293,686 --pct 30` for stills, `--debugcam az,dist,height,lens` to track the hero from a fixed angle, or `--anim --pct 25 --samples 6` for a full low-resolution pass (about 7 minutes).
