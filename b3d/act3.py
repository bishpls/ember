"""ACT III — the alpha.  CODA — ash and moonlight."""
import math
import numpy as np
from tl import *
from ch import *
from ch import lerp
import kin
from kin import v3, norm, D2R, UP, rot_axis
import act2 as A2

HERO_TREE = v3(-9.2, 5.6, 0.0)
AS = 3.0
AZ = 0.78 * AS


def yaw_to(a, b):
    return math.degrees(math.atan2(b[1] - a[1], b[0] - a[0]))


def fvec(yaw):
    return v3(math.cos(yaw * D2R), math.sin(yaw * D2R), 0)


PH = HR(23.9)                           # where she stands when it arrives
PH[2] = 0.76
AL = wolf('ALPHA', (-19.5, -3.5, AZ), 0.3, s=AS, seed=21)
AL.hidden_until = 23.4
AL.tr.key(0.0, eye=1.0)
AL.tr.key(0.0, jaw=0.2)

# ============================================================== it comes out of the fog
stop1 = PH + norm(v3(-19.5, -3.5, 0) - PH * v3(1, 1, 0)) * 6.2
stop1[2] = AZ
AL.mode(23.4, 'walk')
AL.m.key(23.4, (-19.5, -3.5, AZ))
AL.m.key(27.4, stop1, 'out2')
AL.tr.key(23.4, hp=-8.0).key(27.0, hp=-4.0)
yaw_al = yaw_to(PH, stop1)
pose(23.0, 'lin', pitch=0.0, roll=0.0)
pose(24.0, 'io', yaw=yaw_al, wa=-165.0, wtilt=22.0, lean=18, pitch=0.0, roll=0.0)
lock('r', 23.2, 26.0)
lock('l', 23.2, 26.0)
root(24.0, PH)
# three shots at its head: recoil nudges her back each time; the hide just sparks
AIM = dict(wa=4.0, wtilt=0.0, wx=0.36, wy=0.0, wz=0.12, g1=0.32, g2=0.55, two=1.0, lean=6, head=-4,
           bside=1.0, fx1=0.3, fz1=0.18, fy1=-0.76, fx2=-0.34, fz2=-0.15, fy2=-0.76)
pose(25.7, 'io', **AIM)
back = -fvec(yaw_al)
for i, ts in enumerate(T_SHOTS):
    head_pt = AL.state(ts).W(0.78, 0.25)
    wa_up = math.degrees(math.atan2(head_pt[2] - 1.35, np.linalg.norm((head_pt - PH)[:2])))
    pose(ts - 0.06, 'io', wa=wa_up)
    pose(ts + 0.05, 'outx', wa=wa_up + 20, lean=-6, sq=0.97)
    pose(ts + 0.3, 'io', wa=wa_up + 4, lean=4, sq=1.0)
    root(ts, PH + back * 0.18 * i, 'lin')
    root(ts + 0.2, PH + back * 0.18 * (i + 1), 'outx')
    event(ts, 'shot', HP(ts).muzzle, dir=tuple(norm(head_pt - HP(ts).muzzle)), big=False)
    event(ts + 0.02, 'hit', head_pt, dir=tuple(-norm(head_pt - PH)), n=50, ricochet=True)
    AL.tr.key(ts, hy=0.0).key(ts + 0.06, 'outx', hy=(-8 if i % 2 else 8)).key(ts + 0.35, 'io', hy=0.0)
walk(26.0, 27.4, period=0.35, width=0.14, lift=0.1, first='r')   # re-plants between shots
P_SH = HR(27.4)
# roar
AL.mode(27.4, 'stand')
AL.tr.key(T_ROAR - 0.1, jaw=0.2, hp=-4.0).key(T_ROAR + 0.2, 'out', jaw=1.0, hp=22.0)
AL.tr.key(T_CHARGE - 0.05, jaw=0.9, hp=15.0).key(T_CHARGE + 0.2, jaw=0.5, hp=-5.0)
pose(T_ROAR, 'io', wa=-150.0, wtilt=20.0, lean=24, head=-12, wx=-0.02, wy=-0.3,
     fx1=0.36, fz1=0.18, fy1=-0.72, fx2=-0.4, fz2=-0.16, fy2=-0.72)
lock('r', 27.42, 28.9)
lock('l', 27.42, 28.9)
pose(T_ROAR + 0.5, 'io', lean=28)
event(T_ROAR, 'roar', stop1 + fvec(yaw_al + 180) * 2.0 + v3(0, 0, 2.0), dir=tuple(-fvec(yaw_al)))

# ============================================================== charge, swat, the tree
AL.mode(T_CHARGE, 'run')
to_tree = norm((HERO_TREE - P_SH) * v3(1, 1, 0))
swat_from = P_SH + fvec(yaw_al) * 2.3 + np.cross(to_tree, UP) * 0.0
swat_from[2] = AZ - 0.2
AL.m.key(T_CHARGE, stop1)
AL.m.key(T_SWAT - 0.05, swat_from, 'in2')
AL.mode(T_SWAT - 0.3, 'stand')
# the paw sweeps across her toward the tree side
grip_sw = HP(T_SWAT).w_grip
paw_a = grip_sw - to_tree * 1.4 + v3(0, 0, 0.3)
paw_b = grip_sw + to_tree * 1.2 + v3(0, 0, -0.1)
AL.paws.append((T_SWAT - 0.3, T_SWAT + 0.25, 'fr',
                lambda t: lerp(paw_a, paw_b, EASE['in2'](clamp((t - (T_SWAT - 0.3)) / 0.35)))))
BLOCK = dict(wa=95.0, wtilt=0.0, wx=0.3, wy=0.05, wz=0.0, g1=0.22, g2=0.65, two=1.0, lean=-4, head=-6,
             twist=-10)
pose(T_SWAT - 0.12, 'io', **BLOCK)
pose(T_SWAT, 'lin', yaw=yaw_al - 25, pitch=0.0, roll=0.0)
# she is thrown: ballistic into the trunk
tree_hit = HERO_TREE + norm(P_SH - HERO_TREE) * v3(1, 1, 0) * 0.55
tree_hit[2] = 1.3
HR.arc(T_SWAT, T_TREE, HR(T_SWAT), tree_hit, g=9.81)
yaw_back_to_tree = yaw_to(tree_hit, P_SH)       # she faces away from the tree as she hits it
pose(T_SWAT + 0.2, 'out', yaw=yaw_back_to_tree, pitch=-25.0, lean=-20, head=25, gnd=0.0, roll=12,
     fx1=0.35, fz1=0.2, fy1=-0.6, fx2=0.1, fz2=-0.2, fy2=-0.75, wa=130.0, wx=0.2, wy=0.1, two=0.0,
     hx=-0.1, hy=0.1, hz=-0.4)
pose(T_TREE, 'lin', pitch=-5.0, lean=-8, head=-10, roll=0.0, sq=0.9)
# slides down the trunk, crumples
slump = HERO_TREE + norm(P_SH - HERO_TREE) * v3(1, 1, 0) * 0.62
slump[2] = 0.42
root(T_TREE + 0.45, slump, 'in2')
SLUMP = dict(pitch=-18.0, lean=25, head=35, gnd=1.0, fx1=0.55, fz1=0.25, fy1=-0.38, fx2=0.5, fz2=-0.22,
             fy2=-0.4, wa=-60.0, wtilt=40.0, wx=0.25, wy=-0.35, two=0.0, hx=0.2, hy=-0.35, hz=-0.3,
             sq=1.0, twist=0.0)
pose(T_TREE + 0.45, 'out', **SLUMP)
for k in range(3):     # ragged breathing, head hanging
    tb = 30.4 + k * 0.7
    pose(tb, 's', sq=1.02, head=33)
    pose(tb + 0.35, 's', sq=0.99, head=37)
AL.mode(T_SWAT + 0.3, 'walk')
AL.m.key(T_SWAT + 0.3, swat_from)
# it stalks: a slow arc, head low, watching her
stalk_c = slump * v3(1, 1, 0)
stalk_a = swat_from
outward = norm(stalk_c)
stalk_mid = stalk_c + rot_axis(UP, -1.1) @ outward * 6.0
stalk_mid[2] = AZ
stand_pt = stalk_c - outward * 2.3          # she limps out from the tree into the open
stalk_end = stand_pt + rot_axis(UP, -0.65) @ outward * 5.6
stalk_end[2] = AZ
AL.m.key(31.8, stalk_mid, 's')
AL.m.key(33.9, stalk_end, 's')
AL.tr.key(T_SWAT + 0.3, hp=-12.0, jaw=0.3).key(33.9, hp=-16.0, jaw=0.5)
AL.mode(33.9, 'crouch')
AL.m.key(34.3, stalk_end - v3(0, 0, 0.3), 'io')
# she gets up, leaning on the weapon (planted butt-down like a staff)
CRUTCH = dict(pitch=0.0, wa=100.0, wtilt=0.0, wx=0.3, wy=0.0, wz=0.1, g1=0.55, g2=0.7, two=0.0,
              hx=0.1, hy=-0.2, hz=-0.3, bside=1.0)
pose(31.8, 'io', **CRUTCH, lean=40, head=10, fx1=0.4, fz1=0.2, fy1=-0.45, fx2=-0.1, fz2=-0.2, fy2=-0.5)
root(31.8, slump + v3(0, 0, 0.12))
yaw_stalk = yaw_to(stand_pt, stalk_end)
walk(32.0, 33.2, period=0.4, width=0.14, lift=0.08, first='l')
root(32.0, slump + v3(0, 0, 0.3))
root(33.2, v3(stand_pt[0], stand_pt[1], 0.74), 'io')
pose(32.2, 'io', lean=26, head=4, yaw=yaw_to(slump, stand_pt), fx1=0.12, fz1=0.14, fy1=-0.8, fx2=-0.12,
     fz2=-0.14, fy2=-0.8, sq=1.0)
pose(33.3, 'io', lean=20, head=0, yaw=yaw_stalk - 10, fx1=0.3, fz1=0.18, fy1=-0.72, fx2=-0.3,
     fz2=-0.16, fy2=-0.74)
pose(33.8, 'io', wa=-160.0, wtilt=20.0, g1=0.3, g2=0.52, two=1.0, wx=-0.02, wy=-0.3, lean=20,
     yaw=yaw_stalk, head=-8)
root(33.8, v3(stand_pt[0], stand_pt[1], 0.7))
lock('r', 33.22, 34.25)
lock('l', 33.22, 34.25)

# ============================================================== lunge / slide / sweep
P_L = HR(34.2)
d_l = norm((stalk_end - P_L) * v3(1, 1, 0))
AL.mode(T_LUNGE - 0.2, 'leap')
lunge_to = P_L + d_l * 0.4
lunge_to[2] = AZ + 0.3
AL.m.arc(T_LUNGE - 0.2, T_SWEEP, stalk_end - v3(0, 0, 0.3), lunge_to, g=9.81)
AL.tr.key(T_LUNGE - 0.2, jaw=0.6).key(T_LUNGE + 0.1, jaw=1.0).key(T_LUNGE + 0.25, jaw=0.2)
# she drops and knee-slides under its chest
SLIDE = dict(lean=-35, head=18, fx1=0.55, fz1=0.18, fy1=-0.42, fx2=-0.15, fz2=-0.16, fy2=-0.52, gnd=1.0)
pose(34.35, 'io', lean=35, yaw=yaw_to(P_L, stalk_end))
pose(T_LUNGE, 'io', **SLIDE, wa=-170.0, wtilt=80.0, wx=-0.1, wy=-0.25, bside=-1.0)
slide_end = P_L + d_l * 3.6
root(34.3, P_L)
root(T_LUNGE, P_L + d_l * 0.8 + v3(0, 0, -0.2), 'in2')
root(T_SWEEP, slide_end * v3(1, 1, 0) + v3(0, 0, 0.45), 'out')
# hook the hind leg as it passes over, and fire: recoil torque whips the blade through
pose(T_SWEEP, 'in2', wa=-40.0, wtilt=80.0, lean=-20)
pose(T_SWEEP + 0.25, 'outx', wa=30.0)
C_SWEEP = HP(T_SWEEP).blade_tip
event(T_SWEEP, 'shot', HP(T_SWEEP).muzzle, dir=tuple(-d_l), big=True)
event(T_SWEEP, 'hit', C_SWEEP, dir=tuple(d_l), n=90, big=True)
event(T_SWEEP, 'ichor', C_SWEEP, dir=tuple(d_l * 2), n=200)
for k in range(6):
    tt = T_LUNGE + k * 0.09
    event(tt, 'plough', HR(tt) * v3(1, 1, 0), dir=tuple(d_l), n=45)
# its legs go, momentum carries it on: crashes onto its side, ploughs
AL.mode(T_SWEEP, 'limp')
crash_p = lunge_to - d_l * 3.2
crash_p[2] = 0.3 * AS + 0.15
AL.m.key(T_SWEEP, lunge_to)
AL.m.key(T_CRASH, lunge_to - d_l * 1.8 + v3(0, 0, -0.7), 'in2')
AL.m.key(T_CRASH + 0.7, crash_p, 'outx')
AL.tr.key(T_SWEEP, roll=0.0, pitch=0.0, heading=math.atan2(-d_l[1], -d_l[0]), auto=0.0)
AL.tr.key(T_CRASH, 'in2', roll=-72.0, pitch=-12.0)
AL.tr.key(T_CRASH + 0.7, 'out', roll=-84.0, pitch=0.0, jaw=0.8)
for k in range(8):
    tt = T_CRASH + k * 0.09
    event(tt, 'thud', AL.m(tt) * v3(1, 1, 0), n=150, speed=5.0 - k * 0.5)
event(T_CRASH, 'tremor', (0, 0, 0), n=1)
# struggling up
AL.mode(36.3, 'crouch')
AL.tr.key(36.3, roll=-84.0).key(37.4, 'io', roll=0.0, pitch=4.0, jaw=0.6)
AL.m.key(36.3, crash_p)
AL.m.key(37.4, crash_p * v3(1, 1, 0) + v3(0, 0, AZ - 0.35), 'io')
AL.mode(37.4, 'stand')

# ============================================================== leap onto its back
P_S = HR(T_SWEEP + 0.4)
yaw_b = yaw_to(P_S, crash_p)
pose(T_SWEEP + 0.45, 'io', lean=20, head=0, yaw=yaw_b, gnd=1.0, fx1=0.38, fz1=0.18, fy1=-0.66,
     fx2=-0.36, fz2=-0.16, fy2=-0.7, wa=-120.0, wtilt=10.0, bside=1.0)
root(T_SWEEP + 0.45, v3(P_S[0], P_S[1], 0.7))
run_to = crash_p * v3(1, 1, 0) - fvec(yaw_b) * 2.3
run_to[2] = 0.78
walk(35.75, 36.75, period=0.25, width=0.12, lift=0.16, first='r')
root(35.75, v3(P_S[0], P_S[1], 0.76))
root(36.75, run_to, 'io')
pose(35.75, 'io', lean=28)
lock('r', 36.77, T_LEAP)
lock('l', 36.77, T_LEAP)
# muzzle into the snow beneath her, fire: the recoil throws her up
pose(T_LEAP - 0.1, 'io', wa=-95.0, wtilt=0.0, wx=0.12, wy=-0.15, g1=0.72, two=0.0, hx=-0.3, hy=0.1, hz=-0.2,
     lean=8, sq=0.92)
root(T_LEAP - 0.1, v3(run_to[0], run_to[1], 0.62))


def al_frame(t):
    st = AL.state(t)
    return st


mount_local = (0.12, 0.43, 0.0)        # kneeling astride its shoulders (body frame, x scale)


def on_back(t):
    st = AL.state(t)
    return st.W(*mount_local)


land_on = on_back(T_MOUNT)
HR.arc(T_LEAP, T_MOUNT, HR(T_LEAP - 1e-3), land_on, g=9.81)
pose(T_LEAP + 0.1, 'outx', sq=1.06, lean=-8, pitch=0.0, **dict(fx1=0.25, fz1=0.18, fy1=-0.45, fx2=-0.2,
                                                            fz2=-0.18, fy2=-0.5, gnd=0.0))
event(T_LEAP, 'shot', HP(T_LEAP).muzzle, dir=(0, 0, -1), big=True)
event(T_LEAP + 0.01, 'thud', HP(T_LEAP).muzzle * v3(1, 1, 0), n=200, speed=5.0)
# ride: root follows the body; yaw/pitch follow its heading/pitch (sampled densely)
HR.fn(T_MOUNT, T_FALL + 0.1, on_back)
RIDE = dict(lean=20, head=-10, fx1=0.3, fz1=0.35, fy1=-0.35, fx2=0.25, fz2=-0.35, fy2=-0.38, gnd=0.0)
pose(T_MOUNT, 'in2', sq=0.88, **RIDE, wa=150.0, wtilt=0.0, wx=0.0, wy=0.15, g1=0.3, g2=0.55, two=1.0,
     bside=-1.0)
pose(T_MOUNT + 0.2, 'out', sq=1.0)
for k in range(int((T_FALL + 0.1 - T_MOUNT) * 24) + 2):
    tt = T_MOUNT + k / 24
    st = AL.state(tt)
    f = st.f
    yaw_k = math.degrees(math.atan2(f[1], f[0]))
    pit_k = -math.degrees(math.asin(clamp(f[2], -1, 1)))
    HT.key(tt, 'lin', yaw=yaw_k, pitch=pit_k)
# it rears to throw her
AL.tr.key(T_REAR - 0.3, pitch=0.0).key(T_REAR + 0.45, 'out', pitch=38.0).key(T_POINTBLANK + 0.1, 'io', pitch=30.0)
AL.m.key(T_REAR - 0.3, crash_p * v3(1, 1, 0) + v3(0, 0, AZ - 0.35))
AL.m.key(T_REAR + 0.45, crash_p * v3(1, 1, 0) + v3(0, 0, AZ + 0.55), 'out')
AL.tr.key(T_REAR - 0.1, jaw=0.4).key(T_REAR + 0.3, jaw=1.0)
# she raises the blade, drives it down into the neck, then fires point-blank
pose(T_REAR + 0.4, 'io', wa=165.0, lean=5, head=-20, wy=0.3)
pose(T_STAB, 'in2', wa=-70.0, lean=48, head=-30, wx=0.45, wy=-0.3)
pose(T_POINTBLANK - 0.05, 'io', wa=-75.0)
pose(T_POINTBLANK + 0.08, 'outx', wa=-68.0, lean=34, sq=0.95)
C_STAB = HP(T_STAB).blade_tip
event(T_STAB, 'hit', C_STAB, dir=(0, 0, 1), n=90, big=True)
event(T_STAB, 'ichor', C_STAB, dir=(0, 0, 2.5), n=220)
event(T_POINTBLANK, 'shot', HP(T_POINTBLANK).muzzle, dir=tuple(norm(HP(T_POINTBLANK).w_u)), big=True)
event(T_POINTBLANK, 'ichor', C_STAB, dir=(0, 0, 3.5), n=300)

# ============================================================== collapse; she's thrown clear
AL.mode(T_FALL, 'limp')
AL.tr.key(T_FALL, roll=0.0, pitch=30.0).key(T_FALL + 1.1, 'in2', roll=92.0, pitch=0.0, jaw=0.9)
fall_p = crash_p * v3(1, 1, 0) + np.cross(fvec(yaw_b), UP) * -1.2 + v3(0, 0, 0.3 * AS + 0.1)
AL.m.key(T_FALL, crash_p * v3(1, 1, 0) + v3(0, 0, AZ + 0.4))
AL.m.key(T_FALL + 1.1, fall_p, 'in2')
event(T_FALL + 1.1, 'thud', fall_p * v3(1, 1, 0), n=400, speed=6.0)
event(T_FALL + 1.1, 'tremor', (0, 0, 0), n=1)
throw_dir = np.cross(fvec(yaw_b), UP) * 1.0
thrown_land = HR(T_FALL + 0.1) * v3(1, 1, 0) + throw_dir * 3.0 + v3(0, 0, 0.35)
HR.arc(T_FALL + 0.1, T_FALL + 0.75, HR(T_FALL + 0.1 - 1e-3), thrown_land, g=9.81)
yaw_thr = yaw_to(v3(0, 0, 0), throw_dir)
pose(T_FALL + 0.1, 'lin', pitch=0.0, yaw=yaw_thr)
pose(T_FALL + 0.35, 'out', pitch=-40.0, lean=10, head=15, gnd=0.0, **dict(fx1=0.3, fz1=0.18, fy1=-0.5,
                                                                     fx2=0.1, fz2=-0.18, fy2=-0.6),
     wa=60.0, wtilt=0.0)
pose(T_FALL + 0.75, 'io', pitch=-150.0, lean=40)
root(T_FALL + 0.75, thrown_land)
root(T_FALL + 1.2, thrown_land + throw_dir * 1.0 + v3(0, 0, -0.05), 'out')
pose(T_FALL + 1.15, 'io', pitch=-360.0, lean=30)
pose(T_FALL + 1.151, 'step', pitch=0.0)
KNEEL = dict(fx1=0.42, fz1=0.18, fy1=-0.42, fx2=-0.3, fz2=-0.16, fy2=-0.52, lean=16, head=-4, gnd=1.0)
yaw_k2 = yaw_to(thrown_land, fall_p)
pose(T_KNEEL, 'io', **KNEEL, yaw=yaw_k2, wa=-130.0, wtilt=20.0, wx=0.1, wy=-0.35, bside=1.0)
P_K = thrown_land + throw_dir * 1.2
root(T_KNEEL, v3(P_K[0], P_K[1], 0.58))
lock('r', T_KNEEL + 0.02, T_STAND - 0.1)
lock('l', T_KNEEL + 0.02, T_STAND + 0.3)
event(T_FALL + 0.75, 'thud', thrown_land * v3(1, 1, 0), n=150, speed=4.0)

# ============================================================== ash
AL.mode(T_FALL + 1.1, 'dead')
AL.tr.key(T_ASH, dissolve=0.0).key(T_ASH + 3.2, 'in2', dissolve=1.0)
AL.t_dead = T_ASH + 3.2
event(T_ASH, 'ash', (0, 0, 0), wolf='ALPHA', t1=AL.t_dead)

# ============================================================== CODA
pose(T_STAND, 'io', lean=6, head=-2, fx1=0.14, fz1=0.13, fy1=-0.84, fx2=-0.12, fz2=-0.14, fy2=-0.84,
     wa=-100.0, wtilt=10.0, sq=1.0)
root(T_STAND, v3(P_K[0], P_K[1], 0.8))
lock('r', T_STAND + 0.02, DUR)
lock('l', T_STAND + 0.4, DUR)
pose(T_FOLD1 - 0.3, 'io', wa=-60.0, wtilt=0.0, g1=0.45, two=0.0, wx=0.25, wy=-0.2, wz=0.15,
     hx=0.0, hy=-0.46, hz=-0.17)
pose(T_FOLD1, 'lin', unfold=1.0)
pose(T_FOLD1 + 0.1, 'outx', unfold=0.5)
pose(T_FOLD2, 'lin', unfold=0.5)
pose(T_FOLD2 + 0.1, 'outx', unfold=0.0)
pose(T_FOLD2 + 0.15, 'io', held=1.0)
pose(T_MOONUP, 'io', held=0.0, two=0.0, h1x=0.02, h1y=-0.47, h1z=0.17)
yaw_moon = math.degrees(math.atan2(TO_MOON[1], TO_MOON[0]))
pose(T_MOONUP + 0.2, 'io', yaw=yaw_k2)
pose(T_MOONUP + 1.4, 'io', yaw=yaw_moon + 25, head=-22, head_yaw=-18, lean=2)
for k in range(6):
    tb = T_STAND + 0.3 + k * 0.9
    pose(tb, 's', sq=1.012)
    pose(tb + 0.45, 's', sq=0.996)

# ============================================================== camera
def behind(H, dist, side, h):
    return H.chest - H.fwd * dist + H.right * side + v3(0, 0, h)


def C3a(t):   # over her shoulder into the moonlit fog: it comes out of the light
    H = HP(t)
    eye = behind(H, 2.2, 0.45, -0.25) + handheld(t, 0.008, 21.0)
    tgt = H.chest + H.fwd * 10.0 + v3(0, 0, 1.2)
    return dict(eye=eye, target=tgt, lens=35, fstop=2.8, focus=np.linalg.norm(AL.m(t) - eye))


def C3b(t):   # the three shots, profile
    H = HP(t)
    s = np.cross(fvec(yaw_al), UP)
    eye = PH + s * 3.2 + fvec(yaw_al) * 1.2 + v3(0, 0, 1.1) + handheld(t, 0.012, 22.0)
    return dict(eye=eye, target=PH + fvec(yaw_al) * 2.5 + v3(0, 0, 1.4), lens=28, fstop=3.2,
                focus=np.linalg.norm(PH - eye))


def C3c(t):   # the roar, from low beside her
    H = HP(t)
    hd = AL.state(t).headp
    eye = H.chest - fvec(yaw_al) * 0.6 + np.cross(fvec(yaw_al), UP) * -0.9 + v3(0, 0, -0.55)
    eye = eye + handheld(t * 3, 0.02 * clamp((t - T_ROAR) * 3), 23.0)
    return dict(eye=eye, target=hd, lens=38, fstop=2.8)


def C3d(t):   # charge + swat: wide over her shoulder, it fills the frame coming in
    Hc = HP(T_CHARGE)
    eye = Hc.chest - Hc.fwd * 3.6 + Hc.right * 1.6 + v3(0, 0, -0.35) + handheld(t, 0.02, 24.0)
    tgt = lerp(Hc.chest, stop1, 0.45) + v3(0, 0, 0.8)
    return dict(eye=eye, target=tgt, lens=24, fstop=4.0, focus=np.linalg.norm(Hc.chest - eye))


def C3e(t):   # at the tree, low; snow comes down on her
    eye = slump + norm(P_SH - slump) * v3(1, 1, 0) * 2.6 + np.cross(to_tree, UP) * 0.9 + v3(0, 0, 0.3)
    sh = 0.07 * math.exp(-max(0, t - T_TREE) * 4) if t > T_TREE else 0
    eye = eye + handheld(t * 6, sh, 25.0)
    return dict(eye=eye, target=slump + v3(0, 0, 0.9), lens=32, fstop=2.2)


def C3f(t):   # the low point: three-quarter front, slow push; it paces through the background
    u = clamp((t - 30.4) / 3.8)
    face_dir = norm((P_SH - slump) * v3(1, 1, 0))
    d = rot_axis(UP, 0.7) @ face_dir
    H = HP(t)
    eye = slump + d * lerp(3.6, 2.4, EASE['io'](u)) + v3(0, 0, lerp(0.75, 1.05, u)) + handheld(t, 0.006, 26.0)
    return dict(eye=eye, target=H.head + v3(0, 0, -0.15), lens=45, fstop=2.2,
                focus=np.linalg.norm(H.head - eye))


def C3g(t):   # lunge / slide / sweep: ground-level, looking up as it passes over her
    eye = P_L + d_l * 5.2 + np.cross(d_l, UP) * 2.2 + v3(0, 0, 0.35) + handheld(t, 0.02, 27.0)
    return dict(eye=eye, target=lerp(P_L, lunge_to, 0.6) + v3(0, 0, 0.9), lens=22, fstop=3.2)


def C3h(t):   # on its side; she launches onto it
    eye = crash_p + np.cross(fvec(yaw_b), UP) * -7.5 - fvec(yaw_b) * 2.5 + v3(0, 0, 1.6) + handheld(t, 0.015, 28.0)
    return dict(eye=eye, target=crash_p + v3(0, 0, 1.3) - fvec(yaw_b) * 1.0, lens=26, fstop=4.0)


def C3i(t):   # rearing against the moon: low, looking up, moon behind them
    c = crash_p * v3(1, 1, 0)
    eye = c - TO_MOON * v3(1, 1, 0) * 9.5 + v3(0, 0, 0.4) + handheld(t, 0.012, 29.0)
    tgt = c + v3(0, 0, 3.2)
    return dict(eye=eye, target=tgt, lens=30, fstop=4.0, focus=np.linalg.norm(c - eye))


def C3j(t):   # point-blank: side-on, far enough to read both of them
    H = HP(T_STAB)
    s_ = np.cross(H.fwd * v3(1, 1, 0), UP)
    eye = H.chest + norm(s_) * 7.0 + v3(0, 0, -1.6) + handheld(t, 0.01, 30.0)
    return dict(eye=eye, target=H.chest + v3(0, 0, 0.2), lens=45, fstop=4.0)


def C3k(t):   # collapse; she's thrown clear
    c = crash_p * v3(1, 1, 0)
    eye = c + throw_dir * 7.5 - fvec(yaw_b) * 4.0 + v3(0, 0, 1.3) + handheld(t, 0.02, 31.0)
    return dict(eye=eye, target=lerp(c, P_K, 0.55) + v3(0, 0, 1.0), lens=26, fstop=4.0)


def C3l(t):   # behind her kneeling, the alpha burning away beyond, embers climbing
    u = clamp((t - T_ASH) / 4.0)
    d = norm((fall_p - P_K) * v3(1, 1, 0))
    s_ = np.cross(d, UP)
    eye = P_K - d * lerp(3.0, 3.6, u) + s_ * 1.0 + v3(0, 0, 0.55) + handheld(t, 0.006, 32.0)
    tgt = fall_p * v3(1, 1, 0) + v3(0, 0, lerp(1.0, 2.2, u))
    return dict(eye=eye, target=tgt, lens=30, fstop=3.5, focus=np.linalg.norm(P_K - eye))


def C4a(t):   # crane up past her to the moon
    u = clamp((t - T_MOONUP) / 5.5)
    H = HP(t)
    eye = H.chest - TO_MOON * v3(1, 1, 0) * 3.5 + v3(0, 0, lerp(0.2, 2.8, EASE['io'](u)))
    tgt = lerp(H.head, H.head + TO_MOON * 60, EASE['io'](clamp((u - 0.15) / 0.8)))
    return dict(eye=eye, target=tgt, lens=lerp(35, 28, u), fstop=4.0, focus=np.linalg.norm(H.head - eye))


shot(23.9, C3a)
shot(25.85, C3b)
shot(T_ROAR - 0.1, C3c)
shot(T_CHARGE + 0.25, C3d)
shot(T_TREE - 0.02, C3e)
shot(30.4, C3f)
shot(34.25, C3g)
shot(T_SWEEP + 0.55, C3h)
shot(T_MOUNT + 0.3, C3i)
shot(T_POINTBLANK - 0.2, C3j)
shot(T_FALL + 0.05, C3k)
shot(T_ASH, C3l)
shot(T_STAND + 1.8, C4a)
