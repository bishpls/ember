// Void wolf: side-view silhouette rig (Promare-flat black, cold rim line, cyan eyes).
import { TAU, rot, add, sub, mul, norm, perp, ik2, taper, pathPoly, pathSmooth, noise1, lerp, clamp, hash } from './engine.js';
import { P } from './palette.js';

// w: {x, y, s (px per body length ~ nose-to-hip), face, phase, mode, jaw, pitch (deg), t, seed, alpha}
export function drawWolf(ctx, w, glow = null) {
  const f = w.face >= 0 ? 1 : -1, s = w.s, pr = (w.pitch || 0) * Math.PI / 180;
  const L = (x, y) => { const q = rot([x * f, y], f * pr); return [w.x + q[0] * s, w.y + q[1] * s]; };
  const ph = w.phase * TAU, mode = w.mode || 'run';
  const seed = w.seed || 0;
  const jit = (i) => 0.012 * noise1(w.t * 9 + i * 1.7 + seed);     // shadow flicker on the mane
  // ---- legs (behind body first: far pair)
  const anch = { fr: [0.32, 0.05], ff: [0.27, 0.04], hr: [-0.38, 0.03], hf: [-0.43, 0.02] };
  const offs = { fr: 0, ff: 0.12, hr: 0.5, hf: 0.62 };
  const paw = (k) => {
    const [ax, ay] = anch[k];
    const front = k[0] === 'f';
    if (mode === 'run') {
      const p = ph + offs[k] * TAU;
      return [ax + 0.26 * Math.cos(p), ay + 0.42 - Math.max(0, 0.16 * Math.sin(p))];
    }
    if (mode === 'leap') return front ? [ax + 0.42, ay + 0.2] : [ax - 0.42, ay + 0.26];
    if (mode === 'crouch') return front ? [ax + 0.18, ay + 0.3] : [ax - 0.02, ay + 0.3];
    if (mode === 'hurt') { const p = w.t * 14 + offs[k] * 8; return [ax + 0.25 * Math.cos(p), ay + 0.28 + 0.12 * Math.sin(p * 1.3)]; }
    return [ax + (front ? 0.03 : 0), ay + 0.44];
  };
  const legPoly = (k) => {
    const A = L(...anch[k]), T = L(...paw(k));
    const front = k[0] === 'f';
    const [j, e] = ik2(A, T, 0.24 * s, 0.26 * s, (front ? 1 : -1) * f);
    const pw = add(e, [f * 0.07 * s, 0.01 * s]);
    return taper([A, j, e, pw], 0.11 * s, 0.035 * s, 0.05 * s);
  };
  const drawPoly = (pts, smooth = false) => {
    (smooth ? pathSmooth : pathPoly)(ctx, pts);
    ctx.fillStyle = P.void; ctx.fill();
  };
  ctx.save();
  ctx.globalAlpha = w.alpha ?? 1;
  drawPoly(legPoly('ff')); drawPoly(legPoly('hf'));
  // ---- body with jagged mane
  const top = [];
  const nsp = 12;
  for (let i = 0; i <= nsp; i++) {
    const u = i / nsp;
    const x = lerp(-0.55, 0.5, u);
    const base = -0.1 - 0.08 * Math.sin(u * Math.PI) - 0.06 * u;
    const spike = i % 2 ? (0.07 + 0.1 * Math.sin(u * Math.PI) + 0.06 * u) * (0.8 + 0.4 * hash(i + seed)) + jit(i) : 0;
    top.push(L(x - (i % 2) * 0.05, base - spike));
  }
  const belly = [L(0.46, 0.02), L(0.3, 0.12), L(0.08, 0.1), L(-0.2, 0.06), L(-0.45, 0.05), L(-0.58, -0.02)];
  const body = top.concat(belly);
  drawPoly(body);
  // tail
  const tw = Math.sin(w.t * 7 + seed) * 0.06;
  const tail = [L(-0.55, -0.12), L(-0.8, -0.2 + tw), L(-0.74, -0.13 + tw), L(-0.98, -0.12 + tw * 1.8), L(-0.76, -0.06 + tw), L(-0.86, 0.0 + tw * 1.4), L(-0.58, -0.02)];
  drawPoly(tail);
  // head + ears
  const jaw = clamp(w.jaw || 0);
  const head = [L(0.44, -0.2), L(0.52, -0.33), L(0.58, -0.24), L(0.63, -0.36), L(0.68, -0.24), L(0.8, -0.2), L(0.98, -0.16),
    L(0.99, -0.12), L(0.8, -0.1), L(0.62, -0.02), L(0.46, 0.0)];
  drawPoly(head);
  const ja = jaw * 0.55;
  const jawPts = [[0.0, 0.0], [0.34, -0.02], [0.33, 0.035], [0.02, 0.06]].map((q) => { const r = rot(q, f * ja); return L(0.64 + r[0] * 1, -0.1 + r[1]); });
  drawPoly(jawPts);
  if (jaw > 0.2) {   // fangs
    ctx.fillStyle = '#e9ecff';
    for (let i = 0; i < 3; i++) {
      const b = L(0.85 - i * 0.07, -0.1), tip = L(0.85 - i * 0.07 + 0.01, -0.06);
      pathPoly(ctx, [add(b, [-0.012 * s, 0]), add(b, [0.012 * s, 0]), tip]); ctx.fill();
    }
  }
  // near legs over body
  drawPoly(legPoly('hr')); drawPoly(legPoly('fr'));
  // cold rim along the back/mane + head top (light from above-left)
  ctx.beginPath(); top.forEach((q, i) => (i ? ctx.lineTo(...q) : ctx.moveTo(...q)));
  ctx.lineTo(...head[1]); ctx.lineTo(...head[3]); ctx.lineTo(...head[5]); ctx.lineTo(...head[6]);
  ctx.lineWidth = Math.max(1.5, 0.012 * s); ctx.strokeStyle = P.voidRim; ctx.lineJoin = 'miter'; ctx.stroke();
  // eye: cyan slit
  const eye = L(0.74, -0.19);
  const ea = f * pr - f * 0.25;
  const slit = [[-0.035, 0.008], [0.04, -0.012], [0.03, 0.006]].map((q) => add(eye, rot([q[0] * s * f, q[1] * s], ea * 0.3)));
  pathPoly(ctx, slit); ctx.fillStyle = P.voidEye; ctx.fill();
  if (glow) {
    glow.globalAlpha = w.alpha ?? 1;
    glow.beginPath(); glow.arc(eye[0], eye[1], 0.06 * s, 0, TAU); glow.fillStyle = P.voidEye; glow.fill();
    glow.globalAlpha = 1;
  }
  ctx.restore();
  return { eye, head: L(0.8, -0.15), body: L(0, -0.05) };
}
