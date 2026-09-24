// Graphic backgrounds: Promare-style flat layered pines, halftone moon, snow fields, skies.
import { W, H, rng, lerp, clamp, TAU, pathPoly, fbm } from './engine.js';
import { P } from './palette.js';

// ---------------------------------------------------------------- pines (precomputed polygons)
function makePine(r, h) {
  const tiers = 4 + Math.floor(r() * 2);
  const out = [];
  for (let k = 0; k < tiers; k++) {
    const y0 = -h * (k / tiers) * 0.85, y1 = y0 - h * (0.42 - 0.04 * k);
    const w = h * (0.34 - 0.055 * k) * (0.9 + 0.2 * r());
    const tri = [[-w, y0], [0, y1], [w, y0]];
    // jagged underside (flat graphic "teeth")
    const teeth = [];
    const nt = 4;
    for (let i = 0; i <= nt; i++) { const x = lerp(w, -w, i / nt); teeth.push([x, y0 + (i % 2 ? h * 0.035 : 0)]); }
    const poly = [[0, y1], [w, y0], ...teeth.slice(1, -1), [-w, y0]];
    // snow cap on the upper-left face
    const cap = [[0, y1], [w * 0.35, y1 + (y0 - y1) * 0.45], [w * 0.05, y1 + (y0 - y1) * 0.38],
      [-w * 0.3, y1 + (y0 - y1) * 0.62], [-w * 0.62, y0 - h * 0.01], [-w * 0.2, y1 + (y0 - y1) * 0.3]];
    out.push({ poly, cap, shade: [[0, y1], [w, y0], ...teeth.slice(1, -1), [w * 0.1, y0]] });
  }
  return { tiers: out, trunk: [[-h * 0.03, 0], [h * 0.03, 0], [h * 0.02, -h * 0.12], [-h * 0.02, -h * 0.12]] };
}

export class Forest {
  constructor(seed, n, xspan, yBase, hmin, hmax, colors, depth) {
    const r = rng(seed);
    this.trees = [];
    for (let i = 0; i < n; i++) {
      const x = lerp(xspan[0], xspan[1], (i + r() * 0.8) / n);
      const h = lerp(hmin, hmax, r());
      this.trees.push({ x, y: yBase + r() * (hmax * 0.08), h, pine: makePine(r, h) });
    }
    this.c = colors;
    this.depth = depth;
  }
  draw(ctx, camx = 0, camy = 0, snowCaps = true) {
    const c = this.c;
    for (const tr of this.trees) {
      const x = tr.x - camx * this.depth, y = tr.y - camy * this.depth;
      if (x < -tr.h || x > W + tr.h) continue;
      ctx.save();
      ctx.translate(x, y);
      pathPoly(ctx, tr.pine.trunk); ctx.fillStyle = c.shade; ctx.fill();
      for (const tier of tr.pine.tiers) {
        pathPoly(ctx, tier.poly); ctx.fillStyle = c.base; ctx.fill();
        pathPoly(ctx, tier.shade); ctx.fillStyle = c.shade; ctx.fill();
        if (snowCaps) { pathPoly(ctx, tier.cap); ctx.fillStyle = c.snow; ctx.fill(); }
        if (c.line) { pathPoly(ctx, tier.poly); ctx.lineWidth = c.lw || 2; ctx.strokeStyle = c.line; ctx.stroke(); }
      }
      ctx.restore();
    }
  }
}

// ---------------------------------------------------------------- sky / moon
let _halftone = null;
export function halftone(Canvas, color = '#a7d7ee', size = 10, r = 2.6) {
  const c = new Canvas(size, size), x = c.getContext('2d');
  x.fillStyle = color; x.beginPath(); x.arc(size / 2, size / 2, r, 0, TAU); x.fill();
  return c;
}

export function sky(ctx, top = P.sky0, bot = P.sky1, y0 = 0, y1 = H) {
  const g = ctx.createLinearGradient(0, y0, 0, y1);
  g.addColorStop(0, top); g.addColorStop(1, bot);
  ctx.fillStyle = g; ctx.fillRect(-W, -H, W * 3, H * 3);
}

export function stars(ctx, t, seed = 5, n = 140, alpha = 1) {
  const r = rng(seed);
  for (let i = 0; i < n; i++) {
    const x = r() * W, y = r() * H * 0.7, s = r() * 1.8 + 0.4;
    const a = (0.4 + 0.6 * Math.abs(Math.sin(t * (0.8 + r() * 2) + i))) * alpha;
    ctx.globalAlpha = a; ctx.fillStyle = '#e8ecff';
    ctx.fillRect(x, y, s, s);
  }
  ctx.globalAlpha = 1;
}

// moon: flat disk, halftone shading on one side, optional eclipse bite (0..1) and ring
export function moon(ctx, cx, cy, R, { pattern = null, bite = 0, ring = 0, glow = null, t = 0 } = {}) {
  ctx.save();
  const lit = ring > 0 ? 0 : 1 - bite;
  if (glow && lit > 0) {
    const g = glow.createRadialGradient(cx, cy, R * 0.95, cx, cy, R * 1.9);
    g.addColorStop(0, `rgba(150,210,255,${0.32 * lit})`); g.addColorStop(1, 'rgba(150,210,255,0)');
    glow.fillStyle = g; glow.beginPath(); glow.arc(cx, cy, R * 1.9, 0, TAU); glow.fill();
  }
  ctx.beginPath(); ctx.arc(cx, cy, R, 0, TAU); ctx.fillStyle = '#e4f4ff'; ctx.fill();
  // flat maria + halftone terminator shading (graphic, not photographic)
  ctx.save(); ctx.beginPath(); ctx.arc(cx, cy, R, 0, TAU); ctx.clip();
  ctx.fillStyle = '#c3def2';
  for (const [x, y, r] of [[-0.3, -0.2, 0.28], [0.25, 0.1, 0.2], [-0.05, 0.38, 0.16], [0.4, -0.35, 0.12]]) { ctx.beginPath(); ctx.ellipse(cx + x * R, cy + y * R, r * R, r * R * 0.8, 0.4, 0, TAU); ctx.fill(); }
  if (pattern) { ctx.beginPath(); ctx.arc(cx + R * 0.55, cy + R * 0.4, R * 1.05, 0, TAU); ctx.fillStyle = ctx.createPattern(pattern, 'repeat'); ctx.fill(); }
  ctx.restore();
  ctx.beginPath(); ctx.arc(cx, cy, R, 0, TAU); ctx.lineWidth = Math.max(2, R * 0.012); ctx.strokeStyle = '#2a1030'; ctx.stroke();
  if (bite > 0) {
    // the void takes a bite: an ink disk with a jagged, tendriled leading edge and a cold rim
    const ox = cx + R * 2.1 * (1 - bite) - R * 0.02, oy = cy - R * 0.08;
    const rr = R * 1.03;
    const pts = [];
    for (let i = 0; i <= 64; i++) {
      const a = (i / 64) * TAU;
      const lead = Math.max(0, -Math.cos(a));                 // the side facing the moon's centre
      const jag = lead * R * (0.05 * Math.sin(i * 7.3 + t * 3) + 0.08 * (i % 2)) ;
      pts.push([ox + Math.cos(a) * (rr + jag), oy + Math.sin(a) * (rr + jag)]);
    }
    ctx.save(); ctx.beginPath(); ctx.arc(cx, cy, R * 1.25, 0, TAU); ctx.clip();
    pathPoly(ctx, pts); ctx.fillStyle = '#030208'; ctx.fill();
    ctx.lineWidth = Math.max(2, R * 0.018); ctx.strokeStyle = '#62f6ff'; ctx.stroke();
    ctx.restore();
  }
  if (ring > 0) {
    ctx.beginPath(); ctx.arc(cx, cy, R * 1.0, 0, TAU); ctx.fillStyle = '#030208'; ctx.fill();
    ctx.beginPath(); ctx.arc(cx, cy, R * 1.01, 0, TAU);
    ctx.lineWidth = R * 0.035 * ring; ctx.strokeStyle = '#fff4e0'; ctx.stroke();
    if (glow) { glow.beginPath(); glow.arc(cx, cy, R * 1.04, 0, TAU); glow.lineWidth = R * 0.16 * ring; glow.strokeStyle = '#ff9a55'; glow.stroke(); }
  }
  ctx.restore();
}

// snow field with graphic shade bands
export function snowField(ctx, y, camx = 0, { col = P.snow, shade = P.snowS, deep = P.snowD, seed = 3 } = {}) {
  ctx.fillStyle = col; ctx.fillRect(-W, y, W * 3, H * 2);
  const r = rng(seed);
  ctx.fillStyle = shade;
  for (let i = 0; i < 9; i++) {
    const x = ((r() * W * 2 - camx * 1.0) % (W * 2) + W * 2) % (W * 2) - W * 0.5;
    const w = 200 + r() * 500, yy = y + 20 + r() * (H - y) * 0.9;
    ctx.beginPath(); ctx.ellipse(x, yy, w, 10 + r() * 22, 0, 0, TAU); ctx.fill();
  }
  ctx.fillStyle = deep; ctx.globalAlpha = 0.35;
  ctx.fillRect(-W, y + (H - y) * 0.8, W * 3, H);
  ctx.globalAlpha = 1;
}
