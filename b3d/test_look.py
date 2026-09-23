import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bpy
from mathutils import Vector, Quaternion
import blib, kin

blib.reset()
blib.make_materials()
blib.render_settings(pct=50, samples=24, mblur=False)
blib.build_ground()
to_moon, sun, fog, pv = blib.build_sky()
blib.build_forest(n=220)
hero = blib.build_hero()
cloak = blib.build_cloak()

# posed huntress: guard stance, weapon low behind, facing +X
p = dict(kin.POSE0)
p.update(yaw=0, lean=22, head=-8, wa=-160, wtilt=12, wx=-0.05, wy=-0.3, wz=0.12, g1=0.3, g2=0.52,
         fx1=0.42, fz1=0.14, fy1=-0.72, fx2=-0.4, fz2=-0.18, fy2=-0.72)
H = kin.Hero(p, (0, 0, 0.7))
tr = H.transforms()
for k, ob in hero.items():
    if k in ('gun', 'accent'):
        loc, q = H.w_head, tr['weapon'][1]
    else:
        loc, q = tr[k]
    ob.location = Vector(loc)
    ob.rotation_quaternion = Quaternion(q)
hero['weapon'].scale = (1, 1, H.w_len)
# cloak: parent-free, place at chest frame
cq = kin.mat_to_quat(kin.frame_from(H.spine, H.chest_r))
cloak.location = Vector(H.pelvis)
cloak.rotation_mode = 'QUATERNION'
cloak.rotation_quaternion = Quaternion(cq)

for i, (pos, hd, mode) in enumerate([((4.2, 0.8, 0.78), math.pi + 0.2, 'crouch'), ((3.0, -3.2, 0.78), 2.2, 'run')]):
    parts = blib.build_wolf(f"W{i}", 1.25, seed=i)
    Wf = kin.Wolf((pos[0], pos[1], 0.98), hd, s=1.25, mode=mode, phase=0.3, jaw=0.5)
    t = Wf.transforms()
    for k, ob in parts.items():
        key = k if k in t else ('head' if k == 'eyes' else 'body')
        if k == 'tail':
            loc = Wf.W(-0.62, 0.1)
            q = t['body'][1]
        else:
            loc, q = t[key]
        ob.location = Vector(loc)
        ob.rotation_quaternion = Quaternion(q)

cam = blib.make_camera()
shots = {
    'wide': ((-7.5, -6.0, 1.6), (1.2, 0, 1.3), 28),
    'low': ((-2.2, 2.2, 0.35), (1.0, -0.2, 1.4), 24),
    'moon': (None, None, 32),
}
out = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'look')
os.makedirs(out, exist_ok=True)
for name, (eye, tgt, lens) in shots.items():
    if name == 'moon':
        # back the camera off along the anti-moon direction so she sits in front of the moon
        h = Vector((0, 0, 1.2))
        eye = h - to_moon * 7.0
        eye.z = 0.45
        tgt = h + to_moon * 6.0
    cam.location = Vector(eye)
    cam.rotation_quaternion = blib.look_quat(eye, tgt)
    cam.data.lens = lens
    cam.data.dof.focus_distance = (Vector(tgt) - Vector(eye)).length
    bpy.context.scene.render.filepath = os.path.join(out, name + '.png')
    bpy.ops.render.render(write_still=True)
bpy.ops.wm.save_as_mainfile(filepath=os.path.join(out, 'look.blend'))

# probe action API for keyframing
act = bpy.data.actions.new('probe')
print('ACTION_API fcurves' if hasattr(act, 'fcurves') else 'ACTION_API layered', [a for a in dir(act) if 'slot' in a or 'layer' in a])
