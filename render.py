"""EMBER — frame renderer.  python render.py [--preview t1,t2,...] [--from s --to s]"""
import sys
import math
import time
import subprocess
import argparse
import numpy as np
import cairo
from common import *
from rig import (draw_hero, draw_wolf, HeroPose, EMBER, EMBER_HOT, INK, poly, smooth_poly, PI, D2R,
                 wolf_paths)
from world import (build_layers, Foreground, draw_sky, draw_moon, draw_layers, draw_ground, draw_shadow,
                   draw_foreground, Snow, Particles, Effects, fx_muzzle, fx_tracer, fx_ring, fx_slash,
                   fx_light, post, BASE_S)
import choreo as C
from choreo import HP, HR, HT, WOLVES

PT = Particles


# ---------------------------------------------------------------------------
# Cloak: verlet cloth hanging from the shoulders
# ---------------------------------------------------------------------------
class Cloak:
    COLS, ROWS = 5, 11

    def __init__(self, t0):
        P = HP(t0)
        self.pos = np.zeros((self.ROWS, self.COLS, 2))
        for r in range(self.ROWS):
            for c in range(self.COLS):
                ax, ay = P.cloak_anchor[c]
                self.pos[r, c] = (ax - 0.04 * r, ay - 0.11 * r)
        self.prev = self.pos.copy()
        self.vl = 0.125
        self.hl = np.array([0.04 + 0.012 * r for r in range(self.ROWS)])

    def step(self, t, dt, n=4):
        if dt <= 0:
            return
        h = dt / n
        for i in range(n):
            ts = t - dt + (i + 1) * h
            P = HP(ts)
            wind = HT.get('wind', ts)
            wx = -wind * (1.4 + 0.9 * math.sin(ts * 1.3) + 0.5 * math.sin(ts * 3.7))
            wy = 0.3 * math.sin(ts * 2.1)
            vel = (self.pos - self.prev) / max(h, 1e-5)
            sp = np.linalg.norm(vel, axis=2, keepdims=True)
            vel = vel * np.minimum(1.0, 25.0 / np.maximum(sp, 1e-9))
            # air drag toward wind velocity, row-dependent flutter
            rows = np.arange(self.ROWS)[:, None]
            flutter = np.sin(ts * 9 + rows * 0.8 + np.arange(self.COLS)[None, :] * 0.5) * wind * 0.8
            air = np.stack([np.full((self.ROWS, self.COLS), wx), wy + flutter], 2)
            acc = (air - vel) * 1.6
            acc[..., 1] -= 9.0
            newp = self.pos + vel * h + acc * h * h
            self.prev = self.pos
            self.pos = newp
            # pin anchors
            for c in range(self.COLS):
                self.pos[0, c] = P.cloak_anchor[c]
            for _ in range(3):
                self._constrain()
            below = self.pos[..., 1] < 0.02
            self.pos[..., 1][below] = 0.02

    def _constrain(self):
        p = self.pos
        # vertical (stiff)
        d = p[1:] - p[:-1]
        L = np.linalg.norm(d, axis=2, keepdims=True) + 1e-9
        corr = d * (1 - self.vl / L) * 0.5
        p[1:] -= corr
        p[:-1] += corr
        p[0] = self.pos[0]
        # horizontal (max distance only)
        d = p[:, 1:] - p[:, :-1]
        L = np.linalg.norm(d, axis=2, keepdims=True) + 1e-9
        hl = self.hl[:, None, None]
        over = L - hl
        over = np.where(over < 0, over * 0.2, over)
        corr = d / L * over * 0.5
        corr[0] = 0
        p[:, 1:] -= corr
        p[:, :-1] += corr
        p[0] = self.pos[0]

    def polys(self):
        p = self.pos
        pts = [tuple(q) for q in p[:, 0]] + [tuple(q) for q in p[-1, 1:]] + \
              [tuple(q) for q in p[::-1, -1][1:]] + [tuple(q) for q in p[0, 1:-1][::-1]]
        return [pts]

    def hem(self):
        return self.pos[-1]


# ---------------------------------------------------------------------------
# Event cues -> particles / effects
# ---------------------------------------------------------------------------
rng = np.random.default_rng(3)
EVENTS = []   # (t, fn(P, E))


def ev(t):
    def deco(f):
        EVENTS.append((t, f))
        return f
    return deco


def _unit(dx, dy):
    L = math.hypot(dx, dy) + 1e-9
    return dx / L, dy / L


def add_shot(t, big=False, target=None):
    def f(Pp, E):
        P = HP(t)
        mx, my = P.muzzle
        dx, dy = _unit(*P.muzzle_dir)
        E.add(t, 0.12 if not big else 0.18, fx_muzzle(mx, my, dx, dy, 1.4 if big else 1.0))
        E.add(t, 0.3, fx_light(mx, my, 2.6 if big else 1.8, a0=0.5))
        for _ in range(8 if big else 5):
            s = rng.uniform(0.5, 3.0)
            Pp.emit(PT.SMOKE, mx, my, dx * s, dy * s + 0.3, 0.9, 0.25, spread=0.6, drag=2.5, rnd=rng)
        Pp.emit(PT.SPARK, mx, my, dx * 9, dy * 9, 0.25, 0.018, n=14 if big else 8, spread=5, drag=3,
                grav=6, rnd=rng)
        # shell casing
        Pp.emit(PT.SPARK, P.w_grip[0], P.w_grip[1], -dx * 1.5 + rng.normal(), 3.5, 0.6, 0.02, grav=12, rnd=rng)
        if big:
            Pp.emit(PT.SNOW, mx, 0.05, 0, 3.5, 1.2, 0.03, n=60, spread=4.5, drag=1.5, grav=5, rnd=rng)
            E.add(t, 0.5, fx_ring(mx, 0.02, 2.5))
        if target is not None:
            E.add(t, 0.14, fx_tracer(mx, my, *target))
    EVENTS.append((t, f))


def add_hit(t, pos_fn, big=False, n=30, col=(1, 1, 1)):
    def f(Pp, E):
        x, y = pos_fn() if callable(pos_fn) else pos_fn
        Pp.emit(PT.SPARK, x, y, 0, 0, 0.35, 0.02, n=n * (2 if big else 1), spread=14 if big else 9,
                drag=4, grav=8, rnd=rng)
        Pp.emit(PT.EMB, x, y, 0, 0.5, 1.2, 0.035, n=n // 2, spread=3, drag=1.5, grav=-0.4, rnd=rng)
        E.add(t, 0.25, fx_light(x, y, 2.2 if big else 1.4, (1.0, 0.7, 0.45), 0.45))
    EVENTS.append((t, f))


def add_slash_mark(t, x0, y0, x1, y1, dur=0.3, w=0.1):
    EVENTS.append((t, lambda Pp, E: E.add(t, dur, fx_slash(x0, y0, x1, y1, w=w))))


def add_burst(w, big=False):
    t = w.t_die

    def f(Pp, E):
        x, y = w.pos(t - 1e-3)
        vx, vy = w.vel(t - 0.02)
        vx *= 0.25
        vy *= 0.25
        s = w.s
        n = int(55 * s * s) if big else 55
        for _ in range(n):
            ox, oy = rng.normal(0, 0.45 * s), rng.normal(0, 0.22 * s)
            Pp.emit(PT.SHARD, x + ox, y + oy + 0.1 * s, vx + ox * 5, vy + oy * 5 + 1.5, 1.4, 0.07 * s ** 0.5,
                    spread=2.5 * s ** 0.5, drag=1.2, grav=2.0, spin=12, rnd=rng)
        Pp.emit(PT.EMB, x, y, vx, vy + 1.0, 2.0, 0.03, n=int(25 * s), spread=4 * s ** 0.5, vspread=0.3 * s,
                drag=1.0, grav=-0.8, rnd=rng)
        for _ in range(int(10 * s)):
            Pp.emit(PT.SMOKE, x + rng.normal(0, 0.4 * s), y + rng.normal(0, 0.2 * s), vx * 0.3, 0.8,
                    1.4, 0.45 * s ** 0.7, spread=0.8, drag=1.5, rnd=rng)
        E.add(t, 0.45 if not big else 0.8, fx_light(x, y, 2.0 * s, (1.0, 0.45, 0.2), 0.5))
        if big:
            E.add(t, 0.8, fx_ring(x, y, 7.0, (1.0, 0.6, 0.35), flat=1.0, width=0.2))
    EVENTS.append((t, f))


def add_snow(t, x, n=40, up=3.0, spread=3.0):
    EVENTS.append((t, lambda Pp, E: Pp.emit(PT.SNOW, x, 0.05, 0, up, 1.3, 0.03, n=n, spread=spread,
                                            drag=1.2, grav=6, rnd=rng)))


def add_ring(t, x, y, r, flat=0.25):
    EVENTS.append((t, lambda Pp, E: E.add(t, 0.6, fx_ring(x, y, r, flat=flat))))


# --- the cue list --------------------------------------------------------
# W1 cleave
c1 = C.C1
add_hit(T_DROP, c1, big=True)
add_slash_mark(T_DROP, *[q for w in [C.W1] for q in w.hits[0][1:]], dur=0.25, w=0.14)
add_burst(C.W1)
add_snow(T_DROP, 0.8, 30, 2.5)
# eyes: tiny glints
# dash 1
add_shot(T_SHOT1)
add_snow(T_SHOT1, 0.6, 30, 3.0)
add_hit(T_HOOK, C.C2)
add_slash_mark(T_HOOK, *C.W2.hits[0][1:], dur=0.2)
add_hit(T_COLLIDE, (-6.7, 1.1), n=15)
add_burst(C.W2)
add_burst(C.W3)
add_snow(T_THROW, -4.6, 40, 2.5)
# kick + shot
add_hit(T_VAULT, C.C4, n=20)
add_shot(T_SHOT2, target=C.P4HIT)
add_burst(C.W4)
add_snow(12.92, -3.05, 45, 3.0)
# spin
add_hit(T_SPIN, C.C5)
add_slash_mark(T_SPIN, *C.W5.hits[0][1:])
add_hit(T_SPIN2, C.C6)
add_slash_mark(T_SPIN2, *C.W6.hits[0][1:])
add_burst(C.W5)
add_burst(C.W6)
# superjump / dive / slam
add_shot(T_SUPERJUMP, big=True)
add_shot(T_DIVE)
add_hit(T_SLAM, lambda: HP(T_SLAM).blade_tip, big=True)
add_snow(T_SLAM, 1.2, 160, 6.0, 6.0)
add_ring(T_SLAM, 1.2, 0.02, 6.0)
for i, tr in enumerate(T_RAPID):
    add_shot(tr, target=C.rapid_targets[i])
for w in (C.W7, C.W8, C.W9):
    add_burst(w)
# dash
for i, (th, w) in enumerate(zip(T_DASH_HITS, C.dash_w)):
    add_hit(th, w.hits[0][1:3], n=18)
    add_slash_mark(th, *w.hits[0][1:], dur=T_DASH_BURST - th + 0.25, w=0.1)
    add_burst(w)
# alpha
add_snow(T_ALPHA, -5.5, 200, 7.0, 7.0)
add_ring(T_ALPHA, -5.5, 0.02, 7.0)
add_hit(T_BLOCK, lambda: C.blk_top, big=True)
add_shot(T_CHARGE)
add_hit(T_LEGHOOK, lambda: HP(T_LEGHOOK).blade_tip, n=25)
add_shot(T_LAUNCH, big=True)
add_shot(T_FINAL, big=True)
for i, tc in enumerate(T_CARVE):
    def _cv(tc=tc):
        return HP(tc).blade[5]
    add_hit(tc, _cv, n=22)
    p0 = HP(tc - 0.05).blade[6]
    p1 = HP(tc + 0.03).blade[6]
    add_slash_mark(tc, p0[0], p0[1], p1[0], p1[1], dur=0.35, w=0.09)
add_hit(T_CLEAVE, (C.ACX, C.ACY), big=True, n=60)
add_slash_mark(T_CLEAVE, *C.AL.hits[0][1:], dur=T_ALPHA_BURST - T_CLEAVE + 0.1, w=0.22)
add_burst(C.AL, big=True)
add_snow(T_CLEAVE + 0.05, C.ACX - 3.2, 80, 3.0, 3.5)
add_snow(T_ALPHA_BURST, C.ACX, 160, 5.0, 6.0)
EVENTS.sort(key=lambda q: q[0])

# intervals
AFTERIMAGE = [(T_SHOT1, T_HOOK), (T_DASH - 0.05, T_DASH_BURST - 0.05), (T_CHARGE, T_LEGHOOK),
              (T_FINAL, C.T_ORB0), (C.T_ORB1, T_CLEAVE + 0.06),
              (T_SUPERJUMP, T_SUPERJUMP + 0.35), (T_DIVE, T_SLAM)]
AFTERIMAGE = [a for a in AFTERIMAGE if a]
SLIDES = [(T_THROW, T_BURST23 + 0.05), (T_BLOCK + 0.05, 20.4), (T_CHARGE + 0.05, T_LEGHOOK + 0.35),
          (T_CLEAVE + 0.02, T_CLEAVE + 0.4), (T_DROP - 0.1, T_DROP + 0.05)]
TRAILS = [(T_SHOT1, T_HOOK), (T_DASH - 0.05, T_DASH_BURST), (T_CHARGE, T_LEGHOOK), (T_FINAL, T_CLEAVE + 0.1),
          (T_SUPERJUMP, T_DIVE), (T_LAUNCH, T_BREAK + 1.0)]


def in_any(t, iv):
    return any(a <= t < b for a, b in iv)


# ---------------------------------------------------------------------------
# Wolf drawing with split
# ---------------------------------------------------------------------------
def draw_wolf_full(ctx, glow, w, t):
    if not w.alive(t):
        return
    wp, p = w.state(t)
    if p['dark'] > 0.995 and p['eye'] < 0.01:
        return
    sep = p['split']
    if sep > 0.001:
        a = w.split_ang * D2R
        nx, ny = -math.sin(a), math.cos(a)
        for sgn in (1, -1):
            ctx.save()
            glow.save()
            # half-plane clip through the body centre
            cx, cy = wp.x, wp.y
            ux, uy = math.cos(a), math.sin(a)
            big = 40
            pts = [(cx - ux * big, cy - uy * big), (cx + ux * big, cy + uy * big),
                   (cx + ux * big + sgn * nx * big, cy + uy * big + sgn * ny * big),
                   (cx - ux * big + sgn * nx * big, cy - uy * big + sgn * ny * big)]
            poly(ctx, pts)
            ctx.clip()
            ctx.translate(sgn * nx * sep * w.s * 0.5 + ux * sgn * sep * 0.3, sgn * ny * sep * w.s * 0.5)
            draw_wolf(ctx, wp, glow, dark=p['dark'], eye=p['eye'])
            ctx.restore()
            glow.restore()
        # burning seam
        cx, cy = wp.x, wp.y
        ux, uy = math.cos(a), math.sin(a)
        L = 1.3 * w.s
        for c, lw, col in ((glow, 0.2 * w.s, (1, 0.45, 0.15, 0.9)), (ctx, 0.03 * w.s, (1, 0.8, 0.5, 1))):
            c.move_to(cx - ux * L, cy - uy * L)
            c.line_to(cx + ux * L, cy + uy * L)
            c.set_line_width(lw)
            c.set_source_rgba(*col)
            c.stroke()
    else:
        draw_wolf(ctx, wp, glow, dark=p['dark'], eye=p['eye'])
    # eye trails when moving fast
    if p['eye'] > 0.3 and p['dark'] < 0.9:
        vx, vy = w.vel(t)
        if math.hypot(vx, vy) > 3:
            from rig import wolf_eyes
            for k in range(1, 6):
                wq, _ = w.state(t - k * 0.018)
                e = wolf_eyes(wq)[0]
                glow.arc(e[0], e[1], 0.04 * w.s * (1 - k / 6), 0, 2 * PI)
                glow.set_source_rgba(0.5, 0.85, 1.0, 0.5 * (1 - k / 6))
                glow.fill()


# ---------------------------------------------------------------------------
# Blade smear
# ---------------------------------------------------------------------------
def draw_smear(ctx, glow, t):
    K = 12
    dtk = 1.0 / (FPS * 3)
    tips, bases = [], []
    for j in range(K):
        P = HP(t - j * dtk)
        tips.append(P.blade[8])
        bases.append(P.blade[3])
    speed = math.hypot(tips[0][0] - tips[2][0], tips[0][1] - tips[2][1]) / (2 * dtk)
    if speed < 9:
        return
    a = clamp((speed - 9) / 20)
    # quad strip, fading
    for j in range(K - 1):
        f = 1 - j / (K - 1)
        seg = math.hypot(tips[j][0] - tips[j + 1][0], tips[j][1] - tips[j + 1][1])
        rot_ = math.hypot(tips[j][0] - bases[j][0] - tips[j + 1][0] + bases[j + 1][0],
                          tips[j][1] - bases[j][1] - tips[j + 1][1] + bases[j + 1][1])
        if seg > 0.9 or rot_ < 0.35 * seg:
            break
        pts = [tips[j], tips[j + 1], bases[j + 1], bases[j]]
        for c, col, al in ((glow, (1.0, 0.5, 0.2), 0.45), (ctx, (1.0, 0.93, 0.85), 0.55)):
            poly(c, pts)
            c.set_source_rgba(*col, al * a * f ** 1.5)
            c.fill()
    # hot leading edge
    ctx.move_to(*tips[0])
    for q in tips[1:]:
        ctx.line_to(*q)
    ctx.set_line_width(0.03)
    ctx.set_source_rgba(1, 1, 1, 0.8 * a)
    ctx.stroke()


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def title_card(ctx, glow, t):
    u = clamp((t - T_TITLE) / 1.0)
    if u <= 0:
        return
    e = EASE['out'](u)
    ctx.identity_matrix()
    ctx.select_font_face('Futura', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    size = 118
    ctx.set_font_size(size)
    word = 'EMBER'
    track = 0.42 * size * (1.4 - 0.4 * e)
    widths = [ctx.text_extents(ch).x_advance for ch in word]
    total = sum(widths) + track * (len(word) - 1)
    x = W * 0.70 - total / 2
    y = H * 0.44
    for ch, wd in zip(word, widths):
        ctx.move_to(x, y)
        ctx.set_source_rgba(0.97, 0.93, 0.88, e)
        ctx.show_text(ch)
        glow.identity_matrix()
        glow.scale(0.5, 0.5)
        glow.move_to(x, y)
        glow.select_font_face('Futura')
        glow.set_font_size(size)
        glow.set_source_rgba(1.0, 0.45, 0.2, 0.6 * e)
        glow.show_text(ch)
        x += wd + track
    # hairline
    lw = total * e
    ctx.move_to(W * 0.70 - lw / 2, y + 36)
    ctx.line_to(W * 0.70 + lw / 2, y + 36)
    ctx.set_line_width(2)
    ctx.set_source_rgba(*EMBER, e)
    ctx.stroke()


def render(frames_to_draw=None, out_png_dir=None, t_from=0.0, t_to=DUR, pipe=None):
    layers = build_layers()
    fg = Foreground()
    snow = Snow()
    Pp = Particles()
    E = Effects()
    cams = C.camera_path()
    nfr = int(DUR * FPS)
    f0 = int(t_from * FPS)
    f1 = min(int(t_to * FPS), nfr)
    base = cairo.ImageSurface(cairo.FORMAT_RGB24, W, H)
    glow_s = cairo.ImageSurface(cairo.FORMAT_RGB24, W // 2, H // 2)
    cloak = Cloak(0.0)
    ev_i = 0
    t_prev = -1e-9
    tstart = time.time()
    # warm-up cloth
    for _ in range(60):
        cloak.step(0.0, 1 / 60)
    for fi in range(0, f1):
        t = fi / FPS
        dt = (t - t_prev) if fi else 1 / FPS
        ts = timescale(t)
        sdt = dt * ts if fi else 0.0
        # fire events
        while ev_i < len(EVENTS) and EVENTS[ev_i][0] <= t:
            EVENTS[ev_i][1](Pp, E)
            ev_i += 1
        # continuous emitters
        P = HP(t)
        cloak.step(t, sdt)
        rx, ry = HR(t)
        rpx, rpy = HR(t - 1 / FPS)
        spd = math.hypot(rx - rpx, ry - rpy) * FPS
        hem = cloak.hem()
        if rng.random() < 0.25 + spd * 0.08:
            q = hem[rng.integers(0, len(hem))]
            Pp.emit(PT.EMB, q[0], q[1], rng.normal(0, 0.3), 0.4, 2.0, 0.022, drag=1.0, grav=-0.3, rnd=rng)
        if in_any(t, TRAILS):
            for k in range(2):
                u = k / 2
                cx, cy = lerp(rpx, rx, u), lerp(rpy, ry, u) + 0.3
                Pp.emit(PT.PETAL if k % 2 else PT.EMB, cx + rng.normal(0, 0.15), cy + rng.normal(0, 0.2),
                        rng.normal(0, 0.4), rng.normal(0, 0.4), 1.2, 0.045, drag=2.0, grav=-0.2,
                        spin=6, rnd=rng)
        if in_any(t, SLIDES) and fi % 1 == 0:
            for q in (P.foot_n, P.foot_f):
                if q[1] < 0.2:
                    Pp.emit(PT.SNOW, q[0], 0.05, -(rx - rpx) * FPS * 0.3, 1.8, 0.8, 0.028, n=4,
                            spread=1.6, drag=1.5, grav=6, rnd=rng)
        for w in WOLVES:
            if w.alive(t) and w.mode_at(t) == 'run' and rng.random() < 0.5:
                x, y = w.pos(t)
                f = w.tr.get('face', t)
                Pp.emit(PT.SNOW, x - f * 0.4 * w.s, 0.04, -f * 0.8, 1.2, 0.5, 0.025, n=2, spread=0.7,
                        drag=2, grav=5, rnd=rng)
        if T_ALPHA + 0.2 < t < 19.5:
            wp, _ = C.AL.state(t)
            mx, my = wp.W(1.1, 0.2)
            Pp.emit(PT.SNOW, mx, my, 9.0, rng.normal(0, 1), 0.7, 0.03, n=6, spread=2.0, vspread=0.2,
                    drag=0.5, grav=0.5, rnd=rng)
        Pp.step(sdt, t)
        t_prev = t

        if fi < f0 or (frames_to_draw is not None and fi not in frames_to_draw):
            # keep effect list pruned
            continue

        cam, fl, imp, ab = cams[fi]
        ctx = cairo.Context(base)
        glow = cairo.Context(glow_s)
        glow.set_source_rgb(0, 0, 0)
        glow.paint()
        glow.set_operator(cairo.OPERATOR_ADD)
        draw_sky(ctx, cam, t)
        draw_moon(ctx, glow, cam, t)
        draw_layers(ctx, cam, layers)
        draw_ground(ctx, cam)
        tw = warp(t)
        snow.layers[0]['a'] = 0.45
        # far snow only
        from world import Snow as _S
        _layers = snow.layers
        snow.layers = _layers[:1]
        snow.draw(ctx, cam, t, tw)
        snow.layers = _layers
        cam.apply(ctx, 1.0)
        cam.apply(glow, 1.0, 0.5)
        # shadows
        draw_shadow(ctx, rx, max(0, ry - 0.86), 0.55)
        for w in WOLVES:
            if w.alive(t):
                x, y = w.pos(t)
                d = w.tr.get('dark', t)
                if d < 0.9:
                    draw_shadow(ctx, x, max(0, y - 0.78 * w.s), 0.8 * w.s, 0.45 * (1 - d))
        for w in WOLVES:
            draw_wolf_full(ctx, glow, w, t)
        # afterimages
        if in_any(t, AFTERIMAGE):
            for k in range(5, 0, -1):
                Pk = HP(t - k * 0.028)
                draw_hero(ctx, Pk, ghost=(0.9, 0.25, 0.15) if k % 2 else (1.0, 0.6, 0.35),
                          alpha=0.28 * (1 - k / 6))
        draw_hero(ctx, P, glow, cloak=cloak.polys())
        # hero eye glint when she looks up
        if T_HEADUP + 0.25 < t < T_HEADUP + 1.1:
            g = math.sin(clamp((t - T_HEADUP - 0.25) / 0.85) * PI)
            ex = P.head[0] + P.face * 0.07
            ey = P.head[1] + 0.005
            glow.arc(ex, ey, 0.05, 0, 2 * PI)
            glow.set_source_rgba(1.0, 0.5, 0.2, 0.9 * g)
            glow.fill()
            ctx.arc(ex, ey, 0.012, 0, 2 * PI)
            ctx.set_source_rgba(1.0, 0.75, 0.5, g)
            ctx.fill()
        draw_smear(ctx, glow, t)
        Pp.draw(ctx, glow, cam)
        E.draw(ctx, glow, cam, t)
        snow.layers = _layers[1:2]
        snow.draw(ctx, cam, t, tw)
        draw_foreground(ctx, cam, fg)
        snow.layers = _layers[2:]
        snow.draw(ctx, cam, t, tw)
        snow.layers = _layers
        title_card(ctx, glow, t)
        base.flush()
        glow_s.flush()
        fade = clamp(t / 0.9) * clamp((DUR - t) / 0.7)
        img = post(base, glow_s, fi, flash=fl, aberr=ab, impact=imp, fade=fade)
        if pipe is not None:
            pipe.write(img.tobytes())
        if out_png_dir is not None:
            from PIL import Image
            Image.fromarray(img).save(f'{out_png_dir}/f{fi:04d}.png')
        if fi % 30 == 0:
            el = time.time() - tstart
            print(f'frame {fi}/{f1}  t={t:.2f}  {el:.0f}s', file=sys.stderr, flush=True)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--preview', default=None)
    ap.add_argument('--out', default='scratch/prev')
    ap.add_argument('--video', action='store_true')
    ap.add_argument('--from_', type=float, default=0.0)
    ap.add_argument('--to', type=float, default=DUR)
    a = ap.parse_args()
    import os
    if a.preview:
        os.makedirs(a.out, exist_ok=True)
        ts = [float(x) for x in a.preview.split(',')]
        frames = set(int(round(x * FPS)) for x in ts)
        render(frames, a.out, t_to=max(ts) + 0.05)
    elif a.video:
        os.makedirs('out', exist_ok=True)
        cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}',
               '-r', str(FPS), '-i', '-', '-i', 'out/ember.wav', '-c:v', 'libx264', '-preset', 'slow',
               '-crf', '16', '-pix_fmt', 'yuv420p', '-c:a', 'aac', '-b:a', '320k', '-movflags', '+faststart',
               '-shortest', 'out/ember.mp4']
        pr = subprocess.Popen(cmd, stdin=subprocess.PIPE)
        render(None, None, pipe=pr.stdin)
        pr.stdin.close()
        pr.wait()
        print('wrote out/ember.mp4')
