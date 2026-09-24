// Shared scenery kit.
import { Canvas } from 'skia-canvas';
import { W, H, TAU, lerp, clamp, rng, pathPoly, ease, onN, noise1 } from './engine.js';
import { P } from './palette.js';
import { Forest, stars, moon, snowField, halftone } from './bg.js';
import { drawWolf } from './wolf.js';

export const HT = halftone(Canvas, '#8fb6dc', 12, 3.4);
export const HTwarm = halftone(Canvas, '#ffb37a', 11, 2.8);

// A reusable night backdrop: sky, stars, moon (optionally bitten/ringed), two forest bands, snow.
const farF = new Forest(21, 70, [-3000, 9000], 640, 150, 260, { base: P.pineFar, shade: P.pineFarS, snow: '#c9cdf6' }, 0.2);
const midF = new Forest(22, 46, [-3000, 10000], 740, 260, 440, { base: P.pine, shade: P.pineS, snow: P.pineSnow, line: P.line, lw: 2 }, 0.5);
export function night(ctx, glow, t, { camx = 0, camy = 0, zoom = 1, moonXY = [1250, 330], moonR = 230, bite = 0, ring = 0,
  horizon = 640, snowY = 900, drain = 0, forest = true } = {}) {
  ctx.save();
  ctx.translate(W / 2, H / 2); ctx.scale(zoom, zoom); ctx.translate(-W / 2, -H / 2);
  const g = ctx.createLinearGradient(0, -camy * 0.1, 0, horizon + 60 - camy * 0.3);
  g.addColorStop(0, P.sky0); g.addColorStop(1, drain ? '#1b1a2c' : P.sky1);
  ctx.fillStyle = g; ctx.fillRect(-W, -H, W * 3, H * 3);
  stars(ctx, t, 5, 150, 0.8 * (1 - drain));
  ctx.save(); ctx.translate(-camx * 0.03, -camy * 0.05);
  moon(ctx, moonXY[0], moonXY[1], moonR, { pattern: HT, bite, ring, glow, t });
  ctx.restore();
  if (forest) {
    ctx.save(); ctx.translate(0, -camy * 0.2);
    ctx.fillStyle = '#8f96dc'; ctx.fillRect(-W, horizon - 30, W * 3, 400);
    farF.draw(ctx, camx, 0);
    ctx.restore();
    ctx.save(); ctx.translate(0, -camy * 0.5);
    ctx.fillStyle = '#b4b9f0'; ctx.fillRect(-W, horizon + 70, W * 3, 400);
    midF.draw(ctx, camx, 0);
    ctx.restore();
  }
  ctx.save(); ctx.translate(0, -camy);
  snowField(ctx, snowY, camx);
  ctx.restore();
  ctx.restore();
}

// cyan eye pairs in darkness (pop on the beat)
export function eyePairs(ctx, glow, list, t) {
  for (const e of list) {
    const age = t - e.t;
    if (age < 0) continue;
    const open = clamp(age / 0.12);
    const blink = (Math.sin(t * 0.7 + e.x) > 0.985) ? 0.1 : 1;
    for (const dx of [-e.gap / 2, e.gap / 2]) {
      const x = e.x + dx, y = e.y, w = e.s, h = e.s * 0.28 * open * blink;
      ctx.beginPath(); ctx.moveTo(x - w, y + h * 0.2); ctx.quadraticCurveTo(x, y - h * 1.6, x + w, y - h * 0.3);
      ctx.quadraticCurveTo(x, y + h * 1.2, x - w, y + h * 0.2); ctx.fillStyle = P.voidEye; ctx.fill();
      if (glow) { glow.beginPath(); glow.arc(x, y, w * 1.1, 0, TAU); glow.fillStyle = P.voidEye; glow.globalAlpha = 0.55 * open; glow.fill(); glow.globalAlpha = 1; }
    }
  }
}

// black ink "void" mass with jagged edge + cyan eyes (for the flood / pile / king)
export function voidMass(ctx, pts, glow = null, rim = true) {
  pathPoly(ctx, pts); ctx.fillStyle = P.void; ctx.fill();
  if (rim) { ctx.lineWidth = 3; ctx.strokeStyle = P.voidRim; ctx.stroke(); }
}

// letterbox bars
export function bars(ctx, amt) {
  const h = H * 0.11 * clamp(amt);
  if (h <= 0) return;
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  ctx.fillStyle = '#000'; ctx.fillRect(0, 0, W, h); ctx.fillRect(0, H - h, W, h);
}
