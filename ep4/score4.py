"""EMBER III (hand-animated) — score on the house synth engine, locked to this cut's beat map.
150 BPM, 160 beats = 64.0 s.  D minor -> Phrygian Eb (the King) -> ignition: E minor -> dawn: E major."""
import os, sys
import numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, 'ep3'))
import audio as Au
import score3 as S3            # helpers: drone, brass, riser, tinnitus, load_wav, fight_bar, THEME, CH

BEAT = 0.4
TOTAL = 168
DUR = TOTAL * BEAT
SR = Au.SR
Au.N = N = int((DUR + 1.5) * SR)
put, new, filt = Au.put, Au.new, Au.filt
b = lambda x: x * BEAT
tt = lambda n: np.arange(n) / SR
THEME, CH = S3.THEME, S3.CH
rng = np.random.default_rng(5)


def build():
    B_ = {k: new() for k in ['pno', 'pad', 'drm', 'gtr', 'bas', 'lead', 'fx', 'amb', 'str']}
    send = new()
    T = tt(N)
    ev = []
    wl = Au.sweep_lp(Au.noise(N), 380 + 250 * np.sin(2 * np.pi * 0.11 * T))
    wr = Au.sweep_lp(Au.noise(N), 400 + 250 * np.sin(2 * np.pi * 0.09 * T + 1))
    wenv = np.interp(T, [0, 1.5, b(40), b(42), b(72), b(74), b(86), b(88), b(100), b(102), b(124), b(126), b(132), b(140), DUR],
                     [0.4, 1, 1, 0.2, 0.2, 0.5, 0.5, 1.0, 1.0, 0.15, 0.15, 0.6, 0.2, 0.6, 0.6])
    B_['amb'] += (np.stack([wl, wr], 1) * 0.1 * wenv[:, None]).astype(np.float32)
    roots = {'Dm': 38, 'Bb': 34, 'C': 36, 'A': 33, 'Em': 40, 'C2': 36, 'D': 38, 'B': 35, 'G': 31}
    # 0-16: the theme alone; the eyes open
    put(B_['pad'], 0, S3.drone(38, b(16)), 1.0)
    for i in range(4):
        for (bb, l, m) in THEME[i % 4]:
            if i * 4 + bb < 15:
                put(B_['pno'], b(i * 4 + bb), Au.piano(m, l * BEAT * 1.15, 0.7), 0.9, 0.15)
    for i, c in enumerate(['Dm', 'Bb', 'C', 'A']):
        put(B_['pno'], b(i * 4), Au.piano(CH[c][0] - 12, b(4), 0.55), 0.8, -0.2)
    put(B_['fx'], b(14.8), Au.piano(93, 1.8, 0.45), 0.7, 0.3)
    put(B_['fx'], b(14.8), Au.make_sfx('whoosh'), 0.35, 0.3)
    # 16-34: eclipse, eyes, tide
    put(B_['pad'], b(16), S3.drone(39, b(18), 1.3), 1.0)
    put(B_['fx'], b(16), Au.boom(0.9, 2.5, 34), 1.0)
    for k in range(9):
        put(B_['fx'], b(22.5 + k * 0.5), Au.piano(88 - (k % 5), 0.5, 0.33), 0.45, ((k % 5) - 2) * 0.3)
    for k in range(6):
        put(B_['drm'], b(28 + k), Au.kick(0.5 + 0.06 * k, 0.7), 1.0)
        put(B_['drm'], b(28 + k + 0.5), Au.tom(43 - (k % 3) * 3, 0.3 + 0.06 * k), 1.0, [-.4, .3, 0][k % 3])
    for i, m in enumerate([50, 53, 57, 60]):
        put(B_['str'], b(28), Au.choir_note(m + 12, b(6), vowel='o'), 0.85, -0.4 + i * 0.26)
    for k, tb in enumerate([26, 28.5, 31]):
        put(B_['fx'], b(tb), Au.make_sfx('growl'), 0.8, [-0.6, -0.2, 0.3][k])
    # 34-42: inserts; launch
    put(B_['fx'], b(34), Au.make_sfx('click'), 1.3, 0.1)
    put(B_['fx'], b(35), Au.make_sfx('clack'), 1.4, -0.1)
    put(B_['fx'], b(36), Au.make_sfx('clack'), 1.2, 0.0)
    for k in range(18):
        put(B_['drm'], b(38 + k / 6), Au.snare(0.22 + 0.035 * k), 1.0)
    put(B_['fx'], b(38), S3.riser(b(3), 1.0), 1.0)
    put(B_['fx'], b(41), Au.make_sfx('shot_big'), 1.0, 0.0)
    put(B_['fx'], b(41), Au.make_sfx('dash'), 1.0, -0.3)
    put(B_['drm'], b(41), Au.crash(1.1), 1.0, 0.2)
    # 42-64: FIGHT, D minor
    prog = ['Dm', 'Bb', 'C', 'A']
    for i, bb in enumerate(range(42, 62, 4)):
        c = prog[i % 4]
        S3.fight_bar(B_, bb, c, roots[c], ev, double=(i >= 2))
    S3.fight_bar(B_, 62, 'Bb', 34, ev, double=True)
    for (bb, l, m) in THEME[0] + [(4 + x, l, m) for (x, l, m) in THEME[1]]:
        put(B_['lead'], b(46 + bb), Au.lead_note(m + 12, l * BEAT * 0.95), 1.0, 0.1)
    for tb, kind, pan in [(45.75, 'whoosh', 0.2), (46, 'slash_big', 0.3), (46.2, 'burst', 0.4), (49.9, 'whoosh', -0.2), (50, 'slash_big', -0.3), (50.2, 'burst', -0.4),
                          (55.2, 'whoosh', 0), (56, 'slash_big', 0), (57, 'burst_big', 0), (61, 'shot_big', -0.4), (61.5, 'impact', 0.3), (62.6, 'burst', 0.5), (62.8, 'slide', 0.2)]:
        put(B_['fx'], b(tb), Au.make_sfx(kind), 1.0, pan)
        if kind in ('slash_big', 'burst_big', 'shot_big'):
            put(send, b(tb), Au.make_sfx(kind), 0.4, pan)
    put(B_['drm'], b(56), Au.crash(1.0), 1.0)
    # 64-68 buried; 68 BURST
    put(B_['pad'], b(64), S3.drone(38, b(4), 1.2), 1.0)
    for k in range(8):
        put(B_['drm'], b(64 + k * 0.5), Au.kick(0.4 + 0.06 * k, 0.6), 1.0)
    for k in range(6):
        put(B_['fx'], b(64.3 + k * 0.3), Au.make_sfx('impact'), 0.5, (k % 3 - 1) * 0.5)
    put(B_['fx'], b(66.5), Au.reverse_swell(b(1.5)), 1.0)
    put(B_['fx'], b(68), Au.make_sfx('slam'), 1.4, 0.0)
    put(B_['fx'], b(68), Au.make_sfx('burst_big'), 1.2, 0.0)
    put(B_['drm'], b(68), Au.crash(1.2, 3.0), 1.0, -0.3)
    put(send, b(68), Au.make_sfx('slam'), 0.6)
    S3.fight_bar(B_, 68, 'Dm', 38, ev, double=True)
    # 72-86: the King; the paw
    for k, bb in enumerate(range(72, 84, 2)):
        put(B_['drm'], b(bb), Au.boom(0.8 + 0.05 * k, 1.5, 36), 1.0)
        put(B_['drm'], b(bb), Au.kick(1.0, 0.6), 1.0)
        if k % 2:
            put(B_['drm'], b(bb + 1), Au.snare(1.1), 1.0)
            put(send, b(bb + 1), Au.snare(0.6), 1.0)
        put(B_['str'], b(bb), S3.brass(39 if k % 2 == 0 else 38, BEAT * 1.8, 1.0), 1.0)
        ev.append((b(bb), 39 if k % 2 == 0 else 38, BEAT * 1.6, False))
    for i, m in enumerate([39, 43, 46, 51]):
        put(B_['pad'], b(72), Au.choir_note(m + 12, b(12), vowel='o'), 1.1, -0.4 + i * 0.26)
    for k in range(5):
        put(B_['fx'], b(77 + k), Au.piano(86 + (k % 3), 0.35, 0.35), 0.45, (k - 2) * 0.3)
    put(B_['fx'], b(77), Au.make_sfx('roar'), 1.3, -0.2)
    put(B_['fx'], b(77), Au.make_sfx('roar'), 1.0, 0.3)
    put(B_['drm'], b(77), Au.crash(1.0), 1.0)
    for k in range(8):
        put(B_['drm'], b(84 + k / 4), Au.snare(0.4 + 0.08 * k), 1.0)
    put(B_['fx'], b(84), S3.riser(b(2), 0.8), 1.0)
    put(B_['fx'], b(86), Au.make_sfx('slam'), 1.5, 0.0)
    put(B_['drm'], b(86), Au.crash(1.3, 3.0), 1.0)
    put(send, b(86), Au.make_sfx('slam'), 0.7)
    put(B_['fx'], b(86.2), S3.tinnitus(b(12)), 1.2)
    # 88-100: the low, memory, the ember
    for (bb, l, m) in [(0, 2, 69), (2, 1, 74), (3, 2, 77), (6, 2, 76)]:
        put(B_['pno'], b(89 + bb), Au.piano(m - 12, l * BEAT * 1.8, 0.55), 1.0, 0.1)
    put(B_['pno'], b(89), Au.piano(38, b(8), 0.5), 0.8, -0.2)
    try:
        m1 = S3.load_wav(os.path.join(ROOT, 'out', 'ember.wav'), 16.0, 0.4)
        m2 = S3.load_wav(os.path.join(ROOT, 'b3d', 'out', 'ember2.wav'), 42.0, 0.4)
        for k, frag in enumerate([m1, m2, m1[::-1].copy(), m2, m1]):
            put(B_['fx'], b(93.5 + k * 0.2), filt(frag, 'bp', [300, 3500]) * 0.8, 1.0)
    except Exception as e:
        print('memory audio skipped:', e)
    for k, pb in enumerate([95.5, 96.5, 97.2, 97.7, 98.1, 98.4, 98.6]):
        put(B_['drm'], b(pb), Au.kick(0.45 + 0.08 * k, 0.6), 1.0)
    put(B_['fx'], b(96), S3.riser(b(2.8), 1.0), 1.0)
    put(B_['fx'], b(98.8), Au.make_sfx('burst_big'), 1.1, 0.0)
    # 100-124: IGNITION + ascent, E minor
    put(B_['fx'], b(100), Au.make_sfx('slash'), 0.8, 0.0)
    put(B_['fx'], b(101.5), Au.make_sfx('slam'), 1.2, 0.0)
    put(B_['fx'], b(105), Au.make_sfx('burst_big'), 1.0, 0.0)
    put(B_['drm'], b(105), Au.crash(1.2, 3.0), 1.0, -0.3)
    put(B_['drm'], b(105), Au.crash(1.0, 3.0), 1.0, 0.3)
    for i, m in enumerate([52, 55, 59, 64]):
        put(B_['str'], b(101.5), Au.choir_note(m + 12, b(3.5)), 0.9, -0.4 + i * 0.26)
    prog2 = ['Em', 'C2', 'D', 'B']
    for i, bb in enumerate(range(104, 124, 4)):
        c = prog2[i % 4]
        S3.fight_bar(B_, bb, c, roots[c], ev, g=1.05, double=True)
    for bar, seq in [(108, THEME[0]), (112, THEME[1]), (116, THEME[2]), (120, THEME[3])]:
        for (bb, l, m) in seq:
            put(B_['lead'], b(bar + bb), Au.lead_note(m + 14, l * BEAT * 0.95, 1.15), 1.0, 0.1)
            put(B_['lead'], b(bar + bb), Au.lead_note(m + 2, l * BEAT * 0.95, 0.6), 1.0, -0.1)
    for c in (112, 114, 116, 118, 120):
        put(B_['fx'], b(c), Au.make_sfx('slash'), 1.0, rng.uniform(-0.4, 0.4))
        put(B_['fx'], b(c) + 0.05, Au.make_sfx('burst'), 0.5, rng.uniform(-0.4, 0.4))
    put(B_['fx'], b(108), Au.make_sfx('rise'), 0.8, 0.0)
    put(B_['fx'], b(122.5), Au.reverse_swell(b(1.5)), 0.9)
    # 124-132: apex, then one beat of silence
    for i, m in enumerate([52, 59, 64, 67, 71, 76]):
        put(B_['pad'], b(124), Au.choir_note(m + 12 if m < 60 else m, b(6.8)), 1.2, -0.5 + i * 0.2)
    put(B_['fx'], b(127.5), Au.reverse_swell(b(3.4)), 1.0)
    # 132.5: THE CUT; 133.5 the split; E major
    put(B_['fx'], b(132.3), Au.make_sfx('whoosh'), 1.2, 0.0)
    put(B_['fx'], b(132.5), Au.make_sfx('slash_big'), 1.6, 0.0)
    put(B_['fx'], b(132.5), Au.boom(1.6, 4.0, 30), 1.0)
    put(B_['drm'], b(132.5), Au.kick(1.4, 0.5), 1.0)
    put(send, b(132.5), Au.make_sfx('slash_big'), 1.0)
    put(B_['drm'], b(133.5), Au.crash(1.4, 3.0), 1.0, -0.3)
    put(B_['drm'], b(133.5), Au.crash(1.2, 3.0), 1.0, 0.3)
    put(B_['fx'], b(133.5), Au.make_sfx('burst_big'), 1.0, 0.0)
    for i, m in enumerate([40, 52, 56, 59, 64, 68, 71, 76]):
        put(B_['pad'], b(133.5), Au.choir_note(m + 12 if m < 60 else m, b(8)), 1.2, -0.6 + i * 0.17)
    ev.append((b(133.5), 40, BEAT * 6, False))
    # 140-168: dawn
    put(B_['fx'], b(140.2), Au.make_sfx('impact'), 0.8, 0.3)
    coda = [(0, 1.5, 71), (1.5, .5, 76), (2, 1, 80), (3, 1, 78), (4, 1.5, 76), (5.5, .5, 75), (6, 2, 76),
            (8, 1.5, 76), (9.5, .5, 78), (10, 1, 80), (11, 1, 83), (12, 3, 80), (15, 1, 78), (16, 4, 76)]
    for (bb, l, m) in coda:
        put(B_['pno'], b(142 + bb), Au.piano(m, l * BEAT * 1.3, 0.7), 1.2, 0.1)
    for bb, c in [(142, 'E'), (146, 'A2'), (150, 'B'), (154, 'E'), (158, 'A2'), (162, 'E')]:
        put(B_['pno'], b(bb), Au.piano(CH[c][0] - 12, b(4), 0.6), 1.0, -0.2)
        for i, m in enumerate(CH[c]):
            put(B_['pad'], b(bb), Au.choir_note(m + 12, b(4), vowel='o'), 0.55, -0.4 + i * 0.26)
    for m in (40, 47, 52, 56, 59, 64):
        put(B_['pno'], b(163), Au.piano(m, 3.5, 0.6), 1.1, -0.1)

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
    gains = {'pno': 1.0, 'pad': 1.2, 'drm': 0.9, 'gtr': 0.55, 'bas': 0.6, 'lead': 2.6, 'fx': 0.85, 'amb': 1.0, 'str': 1.0}
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
    m = np.clip((T - b(86.3)) / 0.3, 0, 1) * np.clip((b(98.8) - T) / 1.5, 0, 1)     # concussed: muffled low point
    out = out * (1 - m[:, None]) + filt(out, 'lp', 600) * m[:, None]
    gate = 1 - np.clip((T - b(131.0)) / 0.05, 0, 1) * np.clip((b(132.3) - 0.01 - T) / 0.05, 0, 1)   # the silent beat
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
    Au.write_wav(os.path.join(HERE, 'out', 'score.wav'), o)
    print('dur', len(o) / SR)
    print('wrote out/score.wav', o.shape)
