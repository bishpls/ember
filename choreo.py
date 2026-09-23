"""EMBER — choreography, camera and FX cues.  Everything keyed to common.py."""
import bisect
import math
import numpy as np
from common import *
from rig import HeroPose, POSE0, WolfPose, D2R, PI


# ---------------------------------------------------------------------------
# Generic sparse keyframe track
# ---------------------------------------------------------------------------
class Track:
    def __init__(self, defaults):
        self.d = dict(defaults)
        self.k = {}
        self._t = {}

    def key(self, t, ease='io', **vals):
        for p, v in vals.items():
            lst = self.k.setdefault(p, [])
            lst.append((t, v, ease))
            lst.sort(key=lambda q: q[0])
            self._t[p] = [q[0] for q in lst]
        return self

    def get(self, p, t):
        ks = self.k.get(p)
        if not ks:
            return self.d[p]
        ts = self._t[p]
        i = bisect.bisect_right(ts, t)
        if i == 0:
            return ks[0][1]
        if i >= len(ks):
            return ks[-1][1]
        t0, v0, _ = ks[i - 1]
        t1, v1, e = ks[i]
        u = (t - t0) / (t1 - t0) if t1 > t0 else 1.0
        return v0 + (v1 - v0) * EASE[e](clamp(u))

    def eval(self, t):
        return {p: self.get(p, t) for p in self.d}


class Arc:
    """Ballistic segment in warped time, optional horizontal drag."""

    def __init__(self, t0, t1, p0, p1, g=24.0, xdrag=0.0):
        self.t0, self.t1, self.p0, self.p1, self.g, self.xdrag = t0, t1, p0, p1, g, xdrag
        self.T = warp(t1) - warp(t0)
        self.vy = (p1[1] - p0[1] + 0.5 * g * self.T ** 2) / self.T

    def __call__(self, t):
        tau = warp(t) - warp(self.t0)
        u = tau / self.T
        if self.xdrag > 0:
            k = self.xdrag
            u = (1 - math.exp(-k * tau)) / (1 - math.exp(-k * self.T))
        x = lerp(self.p0[0], self.p1[0], u)
        y = self.p0[1] + self.vy * tau - 0.5 * self.g * tau * tau
        return (x, y)


class Mover:
    """Root position = keyed track, overridden by arcs / custom functions."""

    def __init__(self, x, y):
        self.tr = Track(dict(x=x, y=y))
        self.segs = []   # (t0, t1, fn)

    def key(self, t, x=None, y=None, ease='io'):
        kw = {}
        if x is not None:
            kw['x'] = x
        if y is not None:
            kw['y'] = y
        self.tr.key(t, ease, **kw)

    def arc(self, t0, t1, p0, p1, g=24.0, xdrag=0.0):
        a = Arc(t0, t1, p0, p1, g, xdrag)
        self.segs.append((t0, t1, a))
        self.key(t0, *p0, ease='lin')
        self.key(t1, *p1, ease='lin')
        return a

    def fn(self, t0, t1, f):
        self.segs.append((t0, t1, f))
        p0, p1 = f(t0), f(t1)
        self.key(t0, *p0, ease='lin')
        self.key(t1, *p1, ease='lin')

    def __call__(self, t):
        for (t0, t1, f) in self.segs:
            if t0 <= t < t1:
                return f(t)
        return (self.tr.get('x', t), self.tr.get('y', t))


# ===========================================================================
# HERO
# ===========================================================================
HT = Track(dict(POSE0, wind=1.0))
HR = Mover(0.0, 0.86)


def pose(t, ease='io', **kw):
    HT.key(t, ease, **kw)


def root(t, x=None, y=None, ease='io'):
    HR.key(t, x, y, ease)


def HP(t):
    p = HT.eval(t)
    return HeroPose(p, HR(t))


STANCE = dict(fx1=0.40, fy1=-0.75, fx2=-0.42, fy2=-0.75, gnd=1.0)
TUCK = dict(fx1=0.25, fy1=-0.45, fx2=-0.2, fy2=-0.55, gnd=0.0)
STAND = dict(fx1=0.14, fy1=-0.9, fx2=-0.16, fy2=-0.9, gnd=1.0)
TWO = dict(g1=0.30, g2=0.52, two=1.0)

# --- INTRO: still, head bowed, weapon on the back --------------------------
IDLE = dict(held=0.0, unfold=0.0, two=0.0, h1x=0.07, h1y=-0.47, hx=-0.03, hy=-0.46,
            head=26, lean=3, **STAND)
pose(0.0, **dict(POSE0, wind=1.0, **IDLE))
for i, tb in enumerate(np.arange(0.0, T_HEADUP, BEAT * 2)):
    pose(tb + BEAT, 's', sq=1.012)
    pose(tb + 2 * BEAT, 's', sq=0.995)
pose(T_HEADUP, 's', sq=1.0, head=26)
pose(T_HEADUP + 0.45, 'out', head=-6, lean=0)
# reach over shoulder
pose(6.05, 'io', h1x=0.07, h1y=-0.47, lean=0)
pose(T_UNFOLD1 - 0.08, 'io', h1x=-0.20, h1y=0.08, lean=8, head=-2)
root(6.05, 0.0, 0.86)
root(T_UNFOLD1, 0.0, 0.82)
# grab + first unfold (click)
pose(T_UNFOLD1 - 0.08, 'io', held=0.0, unfold=0.0, wx=0.22, wy=-0.05, wa=60, g1=0.5, bside=-1,
     two=0.0, hx=-0.03, hy=-0.46)
pose(T_UNFOLD1, 'outx', held=1.0, unfold=0.0, wx=0.20, wy=-0.02, wa=60, g1=0.5)
pose(T_UNFOLD1 + 0.06, 'outx', unfold=0.55)
# twirl + second unfold (clack)
pose(T_UNFOLD2 + 0.05, 'outx', unfold=1.0)
pose(T_UNFOLD1 + 0.08, 'io', wa=60, hx=-0.03, hy=-0.46, lean=8)
pose(T_BREATH - 0.02, 'io', wa=-300 + 20, wx=0.12, wy=-0.12, hx=-0.35, hy=-0.15, lean=12, **STAND)
# GUARD at the breath
pose(T_BREATH, 'io', g1=0.5)
GUARD = dict(wx=-0.05, wy=-0.30, wa=-155, bside=1.0, lean=24, head=-10, **TWO, **STANCE)
pose(T_BREATH + 0.08, 'io', **GUARD)
root(T_BREATH - 0.05, 0.0, 0.82)
root(T_BREATH + 0.10, 0.0, 0.66)
# anticipation
pose(7.36, 'io', wa=-178, lean=30, wx=-0.12, fx1=0.45, g1=0.30)
pose(7.44, 'in2', wa=-90, g1=0.55, wx=0.05, wy=-0.1)
root(7.36, -0.05, 0.60)
# STRIKE (rising cut)
pose(T_DROP, 'lin', wa=20, lean=14, wx=0.25, wy=-0.2, fx1=0.62, fy1=-0.62, head=-12, g1=0.40)
root(T_DROP, 0.35, 0.70, 'in2')
pose(T_DROP + 0.07, 'lin', wa=24, lean=13)            # hit-stop hold
root(T_DROP + 0.07, 0.37, 0.71, 'lin')
pose(T_DROP + 0.32, 'outx', g1=0.30, wa=128, lean=-12, wx=0.1, wy=0.15, fx1=0.35, fy1=-0.85, fx2=-0.3,
     fy2=-0.85, head=-18)
root(T_DROP + 0.32, 0.55, 0.98, 'out')
pose(8.0, 'io', wa=98, lean=4, wx=0.15, wy=-0.05, head=-5, **STAND)
root(8.0, 0.55, 0.86)
# turn left (face flip hidden in a vertical weapon)
pose(8.08, 'io', wa=92)
pose(8.10, 'step', face=-1.0, wa=88)
# crouch, aim weapon back for recoil
AIMBACK = dict(wx=-0.10, wy=-0.28, wa=192, bside=-1.0, lean=36, g1=0.35, g2=0.55, two=1.0,
               fx1=0.35, fy1=-0.62, fx2=-0.45, fy2=-0.58, gnd=1.0, head=-8)
pose(T_SHOT1 - 0.02, 'io', **AIMBACK)
root(T_SHOT1 - 0.02, 0.45, 0.62)
# recoil dash left
pose(T_SHOT1 + 0.06, 'outx', wa=208, lean=52, sq=0.92, **TUCK)
HR.arc(T_SHOT1, T_HOOK, (0.45, 0.62), (-3.95, 1.30), g=5.0, xdrag=2.2)
pose(9.05, 'io', wa=196, lean=40, sq=1.0)
pose(9.22, 'io', wa=150, lean=18, wx=0.0, wy=0.05, fx1=0.3, fy1=-0.7, fx2=-0.3, fy2=-0.75)
# HOOK (CW swing), then cartwheel spin with the wolf on the blade
pose(T_HOOK, 'in2', wa=-28, lean=35, wx=0.40, wy=-0.15, fx1=0.2, fy1=-0.85, fx2=-0.45, fy2=-0.6)
pose(T_HOOK + 0.05, 'lin', wa=-30, rot=0.0)
pose(T_THROW, 'io', rot=-360.0, wa=-10, lean=20)
HR.arc(T_HOOK, T_THROW, (-3.95, 1.30), (-4.55, 0.66), g=14.0)
pose(T_THROW + 0.001, 'step', rot=0.0)
# slide
pose(T_THROW + 0.08, 'out', wa=170, lean=30, wx=-0.1, wy=-0.2, fx1=0.55, fy1=-0.55, fx2=-0.4, fy2=-0.55,
     gnd=1.0, sq=0.9)
root(T_THROW, -4.55, 0.66)
root(T_BURST23 + 0.05, -5.55, 0.60, 'outx')
pose(T_BURST23 - 0.05, 'io', wa=95, lean=20, sq=1.0)
pose(T_BURST23, 'step', face=1.0, wa=85)
# anticipate W4
pose(10.78, 'io', wa=200, wx=-0.15, wy=-0.2, g1=0.4, two=0.0, hx=0.3, hy=-0.1, lean=25, bside=-1.0,
     fx1=0.3, fy1=-0.55, fx2=-0.35, fy2=-0.55, sq=0.95)
root(10.78, -5.5, 0.55)
# spinning jump kick
KICK = dict(fx1=0.88, fy1=-0.12, fx2=-0.25, fy2=-0.55, gnd=0.0)
pose(10.9, 'io', rot=0.0, **TUCK)
HR.arc(10.84, T_VAULT, (-5.5, 0.55), (-4.35, 1.75), g=20.0)
pose(T_VAULT - 0.04, 'in2', rot=-340.0, lean=-5, **KICK)
pose(T_VAULT, 'lin', rot=-360.0)
pose(T_VAULT + 0.06, 'lin', rot=-362.0)
pose(T_VAULT + 0.3, 'out', rot=-360.0, lean=10, **TUCK)
pose(T_VAULT + 0.301, 'step', rot=0.0)
HR.arc(T_VAULT, T_SHOT2, (-4.35, 1.75), (-4.0, 2.55), g=16.0)
# aim & fire at W4 in the air (wa filled after W4 is defined)
HR.arc(T_SHOT2, 12.92, (-4.0, 2.55), (-3.05, 0.60), g=22.0, xdrag=1.0)
pose(12.92, 'in2', sq=0.84, lean=28, wx=0.1, wy=-0.2, **STANCE)
pose(13.02, 'out', sq=1.0)
root(13.02, -3.05, 0.66, 'out')
# 720 helicopter spin: W5 (right) then W6 (left)
SPIN = dict(g1=0.5, two=0.0, hx=-0.32, hy=0.0, wx=0.06, wy=-0.02, bside=-1.0)
pose(12.95, 'io', wa=165, **SPIN)
pose(T_SPIN, 'in2', wa=-18, lean=12)
pose(T_SPIN2, 'lin', wa=-198)
pose(T_BURST56, 'out', wa=-400, lean=5)
root(T_SPIN2, -2.95, 0.72)
# SUPER JUMP: muzzle down, fire
DOWN = dict(wx=0.14, wy=-0.12, wa=-90, g1=0.72, two=0.0, hx=-0.3, hy=0.1, bside=1.0)
pose(13.9, 'io', lean=10, sq=0.9, **DOWN, **STANCE)
root(13.9, -2.95, 0.55)
pose(T_SUPERJUMP + 0.08, 'outx', sq=1.12, lean=-4, **TUCK)
HR.arc(T_SUPERJUMP, T_DIVE, (-2.95, 0.55), (-0.6, 6.9), g=14.0)
pose(14.3, 'io', sq=1.0, rot=0.0)
pose(14.95, 'io', rot=360.0, wa=60, wx=0.15, wy=0.1, g1=0.3, two=1.0, **TUCK)
pose(T_DIVE, 'lin', rot=360.0, wa=90)
pose(T_DIVE + 0.001, 'step', rot=0.0)
# fire upward -> dive, overhead chop into the snow
pose(T_DIVE + 0.28, 'io', wa=125, wx=-0.05, wy=0.25, lean=-8, bside=-1.0, fx1=0.3, fy1=-0.8, fx2=-0.25,
     fy2=-0.85, gnd=0.0, **TWO)
HR.arc(T_DIVE, T_SLAM, (-0.6, 6.9), (0.5, 0.62), g=30.0)
pose(T_SLAM, 'in2', wa=-38, wx=0.35, wy=-0.2, lean=40, sq=0.8, **STANCE)
pose(T_SLAM + 0.2, 'out', sq=1.0, lean=25)
root(T_SLAM + 0.2, 0.5, 0.68, 'out')
# rapid fire (angles filled after W7-9)
# ---- DASH (slow-mo) ------------------------------------------------------
DASHP = dict(lean=62, g1=0.4, two=0.0, hx=-0.3, hy=-0.1, fx1=0.35, fy1=-0.55, fx2=-0.55, fy2=-0.35, gnd=0.0)
# waypoints: (t, x, y, face)
DASH_WP = [(T_DASH, 0.5, 0.70, 1), (T_DASH_HITS[0], 2.9, 1.25, 1), (T_DASH_HITS[0] + 0.14, 3.7, 1.1, 1),
           (T_DASH_HITS[1], -0.6, 1.3, -1), (T_DASH_HITS[1] + 0.14, -1.7, 1.0, -1),
           (T_DASH_HITS[2], 1.2, 1.35, 1), (T_DASH_BURST - 0.1, 2.9, 0.58, 1)]
pose(T_DASH - 0.15, 'io', wa=200, wx=-0.2, wy=-0.2, bside=-1.0, **DASHP)
root(T_DASH - 0.15, 0.5, 0.62)
for i, (tw_, x, y, f) in enumerate(DASH_WP):
    root(tw_, x, y, 'io' if i else 'io')
for i, th in enumerate(T_DASH_HITS):
    f = [1, -1, 1][i]
    pose(th - 0.14, 'io', wa=200, wx=-0.2)
    pose(th - 0.13, 'step', face=f * 1.0)
    pose(th, 'in2', wa=-10, wx=0.35, wy=-0.05, **DASHP)
    pose(th + 0.1, 'out', wa=-60)
pose(T_DASH_HITS[1] - 0.15, 'step', face=-1.0)
pose(T_DASH_HITS[2] - 0.15, 'step', face=1.0)
# finishing crouch, back to the wolves, blade extended
FINISH = dict(wa=-8, wx=0.42, wy=-0.12, lean=30, g1=0.35, two=0.0, hx=-0.35, hy=0.0, fx1=0.55,
              fy1=-0.5, fx2=-0.55, fy2=-0.5, gnd=1.0, head=-5)
pose(T_DASH_BURST - 0.1, 'out', sq=0.88, **FINISH)
pose(T_DASH_BURST + 0.15, 'io', sq=1.0)
root(T_DASH_BURST + 0.2, 2.9, 0.62)
# ---- ALPHA ---------------------------------------------------------------
pose(18.3, 'step', face=1.0)
pose(18.3, 'io', wa=95, wx=0.1, wy=-0.1, lean=5, g1=0.3, g2=0.52, two=1.0, bside=1.0, **STAND)
root(18.3, 2.9, 0.86)
pose(18.4, 'step', face=-1.0, wa=85)
pose(T_ALPHA + 0.1, 'io', wa=75, lean=15, **STANCE)
root(T_ALPHA + 0.1, 2.6, 0.70)
# brace during the roar
pose(T_ALPHA + 0.1, 'io', wind=1.0)
pose(19.2, 'io', lean=22, head=-12, wind=3.5)
root(19.2, 2.5, 0.66)
# charge in, block the swipe with the shaft
pose(19.3, 'io', lean=40, fx1=0.55, fy1=-0.55, fx2=-0.6, fy2=-0.5, wind=2.0)
root(19.55, -0.55, 0.72, 'io')
BLOCK = dict(wx=0.34, wy=-0.02, wa=98, g1=0.25, g2=0.62, two=1.0, lean=-6, head=-8, **STANCE)
pose(T_BLOCK, 'io', **BLOCK)
root(T_BLOCK, -0.75, 0.72)
# knocked back, sliding in the snow (weight!)
pose(T_BLOCK + 0.08, 'out', lean=28, sq=0.9, fx1=0.62, fy1=-0.5, fx2=-0.35, fy2=-0.6, wind=1.0)
root(T_BLOCK + 0.08, -0.45, 0.60, 'lin')
root(20.45, 2.65, 0.58, 'outx')
pose(20.45, 'io', sq=1.0, lean=32, wa=85)
# charge: recoil shot backward, knee-slide under the alpha, hook its hind leg
pose(T_CHARGE - 0.02, 'io', **AIMBACK)
root(T_CHARGE - 0.02, 2.65, 0.60)
SLIDE = dict(lean=-38, fx1=0.55, fy1=-0.45, fx2=-0.1, fy2=-0.55, gnd=1.0, head=15)
pose(T_CHARGE + 0.1, 'outx', wa=205, **SLIDE)
root(T_CHARGE + 0.02, 2.4, 0.55, 'lin')
root(T_UNDER, -3.3, 0.40, 'out')
pose(T_LEGHOOK - 0.1, 'io', wa=170, bside=1.0, wx=-0.25, wy=0.0)
pose(T_LEGHOOK, 'in2', wa=150, lean=-20)
root(T_LEGHOOK, -5.4, 0.45, 'out')
root(T_LAUNCH - 0.02, -5.8, 0.45, 'out')
# launch: fire into the snow, spin up and over
pose(T_LAUNCH - 0.02, 'io', rot=0.0, wa=-100, wx=0.1, wy=-0.2, g1=0.7, two=0.0, hx=-0.3, hy=0.1, lean=5,
     fx1=0.3, fy1=-0.6, fx2=-0.4, fy2=-0.6, gnd=1.0, head=-10)
HR.arc(T_LAUNCH, T_FINAL, (-5.8, 0.45), (-4.7, 5.0), g=14.0)
pose(T_LAUNCH + 0.1, 'outx', lean=-10, **TUCK)
pose(T_BREAK, 'out', rot=150.0, wa=-80, g1=0.3, g2=0.52, two=1.0, wx=0.2, wy=-0.1, lean=10,
     fx1=0.35, fy1=-0.7, fx2=-0.3, fy2=-0.8, gnd=0.0)
pose(T_RACK - 0.05, 'lin', rot=176.0, wa=-88)
pose(T_RACK + 0.03, 'outx', wa=-80, unfold=0.93)
pose(T_RACK2, 'io', wa=-86, unfold=0.93)
pose(T_RACK2 + 0.04, 'outx', unfold=1.0, wa=-92)
pose(T_FINAL - 0.02, 'io', rot=180.0, wa=-90)
# FINAL: fire up, rocket down onto the alpha, carve around it
pose(T_FINAL + 0.12, 'outx', rot=200.0, wa=-60, **TUCK)
# carve orbit defined after the alpha
# cleave pose + outro set after alpha definition

# ===========================================================================
# WOLVES
# ===========================================================================
class Wolf:
    def __init__(self, name, x, face, s=1.0, seed=0, dark=1.0, eye=0.0):
        self.name = name
        self.s = s
        self.seed = seed
        self.m = Mover(x, 0.78 * s)
        self.tr = Track(dict(pitch=0.0, roll=0.0, jaw=0.0, dark=dark, eye=eye, face=float(face),
                             split=0.0, legs_blend=0.0))
        self.modes = [(-1e9, 'stand')]
        self.attach = []      # (t0, t1, fn(t)->(x,y))
        self.t_die = None
        self.hits = []        # (t, x0, y0, x1, y1)
        self.split_ang = 0.0
        self.paw_fn = None
        self.autopitch = []   # (t0, t1)

    def mode(self, t, m):
        self.modes.append((t, m))
        self.modes.sort(key=lambda q: q[0])

    def mode_at(self, t):
        m = 'stand'
        for (tm, mm) in self.modes:
            if tm <= t:
                m = mm
        return m

    def pos(self, t):
        for (t0, t1, f) in self.attach:
            if t0 <= t < t1:
                return f(t)
        return self.m(t)

    def vel(self, t, e=0.012):
        a, b = self.pos(t - e), self.pos(t + e)
        dw = max(warp(t + e) - warp(t - e), 1e-5)
        return ((b[0] - a[0]) / dw, (b[1] - a[1]) / dw)

    def alive(self, t):
        return self.t_die is None or t < self.t_die

    def state(self, t):
        x, y = self.pos(t)
        p = self.tr.eval(t)
        m = self.mode_at(t)
        face = 1 if p['face'] >= 0 else -1
        pitch = p['pitch']
        for (a, b) in self.autopitch:
            if a <= t < b:
                vx, vy = self.vel(t)
                pitch += clamp(math.degrees(math.atan2(vy, abs(vx) + 1e-6)), -50, 50) * 0.7
        phase = face * x / (1.7 * self.s)
        legs = None
        if self.paw_fn is not None and m == 'swipe':
            legs = {'fn': self.paw_fn(t)}
        w = WolfPose(x, y, face, self.s, pitch, phase, m, p['jaw'], p['roll'], self.seed, t, legs)
        return w, p


WOLVES = []


def wolf(*a, **k):
    w = Wolf(*a, **k)
    WOLVES.append(w)
    return w


def head_center(C, face, s):
    """Body centre such that the wolf's head/neck sits at contact point C."""
    return (C[0] - face * 0.75 * s, C[1] - 0.22 * s)


def body_center(C, face, s):
    return (C[0] - face * 0.15 * s, C[1] - 0.05 * s)


def eyes_open(w, t, d=0.12):
    w.tr.key(t - 0.001, 'lin', eye=0.0)
    w.tr.key(t + d, 'outx', eye=1.0)


def run_to(w, t0, t1, x0, x1):
    w.mode(t0, 'run')
    w.m.key(t0, x0, 0.78 * w.s, 'lin')
    w.m.key(t1, x1, 0.78 * w.s, 'lin')


def emerge(w, t, d=0.25):
    w.tr.key(t, 'lin', dark=1.0)
    w.tr.key(t + d, 'out', dark=0.0)


def blade_pt(t, i=6):
    return HP(t).blade[i]


# --- W1: first cleave -------------------------------------------------------
W1 = wolf('W1', 5.0, -1, seed=1)
eyes_open(W1, EYE_TIMES[0])
W1.mode(6.8, 'crouch')
W1.m.key(6.8, 5.0, 0.78)
W1.m.key(T_BREATH, 4.9, 0.55)
emerge(W1, T_BREATH - 0.1, 0.3)
C1 = blade_pt(T_DROP, 7)
W1.mode(T_BREATH, 'leap')
W1.tr.key(T_BREATH, jaw=0.2).key(T_DROP - 0.1, jaw=1.0)
W1.m.arc(T_BREATH, T_DROP, (4.9, 0.55), head_center(C1, -1, 1.0), g=14)
W1.autopitch.append((T_BREATH + 0.05, T_DROP))
W1.hits.append((T_DROP, C1[0] - 0.9, C1[1] - 0.6, C1[0] + 0.6, C1[1] + 0.9))
W1.mode(T_DROP + 0.05, 'hurt')
hc = head_center(C1, -1, 1.0)
W1.m.arc(T_DROP, T_DROP + 0.14, hc, (hc[0] + 0.7, hc[1] + 0.55), g=5)
W1.tr.key(T_DROP, roll=0.0).key(T_DROP + 0.14, 'lin', roll=-40)
W1.t_die = T_DROP + 0.12
W1.split_ang = 50.0
W1.tr.key(T_DROP + 0.02, split=0.0).key(T_DROP + 0.12, 'out', split=0.35)

# --- W2: hooked and thrown, W3: hit by W2 --------------------------------
W2 = wolf('W2', -5.8, 1, seed=2)
eyes_open(W2, EYE_TIMES[1])
emerge(W2, 8.1, 0.3)
run_to(W2, 8.3, 9.05, -5.8, -5.0)
C2 = HP(T_HOOK).blade_tip
W2.mode(9.05, 'leap')
W2.tr.key(9.05, jaw=0.0).key(T_HOOK - 0.05, jaw=1.0)
W2.m.arc(9.05, T_HOOK, (-5.0, 0.78), head_center(C2, 1, 1.0), g=16)
W2.autopitch.append((9.06, T_HOOK))
W2.hits.append((T_HOOK, C2[0] - 0.3, C2[1] + 0.5, C2[0] + 0.2, C2[1] - 0.5))
_hk_off = (head_center(C2, 1, 1.0)[0] - C2[0], head_center(C2, 1, 1.0)[1] - C2[1])


def _on_blade(t):
    tp = HP(t).blade_tip
    # rotate the attach offset with the hero's spin
    r = -HT.get('rot', t) * D2R * HT.get('face', t)
    ox, oy = _hk_off
    return (tp[0] + math.cos(r) * ox - math.sin(r) * oy, tp[1] + math.sin(r) * ox + math.cos(r) * oy)


W2.attach.append((T_HOOK, T_THROW, _on_blade))
W2.mode(T_HOOK, 'hurt')
W2.tr.key(T_HOOK, 'lin', roll=0.0).key(T_THROW, 'io', roll=360.0)
W3 = wolf('W3', -7.6, 1, seed=3)
eyes_open(W3, EYE_TIMES[3])
emerge(W3, 9.2, 0.3)
run_to(W3, 9.3, T_COLLIDE, -7.6, -6.9)
C3 = (-6.9, 0.95)
rel = _on_blade(T_THROW)
W2.m.arc(T_THROW, T_COLLIDE, rel, (C3[0] + 0.3, C3[1] + 0.2), g=8)
W2.tr.key(T_COLLIDE, 'lin', roll=560.0)
W2.m.arc(T_COLLIDE, T_BURST23, (C3[0] + 0.3, C3[1] + 0.2), (-8.4, 1.6), g=6)
W2.tr.key(T_BURST23, 'lin', roll=640.0)
W3.mode(T_COLLIDE, 'hurt')
W3.m.arc(T_COLLIDE, T_BURST23, (-6.9, 0.78), (-8.2, 1.1), g=10)
W3.tr.key(T_COLLIDE, roll=0.0).key(T_BURST23, 'out', roll=120.0)
W2.t_die = W3.t_die = T_BURST23

# --- W4: jump-kicked, then shot mid-air -----------------------------------
W4 = wolf('W4', 7.0, -1, seed=4)
eyes_open(W4, EYE_TIMES[2])
emerge(W4, 9.3, 0.3)
run_to(W4, 9.35, 10.84, 7.0, -1.3)
C4 = HP(T_VAULT).foot_n
W4.mode(10.84, 'leap')
W4.tr.key(10.84, jaw=0.0).key(T_VAULT - 0.05, jaw=1.0)
W4.m.arc(10.84, T_VAULT, (-1.3, 0.78), head_center(C4, -1, 1.0), g=12)
W4.autopitch.append((10.85, T_VAULT))
W4.mode(T_VAULT, 'hurt')
hc4 = head_center(C4, -1, 1.0)
T4HIT = T_SHOT2 + 0.03
P4HIT = (hc4[0] + 4.4, 2.9)
W4.m.arc(T_VAULT, T4HIT, hc4, P4HIT, g=6)
W4.tr.key(T_VAULT, roll=0.0).key(T4HIT, 'out', roll=-300.0)
W4.t_die = T_SHOT2 + 0.07


def aim_wa(t, target, face):
    """Local weapon angle that points the muzzle from the chest at target."""
    rx, ry = HR(t)
    ch = (rx, ry + 0.5)
    dx, dy = target[0] - ch[0], target[1] - ch[1]
    ang = math.degrees(math.atan2(dy, dx * face))
    return ang


wa4 = aim_wa(T_SHOT2, P4HIT, 1)
pose(T_VAULT + 0.3, 'out', wx=0.2, wy=0.05, g1=0.3, g2=0.52, two=1.0, bside=1.0)
pose(T_SHOT2 - 0.05, 'io', wa=wa4, wx=0.3, wy=0.0, lean=0, head=-5)
pose(T_SHOT2 + 0.07, 'outx', wa=wa4 + 30, lean=-15, **TUCK)

# --- W5, W6: spin victims --------------------------------------------------
W5 = wolf('W5', 9.5, -1, seed=5)
eyes_open(W5, EYE_TIMES[4])
emerge(W5, 11.3, 0.3)
run_to(W5, 11.4, 12.85, 9.5, 0.2)
C5 = HP(T_SPIN).blade[6]
W5.mode(12.85, 'leap')
W5.tr.key(12.85, jaw=0.0).key(T_SPIN - 0.05, jaw=1.0)
W5.m.arc(12.85, T_SPIN, (0.2, 0.78), head_center(C5, -1, 1.0), g=14)
W5.autopitch.append((12.86, T_SPIN))
W5.hits.append((T_SPIN, C5[0] - 0.4, C5[1] - 0.6, C5[0] + 0.4, C5[1] + 0.6))
W5.mode(T_SPIN, 'hurt')
hc5 = head_center(C5, -1, 1.0)
W5.m.arc(T_SPIN, T_BURST56, hc5, (hc5[0] + 1.6, hc5[1] + 0.9), g=8)
W5.tr.key(T_SPIN, roll=0.0).key(T_BURST56, 'out', roll=-90.0)
W5.t_die = T_BURST56
W6 = wolf('W6', -12.0, 1, seed=6, dark=0.0, eye=1.0)
run_to(W6, 11.6, 13.0, -12.0, -6.2)
C6 = HP(T_SPIN2).blade[6]
W6.mode(13.0, 'leap')
W6.tr.key(13.0, jaw=0.0).key(T_SPIN2 - 0.05, jaw=1.0)
W6.m.arc(13.0, T_SPIN2, (-6.2, 0.78), head_center(C6, 1, 1.0), g=14)
W6.autopitch.append((13.01, T_SPIN2))
W6.hits.append((T_SPIN2, C6[0] - 0.4, C6[1] + 0.6, C6[0] + 0.4, C6[1] - 0.6))
W6.mode(T_SPIN2, 'hurt')
hc6 = head_center(C6, 1, 1.0)
W6.m.arc(T_SPIN2, T_BURST56, hc6, (hc6[0] - 1.5, hc6[1] + 0.8), g=8)
W6.tr.key(T_SPIN2, roll=0.0).key(T_BURST56, 'out', roll=90.0)
W6.t_die = T_BURST56

# --- W7, W8, W9: slam + rapid fire ---------------------------------------
W7 = wolf('W7', -12.0, 1, seed=7, dark=0.0, eye=1.0)
W8 = wolf('W8', 11.0, -1, seed=8, dark=0.0, eye=1.0)
W9 = wolf('W9', 13.0, -1, seed=9, dark=0.0, eye=1.0)
run_to(W7, 14.0, T_SLAM, -12.0, -1.6)
run_to(W8, 14.0, T_SLAM, 11.0, 2.7)
run_to(W9, 14.1, T_SLAM, 13.0, 4.1)
rapid_targets = []
for w, tr, dest, rl in [(W7, T_RAPID[0], (-4.2, 3.3), 200), (W8, T_RAPID[1], (4.0, 3.1), -220),
                        (W9, T_RAPID[2], (6.2, 3.8), -160)]:
    w.mode(T_SLAM, 'hurt')
    p0 = w.m(T_SLAM - 0.001)
    th = tr + 0.05
    w.m.arc(T_SLAM, th, p0, dest, g=8)
    w.tr.key(T_SLAM, roll=0.0).key(th, 'out', roll=rl)
    w.t_die = th + 0.01
    rapid_targets.append(dest)
for i, tr in enumerate(T_RAPID):
    f = [-1, 1, 1][i]
    wa_ = aim_wa(tr, rapid_targets[i], f)
    pose(tr - 0.06, 'io', wa=wa_, wx=0.25, wy=0.05, g1=0.3, g2=0.52, two=1.0, lean=0,
         bside=1.0, **STANCE)
    pose(tr - 0.05, 'step', face=f * 1.0)
    pose(tr + 0.04, 'outx', wa=wa_ + 22, lean=-12)
pose(T_RAPID[0] - 0.2, 'io', wa=40, wx=0.2, wy=0.0, lean=10, **STANCE)
root(T_RAPID[0], 0.5, 0.7)
root(T_RAPID[2] + 0.1, 0.5, 0.68)

# --- W10-12: the slow-mo dash ------------------------------------------
dash_w = []
for i, (th, sx, f) in enumerate(zip(T_DASH_HITS, [8.0, -7.0, 7.5], [-1, 1, -1])):
    w = wolf(f'W{10 + i}', sx, f, seed=10 + i, dark=0.0, eye=1.0)
    C = blade_pt(th, 5)
    hc = body_center(C, f, 1.0)
    t_leap = 16.25 + 0.1 * i
    run_to(w, 15.6, t_leap, sx, sx * 0.55)
    w.mode(t_leap, 'leap')
    w.tr.key(t_leap, jaw=0.0).key(th, jaw=1.0)
    w.m.arc(t_leap, th, (sx * 0.55, 0.78), hc, g=12)
    w.autopitch.append((t_leap + 0.01, th))
    drift = w.m.segs[-1][2]
    vx = (hc[0] - sx * 0.55) / drift.T * 0.25
    w.m.arc(th, T_DASH_BURST, hc, (hc[0] + vx * (warp(T_DASH_BURST) - warp(th)), hc[1] + 0.05), g=1.0)
    w.hits.append((th, C[0] - 0.7, C[1] + 0.35 * (-1) ** i, C[0] + 0.7, C[1] - 0.35 * (-1) ** i))
    w.t_die = T_DASH_BURST
    w.split_ang = [-20, 25, -15][i]
    w.tr.key(th + 0.05, split=0.0).key(T_DASH_BURST, 'in', split=0.25)
    dash_w.append(w)

# --- ALPHA -------------------------------------------------------------------
AS = 2.4
AL = wolf('ALPHA', -15.0, 1, s=AS, seed=21, dark=0.0, eye=1.0)
AY = 0.78 * AS
AL.mode(18.2, 'leap')
AL.m.key(18.2, -15.0, 7.0)
AL.m.arc(18.2, T_ALPHA, (-15.0, 7.0), (-5.5, AY), g=20)
AL.autopitch.append((18.21, T_ALPHA - 0.05))
AL.mode(T_ALPHA, 'crouch')
AL.m.key(T_ALPHA + 0.1, -5.5, AY - 0.45, 'out')
AL.mode(T_ALPHA + 0.3, 'stand')
AL.m.key(T_ALPHA + 0.45, -5.5, AY, 'io')
# roar
AL.tr.key(T_ALPHA + 0.05, pitch=0.0, jaw=0.2)
AL.tr.key(T_ALPHA + 0.3, 'out', pitch=14.0, jaw=1.0)
AL.tr.key(19.45, 'io', pitch=10.0, jaw=0.9)
AL.tr.key(19.6, 'io', pitch=-6.0, jaw=0.5)
# lunge + swipe into the block
AL.m.key(19.4, -5.5, AY)
AL.m.key(T_BLOCK, -3.6, AY - 0.1, 'in2')
AL.mode(19.45, 'swipe')
blk = HP(T_BLOCK).w_grip
blk_top = (blk[0] - 0.05, blk[1] + 0.35)
AL.paw_fn = lambda t: (lerp(AL.pos(t)[0] + 1.8, blk_top[0], smooth((t - 19.45) / (T_BLOCK - 19.45))),
                       lerp(AL.pos(t)[1] + 1.2, blk_top[1], smooth((t - 19.45) / (T_BLOCK - 19.45))))
AL.mode(T_BLOCK + 0.25, 'stand')
AL.m.key(20.3, -3.2, AY)
AL.tr.key(20.3, pitch=0.0, jaw=0.4)
# second swipe misses overhead
AL.mode(T_UNDER - 0.2, 'swipe')
AL.mode(T_UNDER + 0.15, 'stand')
# leg hooked: rear drops
AL.tr.key(T_LEGHOOK, pitch=0.0, jaw=0.4)
AL.tr.key(T_LEGHOOK + 0.25, 'out', pitch=-14.0, jaw=1.0)
AL.m.key(T_LEGHOOK, -3.2, AY)
AL.m.key(T_LEGHOOK + 0.25, -3.4, AY - 0.3, 'out')
# rears up, looking at her in the sky
AL.tr.key(T_BREAK - 0.2, 'io', pitch=24.0, jaw=0.9)
AL.m.key(T_BREAK - 0.2, -3.5, AY + 0.1)
AL.tr.key(T_FINAL, 'io', pitch=28.0, jaw=1.0)
AL.mode(T_LAUNCH, 'stand')

# carve: hero orbits the alpha
ACX, ACY = -3.5, AY + 0.35
R_ORB = 2.25
T_ORB0 = T_CARVE0 - 0.1
T_ORB1 = T_CLEAVE - 0.25
HR.fn(T_FINAL, T_ORB0, lambda t: (lerp(-4.7, ACX - 0.4, EASE['in2']((t - T_FINAL) / (T_ORB0 - T_FINAL))),
                                    lerp(5.0, ACY + R_ORB, EASE['in2']((t - T_FINAL) / (T_ORB0 - T_FINAL)))))


def _orbit(t):
    u = (t - T_ORB0) / (T_ORB1 - T_ORB0)
    th = (90 - 450 * EASE['s'](u) - 2) * D2R
    return (ACX + R_ORB * 1.1 * math.cos(th), ACY + R_ORB * 0.85 * math.sin(th))


HR.fn(T_ORB0, T_ORB1, _orbit)
pose(T_ORB0, 'io', rot=180.0 + 180.0, wa=100, g1=0.5, two=0.0, hx=-0.3, hy=0.1, wx=0.05, wy=0.0, bside=-1.0,
     lean=20, **TUCK)
for i, tc in enumerate(T_CARVE):
    pose(tc, 'lin', wa=100 - 360 * (i + 1) + 20)
pose(T_ORB1, 'out', rot=360 - 450.0 + 20, wa=100 - 360 * 7)
for i, tc in enumerate(T_CARVE):
    AL.tr.key(tc, 'outx', pitch=28 - 6 * ((-1) ** i), roll=4 * (-1) ** i)
    AL.tr.key(tc + 0.1, 'io', pitch=22, roll=0)
    bp = None
AL.mode(T_CARVE0, 'stand')
# cleave: from the right side, straight through, finish low on the left
pose(T_ORB1 + 0.001, 'lin', rot=-70.0)
pose(T_CLEAVE - 0.14, 'io', rot=0.0, wa=205, wx=-0.2, wy=-0.25, g1=0.35, g2=0.55, two=1.0,
     bside=-1.0, lean=45, fx1=0.4, fy1=-0.6, fx2=-0.5, fy2=-0.4, gnd=0.0)
pose(T_CLEAVE - 0.139, 'step', face=-1.0)
HR.fn(T_ORB1, T_CLEAVE - 0.14, lambda t: (lerp(_orbit(T_ORB1 - 1e-4)[0], ACX + 2.6,
                                                   smooth((t - T_ORB1) / (T_CLEAVE - 0.14 - T_ORB1))),
                                              lerp(_orbit(T_ORB1 - 1e-4)[1], 1.6,
                                                   smooth((t - T_ORB1) / (T_CLEAVE - 0.14 - T_ORB1)))))
root(T_CLEAVE + 0.06, ACX - 3.2, 0.62, 'in2')
pose(T_CLEAVE, 'in2', **dict(FINISH, wa=-10, wx=0.4, wy=-0.1))
pose(T_CLEAVE + 0.06, 'out', sq=0.86)
pose(T_CLEAVE + 0.35, 'io', sq=1.0)
root(T_CLEAVE + 0.5, ACX - 3.35, 0.62, 'out')
AL.hits.append((T_CLEAVE, ACX + 2.0, ACY + 0.1, ACX - 2.4, ACY - 0.25))
AL.split_ang = 3.0
AL.tr.key(T_CLEAVE + 0.2, split=0.0).key(T_ALPHA_BURST, 'in', split=0.5)
AL.t_die = T_ALPHA_BURST
AL.mode(T_CLEAVE, 'stand')
AL.tr.key(T_CLEAVE, pitch=20.0, jaw=1.0, roll=0)
# outro: rise, twirl, fold, weapon to the back
pose(T_ALPHA_BURST + 0.25, 'io', **FINISH)
pose(27.3, 'io', lean=4, head=-4, wx=0.1, wy=-0.05, wa=0.0, g1=0.5, sq=1.0, **STAND)
root(27.3, ACX - 3.35, 0.86)
pose(27.75, 'out', wa=520.0 - 360)
pose(T_FOLD, 'io', wa=170.0, unfold=1.0)
pose(T_FOLD + 0.06, 'outx', unfold=0.5)
pose(T_FOLD + 0.2, 'outx', unfold=0.0)
pose(T_FOLD + 0.2, 'io', held=1.0, h1x=0.07, h1y=-0.47)
pose(28.45, 'io', held=0.0, two=0.0, hx=-0.03, hy=-0.46)
pose(29.2, 's', head=-14, wind=1.6)

# ===========================================================================
# CAMERA
# ===========================================================================
CT = Track(dict(fx=0.0, fy=1.2, follow=0.0, ox=0.0, oy=0.5, zoom=1.0, roll=0.0, stiff=10.0))


def cam(t, ease='io', **kw):
    CT.key(t, ease, **kw)


cam(0.0, fx=0.9, fy=10.5, zoom=0.72, follow=0.0, roll=-1.5, stiff=30)
cam(3.4, 'io', fx=0.0, fy=1.55, zoom=1.25, roll=0.0)
cam(T_HEADUP, 'io', fx=0.15, fy=1.45, zoom=1.9, roll=1.5)
cam(T_HEADUP + 0.6, 'out', fx=0.4, fy=1.7, zoom=1.0, roll=0.0)
cam(T_BREATH, 'io', fx=0.8, fy=1.4, zoom=1.12)
cam(T_DROP, 'in', fx=1.2, fy=1.6, zoom=1.3, roll=-3)
cam(T_DROP + 0.3, 'out', fx=0.8, fy=1.5, zoom=1.05, roll=0, follow=0.0, stiff=8)
cam(T_SHOT1, 'io', follow=0.0, fx=0.3, fy=1.4, zoom=1.0)
cam(T_SHOT1 + 0.25, 'out', follow=1.0, ox=-0.8, oy=0.6, zoom=1.05, stiff=7)
cam(T_HOOK, 'io', ox=-0.3, oy=0.7, zoom=1.2, roll=4)
cam(T_BURST23, 'io', ox=-0.6, oy=0.8, zoom=0.95, roll=0)
cam(10.8, 'io', follow=0.6, fx=-3.0, fy=1.4, ox=0.8, oy=0.8, zoom=0.95)
cam(T_VAULT, 'io', follow=1.0, ox=0.6, oy=0.3, zoom=1.15, roll=-4)
cam(T_SHOT2, 'io', ox=1.4, oy=0.2, zoom=0.95, roll=0)
cam(T_SPIN, 'io', ox=0.2, oy=0.7, zoom=1.2, roll=2)
cam(T_SUPERJUMP, 'io', ox=0.3, oy=0.8, zoom=1.0, roll=0, stiff=9)
cam(T_SUPERJUMP + 0.25, 'out', ox=0.6, oy=0.3, zoom=0.88, stiff=40)
cam(T_DIVE, 'io', ox=0.3, oy=-0.2, zoom=0.85, roll=6, stiff=12)
cam(T_SLAM, 'in', ox=0.2, oy=0.9, zoom=0.82, roll=0, stiff=10)
cam(T_RAPID[2], 'io', follow=0.5, fx=0.5, fy=1.9, ox=0.0, oy=1.0, zoom=0.78)
cam(T_DASH, 'io', follow=0.3, fx=0.8, fy=1.5, zoom=1.02, roll=-2, stiff=10)
cam(T_DASH_BURST - 0.05, 'io', follow=0.3, fx=1.0, fy=1.5, zoom=1.2, roll=3)
cam(T_DASH_BURST + 0.2, 'out', zoom=1.0, roll=0)
cam(18.2, 'io', follow=0.0, fx=1.5, fy=1.6, zoom=1.0)
cam(T_ALPHA, 'io', follow=0.0, fx=-1.6, fy=2.3, zoom=0.78, roll=0, stiff=8)
cam(19.4, 'io', fx=-1.4, fy=2.2, zoom=0.82)
cam(T_BLOCK, 'in', fx=-1.4, fy=1.9, zoom=0.98, roll=-3)
cam(20.4, 'io', fx=-0.6, fy=1.9, zoom=0.88, roll=0)
cam(T_CHARGE + 0.2, 'io', fx=-2.8, fy=1.8, zoom=0.8)
cam(T_LEGHOOK, 'io', fx=-4.0, fy=1.8, zoom=0.85)
cam(T_LAUNCH + 0.15, 'io', follow=0.0, fx=-4.8, fy=3.2, zoom=0.82, stiff=8)
cam(T_BREAK + 0.2, 'io', fx=-5.0, fy=4.4, zoom=0.95, roll=-5, stiff=6)
cam(T_FINAL - 0.05, 'io', fx=-4.95, fy=4.6, zoom=1.12, roll=5)
cam(T_FINAL + 0.2, 'out', fx=-3.6, fy=2.6, zoom=0.82, roll=0, stiff=12)
cam(T_CLEAVE - 0.2, 'io', fx=-3.8, fy=2.3, zoom=0.86)
cam(T_CLEAVE, 'in', fx=-4.8, fy=1.8, zoom=1.05, roll=-4)
cam(T_ALPHA_BURST, 'io', fx=-5.4, fy=2.0, zoom=0.85, roll=0)
cam(T_TITLE, 'io', fx=-5.6, fy=1.75, zoom=1.08)
cam(DUR, 'io', fx=-5.55, fy=1.8, zoom=1.18)

SHAKES = []   # (t, amp_px, decay)
PUNCH = []    # (t, amt, decay)
FLASH = []    # (t, amt, decay)
IMPACT = []   # (t, frames)


def shake(t, a, d=8.0):
    SHAKES.append((t, a, d))


def punch(t, a, d=10.0):
    PUNCH.append((t, a, d))


def flash(t, a, d=12.0):
    FLASH.append((t, a, d))


for t_, a_, fl_, imp_ in [(T_DROP, 26, 0.35, 1), (T_HOOK, 12, 0.15, 0), (T_VAULT, 16, 0.2, 0),
                          (T_SPIN, 12, 0.15, 0), (T_SPIN2, 10, 0.1, 0), (T_SLAM, 40, 0.3, 1),
                          (T_DASH_BURST, 22, 0.4, 1), (T_ALPHA, 38, 0.0, 0), (T_BLOCK, 30, 0.3, 1),
                          (T_LEGHOOK, 10, 0.1, 0), (T_CLEAVE, 45, 0.6, 2), (T_ALPHA_BURST, 30, 0.35, 0),
                          (T_COLLIDE, 8, 0.0, 0), (T_BURST23, 10, 0.1, 0), (T_BURST56, 10, 0.1, 0)]:
    shake(t_, a_)
    punch(t_, a_ / 400.0)
    if fl_:
        flash(t_, fl_)
    if imp_:
        IMPACT.append((t_, imp_))
for t_ in [T_SHOT1, T_SHOT2, T_DIVE, T_CHARGE, T_LAUNCH] + T_RAPID:
    shake(t_, 9, 14)
    punch(t_, 0.02, 14)
for t_ in [T_SUPERJUMP, T_FINAL]:
    shake(t_, 18, 10)
    punch(t_, 0.04, 10)
    flash(t_, 0.15)
shake(T_ALPHA + 0.15, 14, 1.4)   # roar rumble
for t_ in T_CARVE:
    shake(t_, 9, 16)
    punch(t_, 0.02, 16)


def _noise1(x, seed):
    return (math.sin(x * 1.7 + seed) * 0.5 + math.sin(x * 3.1 + seed * 2.3) * 0.3 +
            math.sin(x * 7.3 + seed * 0.7) * 0.2)


def cam_fx(t):
    sx = sy = 0.0
    ab = 0.0
    for (t0, a, d) in SHAKES:
        if t >= t0:
            e = a * math.exp(-(t - t0) * d)
            if e > 0.2:
                sx += e * _noise1(t * 40, t0)
                sy += e * _noise1(t * 40, t0 + 5)
                ab = max(ab, e * 0.25)
    z = 1.0
    for (t0, a, d) in PUNCH:
        if t >= t0:
            z += a * math.exp(-(t - t0) * d)
    fl = 0.0
    for (t0, a, d) in FLASH:
        if t >= t0:
            fl += a * math.exp(-(t - t0) * d)
    imp = 0.0
    for (t0, nf) in IMPACT:
        if t0 <= t < t0 + nf / FPS:
            imp = 1.0
    return (sx, sy), z, min(fl, 1.0), imp, ab


def camera_path(n_sub=4):
    """Spring-smoothed camera, sampled per frame."""
    from world import Cam
    out = []
    dt = 1.0 / (FPS * n_sub)
    t = 0.0
    p0 = CT.eval(0.0)
    x, y = p0['fx'], p0['fy']
    vx = vy = 0.0
    nfr = int(DUR * FPS)
    for f in range(nfr):
        tf = f / FPS
        while t < tf:
            p = CT.eval(t)
            hx, hy = HR(t)
            tx = lerp(p['fx'], hx + p['ox'], p['follow'])
            ty = lerp(p['fy'], hy + p['oy'], p['follow'])
            k = p['stiff']
            ax = k * k * (tx - x) - 2 * k * vx
            ay = k * k * (ty - y) - 2 * k * vy
            vx += ax * dt
            vy += ay * dt
            x += vx * dt
            y += vy * dt
            t += dt
        p = CT.eval(tf)
        sh, z, fl, imp, ab = cam_fx(tf)
        out.append((Cam(x, y, p['zoom'] * z, p['roll'], sh), fl, imp, ab))
    return out
