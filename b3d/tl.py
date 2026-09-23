"""EMBER II — master timeline.  120 BPM, 24 fps: one beat == 12 frames exactly."""
import math

BPM = 120.0
BEAT = 0.5
BAR = 2.0
FPS = 24
NBARS = 26
DUR = NBARS * BAR          # 52 s
NFR = int(DUR * FPS)       # 1248 frames
SR = 48000


def B(bar, beat=0.0):
    return bar * BAR + beat * BEAT


def F(t):
    """Seconds -> Blender frame number (1-based)."""
    return int(round(t * FPS)) + 1


# ---------------------------------------------------------------- ACT I
T_STOP = B(2, 0)
T_LISTEN = B(2, 2)
T_EYES = [B(3, 0), B(3, 1), B(3, 2)]
T_REACH = B(4, 0)
T_UNFOLD1 = B(4, 2)
T_UNFOLD2 = B(4, 3)
T_CIRCLE = B(5, 0)
T_BREATH = B(5, 3)
# ---------------------------------------------------------------- ACT II
T_DROP = B(6, 0)          # rising cut on W1
T_W2SHOT = B(6, 3)        # spin + point-blank shot on W2
T_CHOP = B(7, 2)          # finishing chop on W2
T_TACKLE = B(8, 0)        # W3 tackles her
T_UP = B(8, 3)            # back on her feet
T_DASHSHOT = B(9, 1)      # recoil dash
T_HOOK = B(9, 2)          # hook W3 foreleg
T_W3DOWN = B(9, 3)
T_PLANT = B(10, 0)        # blade into W3's neck
T_TREMOR1 = B(11, 0)
T_TREMOR2 = B(11, 2)
# ---------------------------------------------------------------- ACT III
T_ALPHA = B(12, 0)        # alpha emerges
T_SHOTS = [B(13, 0), B(13, 1), B(13, 2)]
T_ROAR = B(13, 3)
T_CHARGE = B(14, 0)
T_SWAT = B(14, 2)
T_TREE = B(14, 3)
T_RISE = B(15, 0)
T_LUNGE = B(17, 1)
T_SWEEP = B(17, 2)
T_CRASH = B(17, 3)
T_LEAP = B(18, 2)
T_MOUNT = B(18, 3)
T_REAR = B(19, 0)
T_STAB = B(19, 2)
T_POINTBLANK = B(19, 3)
T_FALL = B(20, 0)
T_KNEEL = B(20, 3)
T_ASH = B(21, 0)
# ---------------------------------------------------------------- CODA
T_STAND = B(22, 0)
T_FOLD1 = B(22, 2)
T_FOLD2 = B(22, 3)
T_MOONUP = B(23, 0)
T_TITLE = B(24, 0)


# Speed ramps are used sparingly, the way live action uses them.
SLOWMO = [(T_DROP - 0.02, T_DROP + 0.22, 0.35, 0.06),
          (T_POINTBLANK - 0.04, T_POINTBLANK + 0.3, 0.3, 0.08)]


def _bump(t, a, b, lo, ramp):
    if t < a - ramp or t > b + ramp:
        return 1.0
    u = (t - (a - ramp)) / ramp if t < a else (1 - (t - b) / ramp if t > b else 1.0)
    u = u * u * (3 - 2 * u)
    return 1.0 + (lo - 1.0) * u


def timescale(t):
    s = 1.0
    for (a, b, lo, r) in SLOWMO:
        s = min(s, _bump(t, a, b, lo, r))
    return s


_WDT = 1.0 / 960
_W = [0.0]
for _i in range(int((DUR + 3) / _WDT)):
    _W.append(_W[-1] + timescale((_i + 0.5) * _WDT) * _WDT)


def warp(t):
    x = t / _WDT
    if x <= 0:
        return t
    i = int(x)
    if i >= len(_W) - 1:
        return _W[-1] + (t - (len(_W) - 1) * _WDT)
    f = x - i
    return _W[i] * (1 - f) + _W[i + 1] * f


def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def smooth(u):
    u = clamp(u)
    return u * u * (3 - 2 * u)


EASE = {
    'lin': lambda u: u,
    'in': lambda u: u ** 3,
    'out': lambda u: 1 - (1 - u) ** 3,
    'io': lambda u: 4 * u ** 3 if u < .5 else 1 - (-2 * u + 2) ** 3 / 2,
    'in2': lambda u: u * u,
    'out2': lambda u: 1 - (1 - u) ** 2,
    'outx': lambda u: 1 - (1 - u) ** 5,
    'inx': lambda u: u ** 5,
    'back': lambda u: 1 + 2.4 * (u - 1) ** 3 + 1.4 * (u - 1) ** 2,
    'step': lambda u: 0.0 if u < 1 else 1.0,
    's': smooth,
}
