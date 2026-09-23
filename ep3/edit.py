"""EMBER III — the edit + compositor.  Beat-locked (150 BPM), anime retiming (ones/twos/threes),
impact frames, speed lines, embers, grade, title.  Writes frames straight into ffmpeg.

python edit.py [--from BEAT] [--to BEAT] [--stills b1,b2,...] [--out file.mp4] [--half]
"""
import os
import sys
import math
import argparse
import subprocess
import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
os.chdir(HERE)
FPS = 24
BPM = 150.0
BEAT = 60.0 / BPM          # 0.4 s
W, H = 1920, 1080
TOTAL_BEATS = 182
DUR = TOTAL_BEATS * BEAT   # 72.8 s

# ------------------------------------------------------------------------------------------------ EDL
# (b0, b1, kind, source, src_in, src_out, step, grade, extra)
EDL = [
    (0, 8, 'still', 'keys/s01_clearing.png', 0, 0, 3, 'night', dict(zoom=(1.0, 1.09), pan=(0.0, -0.02), fadein=1.2, embers=1, snow=1)),
    (8, 16, 'clip', 'clips/s02_eye_lite.mp4', 0.0, 1.75, 2, 'night', dict(embers=0.6)),
    (16, 20, 'clip', 'clips/s03_eclipse_fast.mp4', 0.8, 4.0, 2, 'night', {}),
    (20, 28, 'clip', 'clips/s04_tide_fast.mp4', 0.3, 6.0, 2, 'night', dict(shake=4)),
    (28, 29, 'still', 'keys/s05a_unfold.png', 0, 0, 1, 'night', dict(zoom=(1.12, 1.0), punch=1, lines=1)),
    (29, 30, 'still', 'keys/s05b_blade.png', 0, 0, 1, 'night', dict(zoom=(1.0, 1.12), punch=1, lines=1)),
    (30, 32, 'still', 'keys/s05c_chamber.png', 0, 0, 1, 'night', dict(zoom=(1.05, 1.2), punch=1, lines=1, shake=6)),
    (32, 40, 'clip', 'clips/s06_launch_lite.mp4', 0.0, 3.4, 2, 'night', dict(shake=3)),
    (40, 46, 'clip', 'clips/s07a_run_fast.mp4', 0.4, 5.0, 2, 'night', dict(lines=0.5)),
    (46, 48, 'clip', 'clips/i2_blade_fast.mp4', 0.0, 1.9, 1, 'night', dict(echo=1, shake=5)),
    (48, 53, 'clip', 'clips/s07b_spin_fast.mp4', 0.2, 4.0, 1, 'night', dict(echo=1)),
    (53, 55, 'clip', 'clips/i1_cry_fast.mp4', 0.0, 1.6, 2, 'night', dict(shake=7)),
    (55, 58, 'clip', 'clips/s07c_recoil_fast.mp4', 0.0, 2.3, 2, 'night', dict(shake=6)),
    (58, 60, 'clip', 'clips/i3_lunge_fast.mp4', 0.6, 3.0, 1, 'night', dict(shake=5, echo=1)),
    (60, 64, 'clip', 'clips/s07d_slide_lite.mp4', 0.3, 4.0, 2, 'night', {}),
    (64, 72, 'clip', 'clips/s07f_burst_fast.mp4', 0.0, 4.0, 1, 'night', dict(shake=5)),
    (72, 84, 'clip', 'clips/s08_king_v2_fast.mp4', 0.5, 8.0, 3, 'eclipse', dict(shake=2)),
    (84, 88, 'clip', 'clips/s09_paw_fast.mp4', 0.4, 3.2, 1, 'eclipse', dict(shake=10)),
    (88, 96, 'clip', 'clips/s10_crater_fast.mp4', 1.5, 6.0, 3, 'low', dict(snow=0.6)),
    (96, 98, 'memory', None, 0, 0, 1, 'memory', {}),
    (98, 104, 'clip', 'clips/s10b_hand_lite.mp4', 0.0, 4.0, 2, 'low', {}),
    (104, 108, 'clip', 'clips/s11a_eyes_lite.mp4', 0.4, 3.6, 2, 'fire', dict(shake=3)),
    (108, 116, 'clip', 'clips/s11b_ignite_std1080.mp4', 0.0, 5.2, 2, 'fire', dict(embers=1.5, shake=4)),
    (116, 121, 'clip', 'clips/s12a_ascend_fast.mp4', 0.0, 4.2, 1, 'fire', dict(shake=4, lines=0.6, echo=1)),
    (121, 124, 'clip', 'clips/i4_lookdown_fast.mp4', 0.3, 3.6, 2, 'fire', dict(embers=1.2)),
    (124, 130, 'clip', 'clips/s12b_tendrils_fast.mp4', 0.0, 4.0, 2, 'fire', dict(shake=5)),
    (130, 140, 'clip', 'clips/s13_apex_std1080.mp4', 0.0, 7.5, 3, 'fire', dict(embers=1.2, bars=1)),
    (140, 148, 'clip', 'clips/s14_cut_std1080.mp4', 0.0, 7.6, 1, 'fire', dict(shake=8)),
    (148, 162, 'clip', 'clips/s15_dawn_fast.mp4', 0.0, 7.0, 3, 'dawn', dict(embers=1.0, fall=1)),
    (162, 172, 'clip', 'clips/s15b_smile_lite.mp4', 0.0, 4.0, 3, 'dawn', dict(embers=0.8, fall=1)),
    (172, 182, 'title', 'clips/s15_dawn_fast.mp4', 7.9, 7.9, 3, 'dawn', dict(embers=0.8, fall=1)),
]

# impact frames / flashes / hit-stops at absolute beats: (beat, kind, frames)
HITS = [
    (40.0, 'impact', 2), (40.0, 'flash', 4),
    (46.6, 'impact', 1), (47.0, 'flash', 3),
    (50.0, 'impact', 1), (52.0, 'flash', 3),
    (53.2, 'flash', 4),
    (55.4, 'flash', 4),
    (59.3, 'impact', 1),
    (62.0, 'impact', 1),
    (66.0, 'impact', 2), (66.0, 'flash', 5),
    (72.0, 'flash', 3),
    (86.0, 'impact', 2), (86.0, 'white', 10),
    (108.0, 'impact', 3), (108.0, 'flash', 6),
    (116.0, 'flash', 3),
    (125.0, 'impact', 1), (127.0, 'impact', 1),
    (140.0, 'impact', 2), (141.0, 'flash', 6),
    (145.0, 'white', 30),
]


def beat_t(b):
    return b * BEAT


# ------------------------------------------------------------------------------------------------ sources
_clip_cache = {}


def load_clip(path):
    if path in _clip_cache:
        return _clip_cache[path]
    if len(_clip_cache) > 2:
        _clip_cache.pop(next(iter(_clip_cache)))
    w, h = 1280, 720
    raw = subprocess.run(['ffmpeg', '-v', 'error', '-i', path, '-f', 'rawvideo', '-pix_fmt', 'rgb24',
                          '-s', f'{w}x{h}', '-'], capture_output=True, check=True).stdout
    arr = np.frombuffer(raw, np.uint8).reshape(-1, h, w, 3)
    _clip_cache[path] = arr
    return arr


_still_cache = {}


def load_still(path):
    if path not in _still_cache:
        im = Image.open(path).convert('RGB')
        s = max(W / im.width, H / im.height) * 1.25
        _still_cache[path] = im.resize((int(im.width * s), int(im.height * s)), Image.LANCZOS)
    return _still_cache[path]


def still_frame(path, u, zoom, pan):
    im = load_still(path)
    z = zoom[0] + (zoom[1] - zoom[0]) * u
    cw, ch = im.width / 1.25 / z, im.height / 1.25 / z
    cx = im.width / 2 + pan[0] * u * im.width
    cy = im.height / 2 + pan[1] * u * im.height
    box = (cx - cw / 2, cy - ch / 2, cx + cw / 2, cy + ch / 2)
    return np.asarray(im.resize((W, H), Image.LANCZOS, box=box), np.float32) / 255


def clip_frame(path, src_t):
    arr = load_clip(path)
    i = int(round(src_t * FPS))
    i = max(0, min(len(arr) - 1, i))
    im = Image.fromarray(arr[i]).resize((W, H), Image.LANCZOS)
    return np.asarray(im, np.float32) / 255


MEM = []


def memory_frames():
    if MEM:
        return MEM
    for src, t in [('../out/ember_final.mp4', 23.3), ('../b3d/out/ember2_final.mp4', 39.2),
                   ('../out/ember_final.mp4', 7.55), ('../b3d/out/ember2_final.mp4', 31.0),
                   ('../out/ember_final.mp4', 26.4), ('../b3d/out/ember2_final.mp4', 12.2)]:
        raw = subprocess.run(['ffmpeg', '-v', 'error', '-ss', str(t), '-i', src, '-frames:v', '1', '-f', 'rawvideo',
                              '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-'], capture_output=True, check=True).stdout
        MEM.append(np.frombuffer(raw, np.uint8).reshape(H, W, 3).astype(np.float32) / 255)
    return MEM


# ------------------------------------------------------------------------------------------------ FX
_yy, _xx = np.mgrid[0:H, 0:W].astype(np.float32)
VIG = np.clip(1 - 0.45 * (((_xx - W / 2) / (W * 0.62)) ** 2 + ((_yy - H / 2) / (H * 0.75)) ** 2) ** 1.4, 0.35, 1)[..., None]
GRAIN = [np.random.default_rng(i).normal(0, 1, (H // 2, W // 2)).astype(np.float32) for i in range(8)]


def grade(img, g, t):
    lum = img @ np.array([0.3, 0.59, 0.11], np.float32)
    lum = lum[..., None]
    if g == 'night':
        img = img * np.array([0.94, 0.98, 1.06], np.float32)
        img = 0.5 + (img - 0.5) * 1.06
    elif g == 'eclipse':
        img = lum + (img - lum) * 0.55
        img = img * np.array([0.9, 0.97, 1.1], np.float32)
        img = 0.5 + (img - 0.5) * 1.12
    elif g == 'low':
        warm = np.clip((img[..., 0:1] - img[..., 2:3]) * 3, 0, 1)      # keep the ember
        grey = lum * np.array([0.85, 0.9, 1.0], np.float32)
        img = grey * (1 - warm) + img * warm
        img = img * 0.85
    elif g == 'fire':
        img = lum + (img - lum) * 1.18
        img = img * np.array([1.06, 0.98, 0.92], np.float32)
        img = 0.5 + (img - 0.5) * 1.08
    elif g == 'dawn':
        img = img * np.array([1.05, 1.0, 0.94], np.float32) + 0.015
    elif g == 'memory':
        img = lum * np.array([1.1, 0.85, 0.6], np.float32) + 0.05
    return img


class Embers:
    """Deterministic analytic embers: position is a pure function of t (render any frame, any order)."""

    def __init__(self, n=160, seed=3, fall=False):
        r = np.random.default_rng(seed)
        self.x0 = r.uniform(0, W, n)
        self.y0 = r.uniform(0, H, n)
        self.sp = r.uniform(25, 90, n) * (1 if fall else -1)
        self.sw = r.uniform(10, 40, n)
        self.ph = r.uniform(0, 6.28, n)
        self.sz = r.uniform(1.5, 4.5, n)
        self.fl = r.uniform(2, 7, n)

    def draw(self, t, amount, layer):
        d = ImageDraw.Draw(layer)
        n = int(len(self.x0) * min(1.0, amount))
        x = (self.x0 + self.sw * np.sin(t * 0.9 + self.ph) + t * 12) % W
        y = (self.y0 + self.sp * t) % (H + 40) - 20
        a = 0.55 + 0.45 * np.sin(t * self.fl + self.ph)
        for i in range(n):
            s = self.sz[i]
            v = int(255 * a[i])
            d.ellipse((x[i] - s, y[i] - s, x[i] + s, y[i] + s), fill=(v, int(v * 0.45), int(v * 0.12)))


EMB_UP = Embers(170, 3, False)
EMB_DOWN = Embers(220, 5, True)
SNOW = Embers(260, 9, True)


def speedlines(t, amt, cx=W / 2, cy=H / 2, seed=0):
    layer = Image.new('L', (W, H), 0)
    d = ImageDraw.Draw(layer)
    r = np.random.default_rng(int(t * 12) + seed * 1000)
    for _ in range(int(90 * amt)):
        a = r.uniform(0, 2 * math.pi)
        r0 = r.uniform(0.35, 0.6) * W
        r1 = r0 + r.uniform(0.3, 0.8) * W
        wdt = r.uniform(1, 5)
        d.line((cx + math.cos(a) * r0, cy + math.sin(a) * r0, cx + math.cos(a) * r1, cy + math.sin(a) * r1),
               fill=int(r.uniform(90, 220)), width=int(wdt))
    return np.asarray(layer, np.float32)[..., None] / 255


def impact_frame(img, t):
    lum = (img @ np.array([0.3, 0.59, 0.11], np.float32))[..., None]
    warm = np.clip((img[..., 0:1] - img[..., 2:3]) * 2.2 - 0.25, 0, 1)
    inv = np.clip((0.45 - lum) * 6, 0, 1)
    bw = np.concatenate([inv, inv, inv], 2) * 0.97 + 0.02
    red = np.array([0.95, 0.12, 0.06], np.float32)
    return bw * (1 - warm) + red * warm


def active_hits(b):
    out = []
    for (hb, kind, nfr) in HITS:
        df = (b - hb) * BEAT * FPS
        if 0 <= df < nfr:
            out.append((kind, df / nfr))
    return out


def shake_offset(b, amt):
    k = 0.0
    for (hb, kind, nfr) in HITS:
        if b >= hb and kind in ('impact', 'flash', 'white'):
            k += math.exp(-(b - hb) * BEAT * 7)
    s = amt * (0.4 + 2.5 * min(k, 1.5))
    t = b * BEAT
    return (s * math.sin(t * 61.0) * math.sin(t * 13.7), s * math.sin(t * 47.0 + 1.2) * math.sin(t * 9.3))


def title(img, u):
    e = 1 - (1 - min(1, max(0, u))) ** 3
    layer = Image.new('L', (W, H), 0)
    d = ImageDraw.Draw(layer)
    f1 = ImageFont.truetype('/System/Library/Fonts/Supplemental/Futura.ttc', 150)
    try:
        f2 = ImageFont.truetype('/System/Library/Fonts/ヒラギノ角ゴシック W6.ttc', 54)
    except Exception:
        f2 = ImageFont.truetype('/System/Library/Fonts/Supplemental/Futura.ttc', 54)
    f3 = ImageFont.truetype('/System/Library/Fonts/Supplemental/Futura.ttc', 40)
    word = 'EMBER'
    track = 70 * (1.3 - 0.3 * e)
    ws = [d.textlength(c, font=f1) for c in word]
    tot = sum(ws) + track * (len(word) - 1)
    CX = W * 0.30
    x = CX - tot / 2
    y = H * 0.30
    for c, wd in zip(word, ws):
        d.text((x, y), c, font=f1, fill=int(255 * e))
        x += wd + track
    sub1 = 'I I I'
    sw = d.textlength(sub1, font=f3)
    d.text((CX - sw / 2, y + 185), sub1, font=f3, fill=int(230 * e))
    jp = '点火'
    en = 'K I N D L E'
    jw = d.textlength(jp, font=f2)
    ew = d.textlength(en, font=f3)
    d.text((CX - (jw + 30 + ew) / 2, y + 260), jp, font=f2, fill=int(255 * e))
    d.text((CX - (jw + 30 + ew) / 2 + jw + 30, y + 268), en, font=f3, fill=int(220 * e))
    lw = tot * e
    d.line((CX - lw / 2, y + 170, CX + lw / 2, y + 170), fill=int(255 * e), width=3)
    a = np.asarray(layer, np.float32)[..., None] / 255
    g = np.asarray(layer.filter(ImageFilter.GaussianBlur(14)), np.float32)[..., None] / 255
    img = img * (1 - 0.35 * e) + g * np.array([1.0, 0.45, 0.12], np.float32) * 0.9
    return img * (1 - a) + a * np.array([1.0, 0.96, 0.9], np.float32)


# ------------------------------------------------------------------------------------------------ frame
def render_frame(fi):
    t = fi / FPS
    b = t / BEAT
    seg = None
    for e in EDL:
        if e[0] <= b < e[1]:
            seg = e
    if seg is None:
        seg = EDL[-1]
    b0, b1, kind, src, si, so, step, g, ex = seg
    t0, t1 = beat_t(b0), beat_t(b1)
    # anime retime: quantize local time to the shot's step (ones / twos / threes)
    lf = int((t - t0) * FPS)
    lq = (lf // step) * step
    u = lq / max(1, (t1 - t0) * FPS - 1)
    # hit-stop: freeze on impact frames
    for (hb, hk, nfr) in HITS:
        if hk == 'impact' and 0 <= (b - hb) * BEAT * FPS < nfr + 2:
            u = min(u, ((hb * BEAT - t0) * FPS) / max(1, (t1 - t0) * FPS - 1))
    u = max(0.0, min(1.0, u))
    if kind == 'still':
        img = still_frame(src, u, ex.get('zoom', (1, 1)), ex.get('pan', (0, 0)))
        if ex.get('punch') and lf < 3:
            img = still_frame(src, 0, (ex['zoom'][0] * 1.08, ex['zoom'][0] * 1.08), (0, 0))
    elif kind in ('clip', 'title'):
        st = si + (so - si) * u
        img = clip_frame(src, st)
        if ex.get('echo'):
            # smear: trail of the previous two source frames (like a drawn smear/afterimage)
            sp = (so - si) / max(1e-3, (t1 - t0))
            p1 = clip_frame(src, st - sp * step / FPS)
            p2 = clip_frame(src, st - 2 * sp * step / FPS)
            img = np.maximum(img, 0.62 * p1 + 0.38 * img) * 0.55 + (0.5 * img + 0.3 * p1 + 0.2 * p2) * 0.45
    elif kind == 'memory':
        mem = memory_frames()
        k = (lf // 2)
        img = mem[k % len(mem)] if (lf // 2) % 3 != 2 else np.zeros((H, W, 3), np.float32)
    img = grade(img, g, t)
    # overlays
    ov = Image.new('RGB', (W, H), 0)
    if ex.get('embers'):
        (EMB_DOWN if ex.get('fall') else EMB_UP).draw(t, ex['embers'], ov)
    if ex.get('snow'):
        sn = Image.new('RGB', (W, H), 0)
        SNOW.draw(t * 0.6, ex['snow'], sn)
        sna = np.asarray(sn, np.float32)[..., :1] / 255
        img = img + sna * 0.5 * np.array([0.85, 0.9, 1.0], np.float32)
    ova = np.asarray(ov, np.float32) / 255
    if ova.max() > 0:
        glow = np.asarray(ov.filter(ImageFilter.GaussianBlur(6)), np.float32) / 255
        img = img + ova * 0.9 + glow * 1.4
    if ex.get('lines'):
        sl = speedlines(lq / FPS + b0, ex['lines'], seed=int(b0))
        img = img * (1 - sl * 0.55) + sl * 0.55
    # hits
    for (hk, hu) in active_hits(b):
        if hk == 'impact':
            img = impact_frame(img, t)
        elif hk == 'flash':
            img = img + (1 - img) * (1 - hu) * 0.8
        elif hk == 'white':
            img = img + (1 - img) * min(1.0, (1 - hu) * 1.6 if hk == 'white' else 1)
    # camera shake (translate), chromatic aberration on heavy shake
    amt = ex.get('shake', 0)
    if amt:
        dx, dy = shake_offset(b, amt)
        img = np.roll(img, (int(dy), int(dx)), axis=(0, 1))
        ca = int(min(8, abs(dx) * 0.6))
        if ca >= 1:
            img[:, ca:, 0] = img[:, :-ca, 0]
            img[:, :-ca, 2] = img[:, ca:, 2]
    if kind == 'title':
        img = title(img, (t - t0) / 2.2)
    if ex.get('bars'):
        bh = int(H * 0.12 * min(1.0, (t - t0) / 0.5))
        if bh > 0:
            img[:bh] = 0
            img[H - bh:] = 0
    img = img * VIG
    gr = np.asarray(Image.fromarray(((GRAIN[fi % 8] * 0.5 + 0.5).clip(0, 1) * 255).astype(np.uint8)).resize((W, H)),
                    np.float32)[..., None] / 255 - 0.5
    img = img + gr * 0.035
    fade = min(1.0, t / 1.2) * min(1.0, (DUR - t) / 1.8)
    img = img * fade
    return (np.clip(img, 0, 1) * 255).astype(np.uint8)


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('--from_', type=float, default=0)
    ap.add_argument('--to', type=float, default=TOTAL_BEATS)
    ap.add_argument('--stills', default='')
    ap.add_argument('--out', default='out/ep3_picture.mp4')
    a = ap.parse_args()
    if a.stills:
        os.makedirs('board/stills', exist_ok=True)
        for bb in [float(x) for x in a.stills.split(',')]:
            fi = int(round(bb * BEAT * FPS))
            Image.fromarray(render_frame(fi)).save(f'board/stills/b{bb:06.1f}.png')
        sys.exit()
    f0, f1 = int(a.from_ * BEAT * FPS), int(a.to * BEAT * FPS)
    cmd = ['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{H}', '-r', str(FPS),
           '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '15', '-pix_fmt', 'yuv420p', a.out]
    p = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    import time
    t0 = time.time()
    for fi in range(f0, f1):
        p.stdin.write(render_frame(fi).tobytes())
        if fi % 96 == 0:
            print(f'frame {fi}/{f1} {time.time() - t0:.0f}s', flush=True)
    p.stdin.close()
    p.wait()
    print('wrote', a.out)
