"""Character rigs: the Ember huntress (IK biped + gun-scythe) and void wolves."""
import math
import cairo
from common import *

PI = math.pi
D2R = PI / 180

# --- palette --------------------------------------------------------------
INK = (0.030, 0.034, 0.050)
INK2 = (0.055, 0.060, 0.085)
RIM = (0.55, 0.66, 0.85)
EMBER = (0.86, 0.22, 0.14)
EMBER_D = (0.45, 0.07, 0.06)
EMBER_HOT = (1.0, 0.62, 0.30)
VOID_EYE = (0.75, 0.95, 1.0)
STEEL = (0.20, 0.22, 0.28)

# --- hero dimensions ------------------------------------------------------
THIGH, SHIN = 0.45, 0.45
TORSO, NECK, HEADR = 0.50, 0.10, 0.115
UARM, FARM = 0.29, 0.28
SHAFT, BLADE = 1.70, 0.95


def ik2(ax, ay, tx, ty, l1, l2, bend):
    dx, dy = tx - ax, ty - ay
    d = math.hypot(dx, dy)
    d = clamp(d, abs(l1 - l2) + 1e-3, l1 + l2 - 1e-3)
    a = math.atan2(dy, dx)
    c = (l1 * l1 + d * d - l2 * l2) / (2 * l1 * d)
    A = math.acos(clamp(c, -1, 1))
    ang = a + bend * A
    j = (ax + l1 * math.cos(ang), ay + l1 * math.sin(ang))
    e = (ax + d * math.cos(a), ay + d * math.sin(a))
    return j, e


POSE0 = dict(lean=5, head=0, wx=0.30, wy=-0.25, wa=80, g1=0.35, g2=0.62, two=1.0,
             hx=0.25, hy=-0.35, h1x=0.1, h1y=-0.45, held=1.0, bside=1.0,
             fx1=0.18, fy1=-0.88, fx2=-0.18, fy2=-0.88, gnd=1.0,
             unfold=1.0, rot=0.0, sq=1.0, face=1.0)


class HeroPose:
    """Evaluated skeleton in WORLD coordinates."""

    def __init__(self, p, root):
        self.p = p
        rx, ry = root
        face = 1.0 if p['face'] >= 0 else -1.0
        self.face = face
        rot = p['rot'] * D2R
        cr, sr = math.cos(rot), math.sin(rot)
        sq = p['sq']
        sx = 1 / math.sqrt(sq)

        def W(x, y):
            x, y = x * sx, y * sq
            x, y = cr * x - sr * y, sr * x + cr * y
            return (rx + face * x, ry + y)
        self.W = W
        lean = p['lean'] * D2R
        chest = (TORSO * math.sin(lean), TORSO * math.cos(lean))
        hd = (lean + p['head'] * D2R)
        headc = (chest[0] + (NECK + HEADR) * math.sin(hd), chest[1] + (NECK + HEADR) * math.cos(hd))
        self.lchest = chest
        self.pelvis = W(0, 0)
        self.chest = W(*chest)
        self.head = W(*headc)
        self.head_ang = hd
        self.lean = lean
        # shoulders / hips
        self.sh_n = W(chest[0] + 0.02, chest[1] - 0.04)
        self.sh_f = W(chest[0] - 0.05, chest[1] - 0.02)
        self.hip_n = W(0.03, 0.0)
        self.hip_f = W(-0.04, 0.02)
        # weapon
        held = clamp(p['held'])
        ext = lerp(0.42, 1.0, smooth(p['unfold']))
        Ls = SHAFT * ext
        back_g = (chest[0] - 0.16, chest[1] - 0.18)
        gx = lerp(back_g[0], chest[0] + p['wx'], held)
        gy = lerp(back_g[1], chest[1] + p['wy'], held)
        wa = lerp(-35 + p['lean'] * -1, p['wa'], held) * D2R
        ux, uy = math.cos(wa), math.sin(wa)
        butt = (gx - ux * p['g1'] * Ls, gy - uy * p['g1'] * Ls)
        headw = (butt[0] + ux * Ls, butt[1] + uy * Ls)
        self.w_butt = W(*butt)
        self.w_head = W(*headw)
        self.w_grip = W(gx, gy)
        g2 = (butt[0] + ux * p['g2'] * Ls, butt[1] + uy * p['g2'] * Ls)
        # blade: perpendicular at head, curving back toward the butt
        side = 1.0 if p['bside'] >= 0 else -1.0
        bang = lerp(PI * 0.97, PI * 0.5, smooth(p['unfold']))  # angle from +u toward side
        self.blade_pts_local = []
        for i in range(9):
            s = i / 8
            L = BLADE * s
            a = wa + side * (bang + s * 0.55)          # curve back toward butt
            bx = headw[0] + L * math.cos(wa + side * bang) + 0.28 * s * s * math.cos(wa + PI) * (smooth(p['unfold']))
            by = headw[1] + L * math.sin(wa + side * bang) + 0.28 * s * s * math.sin(wa + PI) * (smooth(p['unfold']))
            self.blade_pts_local.append((bx, by))
        self.blade = [W(*q) for q in self.blade_pts_local]
        self.blade_tip = self.blade[-1]
        self.u = (headw[0] - butt[0], headw[1] - butt[1])
        self.muzzle = W(headw[0] + ux * 0.12, headw[1] + uy * 0.12)
        mz2 = W(headw[0] + ux * 0.5, headw[1] + uy * 0.5)
        self.muzzle_dir = (mz2[0] - self.muzzle[0], mz2[1] - self.muzzle[1])
        self.side = side
        self.unfold = p['unfold']
        self.wa = wa
        self.Ls = Ls
        self.W_local_w = (gx, gy)
        # hands
        h1 = (lerp(chest[0] + p['h1x'], gx, held), lerp(chest[1] + p['h1y'], gy, held))
        two = clamp(p['two']) * held
        h2 = (lerp(chest[0] + p['hx'], g2[0], two), lerp(chest[1] + p['hy'], g2[1], two))
        self.hand_n_t = W(*h1)
        self.hand_f_t = W(*h2)
        self.elb_n, self.hand_n = ik2(*self.sh_n, *self.hand_n_t, UARM, FARM, -face * (1 if cr >= -0.2 else -1))
        self.elb_f, self.hand_f = ik2(*self.sh_f, *self.hand_f_t, UARM, FARM, -face * (1 if cr >= -0.2 else -1))
        # feet (IK in world, optional ground clamp)
        f1 = W(p['fx1'], p['fy1'])
        f2 = W(p['fx2'], p['fy2'])
        g = clamp(p['gnd'])
        f1 = (f1[0], lerp(f1[1], 0.04, g))
        f2 = (f2[0], lerp(f2[1], 0.04, g))
        kb = face * (1 if cr > -0.2 else -1)
        self.knee_n, self.foot_n = ik2(*self.hip_n, *f1, THIGH, SHIN, kb)
        self.knee_f, self.foot_f = ik2(*self.hip_f, *f2, THIGH, SHIN, kb)
        # cloak anchors (local -> world), back shoulder to front shoulder
        self.cloak_anchor = [W(chest[0] - 0.13 + 0.035 * i, chest[1] + 0.03 - 0.012 * abs(i - 2)) for i in range(5)]
        self.rot = rot


# --- drawing helpers -------------------------------------------------------
def capsule(ctx, a, ra, b, rb):
    ang = math.atan2(b[1] - a[1], b[0] - a[0])
    ctx.new_sub_path()
    ctx.arc(a[0], a[1], ra, ang + PI / 2, ang + 3 * PI / 2)
    ctx.arc(b[0], b[1], rb, ang - PI / 2, ang + PI / 2)
    ctx.close_path()


def _ccw(pts):
    a = 0.0
    for i in range(len(pts)):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % len(pts)]
        a += x1 * y2 - x2 * y1
    return pts if a >= 0 else pts[::-1]


def poly(ctx, pts):
    pts = _ccw(list(pts))
    ctx.new_sub_path()
    ctx.move_to(*pts[0])
    for q in pts[1:]:
        ctx.line_to(*q)
    ctx.close_path()


def smooth_poly(ctx, pts, closed=True):
    """Catmull-Rom through pts as bezier."""
    n = len(pts)
    if n < 3:
        poly(ctx, pts)
        return
    if closed:
        pts = _ccw(list(pts))
    ctx.new_sub_path()
    ctx.move_to(*pts[0])
    rng_ = range(n) if closed else range(n - 1)
    for i in rng_:
        p0 = pts[(i - 1) % n] if closed or i > 0 else pts[i]
        p1 = pts[i]
        p2 = pts[(i + 1) % n]
        p3 = pts[(i + 2) % n] if closed or i + 2 < n else p2
        c1 = (p1[0] + (p2[0] - p0[0]) / 6, p1[1] + (p2[1] - p0[1]) / 6)
        c2 = (p2[0] - (p3[0] - p1[0]) / 6, p2[1] - (p3[1] - p1[1]) / 6)
        ctx.curve_to(*c1, *c2, *p2)
    if closed:
        ctx.close_path()


def hero_body_path(ctx, P, include_near=True, include_far=True):
    """Silhouette of the body (no cloak / weapon)."""
    if include_far:
        capsule(ctx, P.hip_f, 0.075, P.knee_f, 0.055)
        capsule(ctx, P.knee_f, 0.055, P.foot_f, 0.042)
        capsule(ctx, P.sh_f, 0.05, P.elb_f, 0.04)
        capsule(ctx, P.elb_f, 0.04, P.hand_f, 0.035)
    # torso
    W = P.W
    c = P.lchest
    lean = P.lean
    nx, ny = math.cos(lean), -math.sin(lean)  # local normal (forward)
    tor = [W(0.12, 0.02), W(c[0] * 0.5 + 0.09 * nx, c[1] * 0.5 + 0.09 * ny),
           W(c[0] + 0.12 * nx, c[1] + 0.12 * ny - 0.02), W(c[0] + 0.02, c[1] + 0.06),
           W(c[0] - 0.12 * nx, c[1] - 0.12 * ny), W(c[0] * 0.5 - 0.08 * nx, c[1] * 0.5 - 0.08 * ny),
           W(-0.13, 0.03)]
    smooth_poly(ctx, tor)
    # skirt
    sk = [W(0.13, 0.05), W(0.21, -0.28), W(0.05, -0.24), W(-0.08, -0.30), W(-0.24, -0.25), W(-0.14, 0.05)]
    poly(ctx, sk)
    # neck + head
    capsule(ctx, P.chest, 0.05, P.head, 0.05)
    ctx.new_sub_path()
    ctx.arc(P.head[0], P.head[1], HEADR, 0, 2 * PI)
    if include_near:
        capsule(ctx, P.hip_n, 0.08, P.knee_n, 0.058)
        capsule(ctx, P.knee_n, 0.058, P.foot_n, 0.044)
        # boot toe
        capsule(ctx, P.foot_n, 0.045, (P.foot_n[0] + 0.1 * P.face * math.cos(P.rot), P.foot_n[1] + 0.1 * math.sin(P.rot) * P.face), 0.03)


def hero_arms_near(ctx, P):
    capsule(ctx, P.sh_n, 0.052, P.elb_n, 0.042)
    capsule(ctx, P.elb_n, 0.042, P.hand_n, 0.038)


def hood_path(ctx, P):
    hx, hy = P.head
    a = P.head_ang
    # hood: slightly larger than head, peak trailing back
    back = (-math.cos(a) * P.face, math.sin(a))  # not exact; hood peak trails behind
    fx, fy = P.face * math.sin(a), math.cos(a)
    pts = []
    for i in range(14):
        th = i / 13 * 2 * PI
        r = HEADR * 1.28
        pts.append((hx + r * math.cos(th), hy + r * math.sin(th)))
    # peak
    px = hx - P.face * 0.22 * math.cos(a) - fx * 0.02
    py = hy + 0.04 - 0.1 * math.sin(abs(a))
    ctx.new_sub_path()
    ctx.arc(hx, hy, HEADR * 1.3, 0, 2 * PI)
    poly(ctx, [(hx + fy * 0.1 * P.face * 0 - P.face * 0.02, hy + HEADR * 1.2),
               (px, py), (hx - P.face * 0.05, hy - HEADR * 1.1)])


def weapon_path(ctx, P):
    # shaft
    b, h = P.w_butt, P.w_head
    capsule(ctx, b, 0.022, h, 0.022)
    # receiver block near head
    ux, uy = (h[0] - b[0]) / P.Ls, (h[1] - b[1]) / P.Ls
    vx, vy = -uy, ux
    c = (h[0] - ux * 0.22, h[1] - uy * 0.22)
    r = [(c[0] + ux * 0.2 + vx * 0.055, c[1] + uy * 0.2 + vy * 0.055),
         (c[0] - ux * 0.2 + vx * 0.055, c[1] - uy * 0.2 + vy * 0.055),
         (c[0] - ux * 0.2 - vx * 0.06, c[1] - uy * 0.2 - vy * 0.06),
         (c[0] + ux * 0.2 - vx * 0.06, c[1] + uy * 0.2 - vy * 0.06)]
    poly(ctx, r)
    # barrel extension
    capsule(ctx, h, 0.03, P.muzzle, 0.028)


def blade_path(ctx, P):
    """Crescent: outer (spine) and inner (edge) curves."""
    pts = P.blade
    n = len(pts)
    spine = []
    edge = []
    for i, q in enumerate(pts):
        if i < n - 1:
            dx, dy = pts[i + 1][0] - q[0], pts[i + 1][1] - q[1]
        else:
            dx, dy = q[0] - pts[i - 1][0], q[1] - pts[i - 1][1]
        L = math.hypot(dx, dy) + 1e-9
        nx, ny = -dy / L, dx / L
        # thickness tapers to point
        th = 0.11 * (1 - (i / (n - 1)) ** 1.4) + 0.004
        # normal toward the shaft side (edge) vs away (spine)
        hx, hy = P.w_head
        side = 1 if (nx * (P.w_butt[0] - hx) + ny * (P.w_butt[1] - hy)) > 0 else -1
        spine.append((q[0] - side * nx * th * 0.35, q[1] - side * ny * th * 0.35))
        edge.append((q[0] + side * nx * th * 0.65, q[1] + side * ny * th * 0.65))
    return spine, edge


def draw_hero(ctx, P, glow=None, rim_off=(0.022, 0.018), rim=RIM, ink=INK, alpha=1.0,
              cloak=None, ghost=None):
    """Draw hero silhouette with rim light. cloak: list of polys (world)."""
    def cloak_fill(col, dx=0, dy=0):
        if cloak:
            for pts in cloak:
                smooth_poly(ctx, [(x + dx, y + dy) for x, y in pts])
            ctx.set_source_rgba(*col, alpha)
            ctx.fill()

    if ghost is not None:
        # single-color afterimage
        if cloak:
            for pts in cloak:
                smooth_poly(ctx, pts)
        hero_body_path(ctx, P)
        hood_path(ctx, P)
        weapon_path(ctx, P)
        spine, edge = blade_path(ctx, P)
        poly(ctx, spine + edge[::-1])
        ctx.set_source_rgba(*ghost, alpha)
        ctx.fill()
        return

    ox, oy = rim_off
    # --- cloak (behind everything) ---
    cloak_fill(tuple(min(1, c * 1.4 + 0.1) for c in EMBER), ox, oy)
    cloak_fill(EMBER_D)
    if cloak:
        # lit inner gradient: fake by drawing a smaller offset version
        ctx.save()
        for pts in cloak:
            smooth_poly(ctx, pts)
        ctx.clip()
        for pts in cloak:
            smooth_poly(ctx, [(x + ox * 1.5, y + oy * 1.5) for x, y in pts])
        ctx.set_source_rgba(*EMBER, alpha * 0.85)
        ctx.fill()
        ctx.restore()

    def full(dx, dy, col):
        ctx.save()
        ctx.translate(dx, dy)
        hero_body_path(ctx, P)
        ctx.set_source_rgba(*col, alpha)
        ctx.fill()
        ctx.restore()

    stowed = P.p['held'] < 0.5

    def weapon_all():
        ctx.save()
        ctx.translate(ox * 0.8, oy * 0.8)
        weapon_path(ctx, P)
        ctx.set_source_rgba(*rim, alpha)
        ctx.fill()
        ctx.restore()
        weapon_path(ctx, P)
        ctx.set_source_rgba(*INK2, alpha)
        ctx.fill()
        sp, ed = blade_path(ctx, P)
        poly(ctx, sp + ed[::-1])
        ctx.set_source_rgba(*STEEL, alpha)
        ctx.fill()
        return sp, ed
    if stowed:
        weapon_all()
    full(ox, oy, rim)
    full(0, 0, ink)
    # hood (ember)
    ctx.save()
    ctx.translate(ox, oy)
    hood_path(ctx, P)
    ctx.set_source_rgba(1.0, 0.45, 0.35, alpha)
    ctx.fill()
    ctx.restore()
    hood_path(ctx, P)
    ctx.set_source_rgba(*EMBER, alpha)
    ctx.fill()
    # face shadow
    fx = P.head[0] + P.face * 0.06 * math.cos(P.head_ang)
    fy = P.head[1] - 0.015
    ctx.arc(fx, fy, HEADR * 0.72, 0, 2 * PI)
    ctx.set_source_rgba(*INK, alpha)
    ctx.fill()
    # weapon
    if stowed:
        spine, edge = blade_path(ctx, P)
        ctx.new_path()
    else:
        spine, edge = weapon_all()
    # edge highlight
    ctx.move_to(*edge[0])
    for q in edge[1:]:
        ctx.line_to(*q)
    ctx.set_line_width(0.012)
    ctx.set_source_rgba(0.92, 0.95, 1.0, alpha * 0.9)
    ctx.stroke()
    # red accent stripe on the receiver
    h, b = P.w_head, P.w_butt
    ux, uy = (h[0] - b[0]) / P.Ls, (h[1] - b[1]) / P.Ls
    ctx.move_to(h[0] - ux * 0.40, h[1] - uy * 0.40)
    ctx.line_to(h[0] - ux * 0.06, h[1] - uy * 0.06)
    ctx.set_line_width(0.018)
    ctx.set_source_rgba(*EMBER, alpha)
    ctx.stroke()
    # near arm on top
    ctx.save()
    ctx.translate(ox, oy)
    hero_arms_near(ctx, P)
    ctx.set_source_rgba(*rim, alpha)
    ctx.fill()
    ctx.restore()
    hero_arms_near(ctx, P)
    ctx.set_source_rgba(*INK, alpha)
    ctx.fill()
    if glow is not None:
        glow.move_to(*edge[0])
        for q in edge[1:]:
            glow.line_to(*q)
        glow.set_line_width(0.02)
        glow.set_source_rgba(0.6, 0.75, 1.0, 0.35 * alpha)
        glow.stroke()
        glow.move_to(h[0] - ux * 0.40, h[1] - uy * 0.40)
        glow.line_to(h[0] - ux * 0.06, h[1] - uy * 0.06)
        glow.set_line_width(0.03)
        glow.set_source_rgba(*EMBER, 0.6 * alpha)
        glow.stroke()


# ---------------------------------------------------------------------------
# Void wolf
# ---------------------------------------------------------------------------
class WolfPose:
    def __init__(self, x, y, face=1, s=1.0, pitch=0.0, phase=0.0, mode='run', jaw=0.0,
                 roll=0.0, seed=0, t=0.0, legs=None):
        self.x, self.y, self.face, self.s = x, y, face, s
        self.pitch = pitch
        self.phase = phase
        self.mode = mode
        self.jaw = jaw
        self.roll = roll
        self.seed = seed
        self.t = t
        self.legs = legs

    def W(self, lx, ly):
        a = (self.pitch + self.roll) * D2R
        c, sn = math.cos(a), math.sin(a)
        x, y = lx * self.s, ly * self.s
        x, y = c * x - sn * y, sn * x + c * y
        return (self.x + self.face * x, self.y + y)


def wolf_paths(ctx, w, near=True, far=True, body=True):
    s = w.s
    W = w.W
    ph = w.phase * 2 * PI
    mode = w.mode
    rnd = (w.seed * 7919) % 97 / 97.0
    # --- legs: shoulder/hip anchors and paw targets (local) ---
    anchors = {'fn': (0.42, -0.08), 'ff': (0.36, -0.06), 'hn': (-0.42, -0.06), 'hf': (-0.48, -0.04)}
    offs = {'fn': 0.0, 'ff': 0.35, 'hn': 0.55, 'hf': 0.8}

    def paw(k):
        ax, ay = anchors[k]
        if mode == 'run':
            p = ph + offs[k] * 2 * PI
            dx = 0.38 * math.cos(p)
            dy = -0.72 + max(0.0, 0.26 * math.sin(p))
            return (ax + dx, ay + dy - 0.0)
        if mode == 'leap':
            if k[0] == 'f':
                return (ax + 0.55, ay - 0.25 + (0.05 if k == 'ff' else 0))
            return (ax - 0.55, ay - 0.35 + (0.05 if k == 'hf' else 0))
        if mode == 'crouch':
            return (ax + (0.12 if k[0] == 'f' else -0.05), ay - 0.5)
        if mode == 'stand':
            return (ax + (0.05 if k[0] == 'f' else 0.0), ay - 0.72)
        if mode == 'hurt':
            p = w.t * 13 + offs[k] * 5
            return (ax + 0.3 * math.cos(p), ay - 0.45 + 0.2 * math.sin(p * 1.3))
        if mode == 'swipe':  # front near leg raised and swiping
            if k == 'fn':
                return (ax + 0.75, ay + 0.1)
            return (ax + (0.1 if k[0] == 'f' else 0), ay - 0.72)
        return (ax, ay - 0.7)

    def leg(k):
        a = W(*anchors[k])
        tx, ty = W(*paw(k)) if w.legs is None or k not in w.legs else w.legs[k]
        front = k[0] == 'f'
        l1, l2 = 0.36 * s, 0.40 * s
        bend = (-1 if front else 1) * w.face
        j, e = ik2(a[0], a[1], tx, ty, l1, l2, bend)
        capsule(ctx, a, 0.12 * s, j, 0.065 * s)
        capsule(ctx, j, 0.06 * s, e, 0.04 * s)
        # paw
        capsule(ctx, e, 0.045 * s, (e[0] + w.face * 0.09 * s, e[1] - 0.01 * s), 0.035 * s)
        return e

    if far:
        leg('ff')
        leg('hf')
    if body:
        # --- torso with spiky mane ---
        top = []
        n = 14
        jit = 0.015 * math.sin(w.t * 37 + w.seed)
        for i in range(n + 1):
            u = i / n
            lx = lerp(-0.62, 0.52, u)
            base = 0.12 + 0.12 * math.sin(u * PI) + 0.10 * u * u
            spike = 0.0
            if i % 2 == 1:
                spike = (0.10 + 0.12 * math.sin(u * PI)) * (0.85 + 0.3 * ((i * 31 + w.seed) % 7) / 7) + jit
            top.append((lx - 0.03 * (i % 2), base + spike))
        bot = [(0.55, -0.02), (0.40, -0.26), (0.18, -0.30), (-0.05, -0.20), (-0.30, -0.14), (-0.55, -0.12)]
        poly(ctx, [W(*q) for q in top + bot])
        # neck/head
        hx, hy = 0.72, 0.24
        jaw = w.jaw
        skull = [(0.46, 0.35), (0.62, 0.44), (0.72, 0.40), (0.82, 0.35), (1.08, 0.24), (1.12, 0.18),
                 (0.90, 0.15), (0.66, 0.02), (0.45, -0.1)]
        poly(ctx, [W(*q) for q in skull])
        # ears
        poly(ctx, [W(0.62, 0.40), W(0.56, 0.62), W(0.70, 0.44)])
        poly(ctx, [W(0.69, 0.40), W(0.68, 0.58), W(0.77, 0.40)])
        # jaw (rotates about hinge)
        ja = -jaw * 0.6
        hxj, hyj = 0.70, 0.14
        pts = [(0.0, 0.0), (0.38, 0.02), (0.36, -0.05), (0.02, -0.10)]
        cj, sj = math.cos(ja), math.sin(ja)
        poly(ctx, [W(hxj + cj * x - sj * y, hyj + sj * x + cj * y) for x, y in pts])
        # tail
        tw = math.sin(w.t * 6 + w.seed) * 0.12
        tail = [(-0.58, 0.18), (-0.85, 0.28 + tw), (-1.15, 0.22 + tw * 1.8), (-1.02, 0.14 + tw),
                (-1.10, 0.06 + tw * 1.5), (-0.80, 0.08 + tw * 0.6), (-0.58, 0.0)]
        poly(ctx, [W(*q) for q in tail])
    if near:
        leg('hn')
        leg('fn')


def wolf_eyes(w):
    """Eye positions (world) for near/far eye."""
    return [w.W(0.84, 0.33), w.W(0.79, 0.345)]


def draw_wolf(ctx, w, glow=None, alpha=1.0, rim_off=(0.022, 0.018), dark=0.0, eye=1.0, rim=RIM):
    body_a = alpha * (1 - dark)
    if body_a > 0.01:
        ox, oy = rim_off
        ctx.save()
        ctx.translate(ox * w.s, oy * w.s)
        wolf_paths(ctx, w)
        ctx.set_source_rgba(*rim, body_a * 0.9)
        ctx.fill()
        ctx.restore()
        wolf_paths(ctx, w, near=False)
        ctx.set_source_rgba(0.02, 0.022, 0.032, body_a)
        ctx.fill()
        wolf_paths(ctx, w, far=False, body=False)
        ctx.set_source_rgba(0.035, 0.038, 0.05, body_a)
        ctx.fill()
    if eye > 0.01:
        for i, (ex, ey) in enumerate(wolf_eyes(w)):
            r = 0.035 * w.s * (1 if i == 0 else 0.8)
            ctx.save()
            ctx.translate(ex, ey)
            ctx.scale(1.8, 0.7)
            ctx.arc(0, 0, r, 0, 2 * PI)
            ctx.restore()
            ctx.set_source_rgba(*VOID_EYE, eye * alpha)
            ctx.fill()
            if glow is not None:
                glow.arc(ex, ey, r * (3.5 if w.s < 1.5 else 1.8), 0, 2 * PI)
                glow.set_source_rgba(0.4, 0.8, 1.0, (0.8 if w.s < 1.5 else 0.5) * eye * alpha)
                glow.fill()
