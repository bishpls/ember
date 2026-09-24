// S8 king, S9 paw, S10 low, S11 ignition, S12 ascent, S13 apex, S14 the cut, S15 dawn.
import { W, H, b2t, t2b, lerp, clamp, ease, onN, TAU, rng, add, mul, rot, sub, norm, len, perp, pathPoly, pathSmooth, taper, fbm, noise1, hash } from '../engine.js';
import { P } from '../palette.js';
import { shot, hit } from '../film.js';
import { Actor } from '../actor.js';
import { drawHero, solve } from '../hero.js';
import { drawWolf } from '../wolf.js';
import { night, eyePairs, bars, HT } from '../scene.js';
import { moon, stars, Forest } from '../bg.js';
import { drawEye } from '../eye.js';
import { inkBurst, smearArc, smearTrail, puffs, ring, radialLines, streakLines, embers, snowfall, muzzle, flame, fireBlade, cracks } from '../fx.js';

const hitDecay = (t, tb, k = 7) => (t >= b2t(tb) ? Math.exp(-(t - b2t(tb)) * k) : 0);
const shakeXY = (t, a, s = 0) => [a * fbm(t * 40 + s), a * fbm(t * 40 + s + 7)];

// ============================================================== the Hollow King (giant silhouette)
const KR = rng(777);
const KING_EYES = [];
for (let i = 0; i < 24; i++) { const sx = KR() < 0.5 ? -1 : 1; KING_EYES.push({ x: sx * (0.25 + KR() * 0.55), y: -0.6 + KR() * 0.85, s: 0.02 + KR() * 0.022, b: 72 + Math.floor(KR() * 4) + (KR() < 0.4 ? 0.5 : 0) }); }
KING_EYES.push({ x: -0.19, y: -0.18, s: 0.075, b: 76 }, { x: 0.19, y: -0.18, s: 0.075, b: 76 });
function kingShape(cx, cy, R, form, t) {
  // symmetric, front-facing wolf head + shoulders, built from a half outline (units of R), mirrored
  const half = [[0, -0.95], [0.08, -1.25], [0.14, -0.92], [0.22, -1.18], [0.3, -0.86], [0.36, -0.8],   // broken crown
    [0.55, -1.55], [0.72, -1.05], [0.95, -0.72],                                                   // ear
    [1.12, -0.6], [1.38, -0.42], [1.2, -0.3], [1.5, -0.12], [1.22, -0.02], [1.45, 0.2], [1.12, 0.26], // cheek ruff
    [1.2, 0.5], [0.9, 0.5], [0.62, 0.72], [0.42, 0.98], [0.2, 1.12], [0, 1.18],                    // jaw -> chin
  ];
  const ds = (1 - form) * 2.4;
  const jit = (i) => 0.02 * noise1(t * 3 + i * 1.3);
  const right = half.map(([x, y], i) => [cx + (x + jit(i)) * R, cy + (y + ds) * R]);
  const left = half.slice().reverse().map(([x, y], i) => [cx - (x + jit(i + 40)) * R, cy + (y + ds) * R]);
  const body = [[cx + 1.2 * R, cy + (0.5 + ds) * R], [cx + 2.6 * R, cy + (2.2 + ds) * R], [cx + 3 * R, cy + (4 + ds) * R],
    [cx - 3 * R, cy + (4 + ds) * R], [cx - 2.6 * R, cy + (2.2 + ds) * R], [cx - 1.2 * R, cy + (0.5 + ds) * R]];
  return { head: left.concat(right), body, ds };
}
function drawKing(ctx, glow, cx, cy, R, form, t, eyesB = 999, alpha = 1) {
  ctx.save(); ctx.globalAlpha = alpha;
  const { head, body, ds } = kingShape(cx, cy, R, form, t);
  const Y = (y) => cy + (y + ds) * R;
  pathPoly(ctx, body); ctx.fillStyle = P.void; ctx.fill();
  pathPoly(ctx, head); ctx.fillStyle = P.void; ctx.fill();
  ctx.lineWidth = Math.max(3, R * 0.008); ctx.strokeStyle = P.voidRim; ctx.lineJoin = 'miter'; pathPoly(ctx, head); ctx.stroke();
  // graphic interior: brow ridge V, muzzle plane, nose
  ctx.strokeStyle = '#26245a'; ctx.lineWidth = R * 0.018;
  ctx.beginPath(); ctx.moveTo(cx - 0.7 * R, Y(-0.35)); ctx.lineTo(cx, Y(0.05)); ctx.lineTo(cx + 0.7 * R, Y(-0.35)); ctx.stroke();
  ctx.beginPath(); ctx.moveTo(cx - 0.28 * R, Y(0.2)); ctx.lineTo(cx - 0.2 * R, Y(0.85)); ctx.moveTo(cx + 0.28 * R, Y(0.2)); ctx.lineTo(cx + 0.2 * R, Y(0.85)); ctx.stroke();
  pathPoly(ctx, [[cx - 0.16 * R, Y(0.84)], [cx + 0.16 * R, Y(0.84)], [cx, Y(0.98)]]); ctx.fillStyle = '#1a1840'; ctx.fill();
  // eyes open on the beat: the main pair large and slanted, the rest scattered across brow and cheeks
  const b = t2b(t);
  for (const e of KING_EYES) {
    const age = b - e.b;
    if (age < 0 || b > eyesB) continue;
    const open = clamp(age / 0.3);
    const big = e.s > 0.05;
    const x = cx + e.x * R * (big ? 2 : 1.6), y = Y(e.y * (big ? 1 : 1.1)), s = e.s * R * 2;
    const tilt = big ? (e.x > 0 ? -0.35 : 0.35) : 0;
    ctx.save(); ctx.translate(x, y); ctx.rotate(tilt);
    ctx.beginPath(); ctx.moveTo(-s, 0); ctx.quadraticCurveTo(0, -s * 0.45 * open, s, -s * 0.12); ctx.quadraticCurveTo(0, s * 0.28 * open, -s, 0);
    ctx.fillStyle = P.voidEye; ctx.fill(); ctx.restore();
    if (glow) { glow.globalAlpha = 0.45 * open * alpha; glow.beginPath(); glow.arc(x, y, s * 0.8, 0, TAU); glow.fillStyle = P.voidEye; glow.fill(); glow.globalAlpha = 1; }
  }
  ctx.restore();
}

// fire wings from the shoulders: phoenix feathers (curved fire blades) fanning up and out
function fireWings(ctx, glow, sh, span, open, tq, flap = 0) {
  if (open <= 0) return;
  for (const side of [-1, 1]) {
    for (let i = 6; i >= 0; i--) {
      const fan = (0.25 + i * 0.2) * open + flap * 0.12;
      const L = span * (0.5 + 0.5 * Math.sin((i + 2) / 9 * Math.PI)) * open;
      const a0 = -Math.PI / 2 + side * fan;
      const root = add(sh, [side * 18, 6]);
      const spine = [];
      for (let k = 0; k <= 10; k++) {
        const u = k / 10;
        const a = a0 + side * u * 0.55 * (0.6 + i * 0.08);     // feathers curl outward toward their tips
        spine.push(add(root, [Math.cos(a) * L * u, Math.sin(a) * L * u - Math.sin(u * Math.PI) * L * 0.06]));
      }
      fireBlade(ctx, spine, L * 0.2, tq + i * 0.07, i * 5 + (side > 0 ? 2 : 0), i % 2 ? glow : null);
    }
  }
}

// ============================================================== S8  the King rises (68-80)
{
  const S = 180;
  const hero = new Actor({ face: 1, lean: -8, head: -40, wa: -60, wx: 0.1, wy: 0.02, g1: 0.35, two: 0, bside: 1, windx: -2,
    fx1: 0.16, fy1: 0.48, fx2: -0.18, fy2: 0.48 });
  hero.over((t, p, root) => { root[0] = 960; root[1] = 1010 - 0.48 * S; });
  shot(68, 80, 's08_king', (E) => {
    const { ctx, glow, t } = E;
    const b = t2b(t), tq = onN(t, 2);
    const form = ease.io(clamp((b - 69) / 7));
    const tilt = ease.io(clamp((b - 70) / 7));              // camera tilts up with the rise
    const oy = lerp(0, 420, tilt);
    const sh = shakeXY(t, 8 * clamp((b - 69) / 3) * (1 - clamp((b - 78) / 2)) + 14 * hitDecay(t, 76, 3));
    ctx.save(); ctx.translate(sh[0], sh[1] + oy); glow.save(); glow.translate(sh[0], sh[1] + oy);
    // drained sky, the eclipse closing to a ring behind the King's head
    const g = ctx.createLinearGradient(0, -600, 0, 900); g.addColorStop(0, '#040309'); g.addColorStop(1, '#23223f');
    ctx.fillStyle = g; ctx.fillRect(-W, -H * 2, W * 3, H * 4);
    stars(ctx, t, 8, 90, 0.4);
    const bite = lerp(0.62, 1.0, ease.in2(clamp((b - 70) / 6)));
    const ringA = clamp((b - 75.5) / 1.2);
    ctx.save(); ctx.translate(0, -oy * 0.6);
    moon(ctx, 960, -120, 330, { pattern: HT, bite: ringA > 0 ? 0 : bite, ring: ringA, glow, t });
    ctx.restore();
    // forest band
    ctx.fillStyle = '#3a3b6e'; ctx.fillRect(-W, 760, W * 3, 400);
    const f = new Forest(5, 30, [-400, 2400], 800, 120, 220, { base: '#2c2d5a', shade: '#1f2046', snow: '#8c90c8' }, 0);
    f.draw(ctx, 0, 0);
    // streams of the tide flowing backward & upward into the King
    const r = rng(31);
    const stream = 1 - clamp((b - 76) / 2);
    for (let i = 0; i < 16 && stream > 0; i++) {
      const x0 = lerp(-200, 2120, (i + 0.5) / 16) + 40 * Math.sin(i * 3.1), ph = r();
      const pts = [];
      for (let k = 0; k <= 8; k++) {
        const v = k / 8;
        const flow = (t * 0.9 + ph + v * 0.4) % 1;
        pts.push([lerp(x0, 960 + (x0 - 960) * 0.35, v) + 50 * Math.sin(v * 5 + t * 2 + i), lerp(1010, 520, v) - 30 * Math.sin(flow * TAU)]);
      }
      pathSmooth(ctx, taper(pts, 70 * stream, 14 * stream, 46 * stream), true, 0.6); ctx.fillStyle = P.void; ctx.fill();
      ctx.lineWidth = 2; ctx.strokeStyle = P.voidRim; ctx.stroke();
    }
    drawKing(ctx, glow, 960, 250, 420, form, t);
    // snow field + her, tiny, looking up
    ctx.fillStyle = '#9ea2d8'; ctx.fillRect(-W, 1010, W * 3, 600);
    drawHero(ctx, hero.fn(), tq, { S, ground: 1010, glow });
    ctx.restore(); glow.restore();
    snowfall(ctx, t, { n: 70, speed: 20, wind: -30, alpha: 0.5 });
  });
  hit(76, 'flash', 2);
}
function mix2(a, b, u) { return [lerp(a[0], b[0], u), lerp(a[1], b[1], u)]; }

// ============================================================== S9  the paw (80-84)
{
  const S = 420, G = 1030;
  const hero = new Actor({ face: 1, lean: -20, head: -45, wa: 95, wx: 0.12, wy: -0.18, g1: 0.2, g2: 0.7, two: 1, bside: 1, brow: 1,
    fx1: 0.24, fy1: 0.46, fx2: -0.26, fy2: 0.46, windx: 0.5, mouth: 0.6 });
  hero.over((t, p, root) => { root[0] = 960; root[1] = G - 0.47 * S; });
  shot(80, 84, 's09_paw', (E) => {
    const { ctx, glow, t } = E;
    const b = t2b(t), tq = onN(t, 2);
    if (b >= 82.2) { ctx.fillStyle = '#000'; ctx.fillRect(0, 0, W, H); return; }   // silence
    const u = ease.in(clamp((b - 80) / 2.0));
    const sh = shakeXY(t, 10 + 30 * u);
    ctx.save(); ctx.translate(sh[0], sh[1]); glow.save(); glow.translate(sh[0], sh[1]);
    const g = ctx.createLinearGradient(0, 0, 0, H); g.addColorStop(0, '#040309'); g.addColorStop(1, '#2c2b52');
    ctx.fillStyle = g; ctx.fillRect(-100, -100, W + 200, H + 200);
    ctx.fillStyle = '#9ea2d8'; ctx.fillRect(-100, G, W + 200, 300);
    // wind blast flattening the snow as it descends
    streakLines(ctx, onN(t, 1), [0, 1], 0.5 + u, '#c8ccff', 4, 0.35);
    drawHero(ctx, hero.fn(), tq, { S, ground: G, glow });
    // the paw: huge, from above, claws spread; scale grows with u
    const uu = ease.in2(clamp((b - 80) / 2.1));
    const pc = [960, lerp(40, 860, uu)], ps = lerp(800, 2000, uu);
    // its shadow races across the snow ahead of it
    ctx.fillStyle = 'rgba(4,3,10,0.6)'; ctx.beginPath(); ctx.ellipse(960, 1040, ps * 0.6, 60 + 40 * u, 0, 0, TAU); ctx.fill();
    const pad = [];
    for (let i = 0; i <= 40; i++) { const a = (i / 40) * TAU; pad.push([pc[0] + Math.cos(a) * ps * 0.55, pc[1] + Math.sin(a) * ps * 0.32]); }
    pathPoly(ctx, pad); ctx.fillStyle = P.void; ctx.fill();
    ctx.fillRect(pc[0] - ps * 0.5, pc[1] - ps * 1.5, ps, ps * 1.5);
    for (let k = -2; k <= 2; k++) {
      const base = [pc[0] + k * ps * 0.2, pc[1] + ps * 0.25 - Math.abs(k) * ps * 0.04];
      const claw = [add(base, [-ps * 0.04, 0]), add(base, [k * ps * 0.03, ps * 0.26]), add(base, [ps * 0.04, 0])];
      pathPoly(ctx, claw); ctx.fillStyle = '#d9dcff'; ctx.fill(); ctx.lineWidth = 4; ctx.strokeStyle = P.line; ctx.stroke();
    }
    ctx.lineWidth = 5; ctx.strokeStyle = P.voidRim; pathPoly(ctx, pad); ctx.stroke();
    ctx.restore(); glow.restore();
    if (b > 81.5) radialLines(ctx, 960, 700, onN(t, 1), 1.3, '#ffffff', 5, 0.2, 0.6);
  });
  hit(82, 'impact', 2); hit(82.1, 'white', 3);
}

// ============================================================== S10  the low (84-96)
{
  const S = 520;
  // lying on her back: side rig rotated -90 so her head is to the left
  const hero = new Actor({ face: 1, rot: -90, lean: 0, head: 22, held: 1, wa: -100, wx: 0.02, wy: -0.4, g1: 0.3, two: 0, bside: -1,
    hx: 0.1, hy: 0.18, fx1: 0.13, fy1: 0.4, fx2: -0.04, fy2: 0.5, gnd: 0, eye: 0.12, windx: 0.2, cloakAmt: 0.85 });
  hero.over((t, p, root) => { root[0] = 1080; root[1] = 790; p.sq = 1 + 0.008 * Math.sin(t * 1.6); });
  shot(84, 96, 's10_low', (E) => {
    const { ctx, glow, t } = E;
    const b = t2b(t), tq = onN(t, 3);
    // memory flashes (EMBER I / II in spirit: silhouettes against a red moon), 2 frames each
    if (b >= 90 && b < 91.6) {
      const k = Math.floor((b - 90) * 2.5);
      if (k % 2 === 0) {
        ctx.fillStyle = ['#e8e2d8', '#1b1a3c', '#e8e2d8', '#1b1a3c'][k % 4]; ctx.fillRect(0, 0, W, H);
        ctx.beginPath(); ctx.arc(960 + (k - 2) * 200, 460, 300, 0, TAU); ctx.fillStyle = k % 4 === 0 ? '#b31d36' : '#e4f4ff'; ctx.fill();
        drawHero(ctx, () => ({ p: { ...hero.tr.d, rot: 0, gnd: 1, eye: 1, fx1: 0.3, fy1: 0.44, fx2: -0.3, fy2: 0.46, wa: [150, -20, 60, 200][k % 4], lean: [20, 30, -10, 40][k % 4] }, root: [960, 1000 - 0.47 * 460] }), t, { S: 460, ground: 1000 });
        ctx.globalCompositeOperation = 'multiply'; ctx.fillStyle = '#a0643c'; ctx.fillRect(0, 0, W, H); ctx.globalCompositeOperation = 'source-over';
        return;
      }
    }
    if (b >= 92) {       // ECU: the ember clasp on her collar, guttering... then answering her heartbeat
      drawClasp(ctx, glow, t, b);
      return;
    }
    const push = lerp(1.0, 1.12, ease.io(clamp((b - 84) / 6)));
    ctx.save(); ctx.translate(W / 2, H / 2); ctx.scale(push, push); ctx.translate(-W / 2, -H / 2);
    glow.save(); glow.translate(W / 2, H / 2); glow.scale(push, push); glow.translate(-W / 2, -H / 2);
    // crater cross-section, grey-drained
    ctx.fillStyle = '#16152a'; ctx.fillRect(0, 0, W, H);
    ctx.fillStyle = '#5c5f93'; pathSmooth(ctx, [[-100, 420], [500, 560], [1000, 830], [1500, 560], [2100, 420], [2100, 1200], [-100, 1200]]); ctx.fill();
    drawHero(ctx, hero.fn(), tq, { S, ground: null, glow });
    ctx.fillStyle = '#7a7eb6'; pathSmooth(ctx, [[-100, 560], [480, 690], [1000, 842], [1520, 690], [2100, 560], [2100, 1200], [-100, 1200]]); ctx.fill();
    ctx.fillStyle = '#9195c8'; pathSmooth(ctx, [[300, 760], [1000, 846], [1700, 760], [1700, 790], [1000, 880], [300, 800]]); ctx.fill();
    // the clasp ember: guttering
    const J = solve(hero.pose(t).p, hero.pose(t).root, S, null);
    const fl = 0.25 + 0.2 * Math.abs(noise1(t * 7)) - 0.15 * clamp((b - 84) / 6);
    glow.globalAlpha = Math.max(0.05, fl); glow.beginPath(); glow.arc(J.chest[0], J.chest[1], 40, 0, TAU); glow.fillStyle = P.orange; glow.fill(); glow.globalAlpha = 1;
    ctx.restore(); glow.restore();
    // desaturate everything except warm
    const img = ctx.getImageData(0, 0, W, H), d = img.data;
    for (let i = 0; i < d.length; i += 4) {
      const r0 = d[i], g0 = d[i + 1], b0 = d[i + 2], l = 0.3 * r0 + 0.59 * g0 + 0.11 * b0;
      const warm = clamp((r0 - b0) / 90);
      d[i] = lerp(l * 0.9, r0, warm); d[i + 1] = lerp(l * 0.92, g0, warm); d[i + 2] = lerp(l * 1.05, b0, warm);
    }
    ctx.putImageData(img, 0, 0);
    snowfall(ctx, t * 0.5, { n: 80, speed: 30, wind: 0, size: 1.4, alpha: 0.8 });
  });
  function drawClasp(ctx, glow, t, b) {
    // cloak fabric (crimson, one hard fold shadow), scarf edge, the faceted crystal in its setting
    ctx.fillStyle = '#5c1024'; ctx.fillRect(0, 0, W, H);
    ctx.fillStyle = '#7a1630'; pathSmooth(ctx, [[0, 0], [1100, 0], [760, 1080], [0, 1080]]); ctx.fill();
    ctx.fillStyle = '#3a0a1a'; pathSmooth(ctx, [[1300, 0], [1920, 0], [1920, 1080], [1000, 1080]]); ctx.fill();
    ctx.fillStyle = P.scarf; pathSmooth(ctx, [[-50, -50], [1970, -50], [1970, 160], [1200, 230], [700, 190], [-50, 240]]); ctx.fill();
    // heartbeat pulses accelerate: 92.5, 93.5, 94.2, 94.6, 94.8 -> ignite at 95
    const beats = [92.6, 93.5, 94.15, 94.55, 94.8];
    let pulse = 0; for (const pb of beats) if (b > pb) pulse = Math.max(pulse, Math.exp(-(b - pb) * 6) * (0.4 + 0.15 * beats.indexOf(pb)));
    const flare = clamp((b - 94.85) / 0.25);
    const heat = Math.min(1, 0.12 + pulse + flare);
    const c = [960, 560], R = 250;
    // setting (steel prongs)
    for (let i = 0; i < 4; i++) { const a = i * Math.PI / 2 + Math.PI / 4; ctx.save(); ctx.translate(c[0] + Math.cos(a) * R * 0.95, c[1] + Math.sin(a) * R * 1.15); ctx.rotate(a); ctx.fillStyle = P.steel; ctx.fillRect(-18, -40, 36, 80); ctx.lineWidth = 6; ctx.strokeStyle = P.line; ctx.strokeRect(-18, -40, 36, 80); ctx.restore(); }
    // crystal: long diamond with facets; colours heat from dull brown-red to white-gold
    const top = [c[0], c[1] - R * 1.35], bot = [c[0], c[1] + R * 1.35], lft = [c[0] - R * 0.8, c[1]], rgt = [c[0] + R * 0.8, c[1]], mid = [c[0] + R * 0.12, c[1] - R * 0.1];
    const col = (k) => { const cold = [[70, 22, 20], [110, 36, 26], [150, 60, 40]][k], hot = [[255, 90, 40], [255, 160, 60], [255, 240, 200]][k];
      const q = cold.map((v, i) => Math.round(lerp(v, hot[i], heat))); return `rgb(${q[0]},${q[1]},${q[2]})`; };
    pathPoly(ctx, [top, rgt, mid]); ctx.fillStyle = col(2); ctx.fill();
    pathPoly(ctx, [top, mid, lft]); ctx.fillStyle = col(1); ctx.fill();
    pathPoly(ctx, [lft, mid, bot]); ctx.fillStyle = col(0); ctx.fill();
    pathPoly(ctx, [mid, rgt, bot]); ctx.fillStyle = col(1); ctx.fill();
    pathPoly(ctx, [top, rgt, bot, lft]); ctx.lineWidth = 9; ctx.strokeStyle = P.line; ctx.stroke();
    // a crack across it
    ctx.beginPath(); ctx.moveTo(c[0] - R * 0.5, c[1] - R * 0.3); ctx.lineTo(c[0] - R * 0.1, c[1] - R * 0.05); ctx.lineTo(c[0] + R * 0.05, c[1] + R * 0.4); ctx.lineWidth = 5; ctx.stroke();
    // a snowflake lands and melts (b92-93.4)
    if (b < 93.6) { const fu = clamp((b - 92) / 1.0); const fx = c[0] + 60, fy = lerp(-40, c[1] - 60, ease.out(fu)); const s = 26 * (1 - clamp((b - 93) / 0.6));
      ctx.save(); ctx.translate(fx, fy); ctx.rotate(t); ctx.strokeStyle = '#fff'; ctx.lineWidth = 5; for (let a = 0; a < 3; a++) { ctx.rotate(Math.PI / 3); ctx.beginPath(); ctx.moveTo(-s, 0); ctx.lineTo(s, 0); ctx.stroke(); } ctx.restore(); }
    glow.globalAlpha = heat; glow.beginPath(); glow.arc(c[0], c[1], R * (1.1 + pulse * 0.8 + flare * 2), 0, TAU); glow.fillStyle = P.orange; glow.fill(); glow.globalAlpha = 1;
    if (flare > 0) { for (let i = 0; i < 14; i++) { const a = i / 14 * TAU + 0.2, L = 2400 * flare, w = 0.04; pathPoly(ctx, [c, [c[0] + Math.cos(a - w) * L, c[1] + Math.sin(a - w) * L], [c[0] + Math.cos(a + w) * L, c[1] + Math.sin(a + w) * L]]); ctx.fillStyle = i % 2 ? P.yellow : P.orange; ctx.fill(); } }
  }
  hit(95, 'flash', 4);
}

// ============================================================== S11  IGNITION (96-104)
{
  const S = 560, G = 1010;
  const hero = new Actor({ face: 1, lean: 40, head: 30, wa: -90, wx: 0.15, wy: 0.1, g1: 0.6, two: 0, bside: 1, brow: 1,
    fx1: 0.3, fy1: 0.3, fx2: -0.2, fy2: 0.34, sq: 0.8, windx: 0, fire: 1 });
  hero.key(98, 'io', {});
  hero.key(100, 'io', { lean: 4, head: -8, sq: 1.02, fx1: 0.18, fy1: 0.48, fx2: -0.2, fy2: 0.48, wa: -100, wy: -0.05, mouth: 0 });
  hero.key(100.2, 'outx', { mouth: 1, head: -24 });
  hero.key(102, 'io', { mouth: 0.3, head: -10 });
  hero.over((t, p, root) => { root[0] = 960; root[1] = G - 0.48 * S + (1 - p.sq) * 0.5 * S; p.windy = -1.2; p.windx = 0.2 * Math.sin(t * 3); });
  shot(96, 104, 's11_ignite', (E) => {
    const { ctx, glow, t } = E;
    const b = t2b(t), tq = onN(t, 2);
    if (b < 98) {          // eye reprise: snap open with fire
      const open = b < 97 ? 0 : ease.outx(clamp((b - 97) / 0.15));
      ctx.fillStyle = '#000'; ctx.fillRect(0, 0, W, H);
      drawEye(ctx, glow, 960, 560, 600, { open, look: [0, 0], pupil: 0.45, fire: 1, t: tq, snow: 0, hairShift: 3 * clamp(b - 97) });
      if (b > 97) radialLines(ctx, 960, 560, onN(t, 1), 1.2, P.yellow, 6, 0.25, 0.6);
      return;
    }
    const age = t - b2t(98);
    const sh = shakeXY(t, 30 * hitDecay(t, 98, 4) + 6);
    ctx.save(); ctx.translate(sh[0], sh[1]); glow.save(); glow.translate(sh[0], sh[1]);
    // palette flip: black sky bleeding to magenta at the horizon
    const g = ctx.createLinearGradient(0, 0, 0, H); g.addColorStop(0, '#0a0206'); g.addColorStop(0.7, '#5a0a3c'); g.addColorStop(1, '#ff2e88');
    ctx.fillStyle = g; ctx.fillRect(-100, -100, W + 200, H + 200);
    radialLines(ctx, 960, 520, onN(t, 2), 0.9, '#3a0a28', 11, 0.1, 0.9);
    // melted crater floor
    ctx.fillStyle = '#2a0c24'; pathSmooth(ctx, [[-100, 960], [960, 1000], [2100, 960], [2100, 1200], [-100, 1200]]); ctx.fill();
    // steam ring blasting outward
    puffs(ctx, 960, G, age / 1.4, 99, 3.2, 'rgba(255,240,245,0.95)', 'rgba(230,170,200,0.9)', [1, -0.1], 0.5);
    puffs(ctx, 960, G, age / 1.4, 98, 3.2, 'rgba(255,240,245,0.95)', 'rgba(230,170,200,0.9)', [-1, -0.1], 0.5);
    ring(ctx, 960, G, age / 1.0, 1700, P.yellow, 0.18, 50, glow);
    const pose = hero.fn();
    const J = solve(pose(t).p, pose(t).root, S, G);
    // wings of fire unfold from the shoulders
    const wo = ease.back(clamp((b - 99.2) / 1.2));
    fireWings(ctx, glow, add(J.chest, [0, -10]), 820, wo, tq, Math.sin(t * 5) * 0.2);
    for (let i = 0; i < 8; i++) flame(ctx, 760 + i * 58, G, 90, 160 + 70 * Math.sin(i * 1.7 + t * 11), tq, i + 40, -Math.PI / 2, glow);
    drawHero(ctx, pose, tq, { S, ground: G, glow });
    ctx.restore(); glow.restore();
    embers(ctx, t, { n: 120, seed: 21, glow, rise: 3, size: 1.4 });
  });
  hit(97, 'flash', 3); hit(98, 'impact', 3); hit(98, 'flash', 5);
}

// ============================================================== S12  ascent (104-120)
{
  const S = 520;
  const hero = new Actor({ face: 1, rot: -80, lean: 10, head: -10, wa: 150, wx: -0.05, wy: 0.14, g1: 0.5, two: 0, bside: -1, brow: 1,
    fx1: 0.1, fy1: 0.5, fx2: -0.12, fy2: 0.46, gnd: 0, windx: 0, windy: 2.2, fire: 1 });
  // slashes at the tendrils: 108, 110, 112, 114, 116
  const CUTS = [108, 110, 112, 114, 116];
  CUTS.forEach((c, i) => {
    hero.key(c - 0.5, 'io', { wa: i % 2 ? -40 : 150, lean: 10 });
    hero.key(c, 'in2', { wa: i % 2 ? 150 : -40, lean: i % 2 ? 20 : -10, mouth: 0.8 });
    hero.key(c + 0.5, 'outx', { mouth: 0.1 });
  });
  hero.over((t, p, root) => { root[0] = 960; root[1] = 560 + 18 * Math.sin(t * 7); });
  const pose = hero.fn();
  shot(104, 120, 's12_ascent', (E) => {
    const { ctx, glow, t } = E;
    const b = t2b(t), tq = onN(t, 2);
    const spin = lerp(0, 1.7 * TAU, ease.io(clamp((b - 104) / 14)));            // rotating camera
    const climb = (t - b2t(104)) * 2600;                                         // world scroll
    const sh = shakeXY(t, 10 + CUTS.reduce((a, c) => a + 25 * hitDecay(t, c, 8), 0));
    ctx.save(); ctx.translate(960 + sh[0], 560 + sh[1]); ctx.rotate(spin); ctx.translate(-960, -560);
    glow.save(); glow.translate(960 + sh[0], 560 + sh[1]); glow.rotate(spin); glow.translate(-960, -560);
    // the King's flank as a black wall streaming downward, with eyes and fur spikes
    ctx.fillStyle = '#0a0612'; ctx.fillRect(-1200, -1200, W + 2400, H + 2400);
    const r = rng(404);
    for (let i = 0; i < 70; i++) {
      const x = -900 + r() * 3700, y0 = r() * 5000;
      const y = ((y0 + climb) % 5000) - 2000;
      const L = 200 + r() * 600;
      pathPoly(ctx, [[x - 30, y], [x + 30, y], [x + (r() - 0.5) * 80, y - L]]); ctx.fillStyle = i % 3 ? '#1b1236' : '#2a1f55'; ctx.fill();
    }
    for (let i = 0; i < 18; i++) {
      const x = -700 + r() * 3300, y0 = r() * 5000, y = ((y0 + climb * 0.9) % 5000) - 2000, s = 30 + r() * 40;
      ctx.beginPath(); ctx.ellipse(x, y, s, s * 0.3, 0, 0, TAU); ctx.fillStyle = P.voidEye; ctx.fill();
      glow.beginPath(); glow.arc(x, y, s * 1.3, 0, TAU); glow.fillStyle = P.voidEye; glow.fill();
    }
    // speed streaks along the flight direction (down the screen in world space)
    ctx.save(); ctx.translate(960, 560);
    const rr = rng(Math.floor(tq * 12));
    for (let i = 0; i < 50; i++) { const x = (rr() - 0.5) * 3000, y = (rr() - 0.5) * 3000, L = 300 + rr() * 900; ctx.fillStyle = i % 4 ? 'rgba(255,138,31,0.5)' : 'rgba(255,255,255,0.6)'; ctx.fillRect(x, y, 3 + rr() * 5, L); }
    ctx.restore();
    // tendrils lashing in, each cut on its beat
    CUTS.forEach((c, i) => {
      const age = t - b2t(c - 1.2);
      if (age < 0 || age > 2.2) return;
      const side = i % 2 ? 1 : -1;
      const u = clamp(age / 1.2);
      const start = [960 + side * 1500, 560 + 400 * Math.sin(i)], tip = [960 + side * lerp(1500, 60, ease.in2(u)), 560 - 40];
      const cut = t > b2t(c);
      const pts = [];
      for (let k = 0; k <= 12; k++) { const v = k / 12; pts.push(add(mix2(start, tip, v), [0, 120 * Math.sin(v * 6 + t * 8 + i)])); }
      const shown = cut ? pts.slice(0, 8) : pts;
      pathSmooth(ctx, taper(shown, 90, 6, 60), true, 0.6); ctx.fillStyle = P.void; ctx.fill(); ctx.lineWidth = 3; ctx.strokeStyle = P.voidRim; ctx.stroke();
      if (cut) {
        const ca = t - b2t(c);
        const piece = pts.slice(7).map((q) => add(q, [side * 400 * ca, 700 * ca * ca]));
        if (ca < 0.5) { ctx.globalAlpha = 1 - ca * 2; pathSmooth(ctx, taper(piece, 40, 4, 30), true, 0.6); ctx.fill(); ctx.globalAlpha = 1; }
        inkBurst(ctx, pts[7][0], pts[7][1], ca, 500 + i, 1.0, glow, [side, 0]);
      }
    });
    // fire trail beneath her
    for (let k = 0; k < 6; k++) flame(ctx, 960 + 20 * Math.sin(t * 9 + k), 700 + k * 80, 200 - k * 20, 380 - k * 30, tq + k * 0.2, k + 60, Math.PI / 2, glow);
    const J = solve(pose(t).p, pose(t).root, S, null);
    fireWings(ctx, glow, J.chest, 700, 1, tq, Math.sin(t * 6) * 0.3);
    // smear on each cut
    CUTS.forEach((c) => { const ca = t - b2t(c) + 0.08; if (ca > 0 && ca < 0.25) smearArc(ctx, J.chest[0], J.chest[1], 250, 560, -2.4, 0.6, glow, 1 - ca / 0.25); });
    drawHero(ctx, pose, (CUTS.some((c) => Math.abs(b - c) < 0.4)) ? onN(t, 1) : tq, { S, ground: null, glow });
    ctx.restore(); glow.restore();
    embers(ctx, t, { n: 80, seed: 33, glow, rise: 6, size: 1.2 });
  });
  [108, 110, 112, 114, 116].forEach((c, i) => hit(c, i % 2 ? 'flash' : 'impact', i % 2 ? 3 : 1));
}

// ============================================================== S13  apex (120-128)
{
  const S = 300;
  const hero = new Actor({ face: 1, lean: -6, head: -20, wa: 100, wx: 0.0, wy: -0.28, g1: 0.25, g2: 0.55, two: 1, bside: -1, brow: 1,
    fx1: 0.12, fy1: 0.44, fx2: -0.14, fy2: 0.42, gnd: 0, windx: 0, windy: 0.6, fire: 1 });
  hero.key(120, 'io', {});
  hero.key(126.5, 'io', { wa: 118, wy: -0.34, lean: -12 });            // slowly raises the blade higher
  hero.key(127.6, 'io', { wa: 150, lean: -26, wy: -0.3, sq: 1.04 });      // the wind-up
  hero.over((t, p, root) => { root[0] = 960; root[1] = 440 + 8 * Math.sin(t * 1.3); });
  shot(120, 128, 's13_apex', (E) => {
    const { ctx, glow, t } = E;
    const b = t2b(t), tq = onN(t, 3);
    const slow = (t - b2t(120)) * 0.15;                   // time crawls
    ctx.fillStyle = '#050207'; ctx.fillRect(0, 0, W, H);
    moon(ctx, 960, 420, 360, { ring: 1, glow, t });
    // corona rays
    const rr = rng(3);
    for (let i = 0; i < 40; i++) { const a = rr() * TAU, w = 0.01 + rr() * 0.02, L = 420 + rr() * 500; ctx.fillStyle = i % 2 ? 'rgba(255,138,31,0.35)' : 'rgba(255,46,136,0.3)'; pathPoly(ctx, [[960 + Math.cos(a) * 370, 420 + Math.sin(a) * 370], [960 + Math.cos(a - w) * L, 420 + Math.sin(a - w) * L], [960 + Math.cos(a + w) * L, 420 + Math.sin(a + w) * L]]); ctx.fill(); }
    // the King's head below, looking up, eyes fixed on her
    drawKing(ctx, glow, 960, 1160, 420, 1, 60 + slow);
    const pose = hero.fn();
    const J = solve(pose(t).p, pose(t).root, S, null);
    fireWings(ctx, glow, J.chest, 520, 1, 60 + slow * 2, 0.1 * Math.sin(slow * 4));
    drawHero(ctx, pose, tq, { S, ground: null, glow });
    embers(ctx, 40 + slow, { n: 90, seed: 44, glow, rise: 0.4, size: 1.3 });
    bars(ctx, clamp((b - 120) / 1));
  });
}

// ============================================================== S14  the cut (128-136)
{
  shot(128, 136, 's14_cut', (E) => {
    const { ctx, glow, t } = E;
    const b = t2b(t), tq = onN(t, 2);
    const cutA = -0.35;
    const lineU = ease.outx(clamp((b - 128) / 0.35));
    const split = ease.in2(clamp((b - 129) / 3)) * 260;
    const sh = shakeXY(t, 40 * hitDecay(t, 129, 3));
    ctx.save(); ctx.translate(sh[0], sh[1]); glow.save(); glow.translate(sh[0], sh[1]);
    if (b >= 131) {            // aftermath: the King is ash; the eclipse ring breaks into light
      const a = t - b2t(131);
      const g = ctx.createLinearGradient(0, 0, 0, H); g.addColorStop(0, '#120822'); g.addColorStop(1, lerp(0, 1, clamp(a / 2)) > 0.5 ? '#6a2a5a' : '#2a0c34');
      ctx.fillStyle = g; ctx.fillRect(-200, -200, W + 400, H + 400);
      // light through the broken ring
      const rc = [960, 300];
      for (let i = 0; i < 12; i++) {
        const ang = i / 12 * TAU + 0.15, sp = 380 + 700 * ease.out(clamp(a / 2.5));
        const p0 = [rc[0] + Math.cos(ang) * sp, rc[1] + Math.sin(ang) * sp];
        ctx.save(); ctx.translate(...p0); ctx.rotate(ang + Math.PI / 2 + a * 0.6 * (i % 2 ? 1 : -1));
        ctx.fillStyle = '#fff4e0'; ctx.globalAlpha = 1 - clamp(a / 3); ctx.fillRect(-90, -10, 180, 20); ctx.restore(); ctx.globalAlpha = 1;
      }
      glow.beginPath(); glow.arc(...rc, 180 + 160 * clamp(a / 2), 0, TAU); glow.fillStyle = '#ffb36b'; glow.globalAlpha = 0.25; glow.fill(); glow.globalAlpha = 1;
      ctx.beginPath(); ctx.arc(...rc, 120 + 80 * clamp(a / 2), 0, TAU); ctx.fillStyle = '#fff3cf'; ctx.fill();
      // the King's halves, dissolving upward into embers and ash
      ctx.save(); ctx.globalAlpha = 1 - clamp(a / 3.5);
      for (const side of [1, -1]) {
        ctx.save(); ctx.translate(960, 540); ctx.rotate(cutA);
        ctx.beginPath(); ctx.rect(-3000, side > 0 ? -3000 : 0, 6000, 3000); ctx.clip();
        ctx.rotate(-cutA); ctx.translate(-960, -540); ctx.translate(side * (260 + a * 120), side * 80 + a * 60);
        drawKing(ctx, null, 960, 560, 400, 1, 60, 0);
        ctx.restore();
      }
      ctx.restore();
      const r = rng(13);
      for (let i = 0; i < 160; i++) { const x = 400 + r() * 1100, y0 = 300 + r() * 700, y = y0 - a * (150 + r() * 250); const s2 = 4 + r() * 8;
        ctx.fillStyle = r() > 0.4 ? P.orange : '#1a1030'; ctx.globalAlpha = clamp(1 - a / 4.5); ctx.fillRect(x + Math.sin(a * 2 + i) * 30, y, s2, s2); }
      ctx.globalAlpha = 1;
      ctx.restore(); glow.restore();
      embers(ctx, t, { n: 80, seed: 56, glow, rise: 1.5, size: 1.2 });
      return;
    }
    const drawWorld = () => {
      ctx.fillStyle = '#050207'; ctx.fillRect(-200, -200, W + 400, H + 400);
      moon(ctx, 960, 300, 300, { ring: 1, glow, t });
      drawKing(ctx, glow, 960, 560, 400, 1, 60, b > 129.5 ? 0 : 999);
      ctx.fillStyle = '#2a0c24'; ctx.fillRect(-200, 1000, W + 400, 300);
    };
    // two halves sliding apart along the cut
    const n = [Math.sin(cutA), -Math.cos(cutA)];
    for (const side of [1, -1]) {
      ctx.save(); ctx.translate(960, 540); ctx.rotate(cutA);
      ctx.beginPath(); ctx.rect(-3000, side > 0 ? -3000 : 0, 6000, 3000); ctx.clip();
      ctx.rotate(-cutA); ctx.translate(-960, -540);
      ctx.translate(side * n[0] * split * 0.3 + side * split * 0.8 * Math.cos(cutA), side * n[1] * split * 0.3 + side * split * 0.8 * Math.sin(cutA) + (side < 0 ? split * 0.6 : 0));
      drawWorld();
      ctx.restore();
    }
    // light pouring through the seam
    const seamW = 6 + split * 1.4;
    ctx.save(); ctx.translate(960, 540); ctx.rotate(cutA);
    const gg = ctx.createLinearGradient(0, -seamW, 0, seamW); gg.addColorStop(0, 'rgba(255,216,74,0)'); gg.addColorStop(0.5, '#fff6dc'); gg.addColorStop(1, 'rgba(255,216,74,0)');
    ctx.fillStyle = gg; ctx.fillRect(-2400 * lineU, -seamW, 4800 * lineU, seamW * 2);
    ctx.restore();
    glow.save(); glow.translate(960, 540); glow.rotate(cutA); glow.fillStyle = P.yellow; glow.fillRect(-2400 * lineU, -seamW * 2, 4800 * lineU, seamW * 4); glow.restore();
    ctx.restore(); glow.restore();
    if (b > 129 && b < 131) radialLines(ctx, 960, 540, onN(t, 1), 1.4, '#fff6dc', 7, 0.1, 0.7);
    embers(ctx, t, { n: 100, seed: 55, glow, rise: 2, size: 1.3 });
  });
  hit(128, 'impact', 2); hit(129, 'impact', 1); hit(129.2, 'flash', 4); hit(131, 'white', 6);
}

// ============================================================== S15  dawn (136-160)
{
  const S = 520, G = 960;
  const hero = new Actor({ face: -1, lean: 36, head: 10, wa: 190, wx: -0.1, wy: 0.1, g1: 0.4, two: 0, bside: 1, fx1: 0.34, fy1: 0.34, fx2: -0.38, fy2: 0.4,
    sq: 0.82, gnd: 1, windx: 0.4, fire: 0 });
  hero.key(136, 'io', {});
  hero.key(138.5, 'io', { lean: 6, head: -2, sq: 1.0, fx1: 0.14, fy1: 0.49, fx2: -0.16, fy2: 0.49, wa: 215, wx: -0.04, wy: -0.04, g1: 0.55, bside: -1 });   // rises, blade over the shoulder
  hero.key(144, 'io', { wa: 215 });
  hero.key(145, 'io', { wa: 250, g1: 0.5 });
  hero.key(146, 'step', {});
  hero.key(146.4, 'outx', { unfold: 0.5 });
  hero.key(147.2, 'outx', { unfold: 0 });
  hero.key(148.4, 'io', { held: 0, h1x: 0.03, h1y: 0.17, hx: -0.02, hy: 0.17 });
  hero.key(150, 'io', { head: 0 });
  hero.key(152.5, 'io', { head: -16, eye: 0.35, mouth: 0 });                  // tilts up to the sun, eyes soften
  hero.over((t, p, root) => { root[0] = 1500; root[1] = G - 0.49 * S + (1 - p.sq) * 0.5 * S; p.windx = 0.5 + 0.2 * Math.sin(t); });
  const burnt = new Forest(61, 26, [-200, 2200], 900, 200, 380, { base: '#6a3a5c', shade: '#4a2448', snow: '#ffd6c8' }, 0);
  shot(136, 160, 's15_dawn', (E) => {
    const { ctx, glow, t } = E;
    const b = t2b(t), tq = onN(t, 3);
    if (b >= 145 && b < 152) {           // close: her profile in the sunrise; she closes her eyes and smiles
      const u = clamp((b - 145) / 7);
      const g2 = ctx.createLinearGradient(0, 0, 0, H); g2.addColorStop(0, P.dawn1); g2.addColorStop(1, P.dawn0);
      ctx.fillStyle = g2; ctx.fillRect(0, 0, W, H);
      const sun2 = [300, 720]; glow.beginPath(); glow.arc(...sun2, 600, 0, TAU); glow.fillStyle = '#ffb36b'; glow.globalAlpha = 0.5; glow.fill(); glow.globalAlpha = 1;
      ctx.beginPath(); ctx.arc(...sun2, 260, 0, TAU); ctx.fillStyle = P.sun; ctx.fill();
      const eyeK = [[145, 1], [147.5, 1], [148.3, 0.05], [152, 0.05]];
      let eo = 1; for (let i = 1; i < eyeK.length; i++) if (b < eyeK[i][0]) { eo = lerp(eyeK[i - 1][1], eyeK[i][1], ease.io(clamp((b - eyeK[i - 1][0]) / (eyeK[i][0] - eyeK[i - 1][0])))); break; } else eo = eyeK[i][1];
      const Sc = 3000;
      const cp = () => ({ p: { ...hero.tr.d, face: -1, held: 0, unfold: 0, two: 0, lean: 2, head: lerp(-6, -18, ease.io(u)), eye: eo,
        smile: ease.io(clamp((b - 148.5) / 1.5)), windx: 0.8 + 0.3 * Math.sin(t), h1x: 0.03, h1y: 0.17, hx: -0.02, hy: 0.17, fx1: 0.05, fy1: 0.5, fx2: -0.05, fy2: 0.5 },
        root: [1250 + 40 * u, 1080 + 0.2 * Sc - 360] });
      drawHero(ctx, cp, onN(t, 2), { S: Sc, ground: null, glow, light: [-0.7, -0.6] });
      embers(ctx, t, { n: 70, seed: 67, glow, rise: -0.6, size: 1.6, alpha: 0.9 });
      return;
    }
    const rise = ease.out(clamp((b - 136) / 20));
    const g = ctx.createLinearGradient(0, 0, 0, 960);
    g.addColorStop(0, '#3a2a70'); g.addColorStop(0.45, P.dawn1); g.addColorStop(0.8, P.dawn0); g.addColorStop(1, '#fff1d6');
    ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
    // the sun
    const sun = [560, lerp(900, 640, rise)];
    glow.beginPath(); glow.arc(...sun, 360, 0, TAU); glow.fillStyle = '#ffb36b'; glow.globalAlpha = 0.6; glow.fill(); glow.globalAlpha = 1;
    ctx.beginPath(); ctx.arc(...sun, 150, 0, TAU); ctx.fillStyle = P.sun; ctx.fill();
    // sun rays (Promare triangles)
    const rr = rng(8);
    for (let i = 0; i < 16; i++) { const a = -Math.PI + (i / 15) * Math.PI, w = 0.03, L = 1600; ctx.fillStyle = 'rgba(255,243,207,0.18)'; pathPoly(ctx, [sun, [sun[0] + Math.cos(a - w) * L, sun[1] + Math.sin(a - w) * L], [sun[0] + Math.cos(a + w) * L, sun[1] + Math.sin(a + w) * L]]); ctx.fill(); }
    burnt.draw(ctx, 0, 0);
    ctx.fillStyle = '#ffe6dc'; ctx.fillRect(0, G - 8, W, H);
    ctx.fillStyle = '#f2bfb8'; pathSmooth(ctx, [[0, G + 40], [900, G + 20], [1920, G + 60], [1920, H], [0, H]]); ctx.fill();
    // landing impact puff at the start
    if (b < 139) puffs(ctx, 1500, G, (t - b2t(136)) / 1.3, 610, 1.6, '#fff4ee', '#f0c4c0', [0, -1], 2);
    const pose = hero.fn();
    drawHero(ctx, pose, tq, { S, ground: G, glow, light: [0.6, -0.8] });
    // smouldering hem
    const J = solve(pose(t).p, pose(t).root, S, G);
    for (let i = 0; i < 4; i++) flame(ctx, J.pelvis[0] + 60 + i * 26, J.pelvis[1] + 0.3 * S, 24, 40 + 14 * Math.sin(t * 7 + i), tq, i + 90, -Math.PI / 2, glow);
    // embers falling like snow
    embers(ctx, t, { n: 110, seed: 66, glow, rise: -0.5, size: 1.1, alpha: 0.9 });
    // title
    const tu = clamp((b - 150) / 3);
    if (tu > 0) {
      const e = ease.out(tu);
      ctx.save(); ctx.globalAlpha = e;
      ctx.font = '600 150px Futura'; ctx.fillStyle = '#2e1236';
      const word = 'EMBER', track = 60 * (1.3 - 0.3 * e);
      let x = 1000; for (const ch of word) { ctx.fillText(ch, x, 220); x += ctx.measureText(ch).width + track; }
      ctx.fillStyle = P.cloak; ctx.fillRect(1000, 250, (x - track - 1000) * e, 5);
      ctx.font = '500 58px "Hiragino Sans"'; ctx.fillStyle = '#2e1236'; ctx.fillText('点火', 1000, 330);
      ctx.font = '500 40px Futura'; ctx.fillText('I I I  ·  K I N D L E', 1150, 322);
      ctx.restore();
      glow.save(); glow.globalAlpha = 0.4 * e; glow.font = '600 150px Futura'; glow.fillStyle = P.orange;
      glow.restore();
    }
  });
  hit(136.2, 'flash', 3);
}
