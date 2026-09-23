"""ACT II — the pack.  Grounded: recoil costs her ground, she gets hit, momentum decides."""
import math
import numpy as np
from tl import *
from ch import *
from ch import lerp
import kin
from kin import v3, norm, D2R, UP
import act1 as A1

W1, W2, W3 = A1.W1, A1.W2, A1.W3
S = 1.25                       # wolf scale
STAND_Z = 0.78 * S


def yaw_to(a, b):
    return math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))


def fvec(yaw):
    return v3(math.cos(yaw * D2R), math.sin(yaw * D2R), 0)


P0 = HR(13.0)
Y0 = HT.get('yaw', 13.0)

# ============================================================== W2: spin + point-blank shot
w2_home = v3(-4.6, 2.6, STAND_Z)
W2.mode(12.45, 'run')
W2.m.key(12.45, w2_home)
w2_leap_from = v3(-3.1, 1.55, STAND_Z)
W2.m.key(13.18, w2_leap_from, 'in2')
W2.tr.key(12.45, jaw=0.2).key(13.1, jaw=0.6)
yaw_w2 = yaw_to(P0, w2_leap_from)
# she hears it, turns hard (pivot on the left foot), levels the barrel
lock('l', 13.0, 13.62)
pose(13.05, 'io', yaw=Y0 + 10, wa=-60, wtilt=0.0, lean=12)
pose(13.38, 'io', yaw=yaw_w2 - 6, wa=2.0, wtilt=0.0, wx=0.36, wy=-0.02, wz=0.12, g1=0.32, g2=0.55,
     two=1.0, lean=10, head=-4, twist=4, fx1=0.32, fz1=0.2, fy1=-0.74)
pose(T_W2SHOT - 0.02, 'lin', yaw=yaw_w2 - 2, wa=1.0)
root(13.4, P0 + v3(0, 0, -0.04))
# fire: the slug stops the leap dead; recoil drives her back, heels plough the snow
pose(T_W2SHOT + 0.06, 'outx', wa=24.0, lean=-12, wx=0.24, wy=0.02, head=-10, sq=0.96)
back = -fvec(yaw_w2)
root(T_W2SHOT, P0 + v3(0, 0, -0.04), 'lin')
root(T_W2SHOT + 0.55, P0 + back * 0.8 + v3(0, 0, -0.1), 'outx')
pose(T_W2SHOT + 0.55, 'out', wa=-20.0, lean=18, sq=1.0, fx1=0.45, fz1=0.18, fy1=-0.66,
     fx2=-0.3, fz2=-0.16, fy2=-0.7)
MUZ1 = HP(T_W2SHOT).muzzle
W2.mode(13.18, 'leap')
w2_hit = MUZ1 + fvec(yaw_w2) * 1.5 + v3(0, 0, -0.35)
W2.m.arc(13.18, T_W2SHOT, w2_leap_from, w2_hit, g=9.81)
W2.tr.key(T_W2SHOT - 0.05, jaw=1.0)
W2.mode(T_W2SHOT, 'limp')
T2 = W2.tumble(T_W2SHOT, 14.2, fvec(yaw_w2) * 1.5 + v3(0, 0, 0.9), np.cross(fvec(yaw_w2), UP) * 6.0,
               radius=0.3, restitution=0.15, friction=6.0)
# it survives the shot: scrabbles back up on shaking legs
w2_down = T2.at(14.2)[0]
W2.mode(14.2, 'crouch')
W2.m.key(14.2, v3(w2_down[0], w2_down[1], 0.62))
W2.m.key(14.75, v3(w2_down[0], w2_down[1], STAND_Z - 0.12), 'out')
W2.tr.key(14.2, heading=math.atan2(-fvec(yaw_w2)[1], -fvec(yaw_w2)[0]), auto=0.0, jaw=0.4, roll=12)
W2.tr.key(14.75, roll=-6, hp=-10)
W2.mode(14.75, 'stand')

# ============================================================== advance + overhead chop
P1 = HR(T_W2SHOT + 0.56)
to_w2 = norm((w2_down - P1) * v3(1, 1, 0))
chop_at = w2_down - to_w2 * 1.35
yaw_chop = yaw_to(P1, w2_down)
walk(14.1, 14.9, period=0.38, width=0.14, lift=0.14, first='l')
root(14.1, P1)
root(14.9, v3(chop_at[0], chop_at[1], 0.8), 'io')
pose(14.1, 'io', yaw=yaw_chop, fx1=0.12, fz1=0.14, fy1=-0.84, fx2=-0.12, fz2=-0.14, fy2=-0.84)
# raise: blade climbs over her head (CW chop wants the blade leading clockwise)
pose(14.3, 'io', wa=60.0, bside=-1.0, wtilt=0.0, wx=0.1, wy=0.12, wz=0.1, g1=0.25, g2=0.5, lean=0)
pose(14.88, 'io', wa=148.0, wx=-0.05, wy=0.28, lean=-12, head=-18, sq=1.03)
lock('r', 14.9, 16.02)
lock('l', 14.9, 15.62)
# drop the body into it
pose(T_CHOP, 'in2', wa=-58.0, wx=0.4, wy=-0.3, lean=42, head=-24, sq=0.9,
     fx1=0.35, fz1=0.16, fy1=-0.62, fx2=-0.42, fz2=-0.16, fy2=-0.62)
root(T_CHOP, v3(chop_at[0], chop_at[1], 0.6) + to_w2 * 0.12, 'in2')
# blade bites and sticks; she wrenches it free
pose(T_CHOP + 0.12, 'lin', wa=-60.0, sq=0.92)
pose(T_CHOP + 0.42, 'io', wa=-40.0, lean=24, sq=1.0, wx=0.3, wy=-0.2)
pose(T_CHOP + 0.52, 'outx', wa=-10.0, lean=12)
root(T_CHOP + 0.5, v3(chop_at[0], chop_at[1], 0.74) - to_w2 * 0.1)
C_CHOP = HP(T_CHOP).blade_tip
# W2 finished: slumps under the blade
W2.mode(T_CHOP, 'dead')
W2.tumble(T_CHOP, 17.0, v3(0, 0, -1.5) + to_w2 * 0.4, np.cross(to_w2, UP) * -2.0,
          radius=0.26, restitution=0.05, friction=8.0)
W2.tr.key(T_CHOP, jaw=1.0).key(T_CHOP + 0.4, jaw=0.7)
W2.tr.key(15.8, dissolve=0.0).key(18.8, 'in2', dissolve=1.0)
W2.t_dead = 18.8

# ============================================================== W3 tackles her
P2 = HR(15.55)
w3_start = v3(3.6, 3.9, STAND_Z)
W3.mode(15.1, 'run')
W3.m.key(15.1, w3_start)
dir_in = norm((P2 - w3_start) * v3(1, 1, 0))
w3_pre = P2 - dir_in * 1.6
w3_pre[2] = STAND_Z
W3.m.key(15.78, w3_pre, 'in2')
W3.tr.key(15.1, jaw=0.2).key(15.8, jaw=0.9)
# she turns toward it a moment too late
pose(15.62, 'io', yaw=yaw_chop, wa=-10.0)
pose(15.95, 'io', yaw=yaw_to(P2, w3_pre) - 60, wa=40.0, wtilt=0.0, bside=1.0, lean=4, twist=-20,
     head_yaw=-35)
contact = HP(T_TACKLE).chest + np.cross(UP, dir_in) * 0.0
W3.mode(15.78, 'leap')
W3.m.arc(15.78, T_TACKLE, w3_pre, contact - dir_in * 0.75 * S + v3(0, 0, -0.35), g=9.81)
# momentum exchange: 70 kg wolf at ~7 m/s into a 55 kg huntress
v_w3 = W3.m.vel(T_TACKLE - 0.01)
v_her = v_w3 * (70.0 / (70.0 + 55.0)) * 1.05
v_her[2] = 2.2
land = P2 + v_her * 0.34
land[2] = 0.35
HR.arc(T_TACKLE, T_TACKLE + 0.34, HR(T_TACKLE), land, g=9.81)
roll_dir = norm(v_her * v3(1, 1, 0))
yaw_fall = yaw_to(v3(0, 0, 0), -roll_dir)      # she faces back toward the wolf as she goes over
pose(T_TACKLE, 'lin', yaw=HT.get('yaw', 15.95), roll=0.0, pitch=0.0, sq=1.0)
pose(T_TACKLE + 0.12, 'out', yaw=yaw_fall, pitch=-40.0, lean=-10, head=20, twist=0,
     fx1=0.35, fz1=0.2, fy1=-0.55, fx2=0.15, fz2=-0.2, fy2=-0.7, gnd=0.0, wa=70.0, head_yaw=0)
# back-roll over the shoulder (pitch -360) while sliding
pose(T_TACKLE + 0.34, 'io', pitch=-110.0, lean=35, **dict(fx1=0.25, fz1=0.15, fy1=-0.4, fx2=0.2, fz2=-0.15, fy2=-0.42))
root(T_TACKLE + 0.34, land)
root(T_TACKLE + 0.75, land + roll_dir * 1.1 + v3(0, 0, -0.05), 'out')
pose(T_TACKLE + 0.72, 'io', pitch=-330.0, lean=40)
pose(T_TACKLE + 0.9, 'out', pitch=-360.0, lean=30, gnd=1.0, fx1=0.4, fz1=0.18, fy1=-0.45,
     fx2=-0.2, fz2=-0.16, fy2=-0.5)
pose(T_TACKLE + 0.901, 'step', pitch=0.0)
root(T_TACKLE + 0.95, land + roll_dir * 1.3 + v3(0, 0, 0.18), 'out')
# on one knee, then up
KNEEL = dict(fx1=0.42, fz1=0.18, fy1=-0.42, fx2=-0.3, fz2=-0.16, fy2=-0.52, lean=18, head=-6)
pose(T_UP - 0.35, 'io', **KNEEL, wa=-30.0, wtilt=10.0, wx=0.2, wy=-0.3)
root(T_UP - 0.35, land + roll_dir * 1.35 + v3(0, 0, 0.22))
pose(T_UP, 'io', lean=16, fx1=0.36, fz1=0.18, fy1=-0.68, fx2=-0.36, fz2=-0.16, fy2=-0.72, wa=-150.0,
     wtilt=20.0, bside=1.0)
P3 = land + roll_dir * 1.35
root(T_UP, v3(P3[0], P3[1], 0.74))
lock('r', T_UP + 0.02, 18.45)
lock('l', T_UP + 0.02, 18.45)
# W3 carries on past, skids, turns
W3.mode(T_TACKLE, 'crouch')
w3_skid = contact + dir_in * 2.8
w3_skid[2] = STAND_Z - 0.15
W3.m.key(T_TACKLE, W3.m(T_TACKLE - 1e-3))
W3.m.key(T_TACKLE + 0.5, w3_skid, 'outx')
W3.tr.key(T_TACKLE, roll=0.0, auto=1.0).key(T_TACKLE + 0.25, roll=-18).key(T_TACKLE + 0.6, roll=0)
W3.mode(T_TACKLE + 0.55, 'walk')
w3_circle = P3 + norm(v3(-0.4, 1.0, 0)) * 5.2
w3_circle[2] = STAND_Z
W3.m.key(17.9, w3_circle, 's')
W3.tr.key(T_TACKLE + 0.6, jaw=0.5).key(17.9, jaw=0.8)

# ============================================================== recoil dash + leg hook
yaw_w3 = yaw_to(P3, w3_circle)
pose(17.8, 'io', yaw=yaw_w3, head_yaw=0, twist=0)
W3.mode(17.9, 'run')
meet = P3 + norm((w3_circle - P3) * v3(1, 1, 0)) * 2.6
w3_meet = meet.copy()
w3_meet[2] = STAND_Z
W3.m.key(T_HOOK, w3_meet, 'in2')
# muzzle back (horizontal swing plane), fire -> she is thrown forward, low
HOOKP = dict(wtilt=90.0, wx=-0.05, wy=-0.42, wz=0.18, g1=0.3, g2=0.5, two=1.0, lean=45, head=-20)
pose(T_DASHSHOT - 0.05, 'io', wa=182.0, bside=-1.0, **HOOKP,
     fx1=0.38, fz1=0.2, fy1=-0.6, fx2=-0.45, fz2=-0.16, fy2=-0.62)
root(T_DASHSHOT - 0.05, v3(P3[0], P3[1], 0.66))
dash_end = P3 + norm((meet - P3) * v3(1, 1, 0)) * 1.75
root(T_DASHSHOT, v3(P3[0], P3[1], 0.66), 'lin')
root(T_HOOK, v3(dash_end[0], dash_end[1], 0.6), 'out')
pose(T_DASHSHOT + 0.08, 'outx', wa=200.0, lean=55, gnd=0.2, fx1=0.3, fy1=-0.5, fx2=-0.6, fy2=-0.4)
# swing the blade round, low, into the foreleg
pose(T_HOOK, 'in2', wa=40.0, lean=38, gnd=1.0, fx1=0.45, fz1=0.2, fy1=-0.58, fx2=-0.4, fz2=-0.2, fy2=-0.6)
lock('r', T_HOOK + 0.01, 20.3)
lock('l', T_HOOK + 0.01, 19.7)
C_HOOK = HP(T_HOOK).blade_tip
# momentum: the leg stops, the body doesn't -> faceplant, somersault, skid past her
v_w3b = W3.m.vel(T_HOOK - 0.01)
W3.mode(T_HOOK, 'limp')
T3 = W3.tumble(T_HOOK, T_PLANT, v_w3b * 0.9 + v3(0, 0, 1.4), np.cross(norm(v_w3b), UP) * -9.0,
               radius=0.3, restitution=0.2, friction=6.5)
# she pivots on the hook, rotating with the wolf as it passes
yaw_after = yaw_to(v3(0, 0, 0), v_w3b) + 20
pose(T_W3DOWN, 'out', yaw=yaw_after, wa=-40.0, wtilt=40.0, lean=20, twist=-20)
w3_rest = T3.at(T_PLANT)[0]
# ============================================================== the plant
P4 = HR(T_W3DOWN)
to_w3 = norm((w3_rest - P4) * v3(1, 1, 0))
plant_from = w3_rest - to_w3 * 1.1
walk(19.72, 20.05, period=0.3, width=0.14, lift=0.12, first='l')
root(19.72, P4)
root(T_PLANT - 0.05, v3(plant_from[0], plant_from[1], 0.8))
pose(19.75, 'io', yaw=yaw_to(P4, w3_rest), wa=100.0, wtilt=0.0, bside=-1.0, wx=0.0, wy=0.2, lean=-5,
     twist=0, head=-20)
lock('r', 20.06, 22.9)
lock('l', 20.06, 23.1)
pose(T_PLANT, 'in2', wa=-78.0, wx=0.35, wy=-0.25, lean=45, head=-30, sq=0.92,
     fx1=0.3, fz1=0.18, fy1=-0.62, fx2=-0.35, fz2=-0.15, fy2=-0.62)
root(T_PLANT, v3(plant_from[0], plant_from[1], 0.62) + to_w3 * 0.15, 'in2')
W3.mode(T_PLANT, 'dead')
W3.tumble(T_PLANT, 24.0, v3(0, 0, -1.0), v3(0, 0, 0.3), radius=0.26, restitution=0.0, friction=9.0)
W3.tr.key(T_PLANT + 1.0, dissolve=0.0).key(23.5, 'in2', dissolve=1.0)
W3.t_dead = 23.5
C_PLANT = HP(T_PLANT).blade_tip

# ============================================================== breath; the ground shakes
pose(T_PLANT + 0.6, 'io', wa=-70.0, lean=30, sq=1.0)
pose(21.1, 'io', wa=-150.0, wtilt=15.0, bside=1.0, lean=14, head=-4, wx=0.0, wy=-0.3,
     fx1=0.3, fz1=0.16, fy1=-0.72, fx2=-0.34, fz2=-0.16, fy2=-0.74)
root(21.1, v3(plant_from[0], plant_from[1], 0.76) - to_w3 * 0.25)
for k in range(5):     # heavy breathing
    tb = 21.2 + k * 0.6
    pose(tb, 's', sq=1.018, lean=12)
    pose(tb + 0.3, 's', sq=0.99, lean=15)
yaw_alpha = 205.0     # the thing in the fog is out toward the moon
pose(T_TREMOR1 + 0.1, 'io', head_yaw=0.0)
pose(T_TREMOR1 + 0.5, 'out', head_yaw=-45.0, head=4)
pose(T_TREMOR2 + 0.2, 'io', yaw=yaw_alpha, head_yaw=0.0, twist=0, lean=18, sq=1.0,
     wa=-165.0, wtilt=22.0)
pose(23.9, 'io', yaw=yaw_alpha)

# ============================================================== events
event(T_W2SHOT, 'shot', MUZ1, dir=tuple(fvec(yaw_w2)), big=True)
event(T_W2SHOT + 0.02, 'hit', w2_hit + v3(0, 0, 0.3), dir=tuple(fvec(yaw_w2)), n=60)
event(T_W2SHOT + 0.02, 'ichor', w2_hit + v3(0, 0, 0.3), dir=tuple(fvec(yaw_w2) * 2.5), n=160)
for k in range(6):
    tt = T_W2SHOT + 0.05 + k * 0.08
    f = feet_at(tt)
    event(tt, 'plough', f['r'], dir=tuple(back), n=30)
    event(tt, 'plough', f['l'], dir=tuple(back), n=30)
for (tau, p, vz, vh) in T2.contacts:
    event(T_W2SHOT + tau, 'thud', p * v3(1, 1, 0), n=int(60 + 30 * vz), speed=vz)
event(T_CHOP, 'hit', C_CHOP, dir=(0, 0, 1), n=70, big=True)
event(T_CHOP, 'ichor', C_CHOP, dir=(0, 0, 1.5), n=200)
event(T_CHOP + 0.02, 'thud', C_CHOP * v3(1, 1, 0), n=90, speed=3.0)
event(T_TACKLE, 'hit', contact, dir=tuple(dir_in), n=30)
event(T_TACKLE + 0.34, 'thud', land * v3(1, 1, 0), n=160, speed=4.0)
for k in range(5):
    tt = T_TACKLE + 0.4 + k * 0.1
    event(tt, 'plough', HR(tt) * v3(1, 1, 0), dir=tuple(roll_dir), n=40)
event(T_DASHSHOT, 'shot', HP(T_DASHSHOT).muzzle, dir=tuple(-norm((meet - P3) * v3(1, 1, 0))), big=True)
event(T_DASHSHOT + 0.01, 'thud', HP(T_DASHSHOT).muzzle * v3(1, 1, 0), n=120, speed=3.5)
event(T_HOOK, 'hit', C_HOOK, dir=tuple(-norm(v_w3b)), n=60)
event(T_HOOK, 'ichor', C_HOOK, dir=tuple(norm(v_w3b) * 1.5), n=100)
for (tau, p, vz, vh) in T3.contacts:
    event(T_HOOK + tau, 'thud', p * v3(1, 1, 0), n=int(80 + 30 * vz), speed=vz)
event(T_PLANT, 'hit', C_PLANT, dir=(0, 0, 1), n=60, big=True)
event(T_PLANT, 'ichor', C_PLANT, dir=(0, 0, 1.8), n=180)
event(T_TREMOR1, 'tremor', (0, 0, 0), n=1)
event(T_TREMOR2, 'tremor', (0, 0, 0), n=2)
for w in (W1, W2, W3):
    event(w.tr.k['dissolve'][0][0], 'ash', (0, 0, 0), wolf=w.name, t1=w.t_dead)

# ============================================================== camera
def side_of(a, b, dist, h, along=0.5, flip=1):
    d = norm((b - a) * v3(1, 1, 0))
    s = np.cross(d, UP) * flip
    mid = lerp(a, b, along)
    return v3(mid[0], mid[1], 0) + s * dist + v3(0, 0, h), mid


def A2a(t):   # the turn and the point-blank shot, low and wide
    eye, mid = side_of(P0, w2_leap_from, 5.0, 0.7, 0.4, flip=-1)
    eye = eye + handheld(t, 0.018, 11.0)
    return dict(eye=eye, target=v3(mid[0], mid[1], 0.95), lens=28, fstop=2.8,
                focus=np.linalg.norm(mid - eye))


def A2b(t):   # low behind the downed wolf, looking up at her against the sky
    H = HP(t)
    eye = w2_down - to_w2 * -1.2 + np.cross(to_w2, UP) * 0.7 + v3(0, 0, -0.25) + handheld(t, 0.012, 12.0)
    eye[2] = max(eye[2], 0.25)
    return dict(eye=eye, target=H.chest + v3(0, 0, 0.35), lens=24, fstop=2.8)


def A2c(t):   # tracking her as W3 comes in from off-frame
    H = HP(t)
    eye = H.chest + norm(np.cross(dir_in, UP) + dir_in * 0.35) * 4.4 + v3(0, 0, -0.2) + handheld(t, 0.02, 13.0)
    return dict(eye=eye, target=H.chest - dir_in * 0.5, lens=28, fstop=2.8)


def A2d(t):   # ground level as she rolls toward camera and comes up
    tgt = HR(t) + v3(0, 0, 0.35)
    eye = P3 + roll_dir * 2.6 + np.cross(roll_dir, UP) * 1.0 + v3(0, 0, 0.22) + handheld(t, 0.015, 14.0)
    eye[2] = 0.22
    return dict(eye=eye, target=tgt, lens=28, fstop=2.2)


def A2e(t):   # dolly alongside the recoil dash
    H = HP(t)
    dd = norm((meet - P3) * v3(1, 1, 0))
    s = np.cross(dd, UP)
    base = lerp(P3, dash_end, clamp((t - T_DASHSHOT) / 0.6))
    eye = base + s * 3.4 + dd * 0.6 + v3(0, 0, 0.8) + handheld(t, 0.02, 15.0)
    eye[2] = 0.8
    return dict(eye=eye, target=lerp(H.pelvis, w3_meet, 0.4) + v3(0, 0, 0.2), lens=24, fstop=3.2)


def A2f(t):   # high three-quarter over the plant
    eye = w3_rest + np.cross(to_w3, UP) * 1.8 + to_w3 * 1.2 + v3(0, 0, 3.0) + handheld(t, 0.01, 16.0)
    return dict(eye=eye, target=lerp(plant_from, w3_rest, 0.5) + v3(0, 0, 0.6), lens=30, fstop=3.5)


def A2g(t):   # the breather: wide, embers rising, then the tremor
    H = HP(t)
    u = clamp((t - 21.0) / 3.0)
    eye = H.pelvis + norm(v3(0.9, 0.5, 0)) * lerp(5.5, 4.2, u) + v3(0, 0, lerp(1.6, 0.9, u))
    sh = 0.0
    for tt, a in ((T_TREMOR1, 0.05), (T_TREMOR2, 0.08)):
        if t > tt:
            sh += a * math.exp(-(t - tt) * 3.0)
    eye = eye + handheld(t * 6, sh, 17.0) + handheld(t, 0.012, 18.0)
    return dict(eye=eye, target=H.chest + v3(-1.0, -0.4, -0.1), lens=32, fstop=2.8)


shot(12.45, A2a)
shot(13.8, A2b)
shot(15.35, A2c)
shot(T_TACKLE + 0.3, A2d)
shot(T_DASHSHOT - 0.35, A2e)
shot(19.62, A2f)
shot(20.95, A2g)
