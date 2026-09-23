"""EMBER II — 3D kinematics (pure Python + numpy; runs inside or outside Blender).

World convention: Blender's.  Z is up, ground at z=0, metres.
A character's pose lives in its sagittal frame: a = forward, b = up, c = right,
rotated into the world by heading (yaw), pitch (flips) and roll (side lean).
"""
import math
import numpy as np

PI = math.pi
D2R = PI / 180.0
UP = np.array([0.0, 0.0, 1.0])


def v3(x, y, z):
    return np.array([x, y, z], float)


def norm(v):
    n = np.linalg.norm(v)
    return v / n if n > 1e-12 else v


def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def lerp(a, b, u):
    return a + (b - a) * u


def smooth(u):
    u = clamp(u)
    return u * u * (3 - 2 * u)


def rot_axis(axis, ang):
    """Rotation matrix about unit axis (Rodrigues)."""
    axis = norm(axis)
    x, y, z = axis
    c, s = math.cos(ang), math.sin(ang)
    C = 1 - c
    return np.array([[c + x * x * C, x * y * C - z * s, x * z * C + y * s],
                     [y * x * C + z * s, c + y * y * C, y * z * C - x * s],
                     [z * x * C - y * s, z * y * C + x * s, c + z * z * C]])


def frame_from(zdir, xref):
    """Orthonormal basis with Z along zdir and X as close as possible to xref."""
    z = norm(zdir)
    x = xref - np.dot(xref, z) * z
    if np.linalg.norm(x) < 1e-6:
        x = np.cross(z, UP if abs(z[2]) < 0.9 else v3(1, 0, 0))
    x = norm(x)
    y = np.cross(z, x)
    return np.stack([x, y, z], 1)   # columns


def mat_to_quat(m):
    t = m[0, 0] + m[1, 1] + m[2, 2]
    if t > 0:
        s = math.sqrt(t + 1.0) * 2
        return (0.25 * s, (m[2, 1] - m[1, 2]) / s, (m[0, 2] - m[2, 0]) / s, (m[1, 0] - m[0, 1]) / s)
    if m[0, 0] > m[1, 1] and m[0, 0] > m[2, 2]:
        s = math.sqrt(1.0 + m[0, 0] - m[1, 1] - m[2, 2]) * 2
        return ((m[2, 1] - m[1, 2]) / s, 0.25 * s, (m[0, 1] + m[1, 0]) / s, (m[0, 2] + m[2, 0]) / s)
    if m[1, 1] > m[2, 2]:
        s = math.sqrt(1.0 + m[1, 1] - m[0, 0] - m[2, 2]) * 2
        return ((m[0, 2] - m[2, 0]) / s, (m[0, 1] + m[1, 0]) / s, 0.25 * s, (m[1, 2] + m[2, 1]) / s)
    s = math.sqrt(1.0 + m[2, 2] - m[0, 0] - m[1, 1]) * 2
    return ((m[1, 0] - m[0, 1]) / s, (m[0, 2] + m[2, 0]) / s, (m[1, 2] + m[2, 1]) / s, 0.25 * s)


def ik2(A, T, l1, l2, pole):
    """Two-bone IK in 3D. Joint bends toward `pole` (a direction)."""
    d = T - A
    L = np.linalg.norm(d)
    L = clamp(L, abs(l1 - l2) + 1e-3, l1 + l2 - 1e-3)
    dn = norm(d)
    ca = (l1 * l1 + L * L - l2 * l2) / (2 * l1 * L)
    a = math.acos(clamp(ca, -1, 1))
    p = pole - np.dot(pole, dn) * dn
    if np.linalg.norm(p) < 1e-6:
        p = np.cross(dn, UP if abs(dn[2]) < 0.9 else v3(1, 0, 0))
    p = norm(p)
    J = A + l1 * (math.cos(a) * dn + math.sin(a) * p)
    E = A + L * dn
    return J, E


# ---------------------------------------------------------------------------
# Hero
# ---------------------------------------------------------------------------
THIGH, SHIN = 0.44, 0.44
TORSO, NECK, HEADR = 0.50, 0.09, 0.105
UARM, FARM = 0.29, 0.27
SHAFT, BLADE = 1.70, 0.92
HIP_W, SH_W = 0.10, 0.17

POSE0 = dict(
    lean=5.0, side=0.0, twist=0.0, head=0.0, head_yaw=0.0,
    # weapon: grip rel. chest (a fwd, b up, c right), angle in plane, plane tilt
    wa=80.0, wtilt=0.0, wx=0.28, wy=-0.25, wz=0.10, g1=0.35, g2=0.62, two=1.0,
    bside=1.0, held=1.0, unfold=1.0,
    hx=0.2, hy=-0.35, hz=-0.2,           # free (left) hand target rel chest
    h1x=0.1, h1y=-0.45, h1z=0.2,         # free (right) hand when weapon stowed
    fx1=0.12, fz1=0.12, fy1=-0.86,       # right foot rel pelvis (a, c, b)
    fx2=-0.12, fz2=-0.12, fy2=-0.86,     # left foot
    gnd=1.0,
    yaw=0.0, pitch=0.0, roll=0.0, sq=1.0,
)


class Hero:
    """Evaluated hero skeleton in world space.

    Joints are numpy vec3.  `segments` lists (name, A, B, ref) for rendering.
    """

    def __init__(self, p, root, feet=None):
        self.p = p
        R = v3(*root)
        yaw = p['yaw'] * D2R
        f0 = v3(math.cos(yaw), math.sin(yaw), 0.0)
        r0 = np.cross(f0, UP)
        M = np.stack([f0, r0, UP], 1)                                 # a,c,b -> world
        M = rot_axis(r0, -p['pitch'] * D2R) @ M                        # pitch: + = forward flip
        M = rot_axis(M[:, 0], p['roll'] * D2R) @ M
        sq = p['sq']
        S = np.diag([1 / math.sqrt(sq), 1 / math.sqrt(sq), sq])
        self.M = M
        self.R = R
        f, r, u = M[:, 0], M[:, 1], M[:, 2]
        self.fwd, self.right, self.up = f, r, u

        def W(a, b, c=0.0):
            return R + M @ (S @ v3(a, c, b))
        self.W = W

        lean = p['lean'] * D2R
        side = p['side'] * D2R
        twist = p['twist'] * D2R
        # spine
        cl = v3(TORSO * math.sin(lean), TORSO * math.sin(side), TORSO * math.cos(lean) * math.cos(side))
        self.pelvis = W(0, 0)
        self.chest = W(cl[0], cl[2], cl[1])
        # chest frame (twisted around the spine)
        spine = norm(self.chest - self.pelvis)
        cf = rot_axis(spine, -twist) @ f
        cf = norm(cf - np.dot(cf, spine) * spine)
        cr = np.cross(cf, spine)
        self.chest_f, self.chest_r, self.spine = cf, cr, spine
        hd = lean + p['head'] * D2R
        hdir = norm(math.cos(hd - lean) * spine + math.sin(hd - lean) * cf)
        hdir = rot_axis(spine, -p['head_yaw'] * D2R) @ hdir
        self.neck = self.chest + spine * 0.04
        self.head = self.neck + hdir * (NECK + HEADR)
        self.head_dir = hdir
        self.head_fwd = norm(np.cross(hdir, cr)) * -1 if False else norm(rot_axis(spine, -p['head_yaw'] * D2R) @ cf)
        self.sh_r = self.chest + cr * SH_W - spine * 0.05
        self.sh_l = self.chest - cr * SH_W - spine * 0.05
        self.hip_r = self.pelvis + r * HIP_W
        self.hip_l = self.pelvis - r * HIP_W

        def C(a, b, c):
            """Point relative to chest in chest frame."""
            return self.chest + cf * a + spine * b + cr * c

        # --- weapon ---
        held = clamp(p['held'])
        ext = lerp(0.42, 1.0, smooth(p['unfold']))
        Ls = SHAFT * ext
        tilt = p['wtilt'] * D2R
        e1 = cf
        e2 = math.cos(tilt) * spine + math.sin(tilt) * cr
        wa = p['wa'] * D2R
        u_hand = math.cos(wa) * e1 + math.sin(wa) * e2
        g_hand = C(p['wx'], p['wy'], p['wz'])
        # stowed across the back
        g_back = C(-0.17, -0.15, 0.0)
        u_back = norm(-0.55 * spine + 0.83 * cr + 0.0 * cf)
        u = norm(lerp(u_back, u_hand, smooth(held)))
        g = lerp(g_back, g_hand, smooth(held))
        n_plane = np.cross(e1, e2)
        vb = norm(np.cross(n_plane, u)) * (1.0 if p['bside'] >= 0 else -1.0)
        if held < 0.5:
            vb = norm(-cf - np.dot(-cf, u) * u)
        butt = g - u * p['g1'] * Ls
        headp = butt + u * Ls
        self.w_u, self.w_v, self.w_len = u, vb, Ls
        self.w_butt, self.w_head, self.w_grip = butt, headp, g
        self.muzzle = headp + u * 0.10
        # blade: unfolds from lying along -u to pointing along vb, curving back
        ua = lerp(PI * 0.96, PI * 0.5, smooth(p['unfold']))
        self.blade_axis_ang = ua
        bdir = norm(math.cos(ua) * u + math.sin(ua) * vb)
        self.blade_dir = bdir
        pts = []
        for i in range(9):
            s = i / 8
            pts.append(headp + bdir * BLADE * s - u * 0.26 * s * s * smooth(p['unfold']))
        self.blade = pts
        self.blade_tip = pts[-1]
        # --- arms ---
        g2p = butt + u * p['g2'] * Ls
        two = clamp(p['two']) * held
        h_r = lerp(C(p['h1x'], p['h1y'], p['h1z']), g, held)
        h_l = lerp(C(p['hx'], p['hy'], p['hz']), g2p, two)
        pole_r = -cf * 0.6 - spine * 0.6 + cr * 0.5
        pole_l = -cf * 0.6 - spine * 0.6 - cr * 0.5
        self.elb_r, self.hand_r = ik2(self.sh_r, h_r, UARM, FARM, pole_r)
        self.elb_l, self.hand_l = ik2(self.sh_l, h_l, UARM, FARM, pole_l)
        # --- legs ---
        g_ = clamp(p['gnd'])
        f_r = W(p['fx1'], p['fy1'], p['fz1'])
        f_l = W(p['fx2'], p['fy2'], p['fz2'])
        f_r[2] = lerp(f_r[2], 0.06, g_)
        f_l[2] = lerp(f_l[2], 0.06, g_)
        if feet:
            if feet.get('r') is not None:
                f_r = feet['r']
            if feet.get('l') is not None:
                f_l = feet['l']
        self.f_r_target, self.f_l_target = f_r, f_l
        self.knee_r, self.foot_r = ik2(self.hip_r, f_r, THIGH, SHIN, f + r * 0.15)
        self.knee_l, self.foot_l = ik2(self.hip_l, f_l, THIGH, SHIN, f - r * 0.15)
        self.segments = [
            ('thigh_r', self.hip_r, self.knee_r, r), ('shin_r', self.knee_r, self.foot_r, r),
            ('thigh_l', self.hip_l, self.knee_l, r), ('shin_l', self.knee_l, self.foot_l, r),
            ('uarm_r', self.sh_r, self.elb_r, cr), ('farm_r', self.elb_r, self.hand_r, cr),
            ('uarm_l', self.sh_l, self.elb_l, cr), ('farm_l', self.elb_l, self.hand_l, cr),
            ('torso', self.pelvis, self.chest, cr), ('neck', self.chest, self.head, cr),
        ]
        # feet point along body forward (flattened)
        ff = f.copy()
        ff[2] *= 0.3
        self.foot_fwd = norm(ff)

    def transforms(self):
        """name -> (location, quaternion wxyz) for every rigid part."""
        out = {}
        for name, A, B, ref in self.segments:
            m = frame_from(B - A, ref)
            out[name] = (A, mat_to_quat(m))
        # head: Z = head_dir, Y = facing
        m = frame_from(self.head_dir, self.chest_r)
        out['head'] = (self.head, mat_to_quat(m))
        out['hood'] = out['head']
        for s, P in (('r', self.foot_r), ('l', self.foot_l)):
            m = frame_from(self.foot_fwd, np.cross(self.foot_fwd, UP) * -1)
            out['foot_' + s] = (P, mat_to_quat(m))
        # pelvis block (skirt): Z = up-spine, X = right
        out['pelvis'] = (self.pelvis, mat_to_quat(frame_from(self.spine, self.chest_r)))
        # weapon: Z along shaft from butt, X = blade side
        out['weapon'] = (self.w_butt, mat_to_quat(frame_from(self.w_u, self.w_v)))
        # blade pivots at head; its local X = blade direction, Z = shaft dir
        bz = self.w_u
        out['blade'] = (self.w_head, mat_to_quat(frame_from(bz, self.blade_dir)))
        return out


# ---------------------------------------------------------------------------
# Wolf
# ---------------------------------------------------------------------------
class Wolf:
    """Evaluated wolf.  Body frame: a = forward, b = up, c = right."""
    ANCH = {'fr': (0.42, -0.08, 0.14), 'fl': (0.42, -0.08, -0.14),
            'hr': (-0.42, -0.06, 0.15), 'hl': (-0.42, -0.06, -0.15)}
    OFFS = {'fr': 0.0, 'fl': 0.18, 'hr': 0.55, 'hl': 0.72}

    def __init__(self, pos, heading, s=1.0, pitch=0.0, roll=0.0, phase=0.0, mode='run', jaw=0.0,
                 t=0.0, seed=0, paw_override=None, gait_amp=1.0, M=None, head_pitch=0.0, head_yaw=0.0):
        self.s = s
        if M is None:
            f0 = v3(math.cos(heading), math.sin(heading), 0.0)
            r0 = np.cross(f0, UP)
            M = np.stack([f0, r0, UP], 1)
            M = rot_axis(r0, -pitch * D2R) @ M
            M = rot_axis(M[:, 0], roll * D2R) @ M
        self.head_pitch, self.head_yaw = head_pitch, head_yaw
        self.M = M
        self.P = v3(*pos)
        self.f, self.r, self.u = M[:, 0], M[:, 1], M[:, 2]
        self.jaw = jaw

        def W(a, b, c=0.0):
            return self.P + M @ (v3(a, c, b) * s)
        self.W = W
        ph = phase * 2 * PI
        legs = {}
        for k, (ax, ay, az) in self.ANCH.items():
            A = W(ax, ay, az)
            if mode == 'run':
                pk = ph + self.OFFS[k] * 2 * PI
                pa = (ax + 0.36 * math.cos(pk) * gait_amp, ay - 0.72 + max(0.0, 0.24 * math.sin(pk)) * gait_amp, az)
            elif mode == 'walk':
                pk = ph + self.OFFS[k] * 2 * PI * (1 if k[0] == 'f' else 0.5)
                pa = (ax + 0.2 * math.cos(pk), ay - 0.72 + max(0.0, 0.12 * math.sin(pk)), az)
            elif mode == 'leap':
                pa = (ax + (0.55 if k[0] == 'f' else -0.55), ay - (0.25 if k[0] == 'f' else 0.35), az)
            elif mode == 'crouch':
                pa = (ax + (0.15 if k[0] == 'f' else -0.05), ay - 0.48, az * 1.3)
            elif mode == 'limp':
                w = t * 9 + self.OFFS[k] * 5
                pa = (ax + 0.35 * math.cos(w), ay - 0.4 + 0.2 * math.sin(w * 1.3), az * 1.6)
            else:  # stand
                pa = (ax + (0.05 if k[0] == 'f' else 0.0), ay - 0.72, az)
            T = W(*[pa[0], pa[1], pa[2]])
            if paw_override and k in paw_override:
                T = v3(*paw_override[k])
            front = k[0] == 'f'
            # front legs: elbow bends back; hind: knee forward
            pole = (-self.f if front else self.f) - self.u * 0.2
            J, E = ik2(A, T, 0.36 * s, 0.40 * s, pole)
            legs[k] = (A, J, E)
        self.legs = legs
        self.neck = W(0.55, 0.12)
        self.headp = W(0.72, 0.22)

    def transforms(self):
        # all wolf parts: local X = right, Y = forward, Z = up
        out = {'body': (self.P, mat_to_quat(frame_from(self.u, self.r)))}
        # head (with jaw child keyed separately)
        Hm = rot_axis(self.u, self.head_yaw * D2R) @ rot_axis(self.r, -self.head_pitch * D2R) @ frame_from(self.u, self.r)
        out['head'] = (self.headp, mat_to_quat(Hm))
        out['eyes'] = out['head']
        out['jaw'] = (self.headp, mat_to_quat(rot_axis(Hm[:, 0], self.jaw * 0.55) @ Hm))
        out['tail'] = (self.W(-0.62, 0.12), mat_to_quat(frame_from(self.u, self.r)))
        for k, (A, J, E) in self.legs.items():
            out['up_' + k] = (A, mat_to_quat(frame_from(J - A, self.r)))
            out['lo_' + k] = (J, mat_to_quat(frame_from(E - J, self.r)))
        return out
