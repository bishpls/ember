// EMBER III · studio pipeline — compositing library.
import { Canvas, loadImage } from 'skia-canvas';
import fs from 'fs';
import path from 'path';
import { clamp, lerp, ease, rng, TAU, fbm, noise1 } from '../../ep3b/src/engine.js';
export { clamp, lerp, ease, rng, TAU, fbm, noise1 };

export const W = 1920, H = 1080, FPS = 24, BPM = 150, BEAT = 60 / BPM;
export const bf = (b) => b * BEAT * FPS;                 // beat -> frame (float)
export const fb = (f) => f / (BEAT * FPS);               // frame -> beat
const ROOT = path.resolve(path.dirname(new URL(import.meta.url).pathname), '..');

// ---------------------------------------------------------------- assets
const cache = new Map();
export async function img(p) {
  if (cache.has(p)) return cache.get(p);
  let full = path.join(ROOT, p);
  if (!fs.existsSync(full) && fs.existsSync(path.join(ROOT, 'draw', p + '.png'))) full = path.join(ROOT, 'draw', p + '.png');
  const im = await loadImage(full);
  cache.set(p, im);
  return im;
}
export async function preload(list) { for (const p of list) await img(p); }
export const setImg = (k, im) => cache.set(k, im);
export const I = (p) => { const v = cache.get(p); if (!v) throw new Error('not loaded: ' + p); return v; };

// slice a 3x2 (or cols x rows) effects/cycle sheet into trimmed frames
export async function sheet(p, cols = 3, rows = 2) {
  const key = p + `#${cols}x${rows}`;
  if (cache.has(key)) return cache.get(key);
  const im = await img(p);
  const cw = im.width / cols, ch = im.height / rows, out = [];
  for (let r = 0; r < rows; r++) for (let c = 0; c < cols; c++) {
    const cv = new Canvas(cw, ch), x = cv.getContext('2d');
    x.drawImage(im, c * cw, r * ch, cw, ch, 0, 0, cw, ch);
    out.push(cv);
  }
  cache.set(key, out);
  return out;
}

// ---------------------------------------------------------------- frame buffers
export const main = new Canvas(W, H), glowC = new Canvas(W, H);
export const X = main.getContext('2d'), G = glowC.getContext('2d');
const celC = new Canvas(W, H), rimC = new Canvas(W, H), shakeC = new Canvas(W, H);

export function clearFrame() {
  X.setTransform(1, 0, 0, 1, 0, 0); X.globalAlpha = 1; X.globalCompositeOperation = 'source-over'; X.filter = 'none';
  X.fillStyle = '#000'; X.fillRect(0, 0, W, H);
  G.setTransform(1, 0, 0, 1, 0, 0); G.globalAlpha = 1; G.globalCompositeOperation = 'source-over'; G.clearRect(0, 0, W, H);
}

// ---------------------------------------------------------------- camera: a world->screen transform applied to plates/cels
// cam = {x, y (world point at screen centre), z (zoom), r (roll rad), sx, sy (shake px)}
export function camApply(ctx, cam, par = 1) {
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.translate(W / 2 + (cam.sx || 0) * par, H / 2 + (cam.sy || 0) * par);
  ctx.rotate((cam.r || 0) * par);
  const z = 1 + ((cam.z ?? 1) - 1) * par;
  ctx.scale(z, z);
  ctx.translate(-(cam.x ?? W / 2), -(cam.y ?? H / 2));
}

// painted background plate, cover-fitting a world rect (default the screen), with optional depth blur and grade
export function plate(im, cam, { rect = [0, 0, W, H], blur = 0, par = 1, tint = null, alpha = 1, fit = 'cover', dy = 0, dx = 0 } = {}) {
  X.save();
  camApply(X, cam, par);
  const [rx, ry, rw, rh] = rect;
  const s = fit === 'cover' ? Math.max(rw / im.width, rh / im.height) : Math.min(rw / im.width, rh / im.height);
  const w = im.width * s, h = im.height * s;
  if (blur) X.filter = `blur(${blur}px)`;
  X.globalAlpha = alpha;
  X.drawImage(im, rx + (rw - w) / 2 + dx, ry + (rh - h) / 2 + dy, w, h);
  X.filter = 'none';
  if (tint) { X.globalCompositeOperation = 'source-atop'; X.fillStyle = tint; X.fillRect(rx - 4000, ry - 4000, rw + 8000, rh + 8000); }
  X.restore();
}

// ---------------------------------------------------------------- secondary motion within a held drawing
// cloak (crimson) + hair (silver) pixels ripple with a travelling wave; everything else stays locked.
const warpCache = new Map();
function maskOf(im) {
  if (warpCache.has(im)) return warpCache.get(im);
  const c = new Canvas(im.width, im.height), x = c.getContext('2d');
  x.drawImage(im, 0, 0);
  const d = x.getImageData(0, 0, im.width, im.height);
  const m = new Uint8Array(im.width * im.height);
  for (let i = 0, p = 0; p < m.length; i += 4, p++) {
    const r = d.data[i], g = d.data[i + 1], b = d.data[i + 2], a = d.data[i + 3];
    if (a < 10) { m[p] = 2; continue; }                       // transparent: can be pulled into
    const red = r > 110 && r > g * 1.7 && r > b * 1.5;         // crimson cloak
    const silver = r > 175 && g > 175 && b > 185 && Math.abs(r - b) < 45;   // hair
    m[p] = red || silver ? 1 : 0;
  }
  const res = { c, d, m, w: im.width, h: im.height };
  warpCache.set(im, res);
  return res;
}
const warpOut = new Map();
export function warped(im, t, amp = 4, dir = [1, 0.3], freq = 1) {
  if (amp <= 0) return im;
  const M = maskOf(im);
  let o = warpOut.get(im);
  if (!o) { o = new Canvas(M.w, M.h); warpOut.set(im, o); }
  const ox = o.getContext('2d');
  const src = M.d.data, W2 = M.w, H2 = M.h;
  const out = ox.createImageData(W2, H2), dst = out.data;
  dst.set(src);
  const k = 0.018 * freq, w = t * 7 * freq;
  for (let y = 0; y < H2; y++) {
    const rowPhase = y * k - w;
    for (let x = 0; x < W2; x++) {
      const p = y * W2 + x;
      // only touch cloak/hair and the transparent margin right next to it
      if (M.m[p] === 0) continue;
      const s = Math.sin(rowPhase + x * k * 0.6) + 0.5 * Math.sin(rowPhase * 2.3 + x * 0.011);
      const dx = Math.round(s * amp * dir[0]), dy = Math.round(s * amp * dir[1]);
      const sx = x - dx, sy = y - dy;
      if (sx < 0 || sy < 0 || sx >= W2 || sy >= H2) continue;
      const q = sy * W2 + sx;
      if (M.m[q] === 0 && M.m[p] === 2) continue;         // never smear skin/suit into empty space
      if (M.m[q] === 0) continue;
      const i4 = p * 4, j4 = q * 4;
      dst[i4] = src[j4]; dst[i4 + 1] = src[j4 + 1]; dst[i4 + 2] = src[j4 + 2]; dst[i4 + 3] = src[j4 + 3];
    }
  }
  ox.putImageData(out, 0, 0);
  return o;
}

// ---------------------------------------------------------------- a cel: drawing + rim light + satsuei gradient + contact shadow
// place: {x, y, h, anchor:[ax,ay] (0..1 of image; default bottom-centre), rot, flip, sx, sy, alpha}
export function cel(im, place, cam, { rim = '#8fb6ff', rimOff = [-6, -4], rimA = 0.85, warm = 0, cool = 0.18, shadow = 0, glowCol = null,
  par = 1, light = [-0.5, -1], blur = 0 } = {}) {
  const h = place.h, w = im.width * (h / im.height) * (place.sx || 1), hh = h * (place.sy || 1);
  const [ax, ay] = place.anchor || [0.5, 1];
  const c = celC.getContext('2d');
  c.setTransform(1, 0, 0, 1, 0, 0); c.globalCompositeOperation = 'source-over'; c.globalAlpha = 1; c.clearRect(0, 0, W, H);
  camApply(c, cam, par);
  c.translate(place.x, place.y); c.rotate(place.rot || 0); c.scale(place.flip ? -1 : 1, 1);
  if (blur) c.filter = `blur(${blur}px)`;
  c.drawImage(im, -w * ax, -hh * ay, w, hh);
  c.filter = 'none';
  c.setTransform(1, 0, 0, 1, 0, 0);
  // rim
  const r = rimC.getContext('2d');
  r.setTransform(1, 0, 0, 1, 0, 0); r.globalCompositeOperation = 'source-over'; r.clearRect(0, 0, W, H);
  r.drawImage(celC, 0, 0); r.globalCompositeOperation = 'source-in'; r.fillStyle = rim; r.fillRect(0, 0, W, H);
  // satsuei: light-side gradient over the cel
  c.globalCompositeOperation = 'source-atop';
  const bb = [W / 2 + light[0] * W * 0.6, H / 2 + light[1] * H * 0.6];
  const g = c.createLinearGradient(bb[0], bb[1], W - bb[0], H - bb[1]);
  g.addColorStop(0, `rgba(160,190,255,${cool})`); g.addColorStop(0.55, 'rgba(0,0,0,0)'); g.addColorStop(1, `rgba(255,120,40,${0.35 * warm})`);
  c.fillStyle = g; c.fillRect(0, 0, W, H);
  c.globalCompositeOperation = 'source-over';
  const A = place.alpha ?? 1;
  if (shadow > 0) {
    X.save(); camApply(X, cam, par); X.globalAlpha = shadow * A; X.fillStyle = '#070a1c';
    X.beginPath(); X.ellipse(place.x, place.y, w * 0.34, h * 0.028, 0, 0, TAU); X.fill(); X.restore();
  }
  X.save(); X.setTransform(1, 0, 0, 1, 0, 0); X.globalAlpha = rimA * A; X.drawImage(rimC, rimOff[0], rimOff[1]); X.restore();
  X.save(); X.setTransform(1, 0, 0, 1, 0, 0); X.globalAlpha = A; X.drawImage(celC, 0, 0); X.restore();
  if (glowCol) { G.save(); G.globalAlpha = 0.35 * A; G.drawImage(rimC, 0, 0); G.restore(); }
}

// smear frame: the drawing dragged along its motion (stretched ghost copies) — used between keys on ones
export function smearCel(im, place, cam, { n = 5, dx = 60, dy = 0, drot = 0.12, stretch = 0.2, opts = {} } = {}) {
  for (let i = n; i >= 1; i--) {
    const a = i / n;
    cel(im, { ...place, x: place.x - dx * a, y: place.y - dy * a, rot: (place.rot || 0) - drot * a, sx: 1 + stretch * a, alpha: 0.2 * (1 - a) + 0.06 },
      cam, { ...opts, rimA: 0, shadow: 0 });
  }
  cel(im, { ...place, sx: 1 + stretch * 0.4 }, cam, { ...opts, shadow: 0 });
}

// effects cel playback: sheet frames on twos from t0
export function fxPlay(frames, age, place, cam, { fps = 12, loop = false, glow = 0.6, blend = 'source-over', alpha = 1 } = {}) {
  if (age < 0) return;
  let i = Math.floor(age * fps);
  if (i >= frames.length) { if (!loop) return; i %= frames.length; }
  const im = frames[i];
  const h = place.h, w = im.width * (h / im.height);
  X.save(); camApply(X, cam, place.par ?? 1); X.globalCompositeOperation = blend; X.globalAlpha = alpha;
  X.translate(place.x, place.y); X.rotate(place.rot || 0); X.scale(place.flip ? -1 : 1, 1);
  X.drawImage(im, -w / 2, -h / 2, w, h); X.restore();
  if (glow > 0) { G.save(); camApply(G, cam, place.par ?? 1); G.globalAlpha = glow * alpha; G.translate(place.x, place.y); G.rotate(place.rot || 0); G.scale(place.flip ? -1 : 1, 1); G.drawImage(im, -w / 2, -h / 2, w, h); G.restore(); }
}

// ---------------------------------------------------------------- 2D FX primitives (light, lines)
export function speedLines(cx, cy, seed, amt = 1, col = '#ffffff', inner = 0.3, alpha = 0.7) {
  const r = rng(seed);
  X.save(); X.setTransform(1, 0, 0, 1, 0, 0); X.globalAlpha = alpha; X.fillStyle = col;
  for (let i = 0; i < 80 * amt; i++) {
    const a = r() * TAU, w = 0.003 + r() * 0.01, r0 = (inner + r() * 0.25) * W, r1 = r0 + (0.5 + r()) * W;
    X.beginPath(); X.moveTo(cx + Math.cos(a - w) * r1, cy + Math.sin(a - w) * r1); X.lineTo(cx + Math.cos(a) * r0, cy + Math.sin(a) * r0);
    X.lineTo(cx + Math.cos(a + w) * r1, cy + Math.sin(a + w) * r1); X.fill();
  }
  X.restore();
}
export function streaks(seed, dir = [-1, 0], amt = 1, col = '#ffffff', alpha = 0.5) {
  const r = rng(seed), d = Math.hypot(...dir), ux = dir[0] / d, uy = dir[1] / d;
  X.save(); X.setTransform(1, 0, 0, 1, 0, 0); X.globalAlpha = alpha; X.fillStyle = col;
  for (let i = 0; i < 50 * amt; i++) {
    const x = r() * W, y = r() * H, L = 200 + r() * 700, th = 1 + r() * 3.5;
    X.beginPath(); X.moveTo(x - uy * th, y + ux * th); X.lineTo(x + ux * L, y + uy * L); X.lineTo(x + uy * th, y - ux * th); X.fill();
  }
  X.restore();
}
// blade smear: thin light arcs + one sharp crescent (additive glow)
export function bladeArc(cam, cx, cy, r0, r1, a0, a1, alpha = 1, col = '#ffffff', glowCol = '#9fd0ff') {
  X.save(); camApply(X, cam); X.globalAlpha = alpha; X.lineCap = 'round';
  for (let i = 0; i < 6; i++) {
    const r = r0 + (r1 - r0) * (0.35 + i * 0.13), a = a0 + (a1 - a0) * (0.25 + i * 0.08);
    X.beginPath(); X.arc(cx, cy, r, Math.min(a, a1), Math.max(a, a1)); X.lineWidth = 2 + i * 1.5; X.strokeStyle = i > 3 ? col : 'rgba(210,230,255,0.8)'; X.stroke();
  }
  const n = 24, pts = [];
  for (let i = 0; i <= n; i++) { const u = i / n, a = a0 + (a1 - a0) * u; pts.push([cx + Math.cos(a) * r1, cy + Math.sin(a) * r1]); }
  for (let i = n; i >= 0; i--) { const u = i / n, a = a0 + (a1 - a0) * u, r = r1 - (r1 - r0) * 0.22 * u * u; pts.push([cx + Math.cos(a) * r, cy + Math.sin(a) * r]); }
  X.beginPath(); pts.forEach((q, i) => (i ? X.lineTo(...q) : X.moveTo(...q))); X.closePath(); X.fillStyle = col; X.globalAlpha = 0.92 * alpha; X.fill();
  X.restore();
  G.save(); camApply(G, cam); G.globalAlpha = 0.5 * alpha; G.beginPath(); pts.forEach((q, i) => (i ? G.lineTo(...q) : G.moveTo(...q))); G.closePath(); G.fillStyle = glowCol; G.fill(); G.restore();
}
export function glowDot(cam, x, y, r, col, a = 1) {
  G.save(); camApply(G, cam); const g = G.createRadialGradient(x, y, 0, x, y, r);
  g.addColorStop(0, col); g.addColorStop(1, 'rgba(0,0,0,0)'); G.globalAlpha = a; G.fillStyle = g; G.beginPath(); G.arc(x, y, r, 0, TAU); G.fill(); G.restore();
}
export function embers(t, { n = 60, seed = 1, rise = 1, size = 1, alpha = 1, region = [0, 0, W, H], drift = 20, col = null } = {}) {
  const r = rng(seed);
  X.save(); X.setTransform(1, 0, 0, 1, 0, 0); G.save(); G.setTransform(1, 0, 0, 1, 0, 0);
  for (let i = 0; i < n; i++) {
    const x0 = region[0] + r() * region[2], y0 = region[1] + r() * region[3], sp = (30 + r() * 90) * rise, ph = r() * TAU, s = (1.5 + r() * 4) * size;
    const x = x0 + Math.sin(t * 1.3 + ph) * drift + t * 8;
    const y = ((y0 - sp * t - region[1]) % region[3] + region[3]) % region[3] + region[1];
    const fl = 0.5 + 0.5 * Math.sin(t * (4 + r() * 6) + ph);
    X.globalAlpha = alpha * (0.5 + 0.5 * fl); X.fillStyle = col || (fl > 0.6 ? '#ffd87a' : '#ff8a2a');
    X.beginPath(); X.ellipse(x, y, s, s * 0.6, t * 2 + ph, 0, TAU); X.fill();
    G.globalAlpha = alpha * fl * 0.8; G.fillStyle = col || '#ff8a2a'; G.beginPath(); G.arc(x, y, s * 3, 0, TAU); G.fill();
  }
  X.restore(); G.restore();
}
export function snow(t, { n = 90, seed = 9, speed = 50, size = 1, alpha = 0.85, wind = -40, blur = 0 } = {}) {
  const r = rng(seed);
  X.save(); X.setTransform(1, 0, 0, 1, 0, 0); X.fillStyle = '#eef2ff';
  if (blur) X.filter = `blur(${blur}px)`;
  for (let i = 0; i < n; i++) {
    const x0 = r() * W, y0 = r() * H, sp = speed * (0.6 + r() * 0.8), s = (1.2 + r() * 3) * size, ph = r() * TAU;
    const x = ((x0 + wind * t + Math.sin(t * 0.9 + ph) * 16) % W + W) % W, y = ((y0 + sp * t) % H + H) % H;
    X.globalAlpha = alpha * (0.4 + 0.6 * r()); X.beginPath(); X.arc(x, y, s, 0, TAU); X.fill();
  }
  X.restore();
}

// ---------------------------------------------------------------- post
export function post({ impact = false, flash = 0, flashCol = '255,250,240', shake = [0, 0], bars = 0, grade = null, vign = 0.55, bloom = 1, aberr = 0, fade = 1, grain = 0.05, fi = 0 } = {}) {
  X.setTransform(1, 0, 0, 1, 0, 0); X.filter = 'none'; X.globalAlpha = 1;
  if (shake[0] || shake[1]) {
    const s = shakeC.getContext('2d'); s.setTransform(1, 0, 0, 1, 0, 0); s.clearRect(0, 0, W, H); s.drawImage(main, 0, 0);
    X.fillStyle = '#000'; X.fillRect(0, 0, W, H); X.drawImage(shakeC, shake[0], shake[1]);
  }
  if (bloom > 0) {
    X.save(); X.globalCompositeOperation = 'lighter';
    X.filter = 'blur(10px)'; X.globalAlpha = 0.7 * bloom; X.drawImage(glowC, shake[0], shake[1]);
    X.filter = 'blur(38px)'; X.globalAlpha = 0.65 * bloom; X.drawImage(glowC, shake[0], shake[1]);
    X.restore(); X.filter = 'none';
  }
  if (grade) { X.save(); X.globalCompositeOperation = grade.op || 'soft-light'; X.globalAlpha = grade.a ?? 0.35; X.fillStyle = grade.col; X.fillRect(0, 0, W, H); X.restore(); }
  if (aberr > 0) {
    const s = shakeC.getContext('2d'); s.setTransform(1, 0, 0, 1, 0, 0); s.clearRect(0, 0, W, H); s.drawImage(main, 0, 0);
    X.save(); X.globalCompositeOperation = 'lighter'; X.globalAlpha = 0.25;
    X.filter = 'none'; X.drawImage(shakeC, aberr, 0); X.drawImage(shakeC, -aberr, 0); X.restore();
  }
  if (impact) {
    const img = X.getImageData(0, 0, W, H), d = img.data;
    for (let i = 0; i < d.length; i += 4) {
      const l = 0.3 * d[i] + 0.59 * d[i + 1] + 0.11 * d[i + 2], warm = d[i] - d[i + 2] > 50 && d[i] > 110;
      const v = l > 105 ? 10 : 248;
      d[i] = warm ? 235 : v; d[i + 1] = warm ? 25 : v; d[i + 2] = warm ? 30 : v;
    }
    X.putImageData(img, 0, 0);
  }
  if (flash > 0) { X.fillStyle = `rgba(${flashCol},${Math.min(1, flash)})`; X.fillRect(0, 0, W, H); }
  const vg = X.createRadialGradient(W / 2, H / 2, H * 0.4, W / 2, H / 2, H * 1.05);
  vg.addColorStop(0, 'rgba(0,0,0,0)'); vg.addColorStop(1, `rgba(4,4,18,${vign})`);
  X.fillStyle = vg; X.fillRect(0, 0, W, H);
  if (grain > 0) {
    const r = rng(fi * 7 + 1);
    X.save(); X.globalAlpha = grain;
    for (let i = 0; i < 1400; i++) { X.fillStyle = r() > 0.5 ? '#fff' : '#000'; X.fillRect(r() * W, r() * H, 2, 2); }
    X.restore();
  }
  if (bars > 0) { X.fillStyle = '#000'; X.fillRect(0, 0, W, bars); X.fillRect(0, H - bars, W, bars); }
  if (fade < 1) { X.fillStyle = `rgba(0,0,0,${1 - fade})`; X.fillRect(0, 0, W, H); }
}

// exposure sheet helper: pick a drawing by local frame from [[startFrame, id], ...] (holds until next entry)
export function xsheet(list, lf) { let cur = list[0][1]; for (const [f, id] of list) if (lf >= f) cur = id; return cur; }
// shake from a list of hit frames
export function shakeFrom(f, hits, amp = 24, decay = 5) {
  let s = 0; for (const h of hits) if (f >= h) s += amp * Math.exp(-(f - h) / decay);
  return [s * fbm(f * 1.7), s * fbm(f * 1.7 + 11)];
}
