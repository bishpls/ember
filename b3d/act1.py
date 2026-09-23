"""ACT I — the stalk, and the first cut."""
import math
import numpy as np
from tl import *
from ch import *
from ch import lerp
import kin
from kin import v3, norm, D2R

# ---------------------------------------------------------------- walk in
P_START = (-6.0, 0.6, 0.82)
P_STOP = (-1.2, 0.0, 0.82)
YAW0 = math.degrees(math.atan2(P_STOP[1] - P_START[1], P_STOP[0] - P_START[0]))
WALKPOSE = dict(held=0.0, unfold=0.0, two=0.0, lean=7, head=6, yaw=YAW0, gnd=1.0,
                h1x=0.0, h1y=-0.47, h1z=0.17, hx=0.0, hy=-0.47, hz=-0.17)
pose(0.0, **dict(kin.POSE0, breath=0.0, **WALKPOSE))
root(0.0, P_START, 'lin')
root(T_STOP - 0.25, lerp(np.array(P_START), np.array(P_STOP), 0.97), 'lin')
root(T_STOP, P_STOP, 'out')
walk(0.0, T_STOP, period=BEAT, width=0.12, lift=0.2, first='r')
# arm swing, opposite to the legs (right foot plants on the bar lines)
for k in range(8):
    tb = k * BEAT
    s = 1 if k % 2 == 0 else -1
    pose(tb + 0.25, 's', h1x=-0.13 * s, hx=0.13 * s, twist=-5 * s)
pose(T_STOP, 's', h1x=0.0, hx=0.0, twist=0.0, lean=3)
lock('r', T_STOP - 0.02, 9.6)
lock('l', T_STOP - 0.02, 11.9)
# settle, listen
pose(T_STOP + 0.35, 'out', sq=0.985, head=2)
pose(T_STOP + 0.9, 's', sq=1.0)
pose(T_LISTEN, 'io', head_yaw=0.0, head=2)
pose(T_LISTEN + 0.45, 'out', head_yaw=-50.0, twist=-8, head=-4)    # looks right (toward W1)
pose(T_EYES[1] + 0.1, 'io', head_yaw=-50.0)
pose(T_EYES[1] + 0.55, 'io', head_yaw=35.0, twist=6)                # left (toward W3)
pose(T_EYES[2] + 0.1, 'io', head_yaw=35.0)
pose(T_EYES[2] + 0.5, 'out', head_yaw=0.0, twist=0.0, head=-6)     # hears W2 behind; squares up
# reach over the right shoulder, draw
C_BACK = dict(h1x=-0.14, h1y=0.04, h1z=0.13)
pose(T_REACH, 'io', h1x=0.0, h1y=-0.47, h1z=0.17, held=0.0)
pose(T_REACH + 0.35, 'io', **C_BACK, lean=6)
pose(T_REACH + 0.38, 'lin', held=0.0, wa=-60, wtilt=0.0, wx=0.25, wy=-0.2, wz=0.15, g1=0.45, two=0.0,
     bside=1.0, unfold=0.0)
pose(T_UNFOLD1 - 0.05, 'io', held=1.0, wa=-55, wx=0.28, wy=-0.18, wz=0.14, lean=10, hx=0.1, hy=-0.35, hz=-0.25)
# click: shaft telescopes; clack: blade swings out and locks (a wrist snap drives it)
pose(T_UNFOLD1, 'lin', unfold=0.0, wa=-55)
pose(T_UNFOLD1 + 0.07, 'outx', unfold=0.5, wa=-70)
pose(T_UNFOLD2 - 0.08, 'io', wa=-40)
pose(T_UNFOLD2, 'in2', wa=-85)
pose(T_UNFOLD2 + 0.09, 'outx', unfold=1.0, wa=-95)
# settle into guard: blade low behind, step the right foot back
GUARD = dict(wa=-165.0, wtilt=22.0, wx=-0.02, wy=-0.3, wz=0.14, g1=0.3, g2=0.52, two=1.0, lean=20,
             head=-10, bside=1.0, fx1=-0.42, fz1=0.2, fy1=-0.72, fx2=0.34, fz2=-0.16, fy2=-0.72)
pose(T_CIRCLE - 0.3, 'io', **GUARD)
root(9.6, (P_STOP[0], P_STOP[1], 0.82))
root(T_CIRCLE - 0.2, (P_STOP[0] - 0.1, P_STOP[1], 0.72))
lock('r', T_CIRCLE - 0.18, 11.78)

# ---------------------------------------------------------------- wolves
W1 = wolf('W1', (9.8, -6.0, 0.975), math.pi * 0.85, seed=1)
W2 = wolf('W2', (-10.5, 7.2, 0.975), -0.6, seed=2)
W2.hidden_until = T_EYES[2] - 0.5
W3 = wolf('W3', (10.2, 4.6, 0.975), -2.8, seed=3)
for w, te, near in ((W1, T_EYES[0], (5.2, -3.4)), (W3, T_EYES[1], (5.5, 2.6)), (W2, T_EYES[2], (-6.0, 4.4))):
    w.tr.key(0.0, eye=0.0).key(te, 'lin', eye=0.0).key(te + 0.15, 'outx', eye=1.0)
    # creep forward out of the fog after the eyes open
    w.mode(te - 0.6, 'walk')
    w.m.key(te - 0.6, tuple(w.m(0.0)))
    w.m.key(te + 2.4, (near[0], near[1], 0.975), 'out2')
    w.mode(te + 2.4, 'stand')
# circling in (walk gait), heads low
W1.mode(T_CIRCLE - 0.4, 'walk')
W1.m.key(T_CIRCLE - 0.4, (5.2, -3.4, 0.975))
W1.m.key(11.25, (2.9, -3.1, 0.975), 's')
W1.tr.key(10.0, hp=-12.0).key(11.2, hp=-18.0)
W2.mode(T_CIRCLE, 'walk')
W2.m.key(T_CIRCLE, (-6.0, 4.4, 0.975))
W2.m.key(12.2, (-4.6, 2.6, 0.975), 's')
W3.mode(T_CIRCLE + 0.2, 'walk')
W3.m.key(T_CIRCLE + 0.2, (5.5, 2.6, 0.975))
W3.m.key(12.4, (3.6, 3.9, 0.975), 's')
for w in (W2, W3):
    w.mode(12.4, 'stand')
W1.mode(11.25, 'crouch')
W1.m.key(11.5, (2.85, -3.05, 0.78), 'out')
W1.tr.key(11.25, jaw=0.0).key(11.5, jaw=0.35)

# she tracks W1
yaw_w1 = math.degrees(math.atan2(-3.05 - P_STOP[1], 2.85 - P_STOP[0]))
pose(10.2, 'io', yaw=YAW0)
pose(11.2, 'io', yaw=yaw_w1 + 4)

# ---------------------------------------------------------------- the first cut
# anticipation: sink, wind the blade back
pose(T_BREATH + 0.05, 'io', wa=-178.0, lean=27, wtilt=28.0)
root(T_BREATH + 0.05, (P_STOP[0] - 0.12, P_STOP[1], 0.66))
# right foot drives forward into the cut
pose(11.78, 'io', fx1=-0.42, fz1=0.2, fy1=-0.72)
pose(11.95, 'io', fx1=0.46, fz1=0.18, fy1=-0.66)
lock('r', 11.97, 13.4)
# the swing: accelerate into contact (rising diagonal)
pose(11.84, 'io', wa=-176.0)
pose(T_DROP, 'in2', wa=12.0, lean=12, wx=0.3, wy=-0.22, head=-14)
fdir = v3(math.cos(yaw_w1 * D2R), math.sin(yaw_w1 * D2R), 0)
root(T_DROP, v3(P_STOP[0], P_STOP[1], 0.7) + fdir * 0.32, 'in2')
# follow-through: the wolf's mass drags the blade on past her left side and turns her
pose(T_DROP + 0.4, 'out', wa=78.0, lean=-4, wtilt=35.0, yaw=yaw_w1 + 48, head=-6, twist=-18)
root(T_DROP + 0.4, v3(P_STOP[0], P_STOP[1], 0.76) + fdir * 0.2, 'out')
pose(13.0, 'io', wa=-100.0, wtilt=10.0, lean=14, twist=0, yaw=yaw_w1 + 40, head=-8)
root(13.0, v3(P_STOP[0], P_STOP[1], 0.74) + fdir * 0.15)

# W1 leap, solved backward from where the blade will be at contact
C1 = HP(T_DROP).blade[5]
W1.mode(11.52, 'leap')
w1_from = np.array([2.85, -3.05, 0.9])
w1_dir = norm((C1 - w1_from) * v3(1, 1, 0))
w1_head_off = w1_dir * 0.72 * 1.25 + v3(0, 0, 0.3 * 1.25)
W1.m.arc(11.52, T_DROP, w1_from, C1 - w1_head_off, g=9.81)
W1.tr.key(11.52, jaw=0.35).key(T_DROP - 0.08, 'out', jaw=1.0)
# momentum carries the body through: tumble with the leap velocity, bled by the blade
v_leap = W1.m.vel(T_DROP - 0.01)
right_w1 = np.cross(w1_dir, UP)
W1.mode(T_DROP, 'limp')
T1 = W1.tumble(T_DROP, 14.5, v_leap * 0.55 + v3(0, 0, 1.6), right_w1 * -7.0 + UP * 2.0,
               radius=0.32, restitution=0.2, friction=5.0)
W1.tr.key(T_DROP, jaw=1.0).key(T_DROP + 0.5, jaw=0.6)
W1.tr.key(13.2, dissolve=0.0).key(15.5, 'in2', dissolve=1.0)
W1.t_dead = 15.5

# ---------------------------------------------------------------- events
for (t0, t1, per, wid, lift, first) in WALKS:
    k = 0
    while t0 + k * per <= t1 + 1e-6:
        tt = t0 + k * per
        f = feet_at(tt + 0.02)['r' if k % 2 == 0 else 'l']
        event(tt + 0.03, 'step', f, n=25)
        k += 1
event(T_DROP, 'hit', C1, dir=tuple(-w1_dir), n=90, big=True)
event(T_DROP, 'ichor', C1, dir=tuple(v_leap * 0.3), n=160)
for (tau, p, vz, vh) in T1.contacts:
    tt = T_DROP + tau  # approx (no slow-mo after the ramp)
    event(tt, 'thud', p * v3(1, 1, 0), n=int(60 + 40 * vz), speed=vz)
event(11.95, 'step', feet_at(11.99)['r'], n=40)

# ---------------------------------------------------------------- camera
def _hero_head(t):
    return HP(t).head


def S1(t):
    u = smooth((t - 0.0) / 3.9)
    eye = lerp(v3(6.0, -2.2, 6.5), v3(2.5, -0.9, 1.15), EASE['out2'](u))
    h = HP(t).chest
    moon_look = eye + TO_MOON * 30
    tgt = lerp(moon_look, h + v3(0, 0, 0.1), smooth((t - 0.2) / 2.0))
    return dict(eye=eye, target=tgt, lens=lerp(28, 40, u), fstop=4.0, focus=np.linalg.norm(h - eye))


def S2(t):
    hd = _hero_head(t)
    u = (t - T_STOP) / 2.0
    off = norm(v3(1.3, 1.05, -0.02)) * lerp(1.75, 1.45, u)
    eye = hd + off + handheld(t, 0.012, 1.0)
    return dict(eye=eye, target=hd + v3(0, 0, -0.05), lens=55, fstop=2.0)


def S3(t):
    H = HP(t)
    back = H.chest - H.fwd * 1.5 - H.right * 0.35 + v3(0, 0, 0.2)
    eye = back + handheld(t, 0.01, 2.0)
    tgt = H.chest + H.fwd * 6.0 + v3(0, 0, -0.35)
    rack = smooth((t - T_EYES[0]) / 0.5)
    focus = lerp(1.6, 7.0, rack)
    return dict(eye=eye, target=tgt, lens=28, fstop=2.0, focus=focus)


def S4a(t):
    H = HP(t)
    eye = H.pelvis + v3(1.6, -1.3, -0.35) + handheld(t, 0.01, 3.0)
    return dict(eye=eye, target=H.chest + v3(0, 0, 0.1), lens=30, fstop=2.8)


def S4b(t):
    H = HP(t)
    g = H.w_grip
    eye = H.chest + norm(v3(0.6, -1.0, -0.25)) * 1.35 + handheld(t, 0.006, 4.0)
    tgt = lerp(g, H.w_head, 0.45)
    return dict(eye=eye, target=tgt, lens=40, fstop=4.0, focus=np.linalg.norm(tgt - eye))


def S5(t):
    H = HP(t)
    u = (t - T_CIRCLE) / (T_BREATH + 0.05 - T_CIRCLE)
    ang = lerp(150, 105, EASE['io'](clamp(u))) * D2R
    c = H.chest
    eye = c + v3(math.cos(ang), math.sin(ang), 0) * 3.4 + v3(0, 0, -0.2) + handheld(t, 0.02, 5.0)
    return dict(eye=eye, target=c + v3(0.8, -0.8, -0.15), lens=26, fstop=3.2,
                focus=np.linalg.norm(c - eye))


def S6(t):
    # profile of the clash from the far side, moon in frame behind
    mid = v3(P_STOP[0], P_STOP[1], 0) + fdir * 1.4
    side = np.cross(fdir, UP) * -1          # left of her travel line
    eye = mid + side * 2.6 + fdir * 0.2 + v3(0, 0, 0.55) + handheld(t, 0.02, 6.0)
    return dict(eye=eye, target=mid + v3(0, 0, 1.05) - fdir * 0.5, lens=22, fstop=2.8,
                focus=np.linalg.norm(mid - eye))


shot(0.0, S1)
shot(T_STOP, S2)
shot(T_EYES[0] - 0.25, S3)
shot(T_REACH, S4a)
shot(T_UNFOLD1 - 0.1, S4b)
shot(T_CIRCLE, S5)
shot(11.52, S6)
