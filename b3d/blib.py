"""Blender-side library: meshes, materials, environment, keyframing.  Run inside Blender."""
import bpy
import bmesh
import math
import random
from mathutils import Vector, Matrix, Quaternion

import kin

# ---------------------------------------------------------------------------
# scene / collections
# ---------------------------------------------------------------------------
def reset():
    bpy.ops.wm.read_factory_settings(use_empty=True)
    sc = bpy.context.scene
    return sc


def coll(name):
    c = bpy.data.collections.get(name)
    if c is None:
        c = bpy.data.collections.new(name)
        bpy.context.scene.collection.children.link(c)
    return c


def mesh_obj(name, bm, mat=None, smooth=True, collection='Chars', mats=None):
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    if smooth:
        for p in me.polygons:
            p.use_smooth = True
    ob = bpy.data.objects.new(name, me)
    coll(collection).objects.link(ob)
    if mats:
        for m in mats:
            me.materials.append(m)
    elif mat:
        me.materials.append(mat)
    return ob


# ---------------------------------------------------------------------------
# materials
# ---------------------------------------------------------------------------
def principled(name, color, rough=0.5, metal=0.0, emit=None, emit_strength=0.0, sheen=0.0,
               subsurface=0.0, coat=0.0, spec=0.5):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    b = nt.nodes.get('Principled BSDF')
    b.inputs['Base Color'].default_value = (*color, 1)
    b.inputs['Roughness'].default_value = rough
    b.inputs['Metallic'].default_value = metal
    if 'Specular IOR Level' in b.inputs:
        b.inputs['Specular IOR Level'].default_value = spec
    if sheen and 'Sheen Weight' in b.inputs:
        b.inputs['Sheen Weight'].default_value = sheen
        b.inputs['Sheen Tint'].default_value = (0.7, 0.8, 1.0, 1)
    if subsurface and 'Subsurface Weight' in b.inputs:
        b.inputs['Subsurface Weight'].default_value = subsurface
        b.inputs['Subsurface Radius'].default_value = (0.4, 0.5, 0.9)
    if coat and 'Coat Weight' in b.inputs:
        b.inputs['Coat Weight'].default_value = coat
    if emit is not None:
        b.inputs['Emission Color'].default_value = (*emit, 1)
        b.inputs['Emission Strength'].default_value = emit_strength
    return m


def emission(name, color, strength):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    for n in list(nt.nodes):
        nt.nodes.remove(n)
    e = nt.nodes.new('ShaderNodeEmission')
    e.inputs['Color'].default_value = (*color, 1)
    e.inputs['Strength'].default_value = strength
    o = nt.nodes.new('ShaderNodeOutputMaterial')
    nt.links.new(e.outputs[0], o.inputs[0])
    return m


MAT = {}


def fur_material():
    m = principled('wolf', (0.006, 0.006, 0.008), rough=0.88, sheen=1.0)
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    tc = nt.nodes.new('ShaderNodeTexCoord')
    mp = nt.nodes.new('ShaderNodeMapping')
    mp.inputs['Scale'].default_value = (60.0, 60.0, 9.0)     # stretched along the body: strands
    nt.links.new(tc.outputs['Object'], mp.inputs['Vector'])
    nz = nt.nodes.new('ShaderNodeTexNoise')
    nz.inputs['Scale'].default_value = 1.0
    nz.inputs['Detail'].default_value = 4.0
    nt.links.new(mp.outputs['Vector'], nz.inputs['Vector'])
    bump = nt.nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = 0.8
    nt.links.new(nz.outputs['Fac'], bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'], b.inputs['Normal'])
    return m


def snow_material():
    m = principled('snow', (0.62, 0.68, 0.80), rough=0.55, subsurface=0.1)
    nt = m.node_tree
    b = nt.nodes['Principled BSDF']
    tc = nt.nodes.new('ShaderNodeTexCoord')
    nz = nt.nodes.new('ShaderNodeTexNoise')
    nz.inputs['Scale'].default_value = 3.0
    nz.inputs['Detail'].default_value = 6.0
    nt.links.new(tc.outputs['Object'], nz.inputs['Vector'])
    vo = nt.nodes.new('ShaderNodeTexVoronoi')
    vo.inputs['Scale'].default_value = 900.0
    nt.links.new(tc.outputs['Object'], vo.inputs['Vector'])
    mix = nt.nodes.new('ShaderNodeMath')
    mix.operation = 'MULTIPLY_ADD'
    mix.inputs[1].default_value = 0.35
    nt.links.new(nz.outputs['Fac'], mix.inputs[0])
    nt.links.new(vo.outputs['Distance'], mix.inputs[2])
    bump = nt.nodes.new('ShaderNodeBump')
    bump.inputs['Strength'].default_value = 0.35
    nt.links.new(mix.outputs[0], bump.inputs['Height'])
    nt.links.new(bump.outputs['Normal'], b.inputs['Normal'])
    # large-scale tonal variation
    nz2 = nt.nodes.new('ShaderNodeTexNoise')
    nz2.inputs['Scale'].default_value = 0.08
    nt.links.new(tc.outputs['Object'], nz2.inputs['Vector'])
    ramp = nt.nodes.new('ShaderNodeValToRGB')
    ramp.color_ramp.elements[0].color = (0.45, 0.50, 0.62, 1)
    ramp.color_ramp.elements[1].color = (0.70, 0.76, 0.88, 1)
    nt.links.new(nz2.outputs['Fac'], ramp.inputs['Fac'])
    nt.links.new(ramp.outputs['Color'], b.inputs['Base Color'])
    return m


def make_materials():
    MAT['ink'] = principled('ink', (0.018, 0.019, 0.024), rough=0.55, sheen=0.4)
    MAT['leather'] = principled('leather', (0.03, 0.028, 0.03), rough=0.4, coat=0.3)
    MAT['cloak'] = principled('cloak', (0.30, 0.018, 0.014), rough=0.8, sheen=1.0)
    MAT['steel'] = principled('steel', (0.55, 0.57, 0.62), rough=0.22, metal=1.0)
    MAT['gunmetal'] = principled('gunmetal', (0.05, 0.05, 0.06), rough=0.35, metal=0.8)
    MAT['accent'] = principled('accent', (0.5, 0.03, 0.02), rough=0.3, metal=0.3)
    MAT['skin'] = principled('face', (0.005, 0.005, 0.007), rough=0.8)
    MAT['wolf'] = fur_material()
    MAT['eye'] = emission('eye', (0.55, 0.92, 1.0), 45.0)
    MAT['snow'] = snow_material()
    MAT['bark'] = principled('bark', (0.028, 0.03, 0.036), rough=0.9)
    MAT['moon'] = emission('moon', (0.85, 0.9, 1.0), 14.0)
    MAT['ember'] = emission('ember', (1.0, 0.35, 0.08), 40.0)
    MAT['spark'] = emission('spark', (1.0, 0.75, 0.4), 80.0)
    MAT['flash'] = emission('flash', (1.0, 0.7, 0.35), 200.0)
    MAT['snowflake'] = principled('flake', (0.9, 0.93, 1.0), rough=0.5)
    MAT['ichor'] = principled('ichor', (0.004, 0.004, 0.006), rough=0.2, coat=1.0)
    return MAT


# ---------------------------------------------------------------------------
# primitive builders (bmesh)
# ---------------------------------------------------------------------------
def bm_capsule(bm, r0, r1, L, seg=14, M=None):
    M = M or Matrix()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r0, radius2=r1, depth=L,
                          matrix=M @ Matrix.Translation((0, 0, L / 2)))
    bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=8, radius=r0, matrix=M)
    bmesh.ops.create_uvsphere(bm, u_segments=seg, v_segments=8, radius=r1,
                              matrix=M @ Matrix.Translation((0, 0, L)))


def bm_loft(bm, rings, n=16, cap=True, spikes=None):
    """rings: list of (z, rx, ry, cx, cy) ellipses stacked along Z (x = width, y = depth)."""
    prev = None
    first = None
    for (z, rx, ry, cx, cy) in rings:
        ring = []
        for i in range(n):
            a = 2 * math.pi * i / n
            ring.append(bm.verts.new((cx + rx * math.cos(a), cy + ry * math.sin(a), z)))
        if prev:
            for i in range(n):
                bm.faces.new((prev[i], prev[(i + 1) % n], ring[(i + 1) % n], ring[i]))
        else:
            first = ring
        prev = ring
    if cap:
        bm.faces.new(list(reversed(first)))
        bm.faces.new(prev)


def bm_loft_y(bm, rings, n=16, cap=True):
    """Loft along +Y: rings (y, rx, rz, cx, cz)."""
    tmp = bmesh.new()
    bm_loft(tmp, [(y, rx, rz, cx, cz) for (y, rx, rz, cx, cz) in rings], n, cap)
    # rotate Z->Y (x stays, loft's y(depth)->z)
    bmesh.ops.rotate(tmp, verts=tmp.verts, cent=(0, 0, 0), matrix=Matrix.Rotation(-math.pi / 2, 3, 'X'))
    me = bpy.data.meshes.new('_tmp')
    tmp.to_mesh(me)
    tmp.free()
    bm.from_mesh(me)
    bpy.data.meshes.remove(me)


def bm_cone(bm, r, h, M, seg=6):
    bmesh.ops.create_cone(bm, cap_ends=True, segments=seg, radius1=r, radius2=0.0, depth=h,
                          matrix=M @ Matrix.Translation((0, 0, h / 2)))


# ---------------------------------------------------------------------------
# HERO
# ---------------------------------------------------------------------------
def build_hero(prefix='H'):
    parts = {}
    ink, lea = MAT['ink'], MAT['leather']
    spec = {
        'thigh_r': (0.078, 0.058, kin.THIGH, ink), 'thigh_l': (0.078, 0.058, kin.THIGH, ink),
        'shin_r': (0.056, 0.046, kin.SHIN, lea), 'shin_l': (0.056, 0.046, kin.SHIN, lea),
        'uarm_r': (0.05, 0.042, kin.UARM, ink), 'uarm_l': (0.05, 0.042, kin.UARM, ink),
        'farm_r': (0.043, 0.036, kin.FARM, lea), 'farm_l': (0.043, 0.036, kin.FARM, lea),
        'neck': (0.045, 0.04, kin.NECK + 0.02, ink),
    }
    for k, (r0, r1, L, m) in spec.items():
        bm = bmesh.new()
        bm_capsule(bm, r0, r1, L)
        parts[k] = mesh_obj(f'{prefix}_{k}', bm, m)
    # torso: X = right, Y = forward, Z = spine
    bm = bmesh.new()
    bm_loft(bm, [(-0.06, 0.14, 0.10, 0, 0), (0.10, 0.125, 0.09, 0, 0.01), (0.26, 0.135, 0.10, 0, 0.02),
                 (0.40, 0.185, 0.11, 0, 0.0), (0.50, 0.15, 0.085, 0, -0.01), (0.56, 0.06, 0.05, 0, 0)], n=18)
    parts['torso'] = mesh_obj(f'{prefix}_torso', bm, ink)
    # pelvis + coat skirt (flared, open-bottomed)
    bm = bmesh.new()
    bm_loft(bm, [(0.08, 0.145, 0.105, 0, 0), (-0.05, 0.165, 0.125, 0, 0.0), (-0.28, 0.2, 0.16, 0, 0.0)],
            n=20, cap=False)
    parts['pelvis'] = mesh_obj(f'{prefix}_pelvis', bm, lea)
    # head (dark face) + hood
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=16, v_segments=12, radius=kin.HEADR)
    parts['head'] = mesh_obj(f'{prefix}_head', bm, MAT['skin'])
    bm = bmesh.new()
    bmesh.ops.create_uvsphere(bm, u_segments=20, v_segments=14, radius=kin.HEADR * 1.32)
    # open the face (local +Y is facing), pull a peak back/up
    kill = [f for f in bm.faces if f.calc_center_median().y > kin.HEADR * 0.55 and
            f.calc_center_median().z < kin.HEADR * 0.9 and f.calc_center_median().z > -kin.HEADR * 1.2]
    bmesh.ops.delete(bm, geom=kill, context='FACES')
    for v in bm.verts:
        if v.co.y < -0.05 and v.co.z > 0.02:
            v.co.y -= 0.06 * (v.co.z / (kin.HEADR * 1.3))
        if v.co.z < -0.06:
            v.co.z -= 0.03
    bmesh.ops.solidify(bm, geom=bm.faces[:], thickness=0.012)
    parts['hood'] = mesh_obj(f'{prefix}_hood', bm, MAT['cloak'])
    # boots (local Z = forward, Y = up)
    for s in 'rl':
        bm = bmesh.new()
        bm_capsule(bm, 0.05, 0.042, 0.17, M=Matrix.Translation((0, -0.03, -0.05)))
        parts['foot_' + s] = mesh_obj(f'{prefix}_foot_{s}', bm, lea)
    # weapon shaft (unit length, scaled on Z), gun block at head, blade
    bm = bmesh.new()
    bmesh.ops.create_cone(bm, cap_ends=True, segments=10, radius1=0.02, radius2=0.02, depth=1.0,
                          matrix=Matrix.Translation((0, 0, 0.5)))
    parts['weapon'] = mesh_obj(f'{prefix}_weapon', bm, MAT['gunmetal'])
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Translation((0.0, 0, -0.22)) @
                          Matrix.Diagonal((0.075, 0.055, 0.42, 1)))
    bmesh.ops.create_cone(bm, cap_ends=True, segments=10, radius1=0.028, radius2=0.026, depth=0.24,
                          matrix=Matrix.Translation((0, 0, 0.05)))
    bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Translation((-0.05, 0, -0.33)) @
                          Matrix.Diagonal((0.04, 0.03, 0.12, 1)))
    parts['gun'] = mesh_obj(f'{prefix}_gun', bm, MAT['gunmetal'], smooth=False)
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0, matrix=Matrix.Translation((0.039, 0, -0.2)) @
                          Matrix.Diagonal((0.004, 0.058, 0.3, 1)))
    parts['accent'] = mesh_obj(f'{prefix}_accent', bm, MAT['accent'], smooth=False)
    # blade crescent in local XZ (X = blade direction, Z = shaft direction)
    bm = bmesh.new()
    spine, edge = [], []
    for i in range(17):
        s = i / 16
        x = kin.BLADE * s
        z = -0.26 * s * s
        th = 0.13 * (1 - s ** 1.3) + 0.004
        spine.append((x, 0, z + th * 0.35))
        edge.append((x, 0, z - th * 0.65))
    verts_f = [bm.verts.new((x, 0.007, z)) for (x, y, z) in spine + edge[::-1]]
    verts_b = [bm.verts.new((x, -0.007, z)) for (x, y, z) in spine + edge[::-1]]
    n = len(verts_f)
    bm.faces.new(verts_f)
    bm.faces.new(list(reversed(verts_b)))
    for i in range(n):
        j = (i + 1) % n
        bm.faces.new((verts_f[i], verts_b[i], verts_b[j], verts_f[j]))
    # knife edge: pinch edge verts to thin
    for v in bm.verts:
        pass
    parts['blade'] = mesh_obj(f'{prefix}_blade', bm, MAT['steel'], smooth=False)
    for ob in parts.values():
        ob.rotation_mode = 'QUATERNION'
    return parts


def build_cloak(prefix='H', cols=11, rows=16, width=0.36, length=1.25):
    """Cloth sheet hanging from the shoulders; top row pinned (follows the torso)."""
    bm = bmesh.new()
    grid = []
    for r in range(rows):
        row = []
        for c in range(cols):
            u = c / (cols - 1) - 0.5
            flare = 1.0 + 1.6 * (r / (rows - 1)) ** 1.3
            x = u * width * flare
            # wrap slightly around the back: y (forward) goes negative at the centre
            y = -0.15 - 0.09 * math.cos(u * math.pi) * (0.4 + r / (rows - 1)) - 0.16 * (r / (rows - 1))
            z = 0.52 - length * r / (rows - 1)
            row.append(bm.verts.new((x, y, z)))
        grid.append(row)
    for r in range(rows - 1):
        for c in range(cols - 1):
            bm.faces.new((grid[r][c], grid[r][c + 1], grid[r + 1][c + 1], grid[r + 1][c]))
    ob = mesh_obj(f'{prefix}_cloak', bm, MAT['cloak'])
    vg = ob.vertex_groups.new(name='pin')
    vg.add([c for c in range(cols)], 1.0, 'REPLACE')
    # shallow pin falloff on the second row helps it hang from the shoulders
    vg.add([cols + c for c in range(cols)], 0.35, 'REPLACE')
    return ob


# ---------------------------------------------------------------------------
# WOLF  (local X = right, Y = forward, Z = up, unit scale)
# ---------------------------------------------------------------------------
def build_wolf(prefix, s=1.0, seed=0):
    rnd = random.Random(seed)
    parts = {}
    wm = MAT['wolf']
    bm = bmesh.new()
    # (y, half-width, half-height, cx, cz): haunch -> deep chest -> thick neck reaching toward the head
    rings = [(-0.66, 0.05, 0.05, 0, 0.14), (-0.58, 0.14, 0.17, 0, 0.10), (-0.42, 0.19, 0.22, 0, 0.06),
             (-0.2, 0.16, 0.2, 0, 0.02), (0.05, 0.17, 0.25, 0, -0.02), (0.3, 0.2, 0.3, 0, -0.02),
             (0.48, 0.18, 0.26, 0, 0.06), (0.62, 0.13, 0.16, 0, 0.16), (0.72, 0.1, 0.12, 0, 0.21)]
    bm_loft_y(bm, rings, n=18)
    # shoulder + haunch muscle masses
    for (x, y, z, r) in [(0.13, 0.42, -0.06, 0.16), (-0.13, 0.42, -0.06, 0.16),
                         (0.14, -0.45, 0.0, 0.18), (-0.14, -0.45, 0.0, 0.18)]:
        bmesh.ops.create_uvsphere(bm, u_segments=12, v_segments=8, radius=r,
                                  matrix=Matrix.Translation((x, y, z)) @ Matrix.Diagonal((0.7, 1.25, 1.3, 1)))
    # ragged fur ridge: many thin swept-back shards along the spine and neck
    for i in range(34):
        u = i / 33
        y = -0.6 + 1.3 * u
        zc = 0.2 + 0.14 * math.sin(math.pi * min(1.0, u * 1.1)) + (0.1 * (u - 0.8) / 0.2 if u > 0.8 else 0)
        h = (0.10 + 0.2 * math.sin(math.pi * u) ** 0.7) * rnd.uniform(0.75, 1.25)
        x = rnd.uniform(-0.09, 0.09)
        M = (Matrix.Translation((x, y, zc)) @ Matrix.Rotation(-0.95 + rnd.uniform(-0.2, 0.2), 4, 'X') @
             Matrix.Rotation(x * 3, 4, 'Y'))
        bm_cone(bm, 0.028, h, M, seg=4)
    parts['body'] = mesh_obj(f'{prefix}_body', bm, wm)
    # head: long wedge skull + snout; origin at the skull base (hinge)
    bm = bmesh.new()
    bm_loft_y(bm, [(-0.14, 0.09, 0.1, 0, 0.0), (0.0, 0.115, 0.115, 0, 0.03), (0.12, 0.09, 0.085, 0, 0.02),
                   (0.3, 0.055, 0.05, 0, -0.02), (0.44, 0.03, 0.03, 0, -0.035), (0.47, 0.012, 0.012, 0, -0.04)], n=12)
    # brow ridge spikes + ears swept back
    for side in (-1, 1):
        bm_cone(bm, 0.045, 0.24, Matrix.Translation((side * 0.06, -0.04, 0.09)) @
                Matrix.Rotation(-1.0, 4, 'X') @ Matrix.Rotation(side * 0.25, 4, 'Y'), seg=5)
        bm_cone(bm, 0.02, 0.1, Matrix.Translation((side * 0.07, 0.08, 0.06)) @
                Matrix.Rotation(-1.2, 4, 'X'), seg=4)
    parts['head'] = mesh_obj(f'{prefix}_head', bm, wm)
    bm = bmesh.new()
    bm_loft_y(bm, [(0.0, 0.07, 0.03, 0, -0.045), (0.2, 0.05, 0.025, 0, -0.06), (0.4, 0.02, 0.015, 0, -0.07)], n=10)
    # teeth
    for i in range(5):
        for side in (-1, 1):
            bm_cone(bm, 0.008, 0.035, Matrix.Translation((side * (0.035 - i * 0.004), 0.08 + i * 0.06, -0.03)), seg=3)
    parts['jaw'] = mesh_obj(f'{prefix}_jaw', bm, [MAT['wolf']][0])
    bm = bmesh.new()
    for side in (-1, 1):
        bmesh.ops.create_uvsphere(bm, u_segments=8, v_segments=6, radius=0.024,
                                  matrix=Matrix.Translation((side * 0.07, 0.13, 0.055)) @
                                  Matrix.Rotation(side * 0.35, 4, 'Z') @ Matrix.Diagonal((0.7, 1.8, 0.5, 1)))
    parts['eyes'] = mesh_obj(f'{prefix}_eyes', bm, MAT['eye'])
    for k in ('fr', 'fl', 'hr', 'hl'):
        hind = k[0] == 'h'
        bm = bmesh.new()
        bm_capsule(bm, 0.1 if hind else 0.085, 0.05, 0.36, seg=10)
        parts['up_' + k] = mesh_obj(f'{prefix}_up_{k}', bm, wm)
        bm = bmesh.new()
        bm_capsule(bm, 0.045, 0.03, 0.40, seg=8)
        # paw with claws, pointing forward (local -X/-Y varies; we use a fixed kink)
        bm_capsule(bm, 0.04, 0.03, 0.11, seg=8, M=Matrix.Translation((0, 0, 0.40)) @ Matrix.Rotation(-1.35, 4, 'X'))
        parts['lo_' + k] = mesh_obj(f'{prefix}_lo_{k}', bm, wm)
    bm = bmesh.new()
    bm_loft_y(bm, [(0.0, 0.06, 0.06, 0, 0), (-0.25, 0.08, 0.06, 0, 0.04), (-0.5, 0.05, 0.04, 0, 0.0),
                   (-0.7, 0.004, 0.004, 0, -0.04)], n=8)
    for i in range(8):
        y = -0.05 - 0.07 * i
        bm_cone(bm, 0.02, 0.09, Matrix.Translation((0, y, 0.05)) @ Matrix.Rotation(-1.1, 4, 'X'), seg=4)
    parts['tail'] = mesh_obj(f'{prefix}_tail', bm, wm)
    for ob in parts.values():
        ob.rotation_mode = 'QUATERNION'
        ob.scale = (s, s, s)
    return parts


# ---------------------------------------------------------------------------
# ENVIRONMENT
# ---------------------------------------------------------------------------
def _tree_mesh(name, rnd, h):
    bm = bmesh.new()

    def limb(p0, d, L, r0, depth):
        d = d.normalized()
        p1 = p0 + d * L
        rot = d.to_track_quat('Z', 'Y').to_matrix().to_4x4()
        bmesh.ops.create_cone(bm, cap_ends=False, segments=6 if depth > 1 else 4, radius1=r0,
                              radius2=r0 * 0.62, depth=L, matrix=Matrix.Translation(p0) @ rot @
                              Matrix.Translation((0, 0, L / 2)))
        if depth <= 0:
            return
        nkids = 2 if depth < 3 else rnd.randint(2, 4)
        for _ in range(nkids):
            nd = (d + Vector((rnd.uniform(-0.9, 0.9), rnd.uniform(-0.9, 0.9), rnd.uniform(-0.1, 0.7)))).normalized()
            limb(p1, nd, L * rnd.uniform(0.5, 0.72), r0 * 0.6, depth - 1)

    r = 0.12 + h * 0.018
    lean = Vector((rnd.uniform(-0.05, 0.05), rnd.uniform(-0.05, 0.05), 1)).normalized()
    # trunk in 3 sections, branches from the upper 2/3
    p = Vector((0, 0, -0.4))
    L = (h + 0.4) / 3
    for sec in range(3):
        limb(p, lean, L, r * (1 - 0.28 * sec), 0)
        p = p + lean * L
        if sec >= 1:
            for _ in range(3):
                d = Vector((rnd.uniform(-1, 1), rnd.uniform(-1, 1), rnd.uniform(0.3, 1.2)))
                limb(p - lean * rnd.uniform(0, L), d, h * rnd.uniform(0.18, 0.28), r * 0.4, 3)
    limb(p, lean, h * 0.2, r * 0.3, 2)
    me = bpy.data.meshes.new(name)
    bm.to_mesh(me)
    bm.free()
    return me


def build_forest(n=260, radius_clear=9.0, radius_max=70.0, seed=3, avoid=None):
    rnd = random.Random(seed)
    variants = [_tree_mesh(f'tree{i}', rnd, rnd.uniform(9, 15)) for i in range(8)]
    for m in variants:
        m.materials.append(MAT['bark'])
    c = coll('Forest')
    placed = 0
    tries = 0
    while placed < n and tries < n * 20:
        tries += 1
        r = radius_clear + (radius_max - radius_clear) * math.sqrt(rnd.random())
        a = rnd.uniform(0, 2 * math.pi)
        x, y = r * math.cos(a), r * math.sin(a)
        if avoid and any((x - ax) ** 2 + (y - ay) ** 2 < ar ** 2 for ax, ay, ar in avoid):
            continue
        ob = bpy.data.objects.new(f'tree_{placed}', rnd.choice(variants))
        ob.location = (x, y, 0)
        ob.rotation_euler = (0, 0, rnd.uniform(0, 6.28))
        sc = rnd.uniform(0.8, 1.25)
        ob.scale = (sc, sc, sc * rnd.uniform(0.9, 1.15))
        c.objects.link(ob)
        placed += 1


def add_tree(x, y, h=12.0, seed=99, name='hero_tree'):
    rnd = random.Random(seed)
    me = _tree_mesh(name, rnd, h)
    me.materials.append(MAT['bark'])
    ob = bpy.data.objects.new(name, me)
    ob.location = (x, y, 0)
    coll('Forest').objects.link(ob)
    return ob


def build_ground(size=240, res=160):
    bm = bmesh.new()
    bmesh.ops.create_grid(bm, x_segments=res, y_segments=res, size=size / 2)
    rnd = random.Random(1)
    ph = [rnd.uniform(0, 6.28) for _ in range(6)]
    for v in bm.verts:
        x, y = v.co.x, v.co.y
        d = math.hypot(x, y)
        amp = min(1.0, max(0.0, (d - 10) / 25))   # keep the arena flat
        v.co.z = amp * (0.9 * math.sin(x * 0.07 + ph[0]) * math.cos(y * 0.06 + ph[1]) +
                        0.4 * math.sin(x * 0.19 + ph[2] + y * 0.13)) + \
            0.03 * math.sin(x * 1.7 + ph[3]) * math.sin(y * 1.3 + ph[4])
    ob = mesh_obj('ground', bm, MAT['snow'], collection='Env')
    return ob


def build_sky(sun_dir_deg=(13.0, 200.0), moon_dist=400.0, moon_r=34.0):
    """Moon (emissive disc far away) + sun light + world + fog volume."""
    elev, az = [a * math.pi / 180 for a in sun_dir_deg]
    to_moon = Vector((math.cos(elev) * math.cos(az), math.cos(elev) * math.sin(az), math.sin(elev)))
    # sun lamp pointing away from the moon
    ld = bpy.data.lights.new('moonlight', 'SUN')
    ld.energy = 4.0
    ld.color = (0.66, 0.76, 1.0)
    ld.angle = 0.6 * math.pi / 180
    if hasattr(ld, 'use_shadow'):
        ld.use_shadow = True
    lo = bpy.data.objects.new('moonlight', ld)
    lo.rotation_mode = 'QUATERNION'
    lo.rotation_quaternion = (-to_moon).to_track_quat('-Z', 'Y')
    coll('Env').objects.link(lo)
    # moon disc
    bm = bmesh.new()
    bmesh.ops.create_circle(bm, cap_ends=True, segments=64, radius=moon_r)
    mo = mesh_obj('moon', bm, MAT['moon'], collection='Env', smooth=False)
    mo.location = to_moon * moon_dist
    mo.rotation_mode = 'QUATERNION'
    mo.rotation_quaternion = (-to_moon).to_track_quat('Z', 'Y')
    mo.visible_shadow = False
    # world: very dark blue with faint gradient
    w = bpy.data.worlds.new('night')
    bpy.context.scene.world = w
    w.use_nodes = True
    nt = w.node_tree
    bg = nt.nodes.get('Background')
    bg.inputs['Color'].default_value = (0.0025, 0.004, 0.009, 1)
    bg.inputs['Strength'].default_value = 1.0
    # fog volume
    bm = bmesh.new()
    bmesh.ops.create_cube(bm, size=1.0)
    fog = mesh_obj('fog', bm, None, collection='Env', smooth=False)
    fog.scale = (150, 150, 40)
    fog.location = (0, 0, 19.5)
    fm = bpy.data.materials.new('fog')
    fm.use_nodes = True
    nt = fm.node_tree
    for n_ in list(nt.nodes):
        nt.nodes.remove(n_)
    pv = nt.nodes.new('ShaderNodeVolumePrincipled')
    pv.inputs['Color'].default_value = (0.5, 0.6, 0.86, 1)
    pv.inputs['Density'].default_value = 0.0095
    pv.inputs['Anisotropy'].default_value = 0.72
    out = nt.nodes.new('ShaderNodeOutputMaterial')
    nt.links.new(pv.outputs[0], out.inputs['Volume'])
    fog.data.materials.append(fm)
    return to_moon, lo, fog, pv


def render_settings(res=(1920, 1080), pct=100, samples=48, mblur=True):
    sc = bpy.context.scene
    r = sc.render
    r.engine = 'BLENDER_EEVEE'
    r.resolution_x, r.resolution_y = res
    r.resolution_percentage = pct
    r.fps = 24
    r.use_motion_blur = mblur
    r.motion_blur_shutter = 0.5
    r.film_transparent = False
    r.image_settings.file_format = 'PNG'
    r.image_settings.color_depth = '16'
    ee = sc.eevee
    ee.taa_render_samples = samples
    ee.volumetric_start = 0.5
    ee.volumetric_end = 70.0
    ee.volumetric_tile_size = '4'
    ee.volumetric_samples = 96
    ee.volumetric_sample_distribution = 0.85
    ee.use_volumetric_shadows = True
    ee.volumetric_shadow_samples = 16
    ee.use_raytracing = False   # Metal compiler bug on macOS 13 w/ raytracing shaders
    ee.use_shadows = True
    ee.shadow_resolution_scale = 1.0
    sc.view_settings.view_transform = 'AgX'
    try:
        sc.view_settings.look = 'AgX - Medium High Contrast'
    except Exception:
        pass
    sc.view_settings.exposure = 0.0


def make_camera(name='cam', lens=35.0):
    cd = bpy.data.cameras.new(name)
    cd.lens = lens
    cd.sensor_width = 36
    cd.dof.use_dof = True
    cd.dof.aperture_fstop = 2.8
    cd.clip_start = 0.05
    cd.clip_end = 600
    co = bpy.data.objects.new(name, cd)
    co.rotation_mode = 'QUATERNION'
    coll('Env').objects.link(co)
    bpy.context.scene.camera = co
    return co


def look_quat(eye, target, roll=0.0):
    d = (Vector(target) - Vector(eye)).normalized()
    q = d.to_track_quat('-Z', 'Y')
    if roll:
        q = q @ Quaternion((0, 0, 1), roll)
    return q


# ---------------------------------------------------------------------------
# keyframing (fast): write per-frame loc/quat arrays to fcurves
# ---------------------------------------------------------------------------
def key_transforms(ob, frames, locs, quats=None, scales=None):
    ad = ob.animation_data_create()
    act = bpy.data.actions.new(ob.name + '_act')
    ad.action = act
    n = len(frames)

    def curve(path, idx, vals):
        try:
            fc = act.fcurves.new(path, index=idx)
        except AttributeError:
            fc = act.fcurve_ensure_for_datablock(ob, path, index=idx)
        fc.keyframe_points.add(n)
        co = [0.0] * (2 * n)
        co[0::2] = frames
        co[1::2] = vals
        fc.keyframe_points.foreach_set('co', co)
        fc.keyframe_points.foreach_set('interpolation', [0] * n)   # CONSTANT? set linear below
        for kp in fc.keyframe_points:
            kp.interpolation = 'LINEAR'
        fc.update()
    for i in range(3):
        curve('location', i, [float(l[i]) for l in locs])
    if quats is not None:
        for i in range(4):
            curve('rotation_quaternion', i, [float(q[i]) for q in quats])
    if scales is not None:
        for i in range(3):
            curve('scale', i, [float(s[i]) for s in scales])
