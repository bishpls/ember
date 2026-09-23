"""EMBER — shared timeline. Audio and picture both read from this file so
every hit, shot and speed-ramp is locked to the same clock."""
import math

BPM = 128.0
BEAT = 60.0 / BPM          # 0.46875 s
BAR = 4 * BEAT             # 1.875 s  -> 16 bars == 30.0 s
SR = 48000
FPS = 30
DUR = 30.0
W, H = 1920, 1080


def B(bar, beat=0.0):
    """Time (s) of a bar/beat position, both 0-indexed."""
    return bar * BAR + beat * BEAT


S16 = BEAT / 4  # sixteenth note

# ---------------------------------------------------------------------------
# Key choreography beats (the cue sheet).  Section map:
#   bars 0-1  intro (piano)          bars 2-3  build, eyes open, weapon unfolds
#   bars 4-7  Fight A (drop)         bars 8-11 Fight B (double kick, lead, alpha)
#   bar 12    break (slow-mo, piano) bar 13    final flurry
#   bar 14    final cleave (Picardy D major)   bars 14.5-16 outro + title
# ---------------------------------------------------------------------------
EYE_TIMES = [B(2, 0), B(2, 1.5), B(2, 2), B(2, 3), B(3, 0)]
T_HEADUP = B(3, 0)
T_UNFOLD1 = B(3, 2)            # click
T_UNFOLD2 = B(3, 2.5)          # clack
T_BREATH = B(3, 3)             # silence, W1 lunges
T_DROP = B(4, 0)               # first cleave
T_SHOT1 = B(4, 2)              # recoil dash left
T_HOOK = B(5, 0)               # hook W2, spin
T_THROW = B(5, 1)              # fling W2 into W3
T_COLLIDE = B(5, 1.55)
T_BURST23 = B(5, 2)
T_VAULT = B(6, 0)              # pole-vault kick on W4
T_SHOT2 = B(6, 2)              # shoot W4 mid-air
T_SPIN = B(7, 0)               # 720 spin slash W5
T_SPIN2 = B(7, 0.5)            # ...W6
T_BURST56 = B(7, 1)
T_SUPERJUMP = B(7, 2)          # shoot down -> rocket up
T_DIVE = B(8, 0)
T_SLAM = B(8, 1)
T_RAPID = [B(8, 2), B(8, 2) + S16, B(8, 2) + 2 * S16]
T_DASH = B(9, 0)               # slow-mo ember dash
T_DASH_HITS = [B(9, 0.25), B(9, 0.9), B(9, 1.55)]
T_DASH_BURST = B(9, 2)         # delayed kills, snap to speed
T_ALPHA = B(10, 0)             # alpha lands
T_BLOCK = B(10, 2)             # alpha swipe blocked, slide back
T_CHARGE = B(11, 0)
T_UNDER = B(11, 0.6)           # alpha swipe misses overhead
T_LEGHOOK = B(11, 1)
T_LAUNCH = B(11, 2)
T_BREAK = B(12, 0)
T_RACK = B(12, 3) - 0.05       # rack weapon in silence
T_RACK2 = B(12, 3.4)
T_FINAL = B(13, 0)             # fire, rocket down
T_CARVE0 = B(13, 0.5)
T_CARVE = [T_CARVE0 + i * S16 * 2 for i in range(6)]  # 8th-note carves
T_CLEAVE = B(14, 0)            # final cleave, stop-hit
T_ALPHA_BURST = B(14, 1)
T_FOLD = B(15, 0) - 0.3
T_TITLE = B(14, 3)
T_END = DUR


# ---------------------------------------------------------------------------
# Time-scale (for particles / cloth / snow): hit-stops and slow-mo.
# ---------------------------------------------------------------------------
def _bump(t, a, b, lo, ramp):
    """1 outside [a,b], `lo` inside, smooth ramps of length `ramp`."""
    if t < a - ramp or t > b + ramp:
        return 1.0
    if t < a:
        u = (t - (a - ramp)) / ramp
    elif t > b:
        u = 1 - (t - b) / ramp
    else:
        u = 1.0
    u = u * u * (3 - 2 * u)
    return 1.0 + (lo - 1.0) * u


HITSTOPS = [(T_DROP, 0.07), (T_HOOK, 0.05), (T_VAULT, 0.06), (T_SPIN, 0.04),
            (T_SLAM, 0.08), (T_DASH_BURST, 0.06), (T_BLOCK, 0.08),
            (T_LEGHOOK, 0.05), (T_CLEAVE, 0.18)]
SLOWMO = [(T_DASH + 0.05, T_DASH_BURST - 0.1, 0.22, 0.08),
          (T_BREAK + 0.1, T_FINAL - 0.12, 0.10, 0.2)]


def timescale(t):
    s = 1.0
    for (a, d) in HITSTOPS:
        s = min(s, _bump(t, a, a + d, 0.03, 0.012))
    for (a, b, lo, r) in SLOWMO:
        s = min(s, _bump(t, a, b, lo, r))
    return s


# Warped time W(t) = integral of timescale; precomputed on a fine grid.
_WDT = 1.0 / 1200
_WTAB = [0.0]
for _i in range(int((DUR + 2) / _WDT)):
    _WTAB.append(_WTAB[-1] + timescale((_i + 0.5) * _WDT) * _WDT)


def warp(t):
    x = t / _WDT
    if x <= 0:
        return t
    i = int(x)
    if i >= len(_WTAB) - 1:
        return _WTAB[-1] + (t - (len(_WTAB) - 1) * _WDT)
    f = x - i
    return _WTAB[i] * (1 - f) + _WTAB[i + 1] * f


# ---------------------------------------------------------------------------
# Easing
# ---------------------------------------------------------------------------
def clamp(x, a=0.0, b=1.0):
    return a if x < a else b if x > b else x


def lerp(a, b, u):
    return a + (b - a) * u


def smooth(u):
    u = clamp(u)
    return u * u * (3 - 2 * u)


EASE = {
    'lin': lambda u: u,
    'in': lambda u: u * u * u,
    'out': lambda u: 1 - (1 - u) ** 3,
    'io': lambda u: 4 * u * u * u if u < .5 else 1 - (-2 * u + 2) ** 3 / 2,
    'in2': lambda u: u * u,
    'out2': lambda u: 1 - (1 - u) ** 2,
    'outx': lambda u: 1 - (1 - u) ** 5,          # snap: fast strike, long settle
    'inx': lambda u: u ** 5,
    'back': lambda u: 1 + 2.4 * (u - 1) ** 3 + 1.4 * (u - 1) ** 2,  # overshoot
    'step': lambda u: 0.0 if u < 1 else 1.0,
    'hold': lambda u: 0.0,
    's': smooth,
}


# ---------------------------------------------------------------------------
# SFX cue list: (time, kind, pan[-1..1], gain)
# ---------------------------------------------------------------------------
SFX = []


def sfx(t, kind, pan=0.0, gain=1.0):
    SFX.append((t, kind, pan, gain))


sfx(T_UNFOLD1, 'click', 0.1, 0.8)
sfx(T_UNFOLD2, 'clack', 0.1, 1.0)
sfx(T_BREATH + 0.05, 'growl', 0.4, 0.8)
sfx(T_DROP - 0.12, 'whoosh', 0.2, 0.9)
sfx(T_DROP, 'slash_big', 0.2, 1.0)
sfx(T_DROP + 0.12, 'burst', 0.4, 0.9)
sfx(T_SHOT1, 'shot', 0.2, 1.0)
sfx(T_SHOT1 + 0.05, 'dash', -0.3, 0.7)
sfx(T_HOOK, 'clang', -0.4, 0.8)
sfx(T_HOOK + 0.1, 'whoosh', -0.4, 0.8)
sfx(T_THROW, 'whoosh', -0.5, 0.7)
sfx(T_COLLIDE, 'impact', -0.7, 0.8)
sfx(T_BURST23, 'burst', -0.7, 1.0)
sfx(T_THROW + 0.05, 'slide', -0.4, 0.6)
sfx(T_VAULT - 0.25, 'whoosh', -0.3, 0.7)
sfx(T_VAULT, 'kick', -0.2, 1.0)
sfx(T_SHOT2, 'shot', -0.1, 0.9)
sfx(T_SHOT2 + 0.07, 'burst', 0.5, 0.8)
sfx(T_SPIN - 0.1, 'whoosh', 0.0, 0.8)
sfx(T_SPIN, 'slash', 0.2, 1.0)
sfx(T_SPIN2, 'slash', -0.2, 0.9)
sfx(T_BURST56, 'burst', 0.0, 1.0)
sfx(T_SUPERJUMP, 'shot_big', 0.0, 1.0)
sfx(T_SUPERJUMP + 0.05, 'rise', 0.0, 0.7)
sfx(T_DIVE, 'shot', 0.0, 0.9)
sfx(T_SLAM, 'slam', 0.0, 1.0)
for _i, _t in enumerate(T_RAPID):
    sfx(_t, 'shot', [-0.5, 0.5, 0.0][_i], 0.75)
    sfx(_t + 0.06, 'burst', [-0.6, 0.6, 0.1][_i], 0.6)
sfx(T_DASH, 'slowmo', 0.0, 1.0)
for _i, _t in enumerate(T_DASH_HITS):
    sfx(_t, 'slash_soft', [0.4, -0.4, 0.3][_i], 0.7)
sfx(T_DASH_BURST, 'burst_big', 0.0, 1.0)
sfx(T_ALPHA, 'slam', -0.3, 1.0)
sfx(T_ALPHA + 0.12, 'roar', -0.3, 1.0)
sfx(T_BLOCK, 'clang_big', 0.0, 1.0)
sfx(T_BLOCK + 0.05, 'slide', 0.3, 0.9)
sfx(T_CHARGE, 'shot', 0.2, 0.9)
sfx(T_UNDER - 0.08, 'whoosh', -0.2, 0.8)
sfx(T_LEGHOOK, 'clang', -0.2, 0.9)
sfx(T_LAUNCH, 'shot', -0.2, 0.9)
sfx(T_LAUNCH + 0.05, 'rise', 0.0, 0.5)
sfx(T_RACK, 'click', 0.0, 1.0)
sfx(T_RACK2, 'clack', 0.0, 1.1)
sfx(T_FINAL, 'shot_big', 0.0, 1.1)
for _i, _t in enumerate(T_CARVE):
    sfx(_t, 'slash', 0.3 * (-1) ** _i, 0.55 + 0.05 * _i)
sfx(T_CLEAVE - 0.1, 'whoosh', 0.0, 1.0)
sfx(T_CLEAVE, 'slash_big', 0.0, 1.2)
sfx(T_ALPHA_BURST, 'burst_big', -0.2, 1.1)
sfx(T_FOLD, 'click', 0.1, 0.7)
sfx(T_FOLD + 0.18, 'clack', 0.1, 0.8)
