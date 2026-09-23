"""EMBER II — score + sound design.  120 BPM, D minor -> D major.  Reuses the 2D synth engine.
Writes out/ember2.wav"""
import os
import sys
import math
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(1, os.path.dirname(HERE))
import audio as Au                      # 2D engine: instruments, DSP, mixing helpers
from tl import *
import ch
import act1, act2, act3                 # noqa: registers events
from ch import EVENTS

SR = Au.SR
Au.N = N = int((DUR + 1.0) * SR)
put, new, filt = Au.put, Au.new, Au.filt
rng = np.random.default_rng(11)

CH = {'Dm': [50, 53, 57, 62], 'Bb': [46, 50, 53, 58], 'C': [48, 52, 55, 60], 'A': [45, 49, 52, 57],
      'Gm': [43, 50, 55, 58], 'Eb': [51, 55, 58, 63], 'D': [50, 54, 57, 62], 'F': [53, 57, 60, 65]}
# the EMBER theme (from the 2D film), bar-relative (beat, len, midi)
THEME = [[(0, 1.5, 69), (1.5, .5, 74), (2, 1, 77), (3, 1, 76)],
         [(0, 1.5, 74), (1.5, .5, 72), (2, 1.5, 74), (3.5, .5, 70)],
         [(0, 1.5, 72), (1.5, .5, 74), (2, 1, 76), (3, 1, 79)],
         [(0, 3, 76), (3, 1, 73)]]


def tt(n):
    return np.arange(n) / SR


def drone(m, dur, g=1.0):
    n = int((dur + 1.0) * SR)
    t = tt(n)
    f = Au.mtof(m)
    y = Au.saw(f, n) + Au.saw(f * 1.004, n) * 0.8 + Au.saw(f * 0.5, n) * 0.5
    y = Au.sweep_lp(y, 180 + 140 * (0.5 + 0.5 * np.sin(2 * np.pi * 0.2 * t)))
    e = np.minimum(1, t / 1.2) * np.where(t > dur, np.exp(-(t - dur) * 2), 1)
    return y * e * 0.18 * g


def trem_strings(chord, dur, g=1.0):
    n = int((dur + 0.6) * SR)
    t = tt(n)
    y = np.zeros(n)
    for m in chord:
        f = Au.mtof(m)
        y += Au.saw(f * (1 + 0.003 * np.sin(2 * np.pi * 5 * t)), n)
    trem = 0.55 + 0.45 * np.sign(np.sin(2 * np.pi * 8 * t))
    y = filt(y, 'lp', 2400) * filt(trem, 'lp', 60)
    e = np.minimum(1, t / 0.8) * np.where(t > dur, np.exp(-(t - dur) * 5), 1)
    return y * e * 0.05 * g


def brass_hit(m, dur=1.2, g=1.0):
    n = int((dur + 0.6) * SR)
    t = tt(n)
    y = np.zeros(n)
    for iv in (0, 7, 12, -12):
        f = Au.mtof(m + iv)
        y += Au.saw(f, n) + Au.saw(f * 1.006, n)
    fc = 300 + 2600 * np.exp(-t * 3)
    y = np.tanh(Au.sweep_lp(y, fc) * 1.5)
    e = np.minimum(1, t / 0.02) * np.exp(-t * 1.2) * np.where(t > dur, np.exp(-(t - dur) * 6), 1)
    return y * e * 0.14 * g


def crunch(g=1.0):
    """footstep in deep snow"""
    n = int(0.25 * SR)
    t = tt(n)
    imp = (rng.random(n) < 0.02 * np.exp(-t * 18)) * rng.standard_normal(n)
    y = filt(imp, 'bp', [400, 4000]) * 1.6 + filt(Au.noise(n), 'lp', 900) * np.exp(-t * 25) * 0.5
    return y * g * 0.5


def tinnitus(dur):
    n = int(dur * SR)
    t = tt(n)
    return np.sin(2 * np.pi * 4150 * t) * np.exp(-t * 0.9) * 0.05


def breath(dur=0.9, g=1.0):
    n = int(dur * SR)
    t = tt(n)
    env = np.sin(np.pi * np.clip(t / dur, 0, 1)) ** 2
    return filt(Au.noise(n), 'bp', [500, 2500]) * env * 0.12 * g


def build():
    B_ = {k: new() for k in ['pno', 'pad', 'drm', 'gtr', 'bas', 'lead', 'fx', 'amb', 'str']}
    send = new()
    T = tt(N)
    # ------------------------------------------------------------- ambience
    wl = Au.sweep_lp(Au.noise(N), 380 + 260 * np.sin(2 * np.pi * 0.11 * T) + 150 * np.sin(2 * np.pi * 0.29 * T))
    wr = Au.sweep_lp(Au.noise(N), 400 + 260 * np.sin(2 * np.pi * 0.09 * T + 1) + 150 * np.sin(2 * np.pi * 0.23 * T))
    wenv = np.interp(T, [0, 2, 11.4, 12, 20.5, 21.5, 24, 29.5, 30.0, 34, 34.3, 42, 44, DUR],
                     [0.5, 1, 1, 0.3, 0.3, 0.9, 0.7, 0.4, 1.1, 1.0, 0.3, 0.3, 0.9, 0.7])
    B_['amb'] += (np.stack([wl, wr], 1) * 0.1 * wenv[:, None]).astype(np.float32)

    # ------------------------------------------------------------- ACT I (0-12)
    put(B_['pad'], 0.0, drone(38, 11.4, 1.0), 1.0, 0.0)
    for i, bar in enumerate([0, 1, 2, 3]):
        for (b, l, m) in THEME[i]:
            put(B_['pno'], B(bar, b), Au.piano(m, l * BEAT * 1.1, 0.7), 0.9, 0.15)
    for bar, ch_ in [(0, 'Dm'), (1, 'Bb'), (2, 'C'), (3, 'A'), (4, 'Dm'), (5, 'Bb')]:
        put(B_['pno'], B(bar), Au.piano(CH[ch_][0] - 12, BAR, 0.55), 0.8, -0.2)
    # heartbeat from the eyes on
    for k in range(10):
        tb = T_EYES[0] + k * BEAT * 2
        if tb > T_BREATH:
            break
        put(B_['drm'], tb, Au.kick(0.6 + 0.04 * k, 0.7), 1.0)
        put(B_['drm'], tb + 0.2, Au.kick(0.4 + 0.03 * k, 0.7), 1.0)
    put(B_['str'], T_EYES[0], trem_strings([62, 65, 69], T_BREATH - T_EYES[0], 1.0), 1.0, 0.0)
    for i, te in enumerate(T_EYES):
        put(B_['fx'], te, Au.make_sfx('growl'), 0.7, [0.6, -0.6, -0.2][i])
    put(B_['fx'], T_UNFOLD1, Au.make_sfx('click'), 1.0, 0.1)
    put(B_['fx'], T_UNFOLD2, Au.make_sfx('clack'), 1.2, 0.1)
    put(send, T_UNFOLD2, Au.make_sfx('clack'), 0.5, 0.1)
    # toms under the circling, then the breath
    for i, b in enumerate([0, 1, 2, 2.5, 3, 3.25, 3.5, 3.75, 4, 4.5, 5]):
        tb = T_CIRCLE + b * BEAT * 0.62
        if tb < T_BREATH:
            put(B_['drm'], tb, Au.tom(43 - (i % 3) * 3, 0.35 + 0.05 * i), 1.0, [-.4, .3, 0][i % 3])
    put(B_['fx'], T_BREATH - 0.35, Au.reverse_swell(0.35 + BEAT), 0.8)

    # ------------------------------------------------------------- ACT II (12-24): the pack
    prog = ['Dm', 'Bb', 'C', 'A', 'Dm', 'Bb', 'Gm', 'A', 'Dm']
    roots = {'Dm': 38, 'Bb': 34, 'C': 36, 'A': 33, 'Gm': 31}
    ev = []
    for j, bar in enumerate(range(6, 11)):
        ch_ = prog[j]
        r = roots[ch_]
        ev.append((B(bar, 0), r, BEAT * 0.8, False))
        for sx in [0.75, 1, 1.25, 1.5, 2.25, 3, 3.25, 3.5, 3.75]:
            ev.append((B(bar, sx), 38 if sx >= 3 else r, BEAT / 4 * 0.8, True))
        ev.append((B(bar, 1.75), r, BEAT * 0.45, False))
        ev.append((B(bar, 2.5), r, BEAT * 0.45, False))
        for k in [0, 0.75, 1.5, 2, 2.75, 3.5]:
            put(B_['drm'], B(bar, k), Au.kick(0.9 if k % 1 == 0 else 0.7), 1.0)
        for sn in [1, 3]:
            put(B_['drm'], B(bar, sn), Au.snare(1.0), 1.0, 0.05)
            put(send, B(bar, sn), Au.snare(0.5), 1.0)
        for h in range(8):
            put(B_['drm'], B(bar, h * .5), Au.hat(0.7 if h % 2 else 0.45), 1.0, 0.35)
        for i, m in enumerate(CH[ch_]):
            put(B_['pad'], B(bar), Au.choir_note(m + 12, BAR), 0.9, -0.5 + i * 0.33)
    for tc in (T_DROP, B(8, 0)):
        put(B_['drm'], tc, Au.crash(1.0), 1.0, 0.3)
        put(send, tc, Au.crash(0.4), 1.0)
    # lead states the theme over the fight
    for i, bar in enumerate([8, 9]):
        for (b, l, m) in THEME[i]:
            put(B_['lead'], B(bar, b), Au.lead_note(m + 12, l * BEAT * 0.95), 1.0, 0.1)
    # breather (21-24): pad + pulse; tremors
    for i, m in enumerate(CH['Dm']):
        put(B_['pad'], 21.0, Au.choir_note(m, 3.0, vowel='o'), 0.7, -0.4 + i * 0.26)
    put(B_['pad'], 21.0, drone(38, 3.0, 0.8), 1.0)

    # ------------------------------------------------------------- ACT III (24-42): the alpha
    put(B_['pad'], 24.0, drone(39, 4.0, 1.2), 1.0)      # Eb: the Phrygian shadow over D
    for k in range(8):                                   # its footfalls, on the beat
        tb = 24.0 + k * BEAT
        put(B_['drm'], tb, Au.boom(0.55 + 0.04 * k, 1.2, 38), 1.0)
    for tb, m in ((24.0, 39), (25.0, 39), (26.0, 38), (27.0, 39)):
        put(B_['str'], tb, brass_hit(m, 0.9, 0.9), 1.0, 0.0)
    put(B_['fx'], T_ROAR, Au.make_sfx('roar'), 1.4, -0.2)
    put(B_['fx'], T_ROAR, Au.make_sfx('roar'), 1.0, 0.3)
    # charge: drums back, frantic
    for k in range(16):
        put(B_['drm'], B(14, k * 0.25), Au.kick(0.85), 1.0)
    for sn in [1, 2, 2.5]:
        put(B_['drm'], B(14, sn), Au.snare(1.0), 1.0)
    ev.append((T_CHARGE, 39, BEAT * 1.0, False))
    for k in range(4, 8):
        ev.append((B(14, k * 0.25), 38, BEAT / 4 * 0.8, True))
    # the tree: everything stops. ringing ears.
    put(B_['fx'], T_TREE, tinnitus(3.6), 1.0, 0.0)
    put(B_['fx'], T_TREE, Au.make_sfx('slam'), 1.2, -0.3)
    put(send, T_TREE, Au.make_sfx('slam'), 0.6)
    # the low point: solo piano, theme fragment, lots of air
    for (b, l, m) in [(0, 1.5, 69), (1.5, .5, 74), (2, 2.0, 77)]:
        put(B_['pno'], B(15, b + 1), Au.piano(m - 12, l * BEAT * 1.6, 0.6), 1.0, 0.1)
    for (b, l, m) in [(0, 1.5, 74), (1.5, .5, 72), (2, 2.5, 74)]:
        put(B_['pno'], B(16, b), Au.piano(m - 12, l * BEAT * 1.6, 0.55), 1.0, 0.1)
    put(B_['pno'], B(15, 1), Au.piano(34, BAR * 2, 0.5), 0.8, -0.2)
    for tb in (30.4, 31.1, 31.8, 32.6):
        put(B_['fx'], tb, breath(0.8), 1.0, 0.1)
    for k in range(6):
        put(B_['drm'], 30.5 + k * 0.62, Au.boom(0.35, 1.0, 36), 1.0, -0.4)
    put(B_['fx'], 33.2, Au.reverse_swell(34.0 - 33.2), 0.8)
    # climax (34-40)
    for bar, ch_ in [(17, 'Bb'), (18, 'C'), (19, 'A')]:
        r = roots.get(ch_, 38)
        for k in range(16):
            put(B_['drm'], B(bar, k * 0.25), Au.kick(0.8), 1.0)
        for sn in [1, 3]:
            put(B_['drm'], B(bar, sn), Au.snare(1.0), 1.0, 0.05)
        ev.append((B(bar, 0), r, BEAT * 0.9, False))
        for sx in [1, 1.5, 2, 2.5, 3, 3.5]:
            ev.append((B(bar, sx), r, BEAT * 0.4, sx % 1 != 0))
        for i, m in enumerate(CH[ch_]):
            put(B_['pad'], B(bar), Au.choir_note(m + 12, BAR), 1.1, -0.5 + i * 0.33)
    for (b, l, m) in THEME[2] + [(4 + b, l, m) for (b, l, m) in THEME[3]]:
        put(B_['lead'], B(18, b), Au.lead_note(m + 12, l * BEAT * 0.95, 1.1), 1.0, 0.1)
    for k in range(8):   # snare roll into the stab
        put(B_['drm'], B(19, 1 + k * 0.125), Au.snare(0.35 + 0.08 * k), 1.0)
    put(B_['drm'], T_SWEEP, Au.crash(1.0), 1.0, -0.3)
    put(B_['fx'], T_CRASH, Au.make_sfx('slam'), 1.3, 0.0)
    put(B_['fx'], T_REAR + 0.1, Au.make_sfx('roar'), 1.3, 0.2)
    # the point-blank shot: then everything drops to a slow, pitched-down tail
    put(B_['fx'], T_POINTBLANK, Au.boom(1.4, 2.5, 30), 1.0)
    # collapse + Picardy D major blooming from the ashes
    put(B_['fx'], T_FALL + 1.1, Au.make_sfx('slam'), 1.4, 0.0)
    put(B_['drm'], T_FALL + 1.1, Au.crash(1.2, 3.0), 1.0, 0.0)
    for i, m in enumerate([50, 54, 57, 62, 66, 69, 74]):
        put(B_['pad'], T_ASH, Au.choir_note(m + 12 if m < 60 else m, 9.5), 1.1, -0.6 + i * 0.2)
    put(B_['pad'], T_ASH, drone(38, 9.0, 0.7), 1.0)
    ev.append((T_ASH, 38, BAR * 1.2, False))
    # ------------------------------------------------------------- CODA: the theme, resolved
    coda = [(B(22, 0), 1.5, 69), (B(22, 1.5), .5, 74), (B(22, 2), 1, 78), (B(22, 3), 1, 76),
            (B(23, 0), 1.5, 74), (B(23, 1.5), .5, 73), (B(23, 2), 2, 74)]
    for (t0, l, m) in coda:
        put(B_['pno'], t0, Au.piano(m, l * BEAT * 1.3, 0.7), 1.3, 0.1)
    for m in (38, 45, 50, 54, 57):
        put(B_['pno'], B(24, 0), Au.piano(m, 4.0, 0.65), 1.2, -0.1)
    put(B_['fx'], T_FOLD1, Au.make_sfx('click'), 0.9, 0.1)
    put(B_['fx'], T_FOLD2, Au.make_sfx('clack'), 1.0, 0.1)

    # guitars/bass
    gl = Au.guitar_track(ev, -1)
    gr = Au.guitar_track(ev, +1)
    B_['gtr'][:, 0] += (gl * 0.9 + gr * 0.15).astype(np.float32)
    B_['gtr'][:, 1] += (gr * 0.9 + gl * 0.15).astype(np.float32)
    bs = Au.bass_track(ev)
    B_['bas'] += np.stack([bs, bs], 1).astype(np.float32)

    # ------------------------------------------------------------- sound design from the choreography
    for e in EVENTS:
        k, t0 = e['kind'], e['t']
        pan = float(np.clip(e['pos'][1] / 8.0, -0.8, 0.8))
        if k == 'step':
            put(B_['fx'], t0, crunch(0.9), 1.0, pan)
        elif k == 'hit':
            x = Au.make_sfx('slash_big' if e.get('big') else 'slash')
            put(B_['fx'], t0, x, 1.0, pan)
            put(send, t0, x, 0.3, pan)
        elif k == 'shot':
            x = Au.make_sfx('shot_big' if e.get('big') else 'shot')
            put(B_['fx'], t0, x, 1.1, pan)
            put(send, t0, x, 0.45, pan)
        elif k == 'thud':
            put(B_['fx'], t0, Au.make_sfx('impact'), min(1.2, 0.3 + e.get('speed', 3) * 0.15), pan)
        elif k == 'plough':
            put(B_['fx'], t0, Au.make_sfx('slide'), 0.35, pan)
        elif k == 'ichor':
            put(B_['fx'], t0, Au.make_sfx('burst'), 0.5, pan)
        elif k == 'tremor':
            put(B_['fx'], t0, Au.make_sfx('slam'), 0.9 + 0.2 * e.get('n', 1), 0.0)
            put(B_['fx'], t0 + 0.4, Au.boom(0.8, 2.0, 32), 1.0)
        elif k == 'ash':
            n_ = int(((e['t1'] - t0) + 1.0) * SR)
            tt_ = tt(n_)
            imp = (rng.random(n_) < 0.006 * np.sin(np.pi * np.clip(tt_ / (e['t1'] - t0), 0, 1))) * rng.standard_normal(n_)
            put(B_['fx'], t0, filt(imp, 'hp', 1800) * 1.6, 0.7, pan)
        elif k == 'roar':
            pass
    # whooshes for the big swings
    for tw in (T_DROP - 0.12, T_CHOP - 0.15, T_HOOK - 0.12, T_PLANT - 0.12, T_SWAT - 0.1, T_SWEEP - 0.1,
               T_STAB - 0.12):
        put(B_['fx'], tw, Au.make_sfx('whoosh'), 0.9, 0.0)
    return B_, send


def mix():
    B_, send = build()
    ke = Au.envelope(B_['drm'], 0.001, 0.09)
    ke /= ke.max() + 1e-9
    duck = 1 - 0.35 * ke[:, None]
    ir = Au.reverb_ir()
    ir_long = Au.reverb_ir(4.5, 9)
    gains = {'pno': 1.0, 'pad': 1.2, 'drm': 0.85, 'gtr': 0.55, 'bas': 0.6, 'lead': 2.6, 'fx': 0.85,
             'amb': 1.0, 'str': 1.0}
    dry = np.zeros((N, 2))
    wet = send.astype(np.float64) * 0.6
    long_in = np.zeros_like(dry)
    for k, g in gains.items():
        x = B_[k].astype(np.float64) * g
        if k in ('pad', 'gtr', 'bas', 'amb', 'lead', 'str'):
            x *= duck
        dry += x
        if k in ('pno', 'pad', 'lead', 'str'):
            long_in += x * (0.6 if k == 'pno' else 0.35)
        if k == 'gtr':
            wet += x * 0.12
    out = dry + Au.conv(wet, ir) * 0.5 + Au.conv(long_in, ir_long) * 0.65
    # slow-mo moments: a quick low-pass "time stretch" dip under the ramps
    T = tt(N)
    for (a, b, lo, r) in SLOWMO:
        m = np.clip(1 - np.maximum(0, np.minimum(T - (a - r), (b + r) - T)) / max(r, 1e-3), 0, 1)
        dip = (1 - m)
        low = filt(out, 'lp', 700)
        out = out * (1 - dip[:, None] * 0.7) + low * dip[:, None] * 0.7
    out = filt(out, 'hp', 28)
    env = Au.envelope(out, 0.005, 0.25)
    thr = 0.35
    gr = np.where(env > thr, (thr / (env + 1e-9)) ** 0.5, 1.0)
    out *= gr[:, None]
    out = np.tanh(out / (np.abs(out).max() + 1e-9) * 1.3)
    out *= np.clip((DUR + 0.2 - T) / 2.5, 0, 1)[:, None] * np.clip(T / 0.5, 0, 1)[:, None]
    out = out / np.abs(out).max() * 0.94
    return out[:int(DUR * SR)].astype(np.float32)


if __name__ == '__main__':
    import time
    t0 = time.time()
    os.makedirs(os.path.join(HERE, 'out'), exist_ok=True)
    out = mix()
    Au.write_wav(os.path.join(HERE, 'out', 'ember2.wav'), out)
    print(f'wrote out/ember2.wav {out.shape} {time.time() - t0:.1f}s')
    for b in range(NBARS):
        seg = out[int(B(b) * SR):int(B(b + 1) * SR)]
        print(f'bar {b:2d} {B(b):5.1f}s rms {20 * np.log10(np.sqrt((seg ** 2).mean()) + 1e-9):6.1f} dB')
