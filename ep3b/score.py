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
TOTAL = 160
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
    # ambience: wind, ducked under the fights
    wl = Au.sweep_lp(Au.noise(N), 380 + 250 * np.sin(2 * np.pi * 0.11 * T))
    wr = Au.sweep_lp(Au.noise(N), 400 + 250 * np.sin(2 * np.pi * 0.09 * T + 1))
    wenv = np.interp(T, [0, 1.5, b(42), b(44), b(68), b(70), b(82), b(84), b(96), b(98), b(120), b(122), b(128), b(136), DUR],
                     [0.4, 1, 1, 0.2, 0.2, 0.5, 0.5, 1.0, 1.0, 0.15, 0.15, 0.6, 0.2, 0.6, 0.6])
    B_['amb'] += (np.stack([wl, wr], 1) * 0.1 * wenv[:, None]).astype(np.float32)

    # ---------------------------------------------------------------- 0-20: the theme, alone; the eye
    put(B_['pad'], 0, S3.drone(38, b(20)), 1.0)
    for i in range(3):
        for (bb, l, m) in THEME[i]:
            put(B_['pno'], b(i * 4 + bb), Au.piano(m, l * BEAT * 1.15, 0.7), 0.9, 0.15)
    for i, c in enumerate(['Dm', 'Bb', 'C', 'A', 'Dm']):
        put(B_['pno'], b(i * 4), Au.piano(CH[c][0] - 12, b(4), 0.55), 0.8, -0.2)
    put(B_['fx'], b(16), Au.piano(93, 1.8, 0.45), 0.7, 0.3)                 # the eye snaps open: a glint
    put(B_['fx'], b(16), Au.make_sfx('whoosh'), 0.35, 0.3)
    # ---------------------------------------------------------------- 20-36: eclipse, eyes, the tide
    put(B_['pad'], b(20), S3.drone(39, b(16), 1.3), 1.0)                       # Eb grinding against D
    put(B_['fx'], b(20), Au.boom(0.9, 2.5, 34), 1.0)
    for k, tb in enumerate([22, 23, 24, 25, 26]):
        put(B_['fx'], b(tb), Au.piano(88 - k, 0.5, 0.35), 0.5, [-0.6, 0.6, -0.3, 0.3, 0][k])
    put(B_['fx'], b(24), Au.make_sfx('slide'), 0.8, 0.0)                      # cracks racing
    for k in range(8):
        put(B_['drm'], b(28 + k), Au.kick(0.5 + 0.05 * k, 0.7), 1.0)
        put(B_['drm'], b(28 + k + 0.5), Au.tom(43 - (k % 3) * 3, 0.3 + 0.05 * k), 1.0, [-.4, .3, 0][k % 3])
    for i, m in enumerate([50, 53, 57, 60]):
        put(B_['str'], b(28), Au.choir_note(m + 12, b(8), vowel='o'), 0.85, -0.4 + i * 0.26)
    for k, tb in enumerate([28.5, 30.5, 33]):
        put(B_['fx'], b(tb), Au.make_sfx('growl'), 0.8, [-0.6, -0.2, 0.3][k])
    # ---------------------------------------------------------------- 36-44: ready; GO
    put(B_['fx'], b(36), Au.make_sfx('click'), 1.3, 0.1)
    put(B_['fx'], b(37), Au.make_sfx('clack'), 1.4, -0.1)
    put(B_['fx'], b(38), Au.make_sfx('click'), 1.0, 0.0)
    put(B_['fx'], b(38.35), Au.make_sfx('clack'), 1.2, 0.0)
    for k in range(18):
        put(B_['drm'], b(40 + k / 6), Au.snare(0.22 + 0.035 * k), 1.0)
    put(B_['fx'], b(40), S3.riser(b(3), 1.0), 1.0)
    put(B_['fx'], b(43), Au.make_sfx('shot_big'), 1.0, 0.0)
    put(B_['fx'], b(43), Au.make_sfx('dash'), 1.0, -0.3)
    put(B_['drm'], b(43), Au.crash(1.1), 1.0, 0.2)
    # ---------------------------------------------------------------- 44-62: FIGHT, D minor
    prog = ['Dm', 'Bb', 'C', 'A']
    roots = {'Dm': 38, 'Bb': 34, 'C': 36, 'A': 33, 'Em': 40, 'C2': 36, 'D': 38, 'B': 35, 'G': 31}
    for i, bb in enumerate(range(44, 60, 4)):
        c = prog[i % 4]
        S3.fight_bar(B_, bb, c, roots[c], ev, double=(i >= 2))
    for (bb, l, m) in THEME[0] + [(4 + x, l, m) for (x, l, m) in THEME[1]]:
        put(B_['lead'], b(48 + bb), Au.lead_note(m + 12, l * BEAT * 0.95), 1.0, 0.1)
    S3.fight_bar(B_, 60, 'Bb', 34, ev, double=True)
    for tb, kind, pan in [(48, 'slash_big', 0.3), (50.5, 'slash', -0.3), (54.8, 'whoosh', 0), (55.5, 'burst_big', 0),
                          (59, 'shot_big', -0.4), (59.5, 'impact', 0.3), (60.2, 'burst', 0.5)]:
        put(B_['fx'], b(tb), Au.make_sfx(kind), 1.0, pan)
        if kind in ('slash_big', 'burst_big', 'shot_big'):
            put(send, b(tb), Au.make_sfx(kind), 0.4, pan)
    put(B_['drm'], b(55.5), Au.crash(1.0), 1.0)
    # 62-66: buried: the band drops to a pulsing low drone + growls; 66: EXPLOSION
    put(B_['pad'], b(62), S3.drone(38, b(4), 1.2), 1.0)
    for k in range(8):
        put(B_['drm'], b(62 + k * 0.5), Au.kick(0.4 + 0.06 * k, 0.6), 1.0)
    for k, tb in enumerate([62.2, 62.9, 63.5]):
        put(B_['fx'], b(tb), Au.make_sfx('growl'), 0.9, [-0.5, 0.4, 0][k])
    put(B_['fx'], b(64.5), Au.reverse_swell(b(1.5)), 1.0)
    put(B_['fx'], b(66), Au.make_sfx('slam'), 1.4, 0.0)
    put(B_['fx'], b(66), Au.make_sfx('burst_big'), 1.2, 0.0)
    put(B_['drm'], b(66), Au.crash(1.2, 3.0), 1.0, -0.3)
    put(send, b(66), Au.make_sfx('slam'), 0.6)
    S3.fight_bar(B_, 66, 'Dm', 38, ev, double=True)
    # ---------------------------------------------------------------- 68-84: the King; the paw; silence
    for k, bb in enumerate(range(68, 80, 2)):
        put(B_['drm'], b(bb), Au.boom(0.8 + 0.05 * k, 1.5, 36), 1.0)
        put(B_['drm'], b(bb), Au.kick(1.0, 0.6), 1.0)
        if k % 2:
            put(B_['drm'], b(bb + 1), Au.snare(1.1), 1.0)
            put(send, b(bb + 1), Au.snare(0.6), 1.0)
        put(B_['str'], b(bb), S3.brass(39 if k % 2 == 0 else 38, BEAT * 1.8, 1.0), 1.0)
        ev.append((b(bb), 39 if k % 2 == 0 else 38, BEAT * 1.6, False))
    for i, m in enumerate([39, 43, 46, 51]):
        put(B_['pad'], b(68), Au.choir_note(m + 12, b(12), vowel='o'), 1.1, -0.4 + i * 0.26)
    for k in range(10):
        put(B_['fx'], b(72 + k * 0.4), Au.piano(86 + (k % 3), 0.3, 0.3), 0.35, (k % 5 - 2) * 0.3)   # eyes opening
    put(B_['fx'], b(76), Au.make_sfx('roar'), 1.3, -0.2)
    put(B_['fx'], b(76), Au.make_sfx('roar'), 1.0, 0.3)
    put(B_['drm'], b(76), Au.crash(1.0), 1.0)
    for k in range(8):
        put(B_['drm'], b(80 + k / 4), Au.snare(0.4 + 0.08 * k), 1.0)
    put(B_['fx'], b(80), S3.riser(b(2), 0.8), 1.0)
    put(B_['fx'], b(82), Au.make_sfx('slam'), 1.5, 0.0)
    put(B_['drm'], b(82), Au.crash(1.3, 3.0), 1.0)
    put(send, b(82), Au.make_sfx('slam'), 0.7)
    put(B_['fx'], b(82.2), S3.tinnitus(b(12)), 1.2)
    # ---------------------------------------------------------------- 84-96: the low, memory, the ember
    for (bb, l, m) in [(0, 2, 69), (2, 1, 74), (3, 2, 77), (6, 2, 76)]:
        put(B_['pno'], b(85 + bb), Au.piano(m - 12, l * BEAT * 1.8, 0.55), 1.0, 0.1)
    put(B_['pno'], b(85), Au.piano(38, b(8), 0.5), 0.8, -0.2)
    for k in range(3):
        put(B_['drm'], b(85 + k * 2.2), Au.kick(0.3, 0.6), 1.0)
        put(B_['drm'], b(85.4 + k * 2.2), Au.kick(0.2, 0.6), 1.0)
    try:
        m1 = S3.load_wav(os.path.join(ROOT, 'out', 'ember.wav'), 16.0, 0.4)
        m2 = S3.load_wav(os.path.join(ROOT, 'b3d', 'out', 'ember2.wav'), 42.0, 0.4)
        for k, frag in enumerate([m1, m2, m1[::-1].copy(), m2]):
            put(B_['fx'], b(90 + k * 0.4), filt(frag, 'bp', [300, 3500]) * 0.8, 1.0)
    except Exception as e:
        print('memory audio skipped:', e)
    for k, pb in enumerate([92.6, 93.5, 94.15, 94.55, 94.8]):                   # the clasp's heartbeat
        put(B_['drm'], b(pb), Au.kick(0.5 + 0.1 * k, 0.6), 1.0)
    put(B_['fx'], b(92), S3.riser(b(3), 1.0), 1.0)
    put(B_['fx'], b(95), Au.make_sfx('burst_big'), 1.1, 0.0)
    put(B_['fx'], b(97), Au.make_sfx('slash'), 0.8, 0.0)
    # ---------------------------------------------------------------- 98-120: IGNITION, E minor
    put(B_['fx'], b(98), Au.make_sfx('slam'), 1.4, 0.0)
    put(B_['drm'], b(98), Au.crash(1.2, 3.0), 1.0, -0.3)
    put(B_['drm'], b(98), Au.crash(1.0, 3.0), 1.0, 0.3)
    prog2 = ['Em', 'C2', 'D', 'B']
    for i, bb in enumerate(range(98, 120, 4)):
        c = prog2[i % 4]
        S3.fight_bar(B_, bb, c, roots[c], ev, g=1.05, double=True)
    for bar, seq in [(104, THEME[0]), (108, THEME[1]), (112, THEME[2]), (116, THEME[3])]:
        for (bb, l, m) in seq:
            put(B_['lead'], b(bar + bb), Au.lead_note(m + 14, l * BEAT * 0.95, 1.15), 1.0, 0.1)
            put(B_['lead'], b(bar + bb), Au.lead_note(m + 2, l * BEAT * 0.95, 0.6), 1.0, -0.1)
    for c in (108, 110, 112, 114, 116):
        put(B_['fx'], b(c), Au.make_sfx('slash'), 1.0, rng.uniform(-0.4, 0.4))
        put(B_['fx'], b(c) + 0.05, Au.make_sfx('burst'), 0.5, rng.uniform(-0.4, 0.4))
    put(B_['fx'], b(104), Au.make_sfx('rise'), 0.8, 0.0)
    # ---------------------------------------------------------------- 120-128: apex; one beat of silence
    for i, m in enumerate([52, 59, 64, 67, 71, 76]):
        put(B_['pad'], b(120), Au.choir_note(m + 12 if m < 60 else m, b(7)), 1.2, -0.5 + i * 0.2)
    put(B_['fx'], b(123), Au.reverse_swell(b(4)), 1.0)
    # ---------------------------------------------------------------- 128: THE CUT; E major
    put(B_['fx'], b(128), Au.make_sfx('slash_big'), 1.6, 0.0)
    put(B_['fx'], b(128), Au.boom(1.6, 4.0, 30), 1.0)
    put(B_['drm'], b(128), Au.kick(1.4, 0.5), 1.0)
    put(B_['drm'], b(129), Au.crash(1.4, 3.0), 1.0, -0.3)
    put(B_['drm'], b(129), Au.crash(1.2, 3.0), 1.0, 0.3)
    put(send, b(128), Au.make_sfx('slash_big'), 1.0)
    for i, m in enumerate([40, 52, 56, 59, 64, 68, 71, 76]):
        put(B_['pad'], b(129), Au.choir_note(m + 12 if m < 60 else m, b(9)), 1.2, -0.6 + i * 0.17)
    ev.append((b(129), 40, BEAT * 6, False))
    put(B_['fx'], b(131), Au.make_sfx('burst_big'), 0.8, 0.0)
    # ---------------------------------------------------------------- 136-160: dawn
    put(B_['fx'], b(136.2), Au.make_sfx('impact'), 0.8, 0.3)                  # she lands
    coda = [(0, 1.5, 71), (1.5, .5, 76), (2, 1, 80), (3, 1, 78), (4, 1.5, 76), (5.5, .5, 75), (6, 2, 76),
            (8, 1.5, 76), (9.5, .5, 78), (10, 1, 80), (11, 1, 83), (12, 3, 80), (15, 1, 78), (16, 4, 76)]
    for (bb, l, m) in coda:
        put(B_['pno'], b(138 + bb), Au.piano(m, l * BEAT * 1.3, 0.7), 1.2, 0.1)
    for bb, c in [(138, 'E'), (142, 'A2'), (146, 'B'), (150, 'E'), (154, 'A2')]:
        put(B_['pno'], b(bb), Au.piano(CH[c][0] - 12, b(4), 0.6), 1.0, -0.2)
        for i, m in enumerate(CH[c]):
            put(B_['pad'], b(bb), Au.choir_note(m + 12, b(4), vowel='o'), 0.55, -0.4 + i * 0.26)
    for m in (40, 47, 52, 56, 59, 64):
        put(B_['pno'], b(158), Au.piano(m, 3.0, 0.6), 1.1, -0.1)
    put(B_['fx'], b(146), Au.make_sfx('click'), 0.9, 0.3)
    put(B_['fx'], b(147), Au.make_sfx('clack'), 1.0, 0.3)

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
    m = np.clip((T - b(82.3)) / 0.3, 0, 1) * np.clip((b(95) - T) / 1.5, 0, 1)     # concussed: muffled low point
    out = out * (1 - m[:, None]) + filt(out, 'lp', 600) * m[:, None]
    gate = 1 - np.clip((T - b(127.0)) / 0.05, 0, 1) * np.clip((b(128) - 0.01 - T) / 0.05, 0, 1)   # the silent beat
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
    print('wrote out/score.wav', o.shape)
