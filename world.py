"""Environment, particles, effects and post-processing."""
import math
import random
import numpy as np
import cairo
from PIL import Image, ImageFilter
from common import *
from rig import PI, EMBER, EMBER_HOT, EMBER_D, INK, RIM, poly, smooth_poly, capsule

# ---------------------------------------------------------------------------
# Camera
# ---------------------------------------------------------------------------
BASE_S = H / 5.0     # px per world unit at zoom 1


class Cam:
    def __init__(self, x, y, zoom, roll, shake=(0, 0)):
        self.x, self.y, self.zoom, self.roll = x, y, zoom, roll
        self.shake = shake

    def apply(self, ctx, k=1.0, scale=1.0):
        """Set ctx transform for a parallax layer with factor k."""
        ctx.identity_matrix()
        ctx.scale(scale, scale)
        ctx.translate(W / 2 + self.shake[0] * k, H / 2 + self.shake[1] * k)
        ctx.rotate(self.roll * PI / 180 * min(1.0, 0.3 + 0.7 * k))
        s = BASE_S * (self.zoom ** min(k, 1.3) if k < 1 else self.zoom * (1 + (k - 1) * 0.5))
        ctx.scale(s, -s)
        ctx.translate(-self.x * k, -self.y * k)

    def to_screen(self, x, y):
        s = BASE_S * self.zoom
        dx, dy = (x - self.x) * s, -(y - self.y) * s
        r = self.roll * PI / 180
        c, sn = math.cos(r), math.sin(r)
        return (W / 2 + c * dx - sn * dy + self.shake[0], H / 2 + sn * dx + c * dy + self.shake[1])


# ---------------------------------------------------------------------------
# Background layers (prebuilt cairo paths)
# ---------------------------------------------------------------------------
def _tree(ctx, rnd, x, h, w, depth_detail=4):
    """Bare winter tree, filled polygons."""
    lean = rnd.uniform(-0.06, 0.06)
    top = (x + lean * h, h)
    # trunk
    poly(ctx, [(x - w, -0.5), (x + w, -0.5), (top[0] + w * 0.15, top[1]), (top[0] - w * 0.15, top[1])])

    def branch(x0, y0, ang, L, wd, d):
        x1 = x0 + math.cos(ang) * L
        y1 = y0 + math.sin(ang) * L
        poly(ctx, [(x0 - math.sin(ang) * wd, y0 + math.cos(ang) * wd),
                   (x0 + math.sin(ang) * wd, y0 - math.cos(ang) * wd),
                   (x1 + math.sin(ang) * wd * 0.3, y1 - math.cos(ang) * wd * 0.3),
                   (x1 - math.sin(ang) * wd * 0.3, y1 + math.cos(ang) * wd * 0.3)])
        if d > 0:
            for _ in range(2 if d < 3 else rnd.randint(2, 3)):
                branch(x1, y1, ang + rnd.uniform(-0.7, 0.7), L * rnd.uniform(0.5, 0.75), wd * 0.55, d - 1)

    nb = int(3 + h * 0.8)
    for i in range(nb):
        u = rnd.uniform(0.35, 0.95)
        y0 = h * u
        x0 = x + lean * y0
        side = rnd.choice([-1, 1])
        ang = PI / 2 - side * rnd.uniform(0.5, 1.1)
        branch(x0, y0, ang, h * rnd.uniform(0.18, 0.32) * (1.2 - u), w * 0.45 * (1.1 - u), depth_detail - 1)
    branch(top[0], top[1], PI / 2 + rnd.uniform(-0.3, 0.3), h * 0.2, w * 0.2, 2)


def _ground_ridge(ctx, rnd, x0, x1, base, amp, step=0.6):
    pts = [(x0, -40)]
    x = x0
    ph = rnd.uniform(0, 6)
    while x <= x1:
        y = base + amp * (math.sin(x * 0.21 + ph) * 0.6 + math.sin(x * 0.53 + ph * 2) * 0.3 + math.sin(x * 1.3) * 0.1)
        pts.append((x, y))
        x += step
    pts.append((x1, -40))
    poly(ctx, pts)


class Layer:
    def __init__(self, k, color, fog, trees, x_range, ground_y, tree_h, tree_w, seed, ridge_amp=0.2,
                 ground_col=None, detail=4):
        self.k, self.color, self.fog = k, color, fog
        rnd = random.Random(seed)
        surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, 4, 4)
        ctx = cairo.Context(surf)
        ctx.new_path()
        for i in range(trees):
            x = rnd.uniform(*x_range)
            h = tree_h * rnd.uniform(0.7, 1.3)
            ctx.save()
            _tree(ctx, rnd, x, h, tree_w * rnd.uniform(0.7, 1.3), detail)
            ctx.restore()
        self.trees = ctx.copy_path()
        ctx.new_path()
        _ground_ridge(ctx, rnd, x_range[0] - 30, x_range[1] + 30, ground_y, ridge_amp)
        self.ground = ctx.copy_path()
        self.ground_col = ground_col or color
        self.ground_y = ground_y


def build_layers():
    L = []
    # far hills
    L.append(Layer(0.12, (0.13, 0.17, 0.26), 0.0, 0, (-60, 60), 1.2, 0, 0, 1, ridge_amp=1.6,
                   ground_col=(0.20, 0.25, 0.35)))
    L.append(Layer(0.25, (0.075, 0.095, 0.15), 0.0, 90, (-50, 50), 0.3, 6.5, 0.12, 2, ridge_amp=0.6,
                   ground_col=(0.30, 0.36, 0.48), detail=3))
    L.append(Layer(0.45, (0.04, 0.05, 0.08), 0.0, 70, (-40, 40), 0.0, 7.5, 0.16, 3, ridge_amp=0.35,
                   ground_col=(0.40, 0.46, 0.58), detail=4))
    L.append(Layer(0.72, (0.045, 0.055, 0.085), 0.0, 38, (-30, 30), -0.1, 9.0, 0.22, 4, ridge_amp=0.15,
                   ground_col=(0.52, 0.58, 0.70), detail=4))
    return L


class Foreground:
    def __init__(self):
        rnd = random.Random(11)
        surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, 4, 4)
        ctx = cairo.Context(surf)
        ctx.new_path()
        for x in [-17.0, -13.5, 9.5, 15.0]:
            _tree(ctx, rnd, x, 16, 0.55, 3)
        self.trees = ctx.copy_path()
        ctx.new_path()
        _ground_ridge(ctx, rnd, -60, 60, -1.6, 0.5, 0.4)
        self.ground = ctx.copy_path()


def draw_sky(ctx, cam, t):
    # gradient in parallax space (k=0.1)
    cam.apply(ctx, 0.08)
    g = cairo.LinearGradient(0, -2, 0, 14)
    g.add_color_stop_rgb(0.0, 0.12, 0.15, 0.23)
    g.add_color_stop_rgb(0.35, 0.045, 0.06, 0.10)
    g.add_color_stop_rgb(1.0, 0.01, 0.012, 0.025)
    ctx.set_source(g)
    ctx.rectangle(-200, -200, 400, 400)
    ctx.fill()
    # stars
    rnd = random.Random(5)
    for i in range(160):
        x, y = rnd.uniform(-30, 30), rnd.uniform(1, 18)
        a = rnd.uniform(0.15, 0.6) * (0.75 + 0.25 * math.sin(t * rnd.uniform(1, 3) + i))
        ctx.arc(x, y, rnd.uniform(0.008, 0.02), 0, 2 * PI)
        ctx.set_source_rgba(0.8, 0.85, 1.0, a)
        ctx.fill()


MOON = (0.06, 1.16, 1.45)   # layer-space x, y, radius (k=0.04)


def draw_moon(ctx, glow, cam, t):
    k = 0.04
    cam.apply(ctx, k)
    mx, my, mr = MOON
    # halo
    g = cairo.RadialGradient(mx, my, mr * 0.9, mx, my, mr * 3.2)
    g.add_color_stop_rgba(0, 0.55, 0.65, 0.85, 0.18)
    g.add_color_stop_rgba(1, 0.2, 0.3, 0.5, 0.0)
    ctx.set_source(g)
    ctx.arc(mx, my, mr * 3.2, 0, 2 * PI)
    ctx.fill()
    g = cairo.RadialGradient(mx - mr * 0.3, my + mr * 0.3, mr * 0.1, mx, my, mr)
    g.add_color_stop_rgb(0, 0.95, 0.96, 0.98)
    g.add_color_stop_rgb(1, 0.78, 0.82, 0.90)
    ctx.set_source(g)
    ctx.arc(mx, my, mr, 0, 2 * PI)
    ctx.fill()
    # maria
    rnd = random.Random(8)
    ctx.save()
    ctx.arc(mx, my, mr, 0, 2 * PI)
    ctx.clip()
    for i in range(14):
        a = rnd.uniform(0, 2 * PI)
        r = mr * math.sqrt(rnd.uniform(0, 0.8))
        ctx.arc(mx + r * math.cos(a), my + r * math.sin(a), mr * rnd.uniform(0.07, 0.3), 0, 2 * PI)
        ctx.set_source_rgba(0.55, 0.60, 0.72, rnd.uniform(0.12, 0.3))
        ctx.fill()
    ctx.restore()
    cam.apply(glow, k, 0.5)
    glow.arc(mx, my, mr * 1.05, 0, 2 * PI)
    glow.set_source_rgba(0.5, 0.6, 0.8, 0.16)
    glow.fill()
    # drifting cloud streaks
    cam.apply(ctx, 0.06)
    for i in range(5):
        cx = -8 + ((i * 4.7 + t * 0.12 * (1 + i * 0.2)) % 18)
        cy = 2.8 + i * 0.55
        ctx.save()
        ctx.translate(cx, cy)
        ctx.scale(3.2 + i * 0.3, 0.16)
        g = cairo.RadialGradient(0, 0, 0, 0, 0, 1)
        g.add_color_stop_rgba(0, 0.12, 0.15, 0.22, 0.75)
        g.add_color_stop_rgba(1, 0.12, 0.15, 0.22, 0.0)
        ctx.set_source(g)
        ctx.arc(0, 0, 1, 0, 2 * PI)
        ctx.fill()
        ctx.restore()


def draw_layers(ctx, cam, layers):
    for L in layers:
        cam.apply(ctx, L.k)
        ctx.new_path()
        ctx.append_path(L.ground)
        ctx.set_source_rgb(*L.ground_col)
        ctx.fill()
        if L.trees:
            ctx.new_path()
            ctx.append_path(L.trees)
            ctx.set_source_rgb(*L.color)
            ctx.fill()
        # fog band above this layer's ground
        g = cairo.LinearGradient(0, L.ground_y - 0.5, 0, L.ground_y + 4.0)
        g.add_color_stop_rgba(0, 0.30, 0.37, 0.50, 0.38 * (1 - L.k) ** 0.7)
        g.add_color_stop_rgba(1, 0.30, 0.37, 0.50, 0.0)
        ctx.set_source(g)
        ctx.rectangle(-300, L.ground_y - 0.5, 600, 4.5)
        ctx.fill()


def draw_ground(ctx, cam):
    cam.apply(ctx, 1.0)
    g = cairo.LinearGradient(0, 0.05, 0, -3.5)
    g.add_color_stop_rgb(0, 0.66, 0.73, 0.84)
    g.add_color_stop_rgb(0.25, 0.50, 0.57, 0.70)
    g.add_color_stop_rgb(1, 0.20, 0.24, 0.33)
    ctx.set_source(g)
    ctx.move_to(-200, -30)
    x = -200.0
    while x <= 200:
        ctx.line_to(x, 0.02 * math.sin(x * 2.1) + 0.015 * math.sin(x * 5.3))
        x += 0.5
    ctx.line_to(200, -30)
    ctx.close_path()
    ctx.fill()
    # top highlight
    ctx.move_to(-200, 0.0)
    ctx.line_to(200, 0.0)
    ctx.set_line_width(0.02)
    ctx.set_source_rgba(0.85, 0.9, 1.0, 0.5)
    ctx.stroke()


def draw_shadow(ctx, x, h, w=0.6, a=0.45):
    """Soft contact shadow on the snow; fades with height h."""
    f = clamp(1 - h / 4.0)
    if f <= 0:
        return
    ctx.save()
    ctx.translate(x, 0.0)
    ctx.scale(w * (1.0 + h * 0.15), 0.06)
    g = cairo.RadialGradient(0, 0, 0, 0, 0, 1)
    g.add_color_stop_rgba(0, 0.08, 0.10, 0.16, a * f)
    g.add_color_stop_rgba(1, 0.08, 0.10, 0.16, 0)
    ctx.set_source(g)
    ctx.arc(0, 0, 1, 0, 2 * PI)
    ctx.fill()
    ctx.restore()


def draw_foreground(ctx, cam, fg):
    cam.apply(ctx, 1.5)
    ctx.new_path()
    ctx.append_path(fg.trees)
    ctx.set_source_rgb(0.012, 0.015, 0.024)
    ctx.fill()
    ctx.new_path()
    ctx.append_path(fg.ground)
    ctx.set_source_rgb(0.10, 0.12, 0.18)
    ctx.fill()


# ---------------------------------------------------------------------------
# Snowfall (analytic, uses warped time so it slows in slow-mo)
# ---------------------------------------------------------------------------
class Snow:
    def __init__(self):
        r = np.random.default_rng(4)
        self.layers = []
        for k, n, size, fall, a in [(0.5, 420, 0.012, 0.5, 0.45), (1.0, 260, 0.02, 0.9, 0.7),
                                    (1.6, 40, 0.05, 1.5, 0.35)]:
            self.layers.append(dict(k=k, x=r.uniform(0, 1, n), y=r.uniform(0, 1, n),
                                    ph=r.uniform(0, 6.28, n), sz=size * r.uniform(0.6, 1.4, n),
                                    fall=fall * r.uniform(0.7, 1.3, n), a=a))

    def draw(self, ctx, cam, t, tw, wind=-0.6):
        for L in self.layers:
            k = L['k']
            cam.apply(ctx, k)
            # view box in layer space
            s = BASE_S * (cam.zoom ** min(k, 1.3) if k < 1 else cam.zoom * (1 + (k - 1) * 0.5))
            bw, bh = W / s * 1.5, H / s * 1.5
            cx, cy = cam.x * k, cam.y * k
            xs = (L['x'] * bw + wind * tw + 0.25 * np.sin(tw * 1.3 + L['ph']) - cx + bw / 2) % bw + cx - bw / 2
            ys = (L['y'] * bh - L['fall'] * tw - cy + bh / 2) % bh + cy - bh / 2
            ctx.set_source_rgba(0.88, 0.92, 1.0, L['a'])
            for x, y, r in zip(xs, ys, L['sz']):
                ctx.new_sub_path()
                ctx.arc(x, y, r, 0, 2 * PI)
            ctx.fill()


# ---------------------------------------------------------------------------
# Particles
# ---------------------------------------------------------------------------
class Particles:
    FIELDS = ['x', 'y', 'vx', 'vy', 'life', 'max', 'size', 'rot', 'spin', 'drag', 'grav', 'kind', 'seed']
    # kinds
    EMB, SPARK, SNOW, SHARD, SMOKE, PETAL = range(6)

    def __init__(self):
        self.d = {f: np.zeros(0) for f in self.FIELDS}
        self.pending = []

    def emit(self, kind, x, y, vx, vy, life, size, n=1, spread=0.0, vspread=0.0, drag=1.0, grav=0.0,
             spin=0.0, rnd=None):
        r = rnd or np.random
        for _ in range(n):
            ang = r.uniform(0, 2 * PI)
            sp = r.uniform(0, 1) * spread
            self.pending.append([x + r.normal(0, vspread), y + r.normal(0, vspread),
                                 vx + math.cos(ang) * sp, vy + math.sin(ang) * sp,
                                 life * r.uniform(0.6, 1.2), 0.0, size * r.uniform(0.6, 1.4),
                                 r.uniform(0, 6.28), spin * r.uniform(-1, 1), drag, grav, kind,
                                 r.uniform(0, 1)])

    def step(self, dt, t):
        if self.pending:
            arr = np.array(self.pending)
            arr[:, 5] = arr[:, 4]
            for i, f in enumerate(self.FIELDS):
                self.d[f] = np.concatenate([self.d[f], arr[:, i]])
            self.pending = []
        d = self.d
        if len(d['x']) == 0:
            return
        d['life'] -= dt
        alive = d['life'] > 0
        # snow dies on the ground
        alive &= ~((d['kind'] == self.SNOW) & (d['y'] < -0.05) & (d['vy'] < 0))
        for f in self.FIELDS:
            d[f] = d[f][alive]
        # turbulence for embers
        emb = (d['kind'] == self.EMB) | (d['kind'] == self.PETAL)
        d['vx'][emb] += np.sin(t * 3 + d['seed'][emb] * 40) * 1.5 * dt
        d['vy'][emb] += np.cos(t * 2.3 + d['seed'][emb] * 30) * 1.2 * dt
        d['vy'] -= d['grav'] * dt
        damp = np.exp(-d['drag'] * dt)
        d['vx'] *= damp
        d['vy'] *= damp
        d['x'] += d['vx'] * dt
        d['y'] += d['vy'] * dt
        d['rot'] += d['spin'] * dt
        # ground bounce for sparks/shards
        g = (d['y'] < 0.0) & ((d['kind'] == self.SPARK) | (d['kind'] == self.SHARD))
        d['y'][g] = 0.0
        d['vy'][g] = np.abs(d['vy'][g]) * 0.3
        d['vx'][g] *= 0.6

    def draw(self, ctx, glow, cam):
        d = self.d
        n = len(d['x'])
        if n == 0:
            return
        cam.apply(ctx, 1.0)
        cam.apply(glow, 1.0, 0.5)
        u = d['life'] / np.maximum(d['max'], 1e-6)   # 1 -> 0
        order = np.argsort(d['kind'] == self.SMOKE)[::-1]  # smoke first
        for i in order:
            k = int(d['kind'][i])
            x, y, s, a = d['x'][i], d['y'][i], d['size'][i], u[i]
            if k == self.SMOKE:
                r = s * (1.8 - a)
                g = cairo.RadialGradient(x, y, 0, x, y, r)
                g.add_color_stop_rgba(0, 0.02, 0.02, 0.04, 0.55 * a)
                g.add_color_stop_rgba(1, 0.02, 0.02, 0.04, 0)
                ctx.set_source(g)
                ctx.arc(x, y, r, 0, 2 * PI)
                ctx.fill()
            elif k == self.SNOW:
                ctx.arc(x, y, s, 0, 2 * PI)
                ctx.set_source_rgba(0.9, 0.93, 1.0, min(1, a * 1.5) * 0.9)
                ctx.fill()
            elif k == self.SPARK:
                vx, vy = d['vx'][i], d['vy'][i]
                L = 0.035
                for c, lw, al in ((ctx, s, 1.0), (glow, s * 3, 0.8)):
                    c.move_to(x, y)
                    c.line_to(x - vx * L, y - vy * L)
                    c.set_line_width(lw)
                    c.set_line_cap(cairo.LINE_CAP_ROUND)
                    c.set_source_rgba(1.0, 0.85 * a + 0.3, 0.55 * a + 0.2, al * min(1, a * 2))
                    c.stroke()
            elif k in (self.EMB, self.PETAL):
                col = (1.0, 0.35 + 0.45 * a ** 2, 0.15 + 0.3 * a ** 3) if k == self.EMB else EMBER
                ctx.save()
                ctx.translate(x, y)
                ctx.rotate(d['rot'][i])
                ctx.scale(1.0, 0.45 if k == self.PETAL else 0.6)
                ctx.arc(0, 0, s, 0, 2 * PI)
                ctx.restore()
                ctx.set_source_rgba(*col, min(1, a * 2.5))
                ctx.fill()
                glow.arc(x, y, s * 1.8, 0, 2 * PI)
                glow.set_source_rgba(1.0, 0.4, 0.15, min(1, a * 2) * (0.22 if k == self.EMB else 0.12))
                glow.fill()
            elif k == self.SHARD:
                ctx.save()
                ctx.translate(x, y)
                ctx.rotate(d['rot'][i])
                sc = s * (0.4 + 0.6 * a)
                ctx.move_to(sc, 0)
                ctx.line_to(-sc * 0.6, sc * 0.5)
                ctx.line_to(-sc * 0.4, -sc * 0.6)
                ctx.close_path()
                ctx.restore()
                ctx.set_source_rgba(0.02, 0.02, 0.035, min(1, a * 3))
                ctx.fill_preserve()
                # burning edge
                ctx.set_line_width(0.012)
                heat = clamp((1 - a) * 2.2)
                ctx.set_source_rgba(1.0, 0.45 + 0.3 * (1 - heat), 0.2, min(1, a * 3) * heat)
                ctx.stroke()
                glow.arc(x, y, s * 1.2, 0, 2 * PI)
                glow.set_source_rgba(1.0, 0.35, 0.1, 0.25 * heat * min(1, a * 3))
                glow.fill()


# ---------------------------------------------------------------------------
# Transient effects (drawn in world space)
# ---------------------------------------------------------------------------
class Effects:
    def __init__(self):
        self.items = []   # (t0, dur, fn)

    def add(self, t0, dur, fn):
        self.items.append((t0, dur, fn))

    def draw(self, ctx, glow, cam, t):
        cam.apply(ctx, 1.0)
        cam.apply(glow, 1.0, 0.5)
        keep = []
        for (t0, dur, fn) in self.items:
            u = (t - t0) / dur
            if u < 0:
                keep.append((t0, dur, fn))
                continue
            if u <= 1:
                fn(ctx, glow, u)
                keep.append((t0, dur, fn))
        self.items = keep


def fx_muzzle(x, y, dx, dy, size=1.0):
    ang = math.atan2(dy, dx)

    def fn(ctx, glow, u):
        a = (1 - u) ** 2
        L = size * (0.9 + 0.4 * (1 - u))
        for c, sc, col in ((glow, 1.8, (1.0, 0.6, 0.25, a)), (ctx, 1.0, (1.0, 0.95, 0.8, a))):
            c.save()
            c.translate(x, y)
            c.rotate(ang)
            c.move_to(0, 0)
            c.line_to(L * 0.3 * sc, 0.16 * size * sc)
            c.line_to(L * sc, 0)
            c.line_to(L * 0.3 * sc, -0.16 * size * sc)
            c.close_path()
            c.move_to(0.1, 0)
            c.line_to(0.2 * sc, 0.4 * size * sc)
            c.line_to(0.3 * sc, 0)
            c.line_to(0.2 * sc, -0.4 * size * sc)
            c.close_path()
            c.restore()
            c.set_source_rgba(*col)
            c.fill()
        glow.arc(x, y, 0.8 * size * (1 - u * 0.5), 0, 2 * PI)
        glow.set_source_rgba(1.0, 0.5, 0.2, 0.25 * a)
        glow.fill()
    return fn


def fx_tracer(x0, y0, x1, y1):
    def fn(ctx, glow, u):
        a = 1 - u
        h = clamp(u * 4)
        xa, ya = lerp(x0, x1, max(0, h - 0.4)), lerp(y0, y1, max(0, h - 0.4))
        xb, yb = lerp(x0, x1, h), lerp(y0, y1, h)
        for c, lw, col in ((glow, 0.09, (1.0, 0.55, 0.2, a)), (ctx, 0.025, (1.0, 0.95, 0.8, a))):
            c.move_to(xa, ya)
            c.line_to(xb, yb)
            c.set_line_width(lw)
            c.set_line_cap(cairo.LINE_CAP_ROUND)
            c.set_source_rgba(*col)
            c.stroke()
    return fn


def fx_ring(x, y, rmax, col=(0.85, 0.9, 1.0), flat=0.25, width=0.12):
    def fn(ctx, glow, u):
        r = rmax * (1 - (1 - u) ** 3)
        a = (1 - u) ** 1.5
        ctx.save()
        ctx.translate(x, y)
        ctx.scale(1, flat)
        ctx.arc(0, 0, r, 0, 2 * PI)
        ctx.restore()
        ctx.set_line_width(width * (1 - u) + 0.01)
        ctx.set_source_rgba(*col, a)
        ctx.stroke()
        glow.save()
        glow.translate(x, y)
        glow.scale(1, flat)
        glow.arc(0, 0, r, 0, 2 * PI)
        glow.restore()
        glow.set_line_width(width * 2)
        glow.set_source_rgba(*col, a * 0.5)
        glow.stroke()
    return fn


def fx_slash(x0, y0, x1, y1, col=(1, 1, 1), w=0.08):
    """Bright crescent slash mark in space."""
    mx, my = (x0 + x1) / 2, (y0 + y1) / 2
    nx, ny = -(y1 - y0), (x1 - x0)
    L = math.hypot(nx, ny) + 1e-9
    nx, ny = nx / L, ny / L

    def fn(ctx, glow, u):
        grow = clamp(u * 5)
        a = (1 - u) ** 1.2
        th = w * (1 - u) + 0.005
        ex0, ey0 = lerp(mx, x0, grow), lerp(my, y0, grow)
        ex1, ey1 = lerp(mx, x1, grow), lerp(my, y1, grow)
        for c, k, col2 in ((glow, 1.3, (1.0, 0.6, 0.3, a * 0.6)), (ctx, 1.0, (*col, a))):
            c.move_to(ex0, ey0)
            c.curve_to(mx + nx * th * k * 2, my + ny * th * k * 2, mx + nx * th * k * 2, my + ny * th * k * 2, ex1, ey1)
            c.curve_to(mx - nx * th * k * 0.5, my - ny * th * k * 0.5, mx - nx * th * k * 0.5, my - ny * th * k * 0.5, ex0, ey0)
            c.close_path()
            c.set_source_rgba(*col2)
            c.fill()
    return fn


def fx_light(x, y, r, col=(1.0, 0.5, 0.2), a0=0.6):
    def fn(ctx, glow, u):
        a = a0 * (1 - u) ** 2
        g = cairo.RadialGradient(x, y, 0, x, y, r)
        g.add_color_stop_rgba(0, *col, a)
        g.add_color_stop_rgba(1, *col, 0)
        glow.set_source(g)
        glow.arc(x, y, r, 0, 2 * PI)
        glow.fill()
    return fn


# ---------------------------------------------------------------------------
# Post
# ---------------------------------------------------------------------------
_grain = [np.random.default_rng(i).normal(0, 1, (H, W)).astype(np.float32) for i in range(6)]
_yy, _xx = np.mgrid[0:H, 0:W].astype(np.float32)
_vig = 1 - 0.55 * (((_xx - W / 2) / (W * 0.62)) ** 2 + ((_yy - H / 2) / (H * 0.72)) ** 2) ** 1.4
_vig = np.clip(_vig, 0.25, 1)[..., None].astype(np.float32)


def surf_to_np(surf, w, h):
    buf = np.ndarray((h, w, 4), np.uint8, surf.get_data())
    return buf[..., [2, 1, 0]].astype(np.float32) / 255.0  # BGRA -> RGB


def post(base_surf, glow_surf, frame_i, flash=0.0, aberr=0.0, impact=0.0, fade=1.0, grade_warm=0.0):
    img = surf_to_np(base_surf, W, H)
    gw, gh = W // 2, H // 2
    g = np.ndarray((gh, gw, 4), np.uint8, glow_surf.get_data())
    gimg = Image.fromarray(g[..., [2, 1, 0]].copy())
    b1 = np.asarray(gimg.filter(ImageFilter.GaussianBlur(5)), np.float32) / 255
    b2 = np.asarray(gimg.resize((gw // 4, gh // 4), Image.BILINEAR).filter(ImageFilter.GaussianBlur(6))
                    .resize((gw, gh), Image.BILINEAR), np.float32) / 255
    gsum = np.asarray(g[..., [2, 1, 0]], np.float32) / 255 * 0.45 + b1 * 0.8 + b2 * 1.0
    gsum = np.asarray(Image.fromarray(np.clip(gsum * 255 / 3, 0, 255).astype(np.uint8))
                      .resize((W, H), Image.BILINEAR), np.float32) / 255 * 3
    img = img + gsum * (1 - img * 0.5)
    if int(aberr) > 0:
        sh = int(aberr)
        img[:, sh:, 0] = img[:, :-sh, 0]
        img[:, :-sh, 2] = img[:, sh:, 2]
    # grade: cool shadows, filmic shoulder
    lum = img.mean(2, keepdims=True)
    img = img + (0.012 + 0.03 * (1 - lum)) * np.array([-0.2, 0.1, 0.5], np.float32) * (1 - lum)
    img = img * _vig
    img = 1 - np.exp(-img * 1.35)
    img = img / (1 - math.exp(-1.35))
    if impact > 0:
        l2 = (img * np.array([0.3, 0.55, 0.15], np.float32)).sum(2, keepdims=True)
        red = np.clip((img[..., :1] - img[..., 1:2]) * 2.5 - 0.3, 0, 1)
        # inverted, crushed: dark silhouettes become white, bright snow/sky become ink
        inv = np.clip((0.42 - l2) * 5.0, 0, 1) * 0.97 + 0.02
        imp = np.concatenate([inv, inv, inv], 2)
        imp = imp * (1 - red) + red * np.array([0.95, 0.12, 0.08], np.float32)
        img = img * (1 - impact) + imp * impact
        flash = 0.0
    if flash > 0:
        img = img + (1 - img) * flash
    img = img + _grain[frame_i % 6][..., None] * 0.018
    img = img * fade
    return (np.clip(img, 0, 1) * 255).astype(np.uint8)
