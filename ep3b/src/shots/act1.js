// S1-S6: quiet -> wrong -> the tide -> ready -> GO.
import { W, H, b2t, t2b, lerp, clamp, ease, onN, TAU, rng, add, mul, rot, pathPoly, pathSmooth, taper, fbm, noise1, sub, norm, len } from '../engine.js';
import { P } from '../palette.js';
import { shot, hit } from '../film.js';
import { Actor } from '../actor.js';
import { drawHero, solve } from '../hero.js';
import { drawWolf } from '../wolf.js';
import { night, eyePairs, voidMass, HT } from '../scene.js';
import { drawEye } from '../eye.js';
import { embers, snowfall, cracks, puffs, radialLines, streakLines, ring, muzzle, flame } from '../fx.js';

// ---------------------------------------------------------------- S1  moon clearing (0-12)
const idle = new Actor({ held: 0, unfold: 0, two: 0, h1x: 0.03, h1y: 0.17, hx: -0.02, hy: 0.17, head: 14, lean: 2,
  fx1: 0.05, fy1: 0.5, fx2: -0.07, fy2: 0.5, windx: -0.9 });
idle.over((t, p) => { p.sq = 1 + 0.008 * Math.sin(t * 2.1); });          // breathing
idle.key(0, 'io', { head: 14 }).key(9.5, 'io', { head: 14 }).key(11.2, 'out', { head: -4 });
shot(0, 12, 's01_moon', (E) => {
  const { ctx, glow, t, u } = E;
  const z = lerp(1.0, 1.1, ease.io(u));
  night(ctx, glow, t, { zoom: z, moonXY: [980, 360], moonR: 300, camx: -40 * u });
  ctx.save(); ctx.translate(W / 2, H / 2); ctx.scale(z, z); ctx.translate(-W / 2, -H / 2);
  glow.save(); glow.translate(W / 2, H / 2); glow.scale(z, z); glow.translate(-W / 2, -H / 2);
  // tiny heroine on a snow rise, backlit by the moon
  ctx.fillStyle = P.snow; pathSmooth(ctx, [[600, 905], [880, 862], [1180, 880], [1400, 915], [1400, 1100], [600, 1100]]); ctx.fill();
  drawHero(ctx, (tt) => idle.pose(tt).p ? { p: idle.pose(tt).p, root: [960, 862 - 0.5 * 170] } : null, onN(t, 3), { S: 170, ground: 866, glow });
  // scorch + burnt stubs from the last fight
  ctx.fillStyle = '#4c4f9a'; pathSmooth(ctx, [[380, 960], [560, 940], [700, 975], [520, 995]]); ctx.fill();
  ctx.restore(); glow.restore();
  embers(ctx, t, { n: 70, seed: 3, region: [0, 0, W, H], rise: 1, glow, size: 1.1 });
  snowfall(ctx, t, { n: 90, speed: 35, wind: -25, size: 0.9, alpha: 0.7 });
});

// ---------------------------------------------------------------- S2  ECU eye (12-20)
shot(12, 20, 's02_eye', (E) => {
  const { ctx, glow, t, lt } = E;
  const b = t2b(t);
  // lid acting: closed -> flutter half -> close -> SNAP open (b16) -> saccade right (b18)
  const lidKeys = [[12, 0], [13.6, 0], [14.2, 0.32], [14.5, 0.22], [14.9, 0.0], [15.8, 0.0], [16.0, 1.0], [20, 1.0]];
  let open = 0;
  for (let i = 1; i < lidKeys.length; i++) if (b < lidKeys[i][0]) { const [b0, v0] = lidKeys[i - 1], [b1, v1] = lidKeys[i]; open = lerp(v0, v1, ease.io(clamp((b - b0) / (b1 - b0)))); break; } else open = lidKeys[i][1];
  const lookX = b < 18 ? 0 : lerp(0, 0.75, ease.outx(clamp((b - 18) / 0.35)));
  const pupil = b < 16 ? 1 : lerp(1.2, 0.55, ease.outx(clamp((b - 16) / 0.8)));
  const push = lerp(1.0, 1.06, lt / 3.2);
  ctx.save(); ctx.translate(W / 2, H / 2); ctx.scale(push, push); ctx.translate(-W / 2, -H / 2);
  drawEye(ctx, glow, 930, 560, 560, { open: onN(open, 1), look: [lookX, 0], pupil, t, hairShift: Math.sin(t * 1.1) });
  ctx.restore();
  // breath vapour on the snap
  if (b > 16) puffs(ctx, 1500, 1050, (b - 16) * 0.4 / 1.3, 9, 1.6, 'rgba(235,238,255,0.8)', 'rgba(170,176,230,0.6)', [1, -0.4], 0.6);
  snowfall(ctx, t, { n: 50, speed: 30, wind: -30, size: 2.5, alpha: 0.85 });
  if (b > 18) radialLines(ctx, W * 0.75, H * 0.5, onN(t, 2), 0.5 * (1 - clamp((b - 18) / 1.2)), '#ffffff', 2, 0.25, 0.5);
});
hit(16, 'flash', 2);

// ---------------------------------------------------------------- S3  eclipse + cracks + eyes (20-28)
const eyesS3 = [];
{ const r = rng(33); for (let i = 0; i < 30; i++) eyesS3.push({ x: 120 + r() * 1680, y: 690 + r() * 90, gap: 26 + r() * 14, s: 10 + r() * 6, t: b2t(22 + Math.floor(r() * 5) + (r() < 0.3 ? 0.5 : 0)) }); }
shot(20, 28, 's03_eclipse', (E) => {
  const { ctx, glow, t, u } = E;
  const b = t2b(t);
  const bite = ease.in2(clamp((b - 20) / 7)) * 0.62;
  night(ctx, glow, t, { moonXY: [960, 300], moonR: 260, bite, drain: clamp((b - 24) / 4) * 0.6 });
  // treeline darkness band where eyes open
  const dark = clamp((b - 21) / 3);
  ctx.fillStyle = `rgba(6,5,16,${0.75 * dark})`; ctx.fillRect(0, 640, W, 190);
  eyePairs(ctx, glow, eyesS3, t);
  // cracks racing across the snow toward the camera
  if (b > 24) cracks(ctx, 960, 830, (b - 24) / 3, 7, 1400, glow, Math.PI / 2, 2.4);
  // her silhouette, small, turning to look (face flips on 25)
  const face = b < 25 ? 1 : -1;
  drawHero(ctx, () => ({ p: { ...idle.tr.d, held: 0, unfold: 0, two: 0, h1x: 0.03, h1y: 0.17, hx: -0.02, hy: 0.17, face, head: -4, windx: -1.2, fx1: 0.05, fy1: 0.5, fx2: -0.07, fy2: 0.5 }, root: [1000, 930 - 0.5 * 210] }), onN(t, 2), { S: 210, ground: 935, glow });
  embers(ctx, t, { n: 30, seed: 4, glow, alpha: 0.6 * (1 - dark) });
  snowfall(ctx, t, { n: 70, speed: 30, wind: -25 });
});


// ---------------------------------------------------------------- S4  the tide (28-36)
const TIDE = [];
{ const r = rng(44); for (let i = 0; i < 38; i++) { const d = r(); TIDE.push({ d, x0: -400 - r() * 1800 * (1 - d * 0.5), y: lerp(700, 1020, d), s: lerp(90, 380, d * d), spd: lerp(500, 1300, d) * (0.85 + 0.3 * r()), seed: i, ph: r(), start: 28 + r() * 3 }); } TIDE.sort((a, b) => a.d - b.d); }
const heroS4 = new Actor({ held: 0, unfold: 0, two: 0, face: -1, lean: 10, head: -6, h1x: 0.03, h1y: 0.17, hx: -0.02, hy: 0.17,
  fx1: 0.2, fy1: 0.48, fx2: -0.18, fy2: 0.48, windx: 1.5, brow: 1 });
shot(28, 36, 's04_tide', (E) => {
  const { ctx, glow, t, u } = E;
  const b = t2b(t);
  const sh = 6 * clamp((b - 29) / 3);
  ctx.save(); ctx.translate(sh * fbm(t * 30), sh * fbm(t * 30 + 9));
  night(ctx, glow, t, { moonXY: [1450, 230], moonR: 180, bite: 0.62, drain: 0.6, horizon: 600, snowY: 820 });
  // ink flood welling out of the treeline (left), with eyes
  const fl = clamp((b - 28) / 5);
  const flood = [[-50, 640], [lerp(-50, 500, fl), 610 + 20 * Math.sin(t * 3)], [lerp(0, 820, fl), 700 + 15 * Math.sin(t * 4 + 1)],
    [lerp(0, 1000, fl), 860], [lerp(0, 700, fl), 1000], [-50, 1000]];
  pathSmooth(ctx, flood); ctx.fillStyle = P.void; ctx.fill(); ctx.lineWidth = 3; ctx.strokeStyle = P.voidRim; ctx.stroke();
  // the pack
  for (const w of TIDE) {
    const tt = t - b2t(w.start);
    if (tt < 0) continue;
    const x = w.x0 + w.spd * tt;
    if (x > W + 400) continue;
    drawWolf(ctx, { x, y: w.y - 0.4 * w.s, s: w.s, face: 1, phase: onN(t, 2) * 2.6 + w.ph, mode: 'run', t: onN(t, 2), seed: w.seed, jaw: 0.4 }, glow);
    if (w.d > 0.5) puffs(ctx, x - w.s * 0.5, w.y, (t * 2.5 + w.ph) % 1, w.seed * 5 + Math.floor(t * 2.5), w.s / 500, P.snow, P.snowS, [-1, -0.5], 0.6);
  }
  // her, right foreground, back 3/4 to camera (side rig facing left), bracing
  const S = 520;
  drawHero(ctx, heroS4.fn(), onN(t, 2), { S, ground: 1040, glow });
  ctx.restore();
  snowfall(ctx, t * 1.6, { n: 90, speed: 50, wind: -300, size: 1.3 });
});
// her root for S4
heroS4.over((t, p, root) => { root[0] = 1580; root[1] = 1040 - 0.48 * 520; });

// ---------------------------------------------------------------- S5  weapon inserts (36-40)
function shaftInsert(ctx, glow, t, lt) {           // click: telescoping shaft
  ctx.fillStyle = P.sky1; ctx.fillRect(0, 0, W, H);
  radialLines(ctx, W * 0.1, H * 0.5, onN(t, 1), 0.8, '#3a3a8a', 1, 0.15, 1);
  const ext = ease.outx(clamp(lt / 0.12));
  ctx.save(); ctx.translate(W / 2, H / 2); ctx.rotate(-0.18);
  const segs = [[-1100, -300, 70], [-300, lerp(-300, 500, ext), 58], [lerp(-300, 500, ext), lerp(-300, 1300, ext), 48]];
  segs.forEach(([x0, x1, h], i) => {
    ctx.fillStyle = P.shaft; ctx.fillRect(x0, -h / 2, x1 - x0, h);
    ctx.fillStyle = P.shaftS; ctx.fillRect(x0, h * 0.1, x1 - x0, h * 0.4);
    ctx.fillStyle = P.stripe; ctx.fillRect(x0, -h * 0.28, x1 - x0, h * 0.1);
    ctx.lineWidth = 5; ctx.strokeStyle = P.line; ctx.strokeRect(x0, -h / 2, x1 - x0, h);
    ctx.fillStyle = P.steel; ctx.fillRect(x1 - 26, -h / 2 - 8, 26, h + 16); ctx.strokeRect(x1 - 26, -h / 2 - 8, 26, h + 16);
  });
  // gloved fist
  ctx.fillStyle = P.suit; pathSmooth(ctx, [[-760, -110], [-520, -120], [-470, 0], [-520, 120], [-760, 110], [-800, 0]]); ctx.fill();
  ctx.lineWidth = 6; ctx.strokeStyle = P.line; ctx.stroke();
  for (let i = 0; i < 4; i++) { ctx.beginPath(); ctx.moveTo(-730 + i * 55, -110); ctx.lineTo(-730 + i * 55, 110); ctx.lineWidth = 4; ctx.stroke(); }
  ctx.restore();
  if (lt < 0.15) { ctx.fillStyle = `rgba(255,255,255,${0.7 * (1 - lt / 0.15)})`; ctx.fillRect(0, 0, W, H); }
}
function bladeInsert(ctx, glow, t, lt) {           // clack: blade swings out and locks
  ctx.fillStyle = '#1f1d55'; ctx.fillRect(0, 0, W, H);
  const hinge = [700, 620];
  const a = lerp(-0.1, -1.75, ease.back(clamp(lt / 0.16)));
  // shaft
  ctx.save(); ctx.translate(...hinge); ctx.rotate(0.1);
  ctx.fillStyle = P.shaft; ctx.fillRect(-900, -38, 900, 76); ctx.fillStyle = P.stripe; ctx.fillRect(-900, -18, 900, 8);
  ctx.lineWidth = 6; ctx.strokeStyle = P.line; ctx.strokeRect(-900, -38, 900, 76);
  ctx.restore();
  // smear of the swing
  if (lt < 0.2) {
    ctx.save(); ctx.translate(...hinge);
    ctx.beginPath(); ctx.arc(0, 0, 1050, -0.1, a, true); ctx.arc(0, 0, 780, a, -0.1); ctx.closePath();
    ctx.fillStyle = `rgba(255,216,74,${0.8 * (1 - lt / 0.2)})`; ctx.fill(); ctx.restore();
  }
  // blade
  ctx.save(); ctx.translate(...hinge); ctx.rotate(a);
  const bl = [];
  for (let i = 0; i <= 16; i++) { const s = i / 16; bl.push([s * 1100, -s * s * 260]); }
  const poly = taper(bl, 150, 4, 120);
  pathSmooth(ctx, poly, true, 0.6); ctx.fillStyle = P.blade; ctx.fill();
  ctx.save(); pathSmooth(ctx, poly, true, 0.6); ctx.clip(); ctx.translate(0, 40); pathSmooth(ctx, poly, true, 0.6); ctx.fillStyle = P.bladeS; ctx.fill(); ctx.restore();
  pathSmooth(ctx, poly, true, 0.6); ctx.lineWidth = 7; ctx.strokeStyle = P.line; ctx.stroke();
  ctx.beginPath(); bl.forEach((q, i) => (i ? ctx.lineTo(q[0], q[1] + 55 * (1 - i / 16)) : ctx.moveTo(q[0], q[1] + 55))); ctx.lineWidth = 8; ctx.strokeStyle = P.edge; ctx.stroke();
  glow.save(); glow.translate(...hinge); glow.rotate(a); glow.beginPath(); bl.forEach((q, i) => (i ? glow.lineTo(q[0], q[1] + 55 * (1 - i / 16)) : glow.moveTo(q[0], q[1] + 55))); glow.lineWidth = 24; glow.strokeStyle = P.orange; glow.stroke(); glow.restore();
  // glint travelling along the edge after the lock
  if (lt > 0.18) { const gu = clamp((lt - 0.18) / 0.3); const q = bl[Math.floor(gu * 16)]; star(ctx, q[0], q[1] + 50, 90 * Math.sin(gu * Math.PI)); }
  ctx.restore();
  // hinge bolt
  ctx.beginPath(); ctx.arc(...hinge, 48, 0, TAU); ctx.fillStyle = P.steel; ctx.fill(); ctx.lineWidth = 6; ctx.strokeStyle = P.line; ctx.stroke();
}
function star(ctx, x, y, s) {
  if (s <= 1) return;
  ctx.save(); ctx.translate(x, y); ctx.fillStyle = '#fff';
  pathPoly(ctx, [[0, -s], [s * 0.12, -s * 0.12], [s, 0], [s * 0.12, s * 0.12], [0, s], [-s * 0.12, s * 0.12], [-s, 0], [-s * 0.12, -s * 0.12]]); ctx.fill();
  ctx.restore();
}
function chamberInsert(ctx, glow, t, lt) {         // chamber: bolt racks, round seats
  ctx.fillStyle = P.sky0; ctx.fillRect(0, 0, W, H);
  radialLines(ctx, W * 0.5, H * 0.5, onN(t, 2), 0.6, '#262466', 4, 0.2, 1);
  const rack = lt < 0.12 ? ease.outx(lt / 0.12) : 1 - ease.back(clamp((lt - 0.2) / 0.14));
  ctx.save(); ctx.translate(W / 2 - 60, H / 2); ctx.rotate(-0.08);
  // receiver
  ctx.fillStyle = P.shaft; ctx.fillRect(-700, -170, 1400, 340); ctx.fillStyle = P.shaftS; ctx.fillRect(-700, 40, 1400, 130);
  ctx.lineWidth = 8; ctx.strokeStyle = P.line; ctx.strokeRect(-700, -170, 1400, 340);
  // ejection port
  ctx.fillStyle = '#05040c'; ctx.fillRect(-260, -120, 520, 150);
  // round
  const rx = lerp(-200, 40, clamp((lt - 0.2) / 0.14));
  ctx.fillStyle = '#e0a53a'; ctx.fillRect(rx - 150, -95, 300, 100); ctx.fillStyle = '#b8781c'; ctx.fillRect(rx - 150, -30, 300, 35);
  ctx.fillStyle = '#c9c9d6'; ctx.beginPath(); ctx.moveTo(rx + 150, -95); ctx.lineTo(rx + 230, -45); ctx.lineTo(rx + 150, 5); ctx.fill();
  // bolt handle
  const bx = lerp(0, -330, rack);
  ctx.fillStyle = P.steel; ctx.fillRect(bx - 330, -150, 330, 70); ctx.lineWidth = 6; ctx.strokeRect(bx - 330, -150, 330, 70);
  ctx.beginPath(); ctx.arc(bx - 60, -210, 60, 0, TAU); ctx.fill(); ctx.stroke();
  ctx.fillRect(bx - 80, -210, 40, 90);
  ctx.fillStyle = P.stripe; ctx.fillRect(-700, 120, 1400, 18);
  ctx.restore();
  if (lt > 0.33 && lt < 0.45) { ctx.fillStyle = 'rgba(255,255,255,0.5)'; ctx.fillRect(0, 0, W, H); }
}
shot(36, 40, 's05_insert', (E) => {
  const { ctx, glow, t } = E;
  const b = t2b(t);
  if (b < 37) shaftInsert(ctx, glow, t, t - b2t(36));
  else if (b < 38) bladeInsert(ctx, glow, t, t - b2t(37));
  else chamberInsert(ctx, glow, t, t - b2t(38));
});

// ---------------------------------------------------------------- S6  launch (40-44)
const S6 = 620, G6 = 1000;
const launch = new Actor({ face: 1, lean: 28, wa: 160, wx: -0.05, wy: 0.14, g1: 0.62, two: 0, bside: -1, brow: 1,
  fx1: 0.3, fy1: 0.4, fx2: -0.36, fy2: 0.42, windx: -0.8, head: -8 });
launch.key(40, 'io', { lean: 28 });
launch.key(41.6, 'io', { lean: 44, fx1: 0.34, fy1: 0.3, fx2: -0.42, fy2: 0.33, head: -14, sq: 0.9 });   // sink / coil
launch.key(42.9, 'io', { lean: 52, fx1: 0.36, fy1: 0.26, fx2: -0.46, fy2: 0.3, sq: 0.84, mouth: 0.0 });
launch.key(43.0, 'outx', { lean: 58, sq: 1.18, fx1: 0.2, fy1: 0.42, fx2: -0.55, fy2: 0.38, mouth: 0.9 });   // release!
launch.over((t, p, root) => {
  const b = t2b(t);
  root[0] = 700; root[1] = G6 - 0.47 * S6;
  if (b > 41) root[1] += ease.io(clamp((b - 41) / 1.9)) * 0.12 * S6;
  if (b > 43) { const tt = t - b2t(43); root[0] += 5200 * tt * tt + 2600 * tt; root[1] -= 120 * Math.sin(Math.min(1, tt * 5)); }
});
shot(40, 44, 's06_launch', (E) => {
  const { ctx, glow, t } = E;
  const b = t2b(t);
  const coil = clamp((b - 41) / 2);
  const sh = b > 43 ? 18 * Math.exp(-(t - b2t(43)) * 6) : 3 * coil;
  ctx.save(); ctx.translate(sh * fbm(t * 40), sh * fbm(t * 40 + 5));
  night(ctx, glow, t, { moonXY: [1500, 240], moonR: 170, bite: 0.62, drain: 0.6, horizon: 620, snowY: 870 });
  // the tide approaching in the distance (right)
  for (let i = 0; i < 14; i++) drawWolf(ctx, { x: 1300 + i * 70 + ((i * 37) % 60), y: 820 + (i % 3) * 18, s: 70 + (i % 4) * 8, face: -1, phase: onN(t, 2) * 2.6 + i * 0.3, mode: 'run', t: onN(t, 2), seed: i + 50 }, glow);
  // ground cracks under her as she coils
  if (coil > 0) cracks(ctx, 740, G6 - 5, coil * 0.7 + (b > 43 ? 0.3 : 0), 12, 700, glow, 0, TAU);
  const pose = launch.fn();
  if (b > 43) {           // afterimages on the launch
    for (let k = 3; k >= 1; k--) { ctx.globalAlpha = 0.25 * (1 - k / 4); drawHero(ctx, pose, t - k * 0.03, { S: S6, ground: G6 }); }
    ctx.globalAlpha = 1;
    puffs(ctx, 700, G6, (t - b2t(43)) / 0.9, 21, 2.6, P.snow, P.snowS, [-1, -0.6], 0.9);
    streakLines(ctx, onN(t, 1), [-1, 0], 1.2, '#ffffff', 8, 0.6);
  }
  drawHero(ctx, pose, onN(t, 2), { S: S6, ground: G6, glow });
  // rising embers + dust around the coil
  if (coil > 0 && b < 43) puffs(ctx, 740, G6, ((t * 1.7) % 1), Math.floor(t * 1.7) + 30, 0.9, P.snow, P.snowS, [0, -1], 1.4);
  ctx.restore();
  if (b > 42.2 && b < 43) radialLines(ctx, 740, 700, onN(t, 2), 0.8, '#ffffff', 5, 0.28, 0.35);
});
hit(43, 'impact', 2); hit(43, 'flash', 3);
