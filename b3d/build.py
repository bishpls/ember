"""EMBER II — build the Blender scene from the choreography and (optionally) render.

blender -b --factory-startup --python build.py -- [--until 13] [--frames 1,50,200] [--pct 25]
        [--samples 16] [--anim] [--out DIR] [--nocloth] [--save]
"""
import sys
import os
import math
import argparse
import time

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import bpy
from mathutils import Vector, Quaternion, Matrix
import numpy as np

import blib
import kin
from tl import *

argv = sys.argv[sys.argv.index('--') + 1:] if '--' in sys.argv else []
ap = argparse.ArgumentParser()
ap.add_argument('--until', type=float, default=DUR)
ap.add_argument('--start', type=float, default=0.0)
ap.add_argument('--frames', default='')
ap.add_argument('--pct', type=int, default=25)
ap.add_argument('--samples', type=int, default=12)
ap.add_argument('--anim', action='store_true')
ap.add_argument('--out', default=os.path.join(HERE, 'prev'))
ap.add_argument('--nocloth', action='store_true')
ap.add_argument('--nomblur', action='store_true')
ap.add_argument('--save', action='store_true')
ap.add_argument('--acts', default='123')
ap.add_argument('--debugcam', default='')   # 'az,dist,height,lens' tracking the hero
A = ap.parse_args(argv)

T0 = time.time()
import ch
import act1  # noqa: F401  (registers choreography)
if '2' in A.acts:
    import act2  # noqa
if '3' in A.acts:
    import act3  # noqa
from ch import HP, WOLVES, EVENTS, SHOTS, cam_at, TO_MOON

LAST = min(NFR, F(A.until))
FIRST = max(1, F(A.start))
frames = list(range(1, LAST + 1))
print(f'[build] choreography loaded {time.time() - T0:.1f}s, frames 1..{LAST}')

# ---------------------------------------------------------------------------
blib.reset()
M = blib.make_materials()
blib.render_settings(pct=A.pct, samples=A.samples, mblur=not A.nomblur)
sc = bpy.context.scene
sc.frame_start = FIRST
sc.frame_end = LAST
sc.render.fps = FPS
bpy.context.preferences.edit.keyframe_new_interpolation_type = 'LINEAR'

blib.build_ground()
to_moon, sun, fog, fog_pv = blib.build_sky()
blib.build_forest(n=240, avoid=[(0, 0, 9.0)])
HERO_TREE = (-9.2, 5.6)
blib.add_tree(*HERO_TREE, h=13.0, seed=77)


# ---------------------------------------------------------------------------
# fast keyframing helpers
# ---------------------------------------------------------------------------
def _fc(ob_or_id, action, path, idx):
    return action.fcurve_ensure_for_datablock(ob_or_id, path, index=idx)


def key_arrays(idb, path_vals, frs, interp='LINEAR'):
    """path_vals: {(data_path, index): [values...]} aligned with frs."""
    ad = idb.animation_data_create()
    if ad.action is None:
        ad.action = bpy.data.actions.new(idb.name + '_act')
    act = ad.action
    n = len(frs)
    for (path, idx), vals in path_vals.items():
        fc = _fc(idb, act, path, idx)
        base = len(fc.keyframe_points)
        fc.keyframe_points.add(n)
        co = np.empty(2 * n, np.float32)
        co[0::2] = frs
        co[1::2] = vals
        kp = fc.keyframe_points
        allco = np.empty(2 * len(kp), np.float32)
        kp.foreach_get('co', allco)
        allco[2 * base:] = co
        kp.foreach_set('co', allco)
        ip = np.empty(len(kp), np.int32)
        kp.foreach_get('interpolation', ip)
        ip[base:] = {'LINEAR': 1, 'CONSTANT': 0, 'BEZIER': 2}[interp]
        kp.foreach_set('interpolation', ip)
        fc.update()


def key_xform(ob, frs, locs, quats=None, scales=None):
    pv = {}
    L = np.asarray(locs, np.float32)
    for i in range(3):
        pv[('location', i)] = L[:, i]
    if quats is not None:
        Q = np.asarray(quats, np.float32)
        # keep quaternion hemisphere continuous (avoids flips under interpolation)
        for j in range(1, len(Q)):
            if np.dot(Q[j], Q[j - 1]) < 0:
                Q[j] = -Q[j]
        for i in range(4):
            pv[('rotation_quaternion', i)] = Q[:, i]
    if scales is not None:
        S = np.asarray(scales, np.float32)
        for i in range(3):
            pv[('scale', i)] = S[:, i]
    key_arrays(ob, pv, frs)


def key_sparse(idb, path, idx, pairs, interp='LINEAR'):
    frs = [p[0] for p in pairs]
    key_arrays(idb, {(path, idx): [p[1] for p in pairs]}, frs, interp)


# sub-frame sampling for motion blur fidelity: key on whole frames (Eevee interpolates)
TIMES = [(f - 1) / FPS for f in frames]

# ---------------------------------------------------------------------------
# HERO
# ---------------------------------------------------------------------------
hero = blib.build_hero()
cloak = blib.build_cloak()
tr_per = {k: ([], []) for k in hero}
scales_w = []
t1 = time.time()
for t in TIMES:
    H = HP(t)
    X = H.transforms()
    for k in hero:
        if k in ('gun', 'accent'):
            loc, q = H.w_head, X['weapon'][1]
        else:
            loc, q = X[k]
        tr_per[k][0].append(loc)
        tr_per[k][1].append(q)
    scales_w.append((1.0, 1.0, H.w_len))
for k, ob in hero.items():
    key_xform(ob, frames, tr_per[k][0], tr_per[k][1], scales_w if k == 'weapon' else None)
print(f'[build] hero keyed {time.time() - t1:.1f}s')

# cloak: child of the torso (its mesh is authored in the torso frame)
cloak.parent = hero['torso']
cloak.matrix_parent_inverse = Matrix()
if not A.nocloth:
    cm = cloak.modifiers.new('cloth', 'CLOTH')
    cs = cm.settings
    cs.quality = 10
    cs.mass = 0.35
    cs.air_damping = 1.2
    cs.tension_stiffness = 18
    cs.compression_stiffness = 18
    cs.shear_stiffness = 8
    cs.bending_stiffness = 0.05
    cs.pin_stiffness = 1.0
    cs.vertex_group_mass = 'pin'
    cm.collision_settings.use_collision = True
    cm.collision_settings.distance_min = 0.012
    cm.collision_settings.collision_quality = 3
    cm.point_cache.frame_start = 1
    cm.point_cache.frame_end = LAST
    for k in ('torso', 'thigh_r', 'thigh_l', 'shin_r', 'shin_l'):
        c = hero[k].modifiers.new('col', 'COLLISION')
        hero[k].collision.thickness_outer = 0.02
        hero[k].collision.cloth_friction = 5
    sm = cloak.modifiers.new('sub', 'SUBSURF')
    sm.levels = 1
    sm.render_levels = 2
    so = cloak.modifiers.new('solid', 'SOLIDIFY')
    so.thickness = 0.008

# wind (streams the cloak and snow away from the camera side)
bpy.ops.object.effector_add(type='WIND', location=(20, 0, 2))
wind = bpy.context.active_object
wind.rotation_euler = (0, -math.pi / 2, 0)         # blow toward -X
wind.field.strength = 2.2
wind.field.noise = 1.5
wind.field.flow = 0.3
turb = None
bpy.ops.object.effector_add(type='TURBULENCE', location=(0, 0, 2))
turb = bpy.context.active_object
turb.field.strength = 1.2
turb.field.size = 1.5

# ---------------------------------------------------------------------------
# WOLVES
# ---------------------------------------------------------------------------
def wolf_materials(name):
    body = M['wolf'].copy()
    body.name = name + '_mat'
    nt = body.node_tree
    bsdf = nt.nodes['Principled BSDF']
    out = nt.nodes['Material Output']
    tc = nt.nodes.new('ShaderNodeTexCoord')
    nz = nt.nodes.new('ShaderNodeTexNoise')
    nz.inputs['Scale'].default_value = 4.0
    nz.inputs['Detail'].default_value = 8.0
    nt.links.new(tc.outputs['Object'], nz.inputs['Vector'])
    val = nt.nodes.new('ShaderNodeValue')
    val.name = 'dissolve'
    val.outputs[0].default_value = 0.0
    # threshold t = dissolve*1.3 - 0.15 ; alpha = noise > t ; edge = |noise - t| < w
    thr = nt.nodes.new('ShaderNodeMath')
    thr.operation = 'MULTIPLY_ADD'
    thr.inputs[1].default_value = 1.3
    thr.inputs[2].default_value = -0.15
    nt.links.new(val.outputs[0], thr.inputs[0])
    gt = nt.nodes.new('ShaderNodeMath')
    gt.operation = 'GREATER_THAN'
    nt.links.new(nz.outputs['Fac'], gt.inputs[0])
    nt.links.new(thr.outputs[0], gt.inputs[1])
    sub = nt.nodes.new('ShaderNodeMath')
    sub.operation = 'SUBTRACT'
    nt.links.new(nz.outputs['Fac'], sub.inputs[0])
    nt.links.new(thr.outputs[0], sub.inputs[1])
    edge = nt.nodes.new('ShaderNodeMapRange')
    edge.inputs['From Min'].default_value = 0.0
    edge.inputs['From Max'].default_value = 0.06
    edge.inputs['To Min'].default_value = 1.0
    edge.inputs['To Max'].default_value = 0.0
    nt.links.new(sub.outputs[0], edge.inputs['Value'])
    emis = nt.nodes.new('ShaderNodeMath')
    emis.operation = 'MULTIPLY'
    emis.inputs[1].default_value = 60.0
    nt.links.new(edge.outputs[0], emis.inputs[0])
    # only glow while dissolving
    gate = nt.nodes.new('ShaderNodeMath')
    gate.operation = 'GREATER_THAN'
    gate.inputs[1].default_value = 0.001
    nt.links.new(val.outputs[0], gate.inputs[0])
    emis2 = nt.nodes.new('ShaderNodeMath')
    emis2.operation = 'MULTIPLY'
    nt.links.new(emis.outputs[0], emis2.inputs[0])
    nt.links.new(gate.outputs[0], emis2.inputs[1])
    bsdf.inputs['Emission Color'].default_value = (1.0, 0.32, 0.06, 1)
    nt.links.new(emis2.outputs[0], bsdf.inputs['Emission Strength'])
    tr = nt.nodes.new('ShaderNodeBsdfTransparent')
    mix = nt.nodes.new('ShaderNodeMixShader')
    nt.links.new(gt.outputs[0], mix.inputs['Fac'])
    nt.links.new(tr.outputs[0], mix.inputs[1])
    nt.links.new(bsdf.outputs[0], mix.inputs[2])
    nt.links.new(mix.outputs[0], out.inputs['Surface'])
    eye = M['eye'].copy()
    eye.name = name + '_eye'
    return body, eye


t1 = time.time()
WOBJ = {}
for w in WOLVES:
    parts = blib.build_wolf(w.name, w.s, seed=w.seed)
    body_m, eye_m = wolf_materials(w.name)
    for k in ('body', 'head', 'jaw', 'tail'):
        sm_ = parts[k].modifiers.new('sub', 'SUBSURF')
        sm_.levels = 1
        sm_.render_levels = 1
    for k, ob in parts.items():
        ob.data.materials.clear()
        ob.data.materials.append(eye_m if k == 'eyes' else body_m)
    per = {k: ([], []) for k in parts}
    for t in TIMES:
        st = w.state(t)
        X = st.transforms()
        for k in parts:
            loc, q = X[k] if k in X else X['body']
            per[k][0].append(loc)
            per[k][1].append(q)
    for k, ob in parts.items():
        key_xform(ob, frames, per[k][0], per[k][1])
    # sparse material animation from the track's key times
    def sparse(param, scale=1.0):
        ks = w.tr.k.get(param, [])
        pts = sorted(set([0.0] + [q[0] for q in ks] + [min(A.until, DUR)]))
        # densify between keys so eased curves survive
        dense = []
        for a, b in zip(pts[:-1], pts[1:]):
            for j in range(6):
                dense.append(a + (b - a) * j / 6)
        dense.append(pts[-1])
        return [(F(x), w.tr.get(param, x) * scale) for x in dense if x <= A.until + 0.5]
    key_sparse(body_m.node_tree, 'nodes["dissolve"].outputs[0].default_value', 0, sparse('dissolve'))
    ep = sparse('eye', 45.0)
    dp = dict(sparse('dissolve'))
    ks_d = w.tr.k.get('dissolve', [])
    if ks_d:
        # eyes go out as the body burns away
        t_d0 = ks_d[0][0]
        ep = [(f, v * (1 - clamp(w.tr.get('dissolve', (f - 1) / FPS) * 2.5))) for (f, v) in ep]
        ep += [(F(t_d0 + k * 0.1), 45.0 * w.tr.get('eye', t_d0 + k * 0.1) *
                (1 - clamp(w.tr.get('dissolve', t_d0 + k * 0.1) * 2.5))) for k in range(12)]
        ep = sorted(dict(ep).items())
    key_sparse(eye_m.node_tree, 'nodes["Emission"].inputs[1].default_value', 0, ep)
    hu = getattr(w, 'hidden_until', None)
    if hu:
        for ob in parts.values():
            ob.hide_render = True
            ob.keyframe_insert('hide_render', frame=1)
            ob.hide_render = False
            ob.keyframe_insert('hide_render', frame=F(hu))
    if w.t_dead is not None:
        for ob in parts.values():
            if not hu:
                ob.hide_render = False
                ob.keyframe_insert('hide_render', frame=1)
            ob.hide_render = True
            ob.keyframe_insert('hide_render', frame=F(w.t_dead) + 1)
            ob.hide_render = False
            ob.keyframe_insert('hide_render', frame=F(w.t_dead))
    WOBJ[w.name] = parts
print(f'[build] wolves keyed {time.time() - t1:.1f}s')

# ---------------------------------------------------------------------------
# CAMERAS: one camera per shot, cut with timeline markers (no blur across cuts)
# ---------------------------------------------------------------------------
t1 = time.time()
CAMS = []
shots = [(t0, fn) for (t0, fn) in SHOTS]
for i, (t0, fn) in enumerate(shots):
    t_end = shots[i + 1][0] if i + 1 < len(shots) else DUR
    if t0 > A.until:
        break
    f0, f1 = F(t0), min(F(t_end), LAST + 1)
    cam = blib.make_camera(f'cam{i:02d}')
    frs = list(range(max(1, f0 - 1), f1 + 2))
    locs, quats, lens, focus, fst = [], [], [], [], []
    for f in frs:
        t = (f - 1) / FPS
        tt = min(max(t, t0), t_end - 1e-4)
        c = fn(tt)
        eye = Vector(c['eye'])
        tgt = Vector(c['target'])
        q = blib.look_quat(eye, tgt, c.get('roll', 0.0))
        locs.append(tuple(eye))
        quats.append(tuple(q))
        lens.append(c.get('lens', 35.0))
        fd = c.get('focus')
        focus.append(fd if fd is not None else (tgt - eye).length)
        fst.append(c.get('fstop', 2.8))
    key_xform(cam, frs, locs, quats)
    key_arrays(cam.data, {('lens', 0): lens, ('dof.focus_distance', 0): focus,
                          ('dof.aperture_fstop', 0): fst}, frs)
    m = sc.timeline_markers.new(f'S{i:02d}', frame=f0)
    m.camera = cam
    CAMS.append((f0, f1, cam))
print(f'[build] {len(shots)} cameras {time.time() - t1:.1f}s')
# fill: a large, faint, cool area light slightly above each camera (a bounce board, in effect)
fl = bpy.data.lights.new('camfill', 'AREA')
fl.shape = 'DISK'
fl.size = 2.5
fl.energy = 10
fl.color = (0.6, 0.7, 1.0)
fill = bpy.data.objects.new('camfill', fl)
blib.coll('Env').objects.link(fill)
fill.rotation_mode = 'QUATERNION'
floc, fquat, ffr = [], [], []
for f in frames:
    cam = None
    for (a, b, c) in CAMS:
        if a <= f < b:
            cam = c
    if cam is None:
        cam = CAMS[-1][2] if CAMS else None
    if cam is None:
        break
    sc.frame_set(f) if False else None
    fc_loc = [cam.animation_data.action.fcurve_ensure_for_datablock(cam, 'location', index=i).evaluate(f) for i in range(3)]
    fc_q = [cam.animation_data.action.fcurve_ensure_for_datablock(cam, 'rotation_quaternion', index=i).evaluate(f) for i in range(4)]
    q = Quaternion(fc_q)
    up = q @ Vector((0, 0.8, 0.3))
    floc.append(tuple(Vector(fc_loc) + up))
    fquat.append(tuple(q))
    ffr.append(f)
key_xform(fill, ffr, floc, fquat)

if A.debugcam:
    az, dist, hgt, lens = [float(x) for x in A.debugcam.split(',')]
    for m_ in list(sc.timeline_markers):
        sc.timeline_markers.remove(m_)
    dc = blib.make_camera('debugcam', lens)
    dc.data.dof.use_dof = False
    locs, quats = [], []
    for t in TIMES:
        c = Vector(HP(t).chest)
        e = c + Vector((math.cos(az * math.pi / 180), math.sin(az * math.pi / 180), 0)) * dist + Vector((0, 0, hgt))
        locs.append(tuple(e))
        quats.append(tuple(blib.look_quat(e, c)))
    key_xform(dc, frames, locs, quats)
    sc.camera = dc

# ---------------------------------------------------------------------------
# PARTICLES
# ---------------------------------------------------------------------------
def instance_obj(name, mat, radius=0.02, stretch=1.0):
    import bmesh
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=1, radius=radius)
    if stretch != 1.0:
        bmesh.ops.scale(bm, vec=(1, stretch, 1), verts=bm.verts)
    ob = blib.mesh_obj(name, bm, mat, collection='Proto')
    return ob


proto = blib.coll('Proto')
proto.hide_render = True
P_SNOWBIT = instance_obj('p_snow', M['snowflake'], 0.02)
P_SPARK = instance_obj('p_spark', M['spark'], 0.004, stretch=6.0)
P_ICHOR = instance_obj('p_ichor', M['ichor'], 0.012)
P_FLAKE = instance_obj('p_flake', M['snowflake'], 0.011)
P_EMBER = instance_obj('p_ember', M['ember'], 0.008)
bpy.context.view_layer.update()


def emitter(name, pos, frame, count, inst, life=48, vel_normal=2.0, vel_rand=1.0, obj_vel=(0, 0, 0),
            gravity=1.0, drag=0.0, size=1.0, size_rand=0.5, radius=0.05, align_vel=False, frames_len=1,
            brownian=0.0, damping=0.0):
    import bmesh
    bm = bmesh.new()
    bmesh.ops.create_icosphere(bm, subdivisions=1, radius=radius)
    ob = blib.mesh_obj(name, bm, None, collection='FX', smooth=False)
    ob.location = Vector(pos)
    ob.show_instancer_for_render = False
    ob.show_instancer_for_viewport = False
    ps_mod = ob.modifiers.new('ps', 'PARTICLE_SYSTEM')
    ps = ps_mod.particle_system.settings
    ps.count = count
    ps.frame_start = frame
    ps.frame_end = frame + frames_len
    ps.lifetime = life
    ps.lifetime_random = 0.4
    ps.emit_from = 'FACE'
    ps.normal_factor = vel_normal
    ps.factor_random = vel_rand
    ps.object_align_factor = obj_vel
    ps.effector_weights.gravity = gravity
    ps.drag_factor = drag
    ps.brownian_factor = brownian
    ps.damping = damping
    ps.render_type = 'OBJECT'
    ps.instance_object = inst
    ps.particle_size = size
    ps.size_random = size_rand
    ps.use_rotations = align_vel
    if align_vel:
        ps.rotation_mode = 'VEL'
    ps.use_dead = False
    return ob


fx = blib.coll('FX')
nev = 0
for i, e in enumerate(EVENTS):
    if e['t'] > A.until + 0.1:
        continue
    fr = F(e['t'])
    k = e['kind']
    pos = e['pos']
    d = Vector(e.get('dir', (0, 0, 0)))
    if k == 'step':
        emitter(f'fx{i}', pos, fr, e.get('n', 20), P_SNOWBIT, life=20, vel_normal=0.6, vel_rand=0.5,
                obj_vel=(0, 0, 0.6), drag=0.6, size=0.7, radius=0.06)
    elif k == 'thud':
        sp = e.get('speed', 3.0)
        emitter(f'fx{i}', pos, fr, e.get('n', 80), P_SNOWBIT, life=40, vel_normal=0.8 + sp * 0.35,
                vel_rand=1.2, obj_vel=(0, 0, 1.0 + sp * 0.3), drag=0.5, size=1.0, radius=0.3)
    elif k == 'hit':
        if e.get('ricochet'):
            emitter(f'fx{i}s', pos, fr, 24, P_SPARK, life=6, vel_normal=3.0, vel_rand=2.0,
                    obj_vel=tuple(d * 2), gravity=0.6, size=0.5, size_rand=0.5, radius=0.03)
        # muzzle-flash style point light burst
        ld = bpy.data.lights.new(f'hitl{i}', 'POINT')
        ld.color = (1.0, 0.75, 0.45)
        ld.shadow_soft_size = 0.05
        lo = bpy.data.objects.new(f'hitl{i}', ld)
        lo.location = Vector(pos)
        fx.objects.link(lo)
        for (ff, en) in [(fr - 1, 0), (fr, (260 if e.get('big') else 120) if e.get('ricochet') else 0), (fr + 2, 0), (fr + 5, 0)]:
            ld.energy = en
            ld.keyframe_insert('energy', frame=ff)
    elif k == 'ichor':
        emitter(f'fx{i}', pos, fr, e.get('n', 120), P_ICHOR, life=36, vel_normal=1.2, vel_rand=1.5,
                obj_vel=tuple(d), gravity=1.0, size=1.0, size_rand=0.8, radius=0.1, frames_len=3)
    elif k == 'shot':
        big = e.get('big')
        emitter(f'fx{i}s', pos, fr, 40, P_SPARK, life=6, vel_normal=2.0, vel_rand=3.0,
                obj_vel=tuple(d * 9), gravity=0.3, size=0.8, radius=0.02, align_vel=True)
        ld = bpy.data.lights.new(f'muz{i}', 'POINT')
        ld.color = (1.0, 0.62, 0.3)
        ld.shadow_soft_size = 0.02
        lo = bpy.data.objects.new(f'muz{i}', ld)
        lo.location = Vector(pos) + d * 0.15
        fx.objects.link(lo)
        for (ff, en) in [(fr - 1, 0), (fr, 6000 if big else 3500), (fr + 1, 1200), (fr + 3, 0)]:
            ld.energy = en
            ld.keyframe_insert('energy', frame=ff)
        # flash sprite: emissive star-ish ellipsoid along the barrel, 2 frames
        import bmesh as _bm
        bmf = _bm.new()
        _bm.ops.create_icosphere(bmf, subdivisions=2, radius=1.0)
        _bm.ops.scale(bmf, vec=(0.09, 0.09, 0.35), verts=bmf.verts)
        _bm.ops.translate(bmf, vec=(0, 0, 0.3), verts=bmf.verts)
        fl_ob = blib.mesh_obj(f'flash{i}', bmf, M['flash'], collection='FX')
        fl_ob.location = Vector(pos)
        fl_ob.rotation_mode = 'QUATERNION'
        fl_ob.rotation_quaternion = d.to_track_quat('Z', 'Y') if d.length > 0 else Quaternion()
        for (ff, sc_) in [(fr - 1, 0.0), (fr, 1.0), (fr + 1, 0.6), (fr + 2, 0.0)]:
            fl_ob.scale = (sc_, sc_, sc_)
            fl_ob.keyframe_insert('scale', frame=ff)
        # gun smoke drifting
        emitter(f'fx{i}k', pos, fr, 30, P_SNOWBIT, life=30, vel_normal=0.4, vel_rand=0.5,
                obj_vel=tuple(d * 1.5), gravity=-0.05, drag=0.8, size=1.6, radius=0.05, frames_len=2)
    elif k == 'roar':
        emitter(f'fx{i}', pos, fr, 700, P_SNOWBIT, life=30, vel_normal=0.8, vel_rand=1.2,
                obj_vel=tuple(d * 9.0), gravity=0.2, drag=0.6, size=0.7, radius=0.6, frames_len=14)
        for (ff, st) in [(fr - 2, 2.2), (fr + 3, 11.0), (fr + 18, 8.0), (fr + 30, 2.2)]:
            wind.field.strength = st
            wind.field.keyframe_insert('strength', frame=ff)
    elif k == 'plough':
        emitter(f'fx{i}', pos, fr, e.get('n', 30), P_SNOWBIT, life=26, vel_normal=0.6, vel_rand=0.8,
                obj_vel=tuple(d * 1.4 + Vector((0, 0, 1.4))), drag=0.5, size=0.9, radius=0.08)
    elif k == 'tremor':
        import random as _r
        rr = _r.Random(i)
        for j in range(10 * e.get('n', 1)):
            a = rr.uniform(0, 6.28)
            rad = rr.uniform(3.0, 11.0)
            p_ = (math.cos(a) * rad, math.sin(a) * rad, rr.uniform(6.5, 10.5))
            emitter(f'fx{i}_{j}', p_, fr + rr.randint(0, 10), 260, P_SNOWBIT, life=90, vel_normal=0.1,
                    vel_rand=0.3, gravity=0.55, drag=0.9, size=0.8, size_rand=0.7, radius=0.9, frames_len=6)
    elif k == 'ash':
        parts_ = WOBJ.get(e['wolf'])
        if parts_:
            body = parts_['body']
            f0_, f1_ = fr, F(e['t1'])
            for nm, inst, cnt, grav in (('emb', P_EMBER, 500, -0.08), ('ash', P_ICHOR, 350, -0.02)):
                pm = body.modifiers.new(nm, 'PARTICLE_SYSTEM').particle_system.settings
                pm.count = cnt
                pm.frame_start = f0_
                pm.frame_end = f1_
                pm.lifetime = 70
                pm.lifetime_random = 0.6
                pm.emit_from = 'FACE'
                pm.normal_factor = 0.15
                pm.factor_random = 0.25
                pm.effector_weights.gravity = grav
                pm.brownian_factor = 0.35
                pm.drag_factor = 0.3
                pm.render_type = 'OBJECT'
                pm.instance_object = inst
                pm.particle_size = 1.0 / body.scale[0]
                pm.size_random = 0.6
            body.show_instancer_for_render = True
    nev += 1
print(f'[build] {nev} FX emitters')

# ambient snowfall
import bmesh
bm = bmesh.new()
bmesh.ops.create_grid(bm, x_segments=1, y_segments=1, size=28)
snow_em = blib.mesh_obj('snowfall', bm, None, collection='FX', smooth=False)
snow_em.location = (0, 0, 13)
snow_em.show_instancer_for_render = False
psm = snow_em.modifiers.new('snow', 'PARTICLE_SYSTEM').particle_system.settings
psm.count = 26000
psm.frame_start = -300
psm.frame_end = NFR
psm.lifetime = 420
psm.emit_from = 'FACE'
psm.normal_factor = -0.9
psm.factor_random = 0.2
psm.effector_weights.gravity = 0.0
psm.brownian_factor = 0.4
psm.drag_factor = 0.2
psm.render_type = 'OBJECT'
psm.instance_object = P_FLAKE
psm.particle_size = 1.0
psm.size_random = 0.7

# ---------------------------------------------------------------------------
if not A.nocloth:
    t1 = time.time()
    sc.frame_set(1)
    for f in range(1, LAST + 1):
        sc.frame_set(f)           # steps the cloth + particle caches forward in order
    print(f'[build] sim pass {time.time() - t1:.1f}s')

if A.save:
    bpy.ops.wm.save_as_mainfile(filepath=os.path.join(HERE, 'ember2.blend'))

os.makedirs(A.out, exist_ok=True)
if A.frames:
    for f in [int(x) for x in A.frames.split(',')]:
        sc.frame_set(f)
        sc.render.filepath = os.path.join(A.out, f'f{f:04d}.png')
        bpy.ops.render.render(write_still=True)
    print(f'[build] stills done {time.time() - T0:.1f}s')
if A.anim:
    sc.render.filepath = os.path.join(A.out, 'a')
    bpy.ops.render.render(animation=True)
    print(f'[build] anim done {time.time() - T0:.1f}s')
