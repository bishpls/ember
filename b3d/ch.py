"""EMBER II — choreography infrastructure: tracks, 3D arcs, footstep planner, foot locks,
rigid-body tumbles, wolf scripts and the camera shot list."""
import bisect
import math
import numpy as np
from tl import *
import kin
from kin import v3, norm, UP, D2R, rot_axis

TO_MOON = norm(v3(math.cos(13 * D2R) * math.cos(200 * D2R), math.cos(13 * D2R) * math.sin(200 * D2R),
                  math.sin(13 * D2R)))


def lerp(a, b, u):
    return a + (b - a) * u


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


class Arc3:
    """Ballistic flight between p0@t0 and p1@t1 (warped time), gravity g, optional drag on xy."""

    def __init__(self, t0, t1, p0, p1, g=9.81, drag=0.0):
        self.t0, self.t1 = t0, t1
        self.p0, self.p1 = v3(*p0), v3(*p1)
        self.g, self.drag = g, drag
        self.T = warp(t1) - warp(t0)
        self.vz = (self.p1[2] - self.p0[2] + 0.5 * g * self.T ** 2) / self.T

    def __call__(self, t):
        tau = warp(t) - warp(self.t0)
        u = tau / self.T
        if self.drag > 0:
            k = self.drag
            u = (1 - math.exp(-k * tau)) / (1 - math.exp(-k * self.T))
        p = lerp(self.p0, self.p1, u)
        p[2] = self.p0[2] + self.vz * tau - 0.5 * self.g * tau * tau
        return p

    def vel(self, t):
        e = 1e-3
        return (self(t + e) - self(t - e)) / (warp(t + e) - warp(t - e))


class Mover:
    def __init__(self, p):
        self.tr = Track(dict(x=p[0], y=p[1], z=p[2]))
        self.segs = []

    def key(self, t, p, ease='io'):
        self.tr.key(t, ease, x=p[0], y=p[1], z=p[2])

    def arc(self, t0, t1, p0, p1, g=9.81, drag=0.0):
        a = Arc3(t0, t1, p0, p1, g, drag)
        self.segs.append((t0, t1, a))
        self.key(t0, p0, 'lin')
        self.key(t1, p1, 'lin')
        return a

    def fn(self, t0, t1, f):
        self.segs.append((t0, t1, f))
        self.key(t0, tuple(f(t0)), 'lin')
        self.key(t1, tuple(f(t1 - 1e-6)), 'lin')

    def __call__(self, t):
        for (t0, t1, f) in self.segs:
            if t0 <= t < t1:
                return v3(*f(t))
        return v3(self.tr.get('x', t), self.tr.get('y', t), self.tr.get('z', t))

    def vel(self, t, e=1.0 / 96):
        return (self(t + e) - self(t - e)) / max(warp(t + e) - warp(t - e), 1e-5)


# ---------------------------------------------------------------------------
# Rigid tumble (for bodies knocked flying / collapsing): point-mass + spin with ground contact
# ---------------------------------------------------------------------------
class Tumble:
    def __init__(self, t0, p0, v0, R0, w0, t_end, radius=0.35, restitution=0.25, friction=4.0,
                 spin_damp=1.2, g=9.81, rest_z=None):
        self.t0 = t0
        dt = 1.0 / 480
        p, v, R, w = v3(*p0), v3(*v0), np.array(R0, float), v3(*w0)
        self.samples = []
        self.contacts = []
        tau = 0.0
        airborne = True
        Tw = warp(t_end) - warp(t0)
        rz = radius if rest_z is None else rest_z
        while tau <= Tw + dt:
            self.samples.append((tau, p.copy(), R.copy()))
            v[2] -= g * dt
            p = p + v * dt
            if p[2] < rz:
                p[2] = rz
                if airborne and v[2] < -1.0:
                    self.contacts.append((tau, p.copy(), float(-v[2]), float(math.hypot(v[0], v[1]))))
                airborne = False
                if v[2] < 0:
                    v[2] = -v[2] * restitution
                    # impact converts some linear speed into spin and bleeds energy
                    w = w * 0.7
                sp = math.hypot(v[0], v[1])
                if sp > 1e-4:
                    dec = min(sp, friction * g * 0.1 * dt * 10)
                    v[0] -= v[0] / sp * dec
                    v[1] -= v[1] / sp * dec
                w = w * math.exp(-spin_damp * 3 * dt)
            else:
                if p[2] > rz + 0.05:
                    airborne = True
                w = w * math.exp(-spin_damp * 0.1 * dt)
            ang = np.linalg.norm(w) * dt
            if ang > 1e-9:
                R = rot_axis(w / np.linalg.norm(w), ang) @ R
            tau += dt
        self._taus = [s[0] for s in self.samples]

    def at(self, t):
        tau = warp(t) - warp(self.t0)
        i = min(max(bisect.bisect_left(self._taus, tau), 0), len(self.samples) - 1)
        return self.samples[i][1], self.samples[i][2]


# ---------------------------------------------------------------------------
# HERO: pose track + root mover + footstep planner + foot locks
# ---------------------------------------------------------------------------
HT = Track(dict(kin.POSE0, breath=0.0))
HR = Mover((0, 0, 0.86))
WALKS = []    # (t0, t1, step_period, side_offset, lift, first_foot)
LOCKS = []    # (foot, t0, t1)


def pose(t, ease='io', **kw):
    HT.key(t, ease, **kw)


def root(t, p, ease='io'):
    HR.key(t, p, ease)


def walk(t0, t1, period=0.5, width=0.13, lift=0.16, first='r'):
    WALKS.append((t0, t1, period, width, lift, first))


def lock(foot, t0, t1):
    LOCKS.append((foot, t0, t1))


def _raw_feet(t):
    p = HT.eval(t)
    H = kin.Hero(p, HR(t))
    return {'r': H.f_r_target, 'l': H.f_l_target}, H


def _walk_feet(t):
    """World foot positions from the footstep planner, or None outside walks."""
    for (t0, t1, per, wid, lift, first) in WALKS:
        if t0 - 1e-6 <= t <= t1 + 1e-6:
            res = {}
            for foot in 'rl':
                off = 0 if foot == first else 1
                # plant times for this foot: t0 + (2k+off)*per
                k = math.floor((t - t0 - off * per) / (2 * per))
                tp = t0 + (2 * k + off) * per        # last plant
                tn = tp + 2 * per                    # next plant

                def plant(tt):
                    tt = min(max(tt + 0.6 * per, t0), t1)     # plant under mid-stance
                    P = HR(tt)
                    yaw = HT.get('yaw', tt) * D2R
                    f = v3(math.cos(yaw), math.sin(yaw), 0)
                    r = np.cross(f, UP)
                    return P * v3(1, 1, 0) + r * (wid if foot == 'r' else -wid) + v3(0, 0, 0.06)
                a, b = plant(tp), plant(tn)
                sw = 0.8 * per                       # swing duration before next plant
                if t < tn - sw or tn > t1 + per * 0.5:
                    res[foot] = a
                else:
                    u = clamp((t - (tn - sw)) / sw)
                    q = lerp(a, b, smooth(u))
                    q[2] += lift * math.sin(math.pi * u)
                    res[foot] = q
            return res
    return None


_lock_cache = {}


def feet_at(t):
    raw, _ = _raw_feet(t)
    wf = _walk_feet(t)
    out = dict(raw)
    if wf:
        out.update(wf)
    for (foot, t0, t1) in LOCKS:
        if t0 <= t <= t1:
            key = (foot, t0)
            if key not in _lock_cache:
                wf0 = _walk_feet(t0)
                _lock_cache[key] = (wf0 or _raw_feet(t0)[0])[foot].copy()
            locked = _lock_cache[key]
            # ease in/out of the lock over 3 frames
            b = min(1.0, (t - t0) * 8, (t1 - t) * 8)
            out[foot] = lerp(out[foot], locked, clamp(b)) if b < 1 else locked
    return out


def walk_bob(t):
    for (t0, t1, per, wid, lift, first) in WALKS:
        if t0 <= t <= t1:
            ph = (t - t0) / per
            fade = clamp((t - t0) * 4) * clamp((t1 - t) * 4)
            return v3(0, 0, -0.035 * (0.5 + 0.5 * math.cos(2 * math.pi * ph)) * fade)
    return v3(0, 0, 0)


def HP(t):
    p = HT.eval(t)
    return kin.Hero(p, HR(t) + walk_bob(t), feet=feet_at(t))


# ---------------------------------------------------------------------------
# WOLVES
# ---------------------------------------------------------------------------
class WolfScript:
    def __init__(self, name, p, heading, s=1.25, seed=0):
        self.name, self.s, self.seed = name, s, seed
        self.m = Mover(p)
        self.tr = Track(dict(heading=heading, pitch=0.0, roll=0.0, jaw=0.0, eye=0.0, dissolve=0.0,
                             hp=0.0, hy=0.0, auto=1.0))
        self.modes = [(-1e9, 'stand')]
        self.tumbles = []     # (t0, t1, Tumble)
        self.t_dead = None
        self._dist = None
        self.paws = []        # (t0, t1, leg, fn(t) -> world point)
        self.attach = []      # (t0, t1, fn(t) -> (P, M))

    def mode(self, t, m):
        self.modes.append((t, m))
        self.modes.sort(key=lambda q: q[0])

    def mode_at(self, t):
        m = 'stand'
        for tm, mm in self.modes:
            if tm <= t:
                m = mm
        return m

    def tumble(self, t0, t1, v0, w0, **kw):
        st = self.state(t0 - 1e-4)
        T = Tumble(t0, st.P, v0, st.M, w0, t1, **kw)
        self.tumbles.append((t0, t1, T))
        return T

    def _phase(self, t):
        # gait phase from distance travelled (cached on a 1/48 s grid)
        if self._dist is None:
            ts = np.arange(0, DUR + 1, 1 / 48)
            ps = [self.m(x) for x in ts]
            d = [0.0]
            for i in range(1, len(ps)):
                d.append(d[-1] + float(np.linalg.norm((ps[i] - ps[i - 1])[:2])))
            self._dist = (ts, np.array(d))
        ts, d = self._dist
        return float(np.interp(t, ts, d)) / (1.6 * self.s)

    def state(self, t):
        for (t0, t1, T) in self.tumbles:
            if t >= t0:
                cur = (t0, t1, T)
        tum = None
        for (t0, t1, T) in self.tumbles:
            if t >= t0:
                tum = T
        p = self.tr.eval(t)
        m = self.mode_at(t)
        if tum is not None and m in ('limp', 'dead'):
            P, M = tum.at(t)
            return kin.Wolf(P, 0, s=self.s, mode='limp', jaw=p['jaw'], t=t, seed=self.seed, M=M,
                            head_pitch=p['hp'], head_yaw=p['hy'])
        for (a, b, f) in self.attach:
            if a <= t < b:
                P, M = f(t)
                return kin.Wolf(P, 0, s=self.s, mode=m, jaw=p['jaw'], t=t, seed=self.seed, M=M,
                                head_pitch=p['hp'], head_yaw=p['hy'], phase=self._phase(t))
        P = self.m(t)
        hd = p['heading']
        if p['auto'] > 0.5:
            v = self.m.vel(t)
            if math.hypot(v[0], v[1]) > 0.3:
                hd = math.atan2(v[1], v[0])
        pitch = p['pitch']
        if m == 'leap':
            v = self.m.vel(t)
            pitch += clamp(math.degrees(math.atan2(v[2], math.hypot(v[0], v[1]) + 1e-6)), -40, 40) * 0.7
        po = {leg: f(t) for (a, b, leg, f) in self.paws if a <= t < b} or None
        return kin.Wolf(P, hd, s=self.s, pitch=pitch, roll=p['roll'], phase=self._phase(t), mode=m,
                        jaw=p['jaw'], t=t, seed=self.seed, head_pitch=p['hp'], head_yaw=p['hy'],
                        paw_override=po)


WOLVES = []


def wolf(name, p, heading, s=1.25, seed=0):
    w = WolfScript(name, p, heading, s, seed)
    WOLVES.append(w)
    return w


# ---------------------------------------------------------------------------
# EVENTS (particle bursts, flashes) -- consumed by build.py
# ---------------------------------------------------------------------------
EVENTS = []   # dicts: t, kind, pos, dir, n, ...


def event(t, kind, pos, **kw):
    EVENTS.append(dict(t=t, kind=kind, pos=tuple(float(x) for x in pos), **kw))


# ---------------------------------------------------------------------------
# CAMERA: shot list.  Each shot: t0, fn(t) -> dict(eye, target, lens, roll, fstop, focus, shake)
# ---------------------------------------------------------------------------
SHOTS = []


def shot(t0, fn):
    SHOTS.append((t0, fn))
    SHOTS.sort(key=lambda q: q[0])


def cam_at(t):
    cur = SHOTS[0]
    for s in SHOTS:
        if s[0] <= t:
            cur = s
    c = dict(lens=35.0, roll=0.0, fstop=2.8, focus=None, shake=0.0)
    c.update(cur[1](t))
    return c, cur[0]


def handheld(t, amt, seed=0.0):
    """Low-frequency operator drift + higher-frequency jitter (radians)."""
    def n(x, s):
        return (math.sin(x * 1.3 + s) * 0.5 + math.sin(x * 2.9 + s * 1.7) * 0.3 +
                math.sin(x * 7.1 + s * 0.3) * 0.2)
    return v3(n(t, seed), n(t, seed + 4.1), n(t, seed + 9.3)) * amt
