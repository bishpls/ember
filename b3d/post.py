"""EMBER II — post: grade, bloom, vignette, grain, title.  python post.py IN_DIR OUT_DIR [prefix]"""
import sys
import os
import glob
import math
import numpy as np
from multiprocessing import Pool
from PIL import Image, ImageFilter, ImageDraw, ImageFont

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from tl import FPS, DUR, T_TITLE, EASE, clamp

FONT = '/System/Library/Fonts/Supplemental/Futura.ttc'


def load(path):
    im = Image.open(path)
    a = np.asarray(im)
    if a.dtype == np.uint16:
        a = a.astype(np.float32) / 65535.0
    else:
        a = a.astype(np.float32) / 255.0
    return a[..., :3]


_cache = {}


def vignette(h, w):
    k = (h, w)
    if k not in _cache:
        yy, xx = np.mgrid[0:h, 0:w].astype(np.float32)
        r = ((xx - w / 2) / (w * 0.62)) ** 2 + ((yy - h / 2) / (h * 0.75)) ** 2
        _cache[k] = np.clip(1 - 0.5 * r ** 1.3, 0.3, 1)[..., None]
    return _cache[k]


def title(img, t):
    u = clamp((t - (T_TITLE + 0.3)) / 1.6)
    if u <= 0:
        return img
    h, w, _ = img.shape
    e = EASE['out'](u)
    layer = Image.new('L', (w, h), 0)
    glow = Image.new('L', (w, h), 0)
    d = ImageDraw.Draw(layer)
    size = int(h * 0.11)
    try:
        f1 = ImageFont.truetype(FONT, size)
        f2 = ImageFont.truetype(FONT, int(size * 0.28))
    except Exception:
        f1 = f2 = ImageFont.load_default()
    word = 'EMBER'
    track = size * 0.55 * (1.25 - 0.25 * e)
    widths = [d.textlength(c, font=f1) for c in word]
    total = sum(widths) + track * (len(word) - 1)
    x = w / 2 - total / 2
    y = h * 0.40
    for c, wd in zip(word, widths):
        d.text((x, y), c, font=f1, fill=int(255 * e))
        x += wd + track
    sub = 'I I   ·   A S H'
    sw = d.textlength(sub, font=f2)
    d.text((w / 2 - sw / 2, y + size * 1.35), sub, font=f2, fill=int(200 * e))
    lw = total * e
    d.line([(w / 2 - lw / 2, y + size * 1.2), (w / 2 + lw / 2, y + size * 1.2)], fill=int(255 * e), width=2)
    g = np.asarray(layer.filter(ImageFilter.GaussianBlur(size * 0.12)), np.float32)[..., None] / 255
    a = np.asarray(layer, np.float32)[..., None] / 255
    img = img + g * np.array([1.0, 0.35, 0.1], np.float32) * 0.8
    img = img * (1 - a) + a * np.array([0.98, 0.94, 0.9], np.float32)
    return img


def process(args):
    src, dst, fr = args
    t = (fr - 1) / FPS
    img = load(src)
    h, w, _ = img.shape
    # bloom from highlights (emissive eyes, embers, muzzle flashes, the moon)
    lum = img.mean(2, keepdims=True)
    hi = np.clip((img - 0.72) * 2.5, 0, None) * (lum > 0.5)
    pim = Image.fromarray((np.clip(hi, 0, 1) * 255).astype(np.uint8))
    sm = pim.resize((w // 4, h // 4), Image.BILINEAR)
    b1 = np.asarray(sm.filter(ImageFilter.GaussianBlur(4)).resize((w, h), Image.BILINEAR), np.float32) / 255
    b2 = np.asarray(sm.resize((w // 16, h // 16), Image.BILINEAR).filter(ImageFilter.GaussianBlur(3))
                    .resize((w, h), Image.BILINEAR), np.float32) / 255
    img = img + b1 * 0.35 + b2 * 0.5
    # grade: deeper blacks, cool shadows, gentle S-curve
    img = np.clip(img, 0, None)
    img = img ** 1.12
    img = img * 1.06 - 0.018
    lum = img.mean(2, keepdims=True)
    img = img + (1 - lum) ** 3 * np.array([-0.006, 0.0, 0.018], np.float32)
    img = img * vignette(h, w)
    img = 0.5 + (img - 0.5) * 1.06
    # title + fades
    img = title(img, t)
    fade = clamp(t / 1.2) * clamp((DUR - t) / 1.6)
    img = img * fade
    rng = np.random.default_rng(fr)
    img = img + rng.normal(0, 0.012, (h, w, 1)).astype(np.float32)
    Image.fromarray((np.clip(img, 0, 1) * 255).astype(np.uint8)).save(dst, compress_level=1)
    return fr


if __name__ == '__main__':
    src_dir, dst_dir = sys.argv[1], sys.argv[2]
    prefix = sys.argv[3] if len(sys.argv) > 3 else 'a'
    os.makedirs(dst_dir, exist_ok=True)
    files = sorted(glob.glob(os.path.join(src_dir, prefix + '*.png')))
    jobs = []
    for f in files:
        fr = int(os.path.basename(f)[len(prefix):-4])
        jobs.append((f, os.path.join(dst_dir, f'p{fr:04d}.png'), fr))
    with Pool(8) as p:
        for i, _ in enumerate(p.imap_unordered(process, jobs, chunksize=4)):
            if i % 200 == 0:
                print('post', i, len(jobs), flush=True)
    print('post done', len(jobs))
