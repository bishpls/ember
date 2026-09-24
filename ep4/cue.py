import os, sys, numpy as np
sys.path.insert(0, '..'); sys.path.insert(0, '../ep3')
import audio as Au
import score3 as S3
BEAT = 0.4; DUR = 12 * BEAT; SR = Au.SR
Au.N = N = int((DUR + 1.0) * SR)
put, new = Au.put, Au.new
b = lambda x: x * BEAT
B_ = {k: new() for k in ['pno', 'pad', 'drm', 'fx', 'amb']}
T = np.arange(N) / SR
w = Au.sweep_lp(Au.noise(N), 400 + 200 * np.sin(T)); B_['amb'] += np.stack([w, w], 1).astype(np.float32) * 0.08
put(B_['pad'], 0, S3.drone(39, b(6.5), 1.2), 1.0)
for k in range(3):
    put(B_['drm'], b(k), Au.kick(0.5, 0.6), 1.0); put(B_['drm'], b(k + 0.4), Au.kick(0.35, 0.6), 1.0)
put(B_['fx'], b(0.5), Au.make_sfx('growl'), 0.8, -0.5)
put(B_['fx'], b(2.0), Au.make_sfx('growl'), 0.8, 0.5)
put(B_['fx'], b(3), Au.piano(93, 1.5, 0.5), 0.8, 0.3)
put(B_['fx'], b(3.5), Au.make_sfx('whoosh'), 0.8, 0.2)
for k in range(12): put(B_['drm'], b(4.5 + k / 6), Au.snare(0.25 + 0.05 * k), 1.0)
put(B_['fx'], b(4.5), S3.riser(b(2), 1.0), 1.0)
put(B_['fx'], b(6.2), Au.make_sfx('whoosh'), 1.0, 0.0)
put(B_['fx'], b(6.5), Au.make_sfx('slash_big'), 1.3, 0.0)
put(B_['drm'], b(6.5), Au.kick(1.3, 0.5), 1.0); put(B_['drm'], b(6.5), Au.crash(1.2), 1.0)
put(B_['fx'], b(7), Au.make_sfx('burst_big'), 1.2, 0.0)
for i, m in enumerate([50, 53, 57, 62]): put(B_['pad'], b(7), Au.choir_note(m + 12, b(5)), 0.9, -0.4 + i * 0.26)
for (bb, l, m) in [(0, 1.5, 69), (1.5, .5, 74), (2, 1, 77)]: put(B_['pno'], b(9 + bb), Au.piano(m, l * BEAT * 1.3, 0.6), 1.0, 0.1)
out = sum(B_[k].astype(np.float64) * g for k, g in {'pno': 1.0, 'pad': 1.1, 'drm': 0.9, 'fx': 0.9, 'amb': 1.0}.items())
out = out + Au.conv(out * 0.3, Au.reverb_ir()) * 0.5
out = np.tanh(out / np.abs(out).max() * 1.3); out = out / np.abs(out).max() * 0.94
out *= np.clip((DUR + 0.3 - T) / 1.0, 0, 1)[:, None]
Au.write_wav('cue.wav', out[:int(DUR * SR)].astype(np.float32)); print('cue ok')
