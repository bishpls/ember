"""EMBER III — score + sound design on the house synth engine.  150 BPM.
D minor -> (the King: Phrygian Eb) -> IGNITION: up a whole step to E minor -> dawn: E major.
Writes out/ep3_score.wav, beat-locked to edit.py's EDL/HITS."""
import os
import sys
import wave
import numpy as np

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(1, os.path.dirname(HERE))
import audio as Au
from edit import BEAT, TOTAL_BEATS, DUR, HITS

SR = Au.SR
Au.N = N = int((DUR + 1.5) * SR)
put, new, filt = Au.put, Au.new, Au.filt
rng = np.random.default_rng(33)


def b(x):
    return x * BEAT


def tt(n):
    return np.arange(n) / SR


BAR = 4
THEME = [[(0, 1.5, 69), (1.5, .5, 74), (2, 1, 77), (3, 1, 76)],
         [(0, 1.5, 74), (1.5, .5, 72), (2, 1.5, 74), (3.5, .5, 70)],
         [(0, 1.5, 72), (1.5, .5, 74), (2, 1, 76), (3, 1, 79)],
         [(0, 3, 76), (3, 1, 73)]]
CH = {'Dm': [50, 53, 57, 62], 'Bb': [46, 50, 53, 58], 'C': [48, 52, 55, 60], 'A': [45, 49, 52, 57],
      'Eb': [51, 55, 58, 63], 'Em': [52, 55, 59, 64], 'C2': [48, 52, 55, 60], 'D': [50, 54, 57, 62],
      'B': [47, 51, 54, 59], 'E': [52, 56, 59, 64], 'A2': [45, 52, 57, 61], 'G': [43, 50, 55, 59]}


def drone(m, dur, g=1.0):
    n = int((dur + 1.0) * SR)
    t = tt(n)
    f = Au.mtof(m)
    y = Au.saw(f, n) + Au.saw(f * 1.004, n) * 0.8 + Au.saw(f * 0.5, n) * 0.5
    y = Au.sweep_lp(y, 200 + 150 * (0.5 + 0.5 * np.sin(2 * np.pi * 0.2 * t)))
    e = np.minimum(1, t / 1.0) * np.where(t > dur, np.exp(-(t - dur) * 2), 1)
    return y * e * 0.18 * g


def brass(m, dur=1.2, g=1.0):
    n = int((dur + 0.6) * SR)
    t = tt(n)
    y = np.zeros(n)
    for iv in (0, 7, 12, -12):
        f = Au.mtof(m + iv)
        y += Au.saw(f, n) + Au.saw(f * 1.006, n)
    y = np.tanh(Au.sweep_lp(y, 300 + 2600 * np.exp(-t * 3)) * 1.5)
    e = np.minimum(1, t / 0.02) * np.exp(-t * 1.0) * np.where(t > dur, np.exp(-(t - dur) * 6), 1)
    return y * e * 0.15 * g


def riser(dur, g=1.0):
    n = int(dur * SR)
    t = tt(n)
    u = t / dur
    y = Au.sweep_lp(Au.noise(n), 200 + 9000 * u ** 2) * u ** 2
    y += Au.saw(110 * 2 ** (u * 2), n) * 0.15 * u ** 2
    return y * 0.5 * g


def tinnitus(dur):
    n = int(dur * SR)
    t = tt(n)
    return np.sin(2 * np.pi * 3900 * t) * np.exp(-t * 0.8) * 0.05


def load_wav(path, t0, dur):
    with wave.open(path) as w:
        sr = w.getframerate()
        w.setpos(int(t0 * sr))
        x = np.frombuffer(w.readframes(int(dur * sr)), '<i2').reshape(-1, 2).astype(np.float32) / 32768
    return x


def fight_bar(B_, bar_beat, chord, root, ev, g=1.0, double=False):
    D = B_['drm']
    kicks = [i * 0.5 for i in range(8)] if double else [0, 0.75, 1.5, 2, 2.75, 3.5]
    for k in kicks:
        put(D, b(bar_beat + k), Au.kick(0.9 * g if k % 1 == 0 else 0.7 * g), 1.0)
    for s in (1, 3):
        put(D, b(bar_beat + s), Au.snare(1.0 * g), 1.0, 0.05)
    for h in range(8):
        put(D, b(bar_beat + h * .5), Au.hat(0.7 if h % 2 else 0.45), 1.0, 0.35)
    ev.append((b(bar_beat), root, BEAT * 0.8, False))
    for sx in [0.75, 1, 1.25, 1.5, 2.25, 3, 3.25, 3.5, 3.75]:
        ev.append((b(bar_beat + sx), root, BEAT / 4 * 0.8, True))
    ev.append((b(bar_beat + 1.75), root, BEAT * 0.45, False))
    ev.append((b(bar_beat + 2.5), root, BEAT * 0.45, False))
    for i, m in enumerate(CH[chord]):
        put(B_['pad'], b(bar_beat), Au.choir_note(m + 12, BEAT * 4), 0.9 * g, -0.5 + i * 0.33)


def build():
    B_ = {k: new() for k in ['pno', 'pad', 'drm', 'gtr', 'bas', 'lead', 'fx', 'amb', 'str']}
    send = new()
    T = tt(N)
    ev = []
    # ------------------------------------------------------------------ ambience
    wl = Au.sweep_lp(Au.noise(N), 380 + 250 * np.sin(2 * np.pi * 0.11 * T))
    wr = Au.sweep_lp(Au.noise(N), 400 + 250 * np.sin(2 * np.pi * 0.09 * T + 1))
    wenv = np.interp(T, [0, 1.5, b(38), b(40), b(88), b(89), b(104), b(108), b(148), b(150), DUR],
                     [0.4, 1, 1, 0.25, 0.25, 0.9, 0.9, 0.2, 0.2, 0.7, 0.6])
    B_['amb'] += (np.stack([wl, wr], 1) * 0.1 * wenv[:, None]).astype(np.float32)

    # ------------------------------------------------------------------ 0-28: quiet, then wrong
    put(B_['pad'], 0, drone(38, b(16)), 1.0)
    for i in range(3):
        for (bb, l, m) in THEME[i]:
            put(B_['pno'], b(i * BAR + bb), Au.piano(m, l * BEAT * 1.1, 0.7), 0.9, 0.15)
    for i, c in enumerate(['Dm', 'Bb', 'C', 'A']):
        put(B_['pno'], b(i * BAR), Au.piano(CH[c][0] - 12, b(4), 0.55), 0.8, -0.2)
    put(B_['fx'], b(8), Au.piano(93, 1.5, 0.4), 0.6, 0.3)                       # the eye opens: a glint
    put(B_['pad'], b(16), drone(39, b(12), 1.3), 1.0)                            # eclipse: Eb against D
    put(B_['fx'], b(16) - 0.5, Au.reverse_swell(0.5), 0.8)
    put(B_['fx'], b(16), Au.boom(1.0, 2.5, 34), 1.0)
    for k in range(8):                                                           # tide: heartbeat -> toms
        put(B_['drm'], b(20 + k), Au.kick(0.5 + 0.05 * k, 0.7), 1.0)
        put(B_['drm'], b(20 + k + 0.5), Au.tom(43 - (k % 3) * 3, 0.3 + 0.05 * k), 1.0, [-.4, .3, 0][k % 3])
    for i, m in enumerate([50, 53, 57, 60]):
        put(B_['str'], b(20), Au.choir_note(m + 12, b(8), vowel='o'), 0.8, -0.4 + i * 0.26)
    for k, tb in enumerate([20.5, 22.5, 25.0]):
        put(B_['fx'], b(tb), Au.make_sfx('growl'), 0.7, [-0.5, 0.5, 0.0][k])
    # 28-32: the weapon inserts, one per beat
    put(B_['fx'], b(28), Au.make_sfx('click'), 1.2, 0.1)
    put(B_['fx'], b(29), Au.make_sfx('clack'), 1.3, 0.1)
    put(B_['fx'], b(30), Au.make_sfx('clack'), 1.0, -0.1)
    put(B_['fx'], b(30.5), Au.make_sfx('click'), 0.9, -0.1)
    # 32-40: launch build (snare roll + riser), breath on 39.5
    for k in range(24):
        put(B_['drm'], b(32 + k / 3), Au.snare(0.25 + 0.03 * k), 1.0)
    put(B_['fx'], b(32), riser(b(7.5), 1.0), 1.0)
    for k in range(8):
        ev.append((b(32 + k), 38, BEAT / 4 * 0.8, True))

    # ------------------------------------------------------------------ 40-72: FIGHT (D minor)
    prog = ['Dm', 'Bb', 'C', 'A', 'Dm', 'Bb', 'C', 'A']
    roots = {'Dm': 38, 'Bb': 34, 'C': 36, 'A': 33, 'Em': 40, 'C2': 36, 'D': 38, 'B': 35, 'G': 31}
    for i, bb in enumerate(range(40, 72, 4)):
        fight_bar(B_, bb, prog[i], roots[prog[i]], ev, double=(i >= 4))
    for (bb, l, m) in THEME[0] + [(4 + x, l, m) for (x, l, m) in THEME[1]]:
        put(B_['lead'], b(48 + bb), Au.lead_note(m + 12, l * BEAT * 0.95), 1.0, 0.1)
    for (bb, l, m) in THEME[2] + [(4 + x, l, m) for (x, l, m) in THEME[3]]:
        put(B_['lead'], b(56 + bb), Au.lead_note(m + 12, l * BEAT * 0.95), 1.0, 0.1)

    # ------------------------------------------------------------------ 72-88: the King (half-time doom, Eb over D)
    for k, bb in enumerate(range(72, 84, 2)):
        put(B_['drm'], b(bb), Au.boom(0.8 + 0.05 * k, 1.5, 36), 1.0)
        put(B_['drm'], b(bb), Au.kick(1.0, 0.6), 1.0)
        if k % 2:
            put(B_['drm'], b(bb + 1), Au.snare(1.1), 1.0)
            put(send, b(bb + 1), Au.snare(0.6), 1.0)
        put(B_['str'], b(bb), brass(39 if k % 2 == 0 else 38, BEAT * 1.8, 1.0), 1.0)
        ev.append((b(bb), 39 if k % 2 == 0 else 38, BEAT * 1.6, False))
    for i, m in enumerate([39, 43, 46, 51]):
        put(B_['pad'], b(72), Au.choir_note(m + 12, b(12), vowel='o'), 1.1, -0.4 + i * 0.26)
    put(B_['fx'], b(73), Au.make_sfx('roar'), 1.2, -0.2)
    put(B_['fx'], b(73), Au.make_sfx('roar'), 0.9, 0.3)
    # 84-88: the paw: pickup, IMPACT on 86, then nothing but ringing
    for k in range(8):
        put(B_['drm'], b(84 + k / 4), Au.snare(0.4 + 0.08 * k), 1.0)
    put(B_['fx'], b(86), Au.make_sfx('slam'), 1.5, 0.0)
    put(B_['drm'], b(86), Au.crash(1.3, 3.0), 1.0)
    put(send, b(86), Au.make_sfx('slam'), 0.7)
    put(B_['fx'], b(86.2), tinnitus(b(10)), 1.0)

    # ------------------------------------------------------------------ 88-108: the low, memory, the hand
    for k in range(6):                                              # slow heartbeat
        put(B_['drm'], b(89 + k * 2.4), Au.kick(0.35, 0.6), 1.0)
        put(B_['drm'], b(89.4 + k * 2.4), Au.kick(0.25, 0.6), 1.0)
    for (bb, l, m) in [(0, 2, 69), (2, 1, 74), (3, 2, 77), (6, 2, 76)]:
        put(B_['pno'], b(90 + bb), Au.piano(m - 12, l * BEAT * 1.8, 0.55), 1.0, 0.1)
    put(B_['pno'], b(90), Au.piano(38, b(8), 0.5), 0.8, -0.2)
    # memory flash: fragments of EMBER I and II themselves
    try:
        m1 = load_wav(os.path.join(HERE, '..', 'out', 'ember.wav'), 16.0, 0.4)
        m2 = load_wav(os.path.join(HERE, '..', 'b3d', 'out', 'ember2.wav'), 42.0, 0.4)
        for k, frag in enumerate([m1, m2, m1[::-1].copy(), m2]):
            y = filt(frag, 'bp', [300, 3500])
            put(B_['fx'], b(96 + k * 0.5), y * 0.8, 1.0)
    except Exception as e:
        print('memory audio skipped:', e)
    put(B_['fx'], b(98), riser(b(10), 0.9), 1.0)
    for k in range(10):                                             # heartbeat accelerating toward ignition
        tb = 98 + 10 * (1 - (0.82 ** k)) / (1 - 0.82 ** 10) * 0.97
        put(B_['drm'], b(tb), Au.kick(0.45 + 0.05 * k, 0.6), 1.0)
    for i, m in enumerate([52, 55, 59, 64]):
        put(B_['str'], b(100), Au.choir_note(m + 12, b(7.5)), 0.9, -0.4 + i * 0.26)

    # ------------------------------------------------------------------ 108-130: IGNITION (E minor, +2 semitones)
    put(B_['fx'], b(108), Au.make_sfx('slam'), 1.4, 0.0)
    put(B_['drm'], b(108), Au.crash(1.2, 3.0), 1.0, -0.3)
    put(B_['drm'], b(108), Au.crash(1.0, 3.0), 1.0, 0.3)
    prog2 = ['Em', 'C2', 'D', 'B', 'Em', 'C2']
    for i, bb in enumerate(range(108, 130, 4)):
        c = prog2[i % len(prog2)]
        fight_bar(B_, bb, c, roots[c], ev, g=1.05, double=True)
    for bar, seq in [(112, THEME[0]), (116, THEME[1]), (120, THEME[2]), (124, THEME[3])]:
        for (bb, l, m) in seq:
            put(B_['lead'], b(bar + bb), Au.lead_note(m + 14, l * BEAT * 0.95, 1.15), 1.0, 0.1)
            put(B_['lead'], b(bar + bb), Au.lead_note(m + 14 - 12, l * BEAT * 0.95, 0.6), 1.0, -0.1)
    # 130-140: apex: drums out, huge sustained choir, reverse swell, then a beat of silence
    for i, m in enumerate([52, 59, 64, 67, 71, 76]):
        put(B_['pad'], b(130), Au.choir_note(m + 12 if m < 60 else m, b(8.8)), 1.2, -0.5 + i * 0.2)
    put(B_['fx'], b(134), Au.reverse_swell(b(5)), 1.0)

    # ------------------------------------------------------------------ 140: THE CUT
    put(B_['fx'], b(140), Au.make_sfx('slash_big'), 1.6, 0.0)
    put(B_['fx'], b(140), Au.boom(1.6, 4.0, 30), 1.0)
    put(B_['drm'], b(140), Au.kick(1.4, 0.5), 1.0)
    put(B_['drm'], b(141), Au.crash(1.4, 3.0), 1.0, -0.3)
    put(B_['drm'], b(141), Au.crash(1.2, 3.0), 1.0, 0.3)
    put(send, b(140), Au.make_sfx('slash_big'), 1.0)
    for i, m in enumerate([40, 52, 56, 59, 64, 68, 71, 76]):       # E major: the light comes through
        put(B_['pad'], b(141), Au.choir_note(m + 12 if m < 60 else m, b(10)), 1.2, -0.6 + i * 0.17)
    ev.append((b(141), 40, BEAT * 6, False))

    # ------------------------------------------------------------------ 148-182: DAWN (E major)
    coda = [(0, 1.5, 71), (1.5, .5, 76), (2, 1, 80), (3, 1, 78), (4, 1.5, 76), (5.5, .5, 75), (6, 2, 76),
            (8, 1.5, 76), (9.5, .5, 78), (10, 1, 80), (11, 1, 83), (12, 3, 80), (15, 1, 78), (16, 4, 76)]
    for (bb, l, m) in coda:
        put(B_['pno'], b(150 + bb), Au.piano(m, l * BEAT * 1.3, 0.7), 1.2, 0.1)
    for bb, c in [(150, 'E'), (154, 'A2'), (158, 'B'), (162, 'E'), (166, 'A2'), (170, 'E')]:
        put(B_['pno'], b(bb), Au.piano(CH[c][0] - 12, b(4), 0.6), 1.0, -0.2)
        for i, m in enumerate(CH[c]):
            put(B_['pad'], b(bb), Au.choir_note(m + 12, b(4), vowel='o'), 0.55, -0.4 + i * 0.26)
    for m in (40, 47, 52, 56, 59, 64):
        put(B_['pno'], b(172), Au.piano(m, 4.5, 0.65), 1.2, -0.1)

    # ------------------------------------------------------------------ hits from the picture
    for (hb, kind, nfr) in HITS:
        if kind == 'impact' and hb not in (86.0, 140.0, 108.0):
            put(B_['fx'], b(hb), Au.make_sfx('slash'), 1.0, rng.uniform(-0.4, 0.4))
            put(B_['fx'], b(hb), Au.make_sfx('burst'), 0.6, rng.uniform(-0.4, 0.4))
    for tb, kind in [(40, 'slash_big'), (46.6, 'slash_big'), (50, 'slash'), (51, 'slash'), (53.2, 'burst'),
                     (55.4, 'shot_big'), (59.3, 'slash'), (62, 'slash'), (66, 'burst_big'), (116, 'shot_big'),
                     (125, 'slash'), (127, 'slash'), (35.8, 'dash'), (45.5, 'whoosh'), (48.5, 'whoosh'),
                     (58.2, 'growl'), (60.5, 'slide'), (120, 'rise'), (121, 'dash')]:
        put(B_['fx'], b(tb), Au.make_sfx(kind), 1.0, rng.uniform(-0.3, 0.3))
        if kind in ('shot_big', 'burst_big', 'slash_big'):
            put(send, b(tb), Au.make_sfx(kind), 0.4)

    gl = Au.guitar_track(ev, -1)
    gr = Au.guitar_track(ev, +1)
    B_['gtr'][:, 0] += (gl * 0.9 + gr * 0.15).astype(np.float32)
    B_['gtr'][:, 1] += (gr * 0.9 + gl * 0.15).astype(np.float32)
    bs = Au.bass_track(ev)
    B_['bas'] += np.stack([bs, bs], 1).astype(np.float32)
    return B_, send


def mix():
    B_, send = build()
    ke = Au.envelope(B_['drm'], 0.001, 0.09)
    ke /= ke.max() + 1e-9
    duck = 1 - 0.35 * ke[:, None]
    ir, ir_long = Au.reverb_ir(), Au.reverb_ir(4.5, 9)
    gains = {'pno': 1.0, 'pad': 1.2, 'drm': 0.9, 'gtr': 0.55, 'bas': 0.6, 'lead': 2.6, 'fx': 0.85,
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
    T = tt(N)
    # the low point: muffle everything (as if concussed) from the paw to the hand
    m = np.clip((T - b(86.3)) / 0.3, 0, 1) * np.clip((b(100) - T) / 2.0, 0, 1)
    out = out * (1 - m[:, None]) + filt(out, 'lp', 600) * m[:, None]
    # silence the beat before the cut
    gate = 1 - np.clip((T - b(139.0)) / 0.05, 0, 1) * np.clip((b(140) - 0.01 - T) / 0.05, 0, 1)
    out *= gate[:, None]
    out = filt(out, 'hp', 28)
    env = Au.envelope(out, 0.005, 0.25)
    thr = 0.35
    out *= np.where(env > thr, (thr / (env + 1e-9)) ** 0.5, 1.0)[:, None]
    out = np.tanh(out / (np.abs(out).max() + 1e-9) * 1.3)
    out *= np.clip((DUR + 0.2 - T) / 2.5, 0, 1)[:, None] * np.clip(T / 0.8, 0, 1)[:, None]
    out = out / np.abs(out).max() * 0.94
    return out[:int(DUR * SR)].astype(np.float32)


if __name__ == '__main__':
    os.makedirs(os.path.join(HERE, 'out'), exist_ok=True)
    o = mix()
    Au.write_wav(os.path.join(HERE, 'out', 'ep3_score.wav'), o)
    print('wrote out/ep3_score.wav', o.shape)
    for s0 in range(0, TOTAL_BEATS, 8):
        seg = o[int(b(s0) * SR):int(b(min(s0 + 8, TOTAL_BEATS)) * SR)]
        print(f'beats {s0:3d}-{s0 + 8:3d} rms {20 * np.log10(np.sqrt((seg ** 2).mean()) + 1e-9):6.1f} dB')
