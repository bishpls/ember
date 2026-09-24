// Film: shot table + per-frame composition + post.
import { Canvas } from 'skia-canvas';
import { W, H, FPS, BEAT, b2t, clamp, rng } from './engine.js';
import { impactFrame } from './fx.js';

export const SHOTS = [];     // {b0, b1, name, draw(env)}
export const HITS = [];      // {b, kind: 'impact'|'flash'|'white'|'black', frames}
export function shot(b0, b1, name, draw) { SHOTS.push({ b0, b1, name, draw }); SHOTS.sort((a, b) => a.b0 - b.b0); }
export function hit(b, kind, frames = 2) { HITS.push({ b, kind, frames }); }
export let TOTAL_BEATS = 160;
export function setTotal(b) { TOTAL_BEATS = b; }

const main = new Canvas(W, H), glowC = new Canvas(W, H), tmp = new Canvas(W, H);
const grainTiles = [];
for (let k = 0; k < 4; k++) {
  const g = new Canvas(256, 256), x = g.getContext('2d'), r = rng(k + 1), img = x.createImageData(256, 256);
  for (let i = 0; i < img.data.length; i += 4) { const v = 128 + (r() - 0.5) * 90; img.data[i] = img.data[i + 1] = img.data[i + 2] = v; img.data[i + 3] = 255; }
  x.putImageData(img, 0, 0); grainTiles.push(g);
}

export function renderFrame(fi) {
  const t = fi / FPS, b = t / BEAT;
  let sh = SHOTS[0];
  for (const s of SHOTS) if (b >= s.b0) sh = s;
  const ctx = main.getContext('2d'), glow = glowC.getContext('2d');
  ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.globalAlpha = 1; ctx.globalCompositeOperation = 'source-over'; ctx.filter = 'none';
  ctx.fillStyle = '#000'; ctx.fillRect(0, 0, W, H);
  glow.setTransform(1, 0, 0, 1, 0, 0); glow.globalAlpha = 1; glow.globalCompositeOperation = 'source-over';
  glow.clearRect(0, 0, W, H);
  const t0 = b2t(sh.b0), t1 = b2t(sh.b1);
  const env = { ctx, glow, t, b, lt: t - t0, u: clamp((t - t0) / (t1 - t0)), dur: t1 - t0, fi, Canvas, tmp };
  sh.draw(env);
  // ---- post
  ctx.setTransform(1, 0, 0, 1, 0, 0); ctx.globalAlpha = 1;
  glow.setTransform(1, 0, 0, 1, 0, 0);
  ctx.globalCompositeOperation = 'lighter';
  ctx.filter = 'blur(10px)'; ctx.globalAlpha = 0.75; ctx.drawImage(glowC, 0, 0);
  ctx.filter = 'blur(34px)'; ctx.globalAlpha = 0.6; ctx.drawImage(glowC, 0, 0);
  ctx.filter = 'none'; ctx.globalAlpha = 1; ctx.globalCompositeOperation = 'source-over';
  // hits
  for (const h of HITS) {
    const df = (b - h.b) * BEAT * FPS;
    if (df < 0 || df >= h.frames) continue;
    const u = df / h.frames;
    if (h.kind === 'impact') impactFrame(ctx, 1);
    else if (h.kind === 'flash') { ctx.globalAlpha = 0.85 * (1 - u); ctx.fillStyle = '#fff'; ctx.fillRect(0, 0, W, H); ctx.globalAlpha = 1; }
    else if (h.kind === 'white') { ctx.globalAlpha = Math.min(1, (1 - u) * 1.8); ctx.fillStyle = '#fff'; ctx.fillRect(0, 0, W, H); ctx.globalAlpha = 1; }
    else if (h.kind === 'black') { ctx.fillStyle = '#000'; ctx.fillRect(0, 0, W, H); }
  }
  // vignette + grain
  const vg = ctx.createRadialGradient(W / 2, H / 2, H * 0.45, W / 2, H / 2, H * 1.05);
  vg.addColorStop(0, 'rgba(0,0,0,0)'); vg.addColorStop(1, 'rgba(8,4,20,0.55)');
  ctx.fillStyle = vg; ctx.fillRect(0, 0, W, H);
  ctx.globalCompositeOperation = 'overlay'; ctx.globalAlpha = 0.22;
  const gt = grainTiles[fi % 4];
  ctx.fillStyle = ctx.createPattern(gt, 'repeat'); ctx.fillRect(0, 0, W, H);
  ctx.globalCompositeOperation = 'source-over'; ctx.globalAlpha = 1;
  // fades
  const T = TOTAL_BEATS * BEAT;
  const fade = clamp(t / 0.8) * clamp((T - t) / 1.5);
  if (fade < 1) { ctx.fillStyle = `rgba(0,0,0,${1 - fade})`; ctx.fillRect(0, 0, W, H); }
  return main;
}
