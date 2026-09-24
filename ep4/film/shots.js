// EMBER III · KINDLE (studio pipeline) — every shot: exposure sheets, camera, FX, compositing.
import { W, H, FPS, BEAT, bf, fb, X, G, I, img, preload, sheet, plate, cel, smearCel, fxPlay, warped, speedLines, streaks, bladeArc,
  glowDot, embers, snow, xsheet, shakeFrom, clamp, lerp, ease, rng, TAU, fbm, noise1, camApply, setImg } from './lib.js';
import { shot } from './film.js';

// ---------------------------------------------------------------- assets
const D = (id) => I(id);
const ALL = ['H01_back', 'H02_open', 'H02_half', 'H02_closed', 'H05_shoulder', 'H06_grip', 'H06_extend', 'H06_lock', 'H07_coil', 'H07_mid', 'H07_spring',
  'H08_run0', 'H08_run1', 'H08_run2', 'H08_run3', 'H08_run4', 'H08_run5', 'H08_windup', 'H08_slash_a', 'H08_slash', 'H08_follow', 'H08_hop', 'H08_backhand',
  'H09_b12', 'H09_b23', 'H09_b34', 'H10_aim', 'H10_fire', 'H10_knee', 'H10_land', 'H11_buried', 'H11_burst', 'H11_stand', 'H12_lookup', 'H13_brace',
  'H14_lying', 'H14_closed', 'H15_fireeye', 'H15_rise1', 'H15_rise2', 'H15_roar', 'H16_fly1', 'H16_cutL', 'H16_cutR', 'H16_spin', 'H17_raise',
  'H18_down1', 'H18_down2', 'H19_land', 'H19_stand', 'H19_profile', 'H19_smile'];
await preload(ALL);
await preload(['keys/A1_guard.png', 'keys/C1_coil.png', 'keys/C2_twist.png', 'keys/C3_extend.png', 'keys/C4_follow.png', 'keys/W1_leap.png',
  'keys/W2_leap_front.png', 'keys/W3_hurt.png', 'keys/W4_pounce.png', 'keys/B1_eyes.png',
  'bg/BG01_tilt.png', 'bg/BG03_treeline.png', 'bg/BG04_strip.png', 'bg/BG05_kingsky.png', 'bg/BG06_crater.png', 'bg/BG07_flank.png',
  'bg/BG08_apex.png', 'bg/BG09_dawn.png', 'bg/BG10_night_low.png', 'bg/BG_clearing.png',
  'props/KING.png', 'props/PAW.png', 'props/CLASP.png', 'props/CLASP_lit.png']);
const WOLF = await sheet('props/WOLF_cycle3x2.png', 3, 2);
const FXI = await sheet('fx/FX_ink.png', 3, 2), FXF = await sheet('fx/FX_fire.png', 3, 2), FXS = await sheet('fx/FX_snow.png', 3, 2), FXL = await sheet('fx/FX_slash.png', 3, 2);
await preload(['fx/FX_wing.png']);
const K = (k) => I('keys/' + k + '.png');
const BG = (k) => I('bg/' + k + '.png');
const PR = (k) => I('props/' + k + '.png');
const CAM0 = { x: W / 2, y: H / 2, z: 1, r: 0 };
const cam = (o = {}) => ({ ...CAM0, ...o });
const on = (lf, n) => Math.floor(lf / n) * n;                      // hold on n's
const f_ = (b, b0) => Math.round(bf(b) - bf(b0));                  // local frame of an absolute beat
const hitsAt = (list, b0) => list.map((b) => f_(b, b0));
// tile a plate horizontally (for side-scrolling pans), mirroring every other copy to hide seams
function tileX(im, scroll, y, h, par = 1) {
  const w = im.width * (h / im.height), s = ((scroll * par) % (2 * w) + 2 * w) % (2 * w);
  X.save(); X.setTransform(1, 0, 0, 1, 0, 0);
  for (let k = -1; k < 4; k++) {
    const x = k * w - s;
    X.save(); X.translate(x + (k % 2 ? w : 0), y); X.scale(k % 2 ? -1 : 1, 1); X.drawImage(im, 0, 0, w, h); X.restore();
  }
  X.restore();
}
function tileY(im, scroll, x, w) {
  const h = im.height * (w / im.width), s = ((scroll % (2 * h)) + 2 * h) % (2 * h);
  X.save();
  for (let k = -2; k < 4; k++) { const y = k * h + s - h; X.save(); X.translate(x, y + (k % 2 ? h : 0)); X.scale(1, k % 2 ? -1 : 1); X.drawImage(im, 0, 0, w, h); X.restore(); }
  X.restore();
}
function wolfRun(x, y, h, lf, phase = 0, flip = false, alpha = 1, c = CAM0) {
  const i = (Math.floor((lf + phase) / 2)) % 6;
  cel(WOLF[i], { x, y, h, flip, alpha }, c, { rim: '#6fe0ff', rimA: 0.7, cool: 0, shadow: 0.35 });
}
// wolf split into two halves along a line (delayed kill)
function wolfSplit(im, x, y, h, age, { flip = false, a = 0.4, c = CAM0 } = {}) {
  const w = im.width * (h / im.height);
  for (const side of [1, -1]) {
    X.save(); camApply(X, c); X.translate(x, y); X.rotate(a);
    X.beginPath(); X.rect(-3000, side > 0 ? -3000 : 0, 6000, 3000); X.clip();
    X.rotate(-a); X.translate(side * 40 * age, side * 30 * age + (side < 0 ? 500 * age * age : -100 * age));
    X.rotate(side * age * 0.8); X.scale(flip ? -1 : 1, 1);
    X.globalAlpha = clamp(1 - age * 1.4);
    X.drawImage(im, -w / 2, -h / 2, w, h); X.restore();
  }
  X.save(); camApply(X, c); X.translate(x, y); X.rotate(a); X.globalAlpha = clamp(1 - age * 3); X.fillStyle = '#fff6dc'; X.fillRect(-w * 0.55, -6, w * 1.1, 12); X.restore();
  G.save(); camApply(G, c); G.translate(x, y); G.rotate(a); G.globalAlpha = clamp(1 - age * 2); G.fillStyle = '#ff9a3a'; G.fillRect(-w * 0.6, -30, w * 1.2, 60); G.restore();
}
// cyan slit eyes in the dark, popping open
function eyePair(x, y, s, open, c = CAM0) {
  for (const dx of [-s * 1.1, s * 1.1]) {
    X.save(); camApply(X, c); X.translate(x + dx, y); X.rotate(dx > 0 ? -0.18 : 0.18);
    X.beginPath(); X.moveTo(-s, 0); X.quadraticCurveTo(0, -s * 0.5 * open, s, -s * 0.1); X.quadraticCurveTo(0, s * 0.3 * open, -s, 0);
    X.fillStyle = '#e8ffff'; X.fill(); X.restore();
    glowDot(c, x + dx, y, s * 3.5, 'rgba(90,230,255,0.9)', open);
  }
}
const NIGHT = { col: '#1a2a6a', op: 'soft-light', a: 0.35 };
const FIREGRADE = { col: '#ff5a1e', op: 'soft-light', a: 0.35 };

// ================================================================ S01  tilt down from the moon (0-10)
shot(0, 10, 'S01_tilt', (E) => {
  const { lf, t, u } = E;
  const ty = lerp(560, 2320, ease.io(clamp(u / 0.8)));
  const c = cam({ y: ty, z: lerp(1.0, 1.08, ease.io(clamp((u - 0.7) / 0.3))) });
  plate(BG('BG01_tilt'), c, { rect: [0, 0, W, 2880] });
  glowDot(c, 956, 272, 520, 'rgba(160,200,255,0.35)', 1);
  cel(warped(D('H01_back'), on(lf, 2) / FPS, 3, [1, 0.2]), { x: 960, y: 2640, h: 420 }, c, { shadow: 0.5, rimA: 0.7 });
  embers(t, { n: 55, seed: 3, rise: 0.8, size: 1.0, alpha: 0.9 });
  snow(t, { n: 110, speed: 40, wind: -30, size: 1.1 });
  return { grade: NIGHT, vign: 0.6 };
});

// ================================================================ S02  she opens her eyes (10-16)
shot(10, 16, 'S02_eyes', (E) => {
  const { lf, t, b } = E;
  const X_ = [[0, 'H02_closed'], [f_(13.4, 10), 'H02_half'], [f_(13.4, 10) + 3, 'H02_closed'], [f_(14.6, 10), 'H02_half'], [f_(14.6, 10) + 2, 'H02_open']];
  const id = xsheet(X_, lf);
  const z = lerp(1.0, 1.07, ease.io(E.u)) + (b >= 14.8 ? 0.03 * Math.exp(-(b - 14.8) * 3) : 0);
  plate(warped(D(id), on(lf, 2) / FPS, 2.5, [1, 0.2]), cam({ z }), {});
  snow(t, { n: 40, speed: 70, wind: -60, size: 3.2, alpha: 0.7, blur: 2 });
  if (b >= 14.8 && b < 15.6) speedLines(W * 0.3, H * 0.45, on(lf, 1), 0.7, '#ffffff', 0.32, 0.4);
  return { grade: NIGHT, flash: b >= 14.8 && b < 14.95 ? 0.35 : 0 };
});

// ================================================================ S03  the eclipse bites (16-22)
shot(16, 22, 'S03_eclipse', (E) => {
  const { lf, t, u } = E;
  const c = cam({ x: 956, y: lerp(360, 470, ease.io(u)), z: lerp(1.35, 1.25, u) });
  plate(BG('BG01_tilt'), c, { rect: [0, 0, W, 2880] });
  // the void disk slides across the moon (with a jagged cyan leading edge)
  const mx = 956, my = 272, R = 242;
  const off = lerp(R * 2.2, R * 0.55, ease.in2(u));
  X.save(); camApply(X, c); X.beginPath(); X.arc(mx, my, R * 1.02, 0, TAU); X.clip();
  X.beginPath();
  for (let i = 0; i <= 80; i++) {
    const a = (i / 80) * TAU, lead = Math.max(0, -Math.cos(a));
    const rr = R * 1.02 + lead * R * (0.05 * Math.sin(i * 7 + t * 4) + 0.06 * (i % 2));
    const x = mx + off + Math.cos(a) * rr, y = my - 10 + Math.sin(a) * rr;
    i ? X.lineTo(x, y) : X.moveTo(x, y);
  }
  X.closePath(); X.fillStyle = '#030208'; X.fill(); X.lineWidth = 5; X.strokeStyle = '#6ff0ff'; X.stroke(); X.restore();
  glowDot(c, mx - R * 0.4, my, 400, 'rgba(160,200,255,0.3)', 1 - u * 0.7);
  embers(t, { n: 25, seed: 5, alpha: 0.6 * (1 - u) });
  snow(t, { n: 70, speed: 40, wind: -30 });
  return { grade: { col: '#101a40', op: 'soft-light', a: 0.3 + 0.3 * u }, vign: 0.6 + 0.2 * u };
});

// ================================================================ S04  eyes in the treeline (22-28)
const EYES4 = []; { const r = rng(41); for (let i = 0; i < 26; i++) EYES4.push({ x: 180 + r() * 1560, y: 430 + r() * 300, s: 9 + r() * 10, b: 22.5 + Math.floor(r() * 9) * 0.5 }); }
shot(22, 28, 'S04_treeline', (E) => {
  const { lf, t, u, b } = E;
  const c = cam({ z: lerp(1.0, 1.1, ease.io(u)), x: lerp(960, 1000, u) });
  plate(BG('BG03_treeline'), c, {});
  X.save(); X.fillStyle = `rgba(2,2,8,${0.35 + 0.35 * u})`; X.fillRect(0, 0, W, H); X.restore();
  for (const e of EYES4) { const age = b - e.b; if (age > 0) eyePair(e.x, e.y, e.s, clamp(age / 0.15) * (Math.sin(t * 0.8 + e.x) > 0.97 ? 0.1 : 1), c); }
  // ink welling out along the snow line in the last two beats
  if (b > 26) for (let i = 0; i < 5; i++) fxPlay(FXI, (b - 26 - i * 0.2) * BEAT * 0.6, { x: 300 + i * 330, y: 820, h: 360 }, c, { fps: 6, glow: 0.2 });
  snow(t, { n: 60, speed: 30, wind: -20, alpha: 0.6 });
  return { grade: { col: '#0a1030', op: 'soft-light', a: 0.4 }, vign: 0.75 };
});

// ================================================================ S05  the tide, over her shoulder (28-34)
const TIDE = []; { const r = rng(55); for (let i = 0; i < 34; i++) { const d = r(); TIDE.push({ d, x0: -150 - r() * 900, y: lerp(640, 900, d), h: lerp(90, 330, d * d), v: lerp(500, 1200, d), ph: Math.floor(r() * 12), st: 28 + r() * 2.5 }); } TIDE.sort((a, b) => a.d - b.d); }
shot(28, 34, 'S05_tide', (E) => {
  const { lf, t, u, b } = E;
  const sh = shakeFrom(lf, [0], 6 * u, 1e9);
  const c = cam({ z: 1.02, sx: sh[0], sy: sh[1] });
  plate(BG('BG_clearing'), c, { blur: 2 });
  for (const w of TIDE) { const tt = (b - w.st) * BEAT; if (tt < 0) continue; const x = w.x0 + w.v * tt; if (x > W + 300) continue; wolfRun(x, w.y, w.h, lf, w.ph, false, 1, c); }
  // her, foreground right, big, cropped
  cel(warped(D('H05_shoulder'), on(lf, 2) / FPS, 5, [1, 0.3]), { x: 1500, y: 1650, h: 1700 }, cam({ sx: sh[0] * 0.3 }), { rimA: 0.9 });
  snow(t, { n: 90, speed: 60, wind: -200, size: 1.4 });
  return { grade: NIGHT };
});

// ================================================================ S06  the weapon inserts (34-38)
shot(34, 38, 'S06_insert', (E) => {
  const { lf, b } = E;
  const id = b < 35 ? 'H06_grip' : b < 36 ? 'H06_extend' : 'H06_lock';
  const lb = b < 35 ? b - 34 : b < 36 ? b - 35 : b - 36;
  const z = 1.0 + 0.06 * Math.exp(-lb * 4) + lb * 0.02;
  plate(D(id), cam({ z, r: b < 35 ? 0.02 : b < 36 ? -0.03 : 0.015 }), {});
  if (lb < 0.5) speedLines(W * 0.5, H * 0.5, on(lf, 1), 0.6, '#ffffff', 0.3, 0.35);
  if (id === 'H06_lock' && lb > 0.3 && lb < 1.4) glowDot(CAM0, lerp(560, 1150, clamp((lb - 0.3) / 1)), lerp(760, 250, clamp((lb - 0.3) / 1)), 160, 'rgba(255,255,255,0.9)', 1);
  return { flash: lb < 0.12 ? 0.45 : 0, grade: NIGHT };
});

// ================================================================ S07  launch (38-42)
shot(38, 42, 's07_launch', (E) => {
  const { lf, t, b } = E;
  const fL = f_(40.8, 38), fS = f_(41.0, 38);
  const tension = clamp((b - 38) / 2.7);
  const sh = b < 40.8 ? [2 * tension * fbm(t * 40), 2 * tension * fbm(t * 40 + 5)] : shakeFrom(lf, [fS], 26, 4);
  const c = cam({ z: lerp(1.0, 1.08, tension), sx: sh[0], sy: sh[1] });
  tileX(BG('BG04_strip'), 0, -160, 1400);
  if (b < 40.8) {
    cel(warped(D('H07_coil'), on(lf, 2) / FPS, 2 + 3 * tension, [-1, 0.2]), { x: 760, y: 1080, h: 980 }, c, { shadow: 0.5 });
    if (tension > 0.3) fxPlay(FXS, ((t * 1.3) % 0.5), { x: 720, y: 1010, h: 260 }, c, { fps: 12, glow: 0 });
  } else if (lf < fS) {
    cel(D('H07_mid'), { x: 800, y: 1080, h: 980 }, c, { shadow: 0.4 });
  } else {
    const a = (lf - fS) / FPS;
    const x = 840 + 5200 * a * a + 1800 * a;
    if (a < 0.14) smearCel(D('H07_spring'), { x, y: 1080, h: 980 }, c, { dx: 180, stretch: 0.3 });
    fxPlay(FXS, a, { x: 700, y: 980, h: 520 }, c, { fps: 14, glow: 0 });
    streaks(on(lf, 1), [-1, 0], 1.1, '#ffffff', 0.5);
  }
  snow(t, { n: 60, speed: 50, wind: b > 41 ? -900 : -60 });
  return { grade: NIGHT, impact: lf === fS || lf === fS + 1, flash: lf === fS + 2 ? 0.4 : 0, shake: [0, 0] };
});

// ================================================================ S08  the tracking sprint and two kills (42-52)
shot(42, 52, 's08_run', (E) => {
  const { lf, t, b } = E;
  const f46 = f_(46, 42), f50 = f_(50, 42);
  const speed = 1700;
  const scroll = t * speed;
  const sh = shakeFrom(lf, [f46, f50], 22, 5);
  const c = cam({ sx: sh[0], sy: sh[1] });
  tileX(BG('BG04_strip'), scroll * 0.35, -220, 1500, 1);
  streaks(on(lf, 2), [-1, 0], 0.5, '#dfe8ff', 0.25);
  // run cycle on twos; attack drawings take over around the kills
  const R = ['H08_run0', 'H08_run1', 'H08_run2', 'H08_run3', 'H08_run4', 'H08_run5'];
  let id = R[Math.floor(lf / 2) % 6], h = 900, x = 760, y = 1110, smear = false;
  const lb = b;
  if (lb >= 45.2 && lb < 45.75) id = 'H08_windup';
  else if (lb >= 45.75 && lb < 46) { id = 'H08_slash_a'; smear = true; }
  else if (lb >= 46 && lb < 46.35) id = 'H08_slash';
  else if (lb >= 46.35 && lb < 46.95) id = 'H08_follow';
  else if (lb >= 49.3 && lb < 49.95) { id = 'H08_hop'; y -= 140 * Math.sin(clamp((lb - 49.3) / 1.2) * Math.PI); }
  else if (lb >= 49.95 && lb < 50.7) { id = 'H08_backhand'; y -= 140 * Math.sin(clamp((lb - 49.3) / 1.2) * Math.PI); }
  // pacer wolves alongside
  wolfRun(360 + 60 * Math.sin(t * 1.3), 1000, 300, lf, 3, false, 0.95, c);
  // attacker 1 from the right (leaping in), contact at 46
  if (b < 46) { if (b > 45) { const u = clamp((b - 45) / 1); cel(K('W1_leap'), { x: lerp(2300, 1230, ease.in2(u)), y: lerp(760, 820, u) - Math.sin(u * Math.PI) * 120, h: 520, anchor: [0.5, 0.5] }, c, { rim: '#6fe0ff', cool: 0 }); } }
  else wolfSplit(K('W1_leap'), 1230, 820, 520, (lf - f46) / FPS * 1.4, { a: -0.5, c });
  if (b > 46.2) fxPlay(FXI, (b - 46.2) * BEAT, { x: 1260, y: 820, h: 620 }, c, { fps: 14, glow: 0.2 });
  // attacker 2 from the left (behind), contact at 50
  if (b < 50) { if (b > 49) { const u = clamp((b - 49) / 1); cel(K('W1_leap'), { x: lerp(-400, 330, ease.in2(u)), y: lerp(760, 760, u) - Math.sin(u * Math.PI) * 140, h: 520, anchor: [0.5, 0.5], flip: true }, c, { rim: '#6fe0ff', cool: 0 }); } }
  else wolfSplit(K('W1_leap'), 330, 760, 520, (lf - f50) / FPS * 1.4, { a: 0.5, c, flip: true });
  if (b > 50.2) fxPlay(FXI, (b - 50.2) * BEAT, { x: 330, y: 760, h: 620 }, c, { fps: 14, glow: 0.2 });
  if (smear) smearCel(D(id), { x, y, h }, c, { dx: -120, stretch: 0.25 });
  else cel(warped(D(id), on(lf, 2) / FPS, 3, [-1, 0.1]), { x, y, h }, c, { shadow: 0.5 });
  if (b >= 45.9 && b < 46.4) bladeArc(c, 900, 700, 250, 620, -2.2, 0.5, clamp(1 - (b - 45.9) / 0.5));
  if (b >= 49.9 && b < 50.5) bladeArc(c, 760, 640, 250, 600, -0.6, -3.6, clamp(1 - (b - 49.9) / 0.6));
  if ((b >= 46 && b < 46.3) || (b >= 50 && b < 50.3)) fxPlay(FXL, 0, { x: b < 48 ? 1230 : 330, y: b < 48 ? 820 : 760, h: 700 }, c, { fps: 1, glow: 0.8 });
  // snow kicked up at her feet every step
  if (!smear) fxPlay(FXS, ((lf % 12) / FPS), { x: x - 90, y: 1080, h: 170 }, c, { fps: 16, glow: 0 });
  snow(t, { n: 70, speed: 40, wind: -1400, size: 1.2 });
  return { grade: NIGHT, impact: [f46, f46 + 1, f50].includes(lf), flash: lf === f46 + 2 || lf === f50 + 1 ? 0.35 : 0 };
});

// ================================================================ S09  the spin slash (52-60)
shot(52, 60, 's09_spin', (E) => {
  const { lf, t, b } = E;
  const fHit = f_(56, 52), fBurst = f_(57, 52);
  const sh = shakeFrom(lf, [fHit, fBurst], 26, 5);
  const c = cam({ z: b < 54 ? lerp(1.0, 1.06, (b - 52) / 2) : lerp(1.1, 1.0, clamp((b - 54) / 4)), sx: sh[0], sy: sh[1] });
  plate(BG('BG_clearing'), c, { blur: 4 });
  const P0 = { x: 960, y: 1110, h: 920 };
  // the ring of wolves: circling during the guard, then converging on the contact
  const conv = (from, to, b0) => { const u = clamp((b - b0) / (56 - b0)); return [lerp(from[0], to[0], ease.in2(u)), lerp(from[1], to[1], ease.in2(u)) - Math.sin(u * Math.PI) * 180]; };
  const WL = [{ from: [-600, 600], to: [520, 640], b0: 54.4, flip: true, a: -0.5 }, { from: [2500, 560], to: [1420, 610], b0: 54.7, flip: false, a: 0.5 }];
  const drawWolves = () => {
    for (const w of WL) {
      if (b < 56) { if (b > w.b0) { const p = conv(w.from, w.to, w.b0); cel(K('W1_leap'), { x: p[0], y: p[1], h: 560, anchor: [0.5, 0.5], flip: w.flip }, c, { rim: '#6fe0ff', cool: 0 }); } }
      else if (b < 57) wolfSplit(K('W1_leap'), w.to[0], w.to[1], 560, (lf - fHit) / FPS * 0.7, { flip: w.flip, a: w.a, c });
      else fxPlay(FXI, (b - 57) * BEAT, { x: w.to[0], y: w.to[1], h: 760 }, c, { fps: 14, glow: 0.25 });
    }
  };
  if (b < 54) {
    for (let i = 0; i < 3; i++) wolfRun(((lf * 18 + i * 700) % 2600) - 300, 700 + i * 30, 220 + i * 30, lf, i * 4, false, 0.8, c);
    cel(warped(K('A1_guard'), on(lf, 2) / FPS, 4, [1, 0.2]), { ...P0, x: 900 }, c, { shadow: 0.5 });
  } else {
    // exposure sheet (local frames): C1 hold | b12 | C2 | b23 | smear | C3 contact+hold | b34 | C4 settle
    const fs = f_(55.2, 52);
    const XS = [[0, 'C1'], [fs, 'b12'], [fs + 2, 'C2'], [fs + 4, 'b23'], [fs + 6, 'smear'], [fHit, 'C3'], [fHit + 8, 'b34'], [fHit + 10, 'C4']];
    const k = xsheet(XS, lf);
    drawWolves();
    const map = { C1: K('C1_coil'), b12: D('H09_b12'), C2: K('C2_twist'), b23: D('H09_b23'), C3: K('C3_extend'), b34: D('H09_b34'), C4: K('C4_follow') };
    if (k === 'smear') { bladeArc(c, 960, 720, 240, 700, Math.PI * 0.85, Math.PI * 2.25, 1); smearCel(K('C3_extend'), P0, c, { dx: -60, drot: -0.15, stretch: 0.2 }); }
    else {
      const tension = k === 'C1' ? clamp(lf / fs) : 0;
      cel(k === 'C4' ? warped(map[k], on(lf, 2) / FPS, 3, [1, -0.2]) : map[k], { ...P0, x: P0.x + (k === 'C1' ? 3 * Math.sin(lf * 2.1) * tension : 0) }, c, { shadow: 0.5, warm: k === 'C3' ? 0.4 : 0 });
    }
    if (lf >= fHit && lf < fHit + 8) bladeArc(c, 960, 720, 240, 700, Math.PI * 1.4, Math.PI * 2.3, clamp(1 - (lf - fHit) / 8));
    if (lf >= fHit && lf < fHit + 6) speedLines(960, 640, on(lf, 1), 1.1, '#ffffff', 0.28, 0.55);
    if (b >= 57) { fxPlay(FXS, (b - 57) * BEAT, { x: 960, y: 1000, h: 800 }, c, { fps: 12, glow: 0 }); }
  }
  snow(t, { n: 70, speed: 60, wind: -120, size: 1.4 });
  embers(t, { n: 30, seed: 9, alpha: 0.7 });
  return { grade: NIGHT, impact: [fHit, fHit + 1, fBurst].includes(lf), flash: lf === fHit + 2 ? 0.55 : lf === fBurst + 1 ? 0.35 : 0 };
});

// ================================================================ S10  recoil -> flying knee (60-64)
shot(60, 64, 's10_knee', (E) => {
  const { lf, t, b } = E;
  const fF = f_(61, 60), fK = f_(61.5, 60);
  const sh = shakeFrom(lf, [fF, fK], 24, 5);
  const panx = b < 61 ? 0 : lerp(0, 700, ease.out(clamp((b - 61) / 2)));
  const c = cam({ x: W / 2 + panx, sx: sh[0], sy: sh[1] });
  tileX(BG('BG04_strip'), panx * 0.4, -200, 1450);
  const XS = [[0, 'H10_aim'], [fF, 'H10_fire'], [fF + 3, 'H10_knee'], [f_(62.8, 60), 'H10_land']];
  const id = xsheet(XS, lf);
  const hx = b < 61 ? 700 : b < 62.8 ? 700 + 1300 * ease.out(clamp((b - 61) / 1.3)) : 2000 + 150 * ease.outx(clamp((b - 62.8) / 1));
  const hy = 1110 - (b > 61 && b < 62.8 ? 260 * Math.sin(clamp((b - 61) / 1.8) * Math.PI) : 0);
  // the wolf: charges from the right, jaw meets the knee at 61.5, then tumbles away
  if (b < 61.5) { const u = clamp((b - 60.3) / 1.2); cel(K('W1_leap'), { x: lerp(3100, 2150, ease.in2(u)), y: 780 - Math.sin(u * Math.PI) * 60, h: 560, anchor: [0.5, 0.5] }, c, { rim: '#6fe0ff', cool: 0 }); }
  else if (b < 62.6) { const a = (b - 61.5) * BEAT; cel(K('W3_hurt'), { x: 2150 + 1500 * a, y: 700 - 900 * a + 1400 * a * a, h: 560, anchor: [0.5, 0.5], rot: -a * 7 }, c, { rim: '#6fe0ff', cool: 0 }); }
  else fxPlay(FXI, (b - 62.6) * BEAT, { x: 2150 + 1500 * 0.44, y: 700 - 900 * 0.44 + 1400 * 0.19, h: 700 }, c, { fps: 14, glow: 0.25 });
  if (id === 'H10_fire' || (b >= 61 && b < 61.4)) {
    const a = (lf - fF) / FPS;
    fxPlay(FXF, a, { x: hx - 560, y: 800, h: 520, rot: -Math.PI / 2 }, c, { fps: 16, glow: 0.8 });
    glowDot(c, hx - 480, 820, 400, 'rgba(255,170,80,0.9)', clamp(1 - a * 4));
  }
  cel(warped(D(id), on(lf, 2) / FPS, 3, [-1, 0.1]), { x: hx, y: hy, h: 940 }, c, { shadow: 0.45 * (hy > 1000 ? 1 : 0.3), warm: id === 'H10_fire' ? 0.6 : 0 });
  if (lf >= fK && lf < fK + 3) fxPlay(FXL, 0.9 / 12 * 12, { x: 2130, y: 760, h: 700 }, c, { fps: 1, glow: 1 });
  if (b >= 62.8) fxPlay(FXS, (b - 62.8) * BEAT, { x: hx, y: 1040, h: 480 }, c, { fps: 12, glow: 0 });
  if (b > 61 && b < 62) streaks(on(lf, 1), [-1, 0], 1, '#ffffff', 0.5);
  snow(t, { n: 60, speed: 50, wind: -300 });
  return { grade: NIGHT, impact: lf === fK || lf === fK + 1, flash: lf === fF ? 0.5 : lf === fK + 2 ? 0.4 : 0 };
});

// ================================================================ S11  buried -> BURST (64-72)
shot(64, 72, 's11_burst', (E) => {
  const { lf, t, b } = E;
  const fB = f_(68, 64);
  const tension = clamp((b - 66) / 2);
  const sh = b < 68 ? [4 * tension * fbm(t * 50), 4 * tension * fbm(t * 50 + 3)] : shakeFrom(lf, [fB], 40, 6);
  const c = cam({ z: b < 68 ? lerp(1.0, 1.12, clamp((b - 64) / 4)) : lerp(1.0, 0.94, clamp((b - 68) / 4)), sx: sh[0], sy: sh[1] });
  plate(BG('BG_clearing'), c, { blur: 3, tint: b >= 68 ? `rgba(255,90,30,${0.25 * clamp((b - 68) / 1)})` : null });
  const pile = [[-420, -520, 0.4, false], [360, -560, -0.3, true], [-120, -760, 0.1, false], [480, -300, -0.5, true], [-560, -260, 0.6, false], [120, -420, 0.2, true]];
  if (b < 68) {
    // pouncing in from above, one after another, then heaving
    cel(b < 65.5 ? D('H10_land') : D('H11_buried'), { x: 960, y: 1110, h: 900 }, c, { shadow: 0.5 });
    pile.forEach(([dx, dy, rot, fl], i) => {
      const b0 = 64.3 + i * 0.3, u = clamp((b - b0) / 0.6);
      if (b < b0) return;
      const x = 960 + dx * lerp(1.6, 0.5, ease.in2(u)), y = 1110 + dy * lerp(2.2, 0.55, ease.in2(u)) + (u >= 1 ? 6 * Math.sin(t * 30 + i) * tension : 0);
      cel(u < 1 ? K('W4_pounce') : K('W3_hurt'), { x, y, h: 520, anchor: [0.5, 0.5], rot: rot + (u >= 1 ? 0.05 * Math.sin(t * 20 + i) : 0), flip: fl }, c, { rim: '#6fe0ff', cool: 0 });
    });
    // light cracks leaking through the pile
    if (tension > 0) {
      const r = rng(Math.floor(lf / 2) + 7);
      X.save(); camApply(X, c); X.globalCompositeOperation = 'lighter';
      for (let i = 0; i < 6 + tension * 16; i++) {
        const a = -Math.PI / 2 + (r() - 0.5) * 3, L = (180 + r() * 420) * tension, x0 = 960 + (r() - 0.5) * 120, y0 = 820;
        X.beginPath(); X.moveTo(x0, y0); X.lineTo(x0 + Math.cos(a - 0.03) * L, y0 + Math.sin(a - 0.03) * L); X.lineTo(x0 + Math.cos(a + 0.03) * L, y0 + Math.sin(a + 0.03) * L);
        X.fillStyle = r() > 0.5 ? '#ffd46a' : '#ff7a2a'; X.fill();
      }
      X.restore();
      glowDot(c, 960, 800, 500 * tension, 'rgba(255,140,50,0.9)', tension);
    }
  } else {
    const a = (lf - fB) / FPS;
    // radial light blades
    if (a < 1.2) {
      const r = rng(5);
      X.save(); X.setTransform(1, 0, 0, 1, 0, 0);
      for (let i = 0; i < 28; i++) {
        const ang = r() * TAU, w = 0.04 + r() * 0.06, L = 2400 * ease.outx(clamp(a / 0.5));
        X.globalAlpha = clamp(1 - (a - 0.4) / 0.8) * 0.9; X.fillStyle = ['#ff2e88', '#ff8a1f', '#ffd84a'][i % 3];
        X.beginPath(); X.moveTo(960, 700); X.lineTo(960 + Math.cos(ang - w) * L, 700 + Math.sin(ang - w) * L); X.lineTo(960 + Math.cos(ang + w) * L, 700 + Math.sin(ang + w) * L); X.fill();
      }
      X.restore();
    }
    // wolves flung outward, spinning, burning away
    pile.forEach(([dx, dy, rot, fl], i) => {
      const d = [dx / Math.hypot(dx, dy), dy / Math.hypot(dx, dy)], v = 2600;
      const x = 960 + dx * 0.5 + d[0] * v * a, y = 1110 + dy * 0.55 + (d[1] * v - 600) * a + 1400 * a * a;
      if (a < 0.45) cel(K('W3_hurt'), { x, y, h: 520, anchor: [0.5, 0.5], rot: rot + a * (fl ? -9 : 9), flip: fl, alpha: 1 - a * 1.8 }, c, { rim: '#ffb060', cool: 0 });
      fxPlay(FXI, a - 0.25, { x, y, h: 600 }, c, { fps: 14, glow: 0.2 });
    });
    const id = a < 0.9 ? 'H11_burst' : 'H11_stand';
    fxPlay(FXF, a % 0.5, { x: 960, y: 900, h: 900 }, c, { fps: 12, loop: true, glow: 0.9, alpha: 0.9 });
    cel(warped(D(id), on(lf, 2) / FPS, 5, [0.3, -1]), { x: 960, y: 1110, h: 960 }, c, { shadow: 0.5, warm: 1, rim: '#ffb060' });
    fxPlay(FXS, a, { x: 960, y: 1020, h: 900 }, c, { fps: 12, glow: 0, alpha: 0.9 });
  }
  embers(t, { n: b >= 68 ? 120 : 20, seed: 12, rise: 2, size: 1.3 });
  return { grade: b >= 68 ? FIREGRADE : NIGHT, impact: lf === fB || lf === fB + 1 || lf === fB + 3, flash: lf === fB + 2 ? 0.7 : 0 };
});

// ================================================================ S12  the Hollow King rises (72-84)
shot(72, 84, 's12_king', (E) => {
  const { lf, t, b, u } = E;
  const rise = ease.io(clamp((b - 73) / 8));
  const c = cam({ y: lerp(2320, 1020, ease.io(clamp((b - 72.5) / 9))), sx: 8 * u * fbm(t * 30), sy: 8 * u * fbm(t * 30 + 4) });
  plate(BG('BG05_kingsky'), c, { rect: [0, 0, W, 2880] });
  // the King climbs out of the forest (painted cel), world-space
  cel(PR('KING'), { x: 960, y: lerp(3300, 1300, rise), h: 1750, anchor: [0.5, 0.5] }, c, { rim: '#6fe0ff', rimA: 0.6, cool: 0 });
  // eyes flare on the beats
  for (let k = 0; k < 5; k++) if (b > 77 + k) glowDot(c, 960 + (k - 2) * 140, lerp(3300, 1300, rise) - 150, 240, 'rgba(90,230,255,0.8)', Math.exp(-(b - 77 - k) * 2));
  // her: tiny, far below, looking up
  cel(warped(D('H12_lookup'), on(lf, 2) / FPS, 3, [0.3, -1]), { x: 960, y: 2830, h: 360 }, c, { shadow: 0.5 });
  snow(t, { n: 70, speed: 20, wind: -20, alpha: 0.5 });
  return { grade: { col: '#0a1236', op: 'soft-light', a: 0.45 }, vign: 0.7 };
});

// ================================================================ S13  the paw (84-88)
shot(84, 88, 's13_paw', (E) => {
  const { lf, t, b } = E;
  if (b >= 86.25) { X.fillStyle = '#000'; X.fillRect(0, 0, W, H); return { bloom: 0, vign: 0 }; }   // silence
  const u = ease.in2(clamp((b - 84) / 2.1));
  const c = cam({ z: 1.05, sx: (6 + 30 * u) * fbm(t * 40), sy: (6 + 30 * u) * fbm(t * 40 + 9) });
  plate(BG('BG10_night_low'), c, {});
  cel(warped(D('H13_brace'), on(lf, 2) / FPS, 4, [0, 1]), { x: 960, y: 1180, h: 1000 }, c, { shadow: 0 });
  cel(PR('PAW'), { x: 960, y: lerp(-300, 520, u), h: lerp(700, 2400, u), anchor: [0.5, 0.5] }, c, { rim: '#6fe0ff', cool: 0 });
  if (b > 85.3) speedLines(960, 600, on(lf, 1), 1.2, '#ffffff', 0.2, 0.55);
  return { grade: NIGHT, impact: b >= 86 && b < 86.1, flash: b >= 86.1 && b < 86.25 ? 1 : 0 };
});

// ================================================================ S14  the crater; memory; the ember (88-100)
const MEM = ['../out/ember_final.mp4', '../b3d/out/ember2_final.mp4', '../ep3b/out/EMBER3_KINDLE_hand.mp4', 'pilot_spin.mp4'];
shot(88, 100, 's14_low', (E) => {
  const { lf, t, b } = E;
  if (b >= 93.5 && b < 94.6) {        // memory flashes, 2 frames each
    const k = Math.floor((b - 93.5) / 0.2);
    const mem = I('mem' + (k % 4));
    X.drawImage(mem, 0, 0, W, H);
    X.save(); X.globalCompositeOperation = 'color'; X.fillStyle = '#c8783c'; X.fillRect(0, 0, W, H); X.restore();
    return { bloom: 0.3, flash: lf % 2 === 0 ? 0.15 : 0 };
  }
  if (b >= 94.6) {                   // the clasp, ECU: gutters, then answers the heartbeat
    const beats = [95.5, 96.5, 97.2, 97.7, 98.1, 98.4, 98.6];
    let pulse = 0; for (const pb of beats) if (b > pb) pulse = Math.max(pulse, Math.exp(-(b - pb) * 5) * (0.3 + 0.1 * beats.indexOf(pb)));
    const lit = clamp((b - 98.8) / 0.25);
    const c = cam({ z: lerp(1.0, 1.08, (b - 94.6) / 5.4) + pulse * 0.02 });
    plate(PR('CLASP'), c, {});
    if (lit > 0) plate(PR('CLASP_lit'), c, { alpha: lit });
    glowDot(c, 960, 520, 300 + 300 * pulse + 800 * lit, 'rgba(255,140,50,0.95)', Math.min(1, 0.25 + pulse * 1.4 + lit));
    return { grade: { col: '#300810', op: 'soft-light', a: 0.3 }, flash: b >= 98.8 && b < 99 ? 0.6 : 0 };
  }
  const id = b < 92 ? 'H14_lying' : 'H14_closed';
  const c = cam({ z: lerp(1.0, 1.15, ease.io(clamp((b - 88) / 5.5))), r: 0.02 });
  plate(BG('BG06_crater'), c, {});
  cel(warped(D(id), on(lf, 3) / FPS, 1.5, [1, 0]), { x: 960, y: 560, h: 780, anchor: [0.5, 0.5] }, c, { shadow: 0, rimA: 0.4 });
  glowDot(c, 930, 540, 90, 'rgba(255,140,50,0.9)', 0.3 + 0.2 * Math.abs(noise1(t * 6)) - 0.2 * clamp((b - 88) / 5));
  snow(t * 0.7, { n: 90, speed: 35, wind: 0, size: 1.5, alpha: 0.8 });
  return { grade: { col: '#20283a', op: 'saturation', a: 0.55 }, vign: 0.75 };
});

// ================================================================ S15  IGNITION (100-108)
shot(100, 108, 's15_ignite', (E) => {
  const { lf, t, b } = E;
  if (b < 101.5) {
    const c = cam({ z: lerp(1.0, 1.1, (b - 100) / 1.5) });
    plate(D('H15_fireeye'), c, {});
    speedLines(W / 2, H / 2, on(lf, 1), 0.9, '#ffd46a', 0.3, 0.5);
    embers(t, { n: 60, seed: 4, rise: 3, size: 1.6 });
    return { grade: FIREGRADE, flash: b < 100.12 ? 0.6 : 0 };
  }
  const fR = f_(105, 100);
  const sh = shakeFrom(lf, [f_(101.5, 100), fR], 30, 7);
  const c = cam({ z: lerp(1.08, 1.0, clamp((b - 101.5) / 6)), sx: sh[0], sy: sh[1] });
  plate(BG('BG06_crater'), c, { tint: 'rgba(120,20,10,0.55)' });
  const id = b < 103 ? 'H15_rise1' : b < 105 ? 'H15_rise2' : 'H15_roar';
  const wingOpen = ease.back(clamp((b - 103.4) / 1.6));
  if (wingOpen > 0) {
    const wing = I('fx/FX_wing.png');
    for (const side of [1, -1]) {
      X.save(); camApply(X, c); X.translate(960, 560); X.scale(side * wingOpen * 1.05, wingOpen * 1.05); X.rotate(0.08 * Math.sin(t * 5));
      X.drawImage(wing, -60, -wing.height * 0.62, wing.width * 0.72, wing.height * 0.72); X.restore();
      G.save(); camApply(G, c); G.translate(960, 560); G.scale(side * wingOpen, wingOpen); G.globalAlpha = 0.6; G.drawImage(wing, -60, -wing.height * 0.62, wing.width * 0.72, wing.height * 0.72); G.restore();
    }
  }
  fxPlay(FXF, (t % 0.5), { x: 960, y: 980, h: 520 }, c, { fps: 12, loop: true, glow: 0.8 });
  cel(warped(D(id), on(lf, 2) / FPS, 5, [0.2, -1]), { x: 960, y: 1120, h: 980 }, c, { shadow: 0.4, warm: 1, rim: '#ffb060' });
  // steam ring blasting outward on the rise
  const a = (b - 101.5) * BEAT;
  fxPlay(FXS, a, { x: 560, y: 1000, h: 700 }, c, { fps: 10, glow: 0 }); fxPlay(FXS, a, { x: 1360, y: 1000, h: 700, flip: true }, c, { fps: 10, glow: 0 });
  embers(t, { n: 140, seed: 21, rise: 3, size: 1.4 });
  return { grade: FIREGRADE, impact: lf === fR, flash: lf === fR + 1 ? 0.6 : 0 };
});

// ================================================================ S16  the ascent (108-124)
const CUTS = [112, 114, 116, 118, 120];
shot(108, 124, 's16_ascent', (E) => {
  const { lf, t, b } = E;
  const spin = lerp(0, 1.5 * TAU, ease.io(clamp((b - 108) / 15)));
  const sh = shakeFrom(lf, CUTS.map((cb) => f_(cb, 108)), 22, 5);
  X.save(); X.translate(W / 2 + sh[0], H / 2 + sh[1]); X.rotate(spin); X.translate(-W / 2, -H / 2);
  tileY(BG('BG07_flank'), t * 2600, -600, W + 1200);
  X.restore();
  const c = cam({ r: spin, sx: sh[0], sy: sh[1] });
  // tendrils lashing in on each cut beat, severed on the beat
  CUTS.forEach((cb, i) => {
    const age = (b - (cb - 1.2)) * BEAT; if (age < 0 || age > 1.1) return;
    const side = i % 2 ? 1 : -1, u = clamp(age / 0.48);
    const pts = []; for (let k = 0; k <= 14; k++) { const v = k / 14; pts.push([960 + side * lerp(1500, 80, ease.in2(u) * v + (1 - v) * 0), 560 + 300 * Math.sin(v * 5 + t * 8 + i) * (1 - v) + (v - 0.5) * 200]); }
    const cut = b >= cb;
    X.save(); camApply(X, c); X.lineCap = 'round';
    const draw = (arr, w0) => { for (let k = 0; k < arr.length - 1; k++) { X.beginPath(); X.moveTo(...arr[k]); X.lineTo(...arr[k + 1]); X.lineWidth = w0 * (1 - k / arr.length) + 6; X.strokeStyle = '#05040c'; X.stroke(); } };
    draw(cut ? pts.slice(0, 9) : pts, 90);
    X.restore();
    if (cut) fxPlay(FXI, (b - cb) * BEAT, { x: pts[9][0], y: pts[9][1], h: 520 }, c, { fps: 14, glow: 0.2 });
  });
  // fire trail below her
  fxPlay(FXF, (t % 0.5), { x: 960, y: 900, h: 600, rot: Math.PI }, c, { fps: 12, loop: true, glow: 0.9 });
  const cutK = CUTS.find((cb) => b >= cb - 0.3 && b < cb + 0.6);
  let id = 'H16_fly1';
  if (cutK) id = [ 'H16_cutL', 'H16_cutR', 'H16_spin', 'H16_cutL', 'H16_cutR'][CUTS.indexOf(cutK)];
  const wing = I('fx/FX_wing.png');
  for (const side of [1, -1]) { X.save(); camApply(X, c); X.translate(960, 520); X.scale(side * 0.85, 0.85); X.rotate(0.15 * Math.sin(t * 7)); X.drawImage(wing, -60, -wing.height * 0.6, wing.width * 0.7, wing.height * 0.7); X.restore(); }
  cel(warped(D(id), on(lf, 2) / FPS, 4, [0, 1]), { x: 960, y: 560, h: 900, anchor: [0.5, 0.5] }, c, { warm: 1, rim: '#ffb060' });
  if (cutK && b < cutK + 0.4) { bladeArc(c, 960, 560, 260, 640, (CUTS.indexOf(cutK) % 2 ? -0.4 : Math.PI + 0.4), (CUTS.indexOf(cutK) % 2 ? -2.8 : 0.4), clamp(1 - (b - cutK) / 0.4), '#fff6dc', '#ff9a3a'); fxPlay(FXL, 0, { x: 960 + (CUTS.indexOf(cutK) % 2 ? 420 : -420), y: 560, h: 620 }, c, { fps: 1, glow: 1 }); }
  embers(t, { n: 90, seed: 33, rise: 8, size: 1.3 });
  if (b > 122.5) { const a = clamp((b - 122.5) / 1.5); X.fillStyle = `rgba(255,240,220,${a})`; X.fillRect(0, 0, W, H); }
  return { grade: FIREGRADE, impact: CUTS.some((cb) => lf === f_(cb, 108)), flash: CUTS.some((cb) => lf === f_(cb, 108) + 1) ? 0.3 : 0 };
});

// ================================================================ S17  the apex (124-132)
shot(124, 132, 's17_apex', (E) => {
  const { lf, t, b } = E;
  const slow = (b - 124) * 0.05;
  const c = cam({ z: lerp(1.0, 1.1, ease.io(E.u)) });
  plate(BG('BG08_apex'), c, {});
  cel(PR('KING'), { x: 960, y: 1500, h: 1500, anchor: [0.5, 0.5] }, cam({ z: 1 + slow }), { rim: '#6fe0ff', rimA: 0.5, cool: 0 });
  const wing = I('fx/FX_wing.png');
  for (const side of [1, -1]) { X.save(); camApply(X, c); X.translate(960, 470); X.scale(side * 0.9, 0.9); X.rotate(0.04 * Math.sin(t * 1.5)); X.drawImage(wing, -50, -wing.height * 0.6, wing.width * 0.72, wing.height * 0.72); X.restore(); }
  cel(warped(D('H17_raise'), on(lf, 3) / FPS, 2, [0, 1]), { x: 960, y: 1020, h: 840 }, c, { warm: 1, rim: '#fff0c0', rimA: 1, rimOff: [0, -8] });
  embers(40 + slow * 10, { n: 110, seed: 44, rise: 0.2, size: 1.4 });
  return { grade: FIREGRADE, bars: 120 * clamp((b - 124) / 1), vign: 0.65 };
});

// ================================================================ S18  the cut (132-140)
shot(132, 140, 's18_cut', (E) => {
  const { lf, t, b } = E;
  const fC = f_(132.5, 132), fS = f_(133.5, 132);
  const sh = shakeFrom(lf, [fC, fS], 40, 7);
  const c = cam({ sx: sh[0], sy: sh[1] });
  if (b < 133.5) {
    plate(BG('BG08_apex'), c, { blur: 3 });
    const id = lf < fC ? 'H18_down1' : 'H18_down2';
    if (lf >= fC) { // the line of light, drawn across the whole sky
      const u = ease.outx(clamp((lf - fC) / 4));
      X.save(); X.setTransform(1, 0, 0, 1, 0, 0); X.translate(960, 540); X.rotate(-0.55);
      X.fillStyle = '#fffbe8'; X.fillRect(-1400 * u, -7, 2800 * u, 14); X.restore();
      G.save(); G.translate(960, 540); G.rotate(-0.55); G.fillStyle = '#ffd46a'; G.fillRect(-1400 * u, -60, 2800 * u, 120); G.restore();
    }
    cel(D(id), { x: 960, y: 1120, h: 1020 }, c, { warm: 1, rim: '#fff0c0' });
    return { grade: FIREGRADE, bars: 120, impact: lf === fC || lf === fC + 1, flash: lf === fC + 2 ? 0.5 : 0 };
  }
  // the King splits along the line; light pours through; the ring shatters
  const a = (lf - fS) / FPS, sep = ease.in2(clamp(a / 1.6)) * 420;
  X.fillStyle = '#050208'; X.fillRect(0, 0, W, H);
  for (const side of [1, -1]) {
    X.save(); X.translate(960, 540); X.rotate(-0.55); X.beginPath(); X.rect(-3000, side > 0 ? -3000 : 0, 6000, 3000); X.clip(); X.rotate(0.55); X.translate(-960, -540);
    X.translate(side * sep * 0.55, side * sep * 0.84 * -0.4 + (side < 0 ? sep * 0.5 : 0));
    plate(BG('BG08_apex'), CAM0, {});
    cel(PR('KING'), { x: 960, y: 820, h: 1400, anchor: [0.5, 0.5] }, CAM0, { rim: '#ffcf80', rimA: 0.8, cool: 0 });
    X.restore();
  }
  const seam = 10 + sep * 0.9;
  X.save(); X.translate(960, 540); X.rotate(-0.55);
  const gg = X.createLinearGradient(0, -seam, 0, seam); gg.addColorStop(0, 'rgba(255,212,106,0)'); gg.addColorStop(0.5, '#fffdf0'); gg.addColorStop(1, 'rgba(255,212,106,0)');
  X.fillStyle = gg; X.fillRect(-3000, -seam, 6000, seam * 2); X.restore();
  G.save(); G.translate(960, 540); G.rotate(-0.55); G.fillStyle = '#ffd46a'; G.fillRect(-3000, -seam * 2, 6000, seam * 4); G.restore();
  embers(t, { n: 150, seed: 55, rise: 2, size: 1.5 });
  const wh = clamp((b - 136.5) / 2.5);
  if (wh > 0) { X.fillStyle = `rgba(255,248,235,${wh})`; X.fillRect(0, 0, W, H); }
  return { grade: FIREGRADE, impact: lf === fS, flash: lf === fS + 1 ? 0.5 : 0 };
});

// ================================================================ S19  dawn (140-168)
shot(140, 168, 's19_dawn', (E) => {
  const { lf, t, b } = E;
  const warmIn = clamp((b - 140) / 1.5);
  if (b < 152) {
    const c = cam({ z: lerp(1.0, 1.1, ease.io(clamp((b - 140) / 12))), x: lerp(960, 1000, (b - 140) / 12) });
    plate(BG('BG09_dawn'), c, {});
    const id = b < 143.5 ? 'H19_land' : 'H19_stand';
    cel(warped(D(id), on(lf, 3) / FPS, 3, [1, 0.1]), { x: 1280, y: 1150, h: 900 }, c, { shadow: 0.3, warm: 0.8, rim: '#ffd9a0', cool: 0, light: [-1, 0] });
    if (b < 141.5) fxPlay(FXS, (b - 140) * BEAT, { x: 1280, y: 1060, h: 700 }, c, { fps: 12, glow: 0 });
    embers(t, { n: 110, seed: 66, rise: -0.45, size: 1.2 });
    if (b < 141) { X.fillStyle = `rgba(255,248,235,${1 - warmIn})`; X.fillRect(0, 0, W, H); }
    return { grade: { col: '#ff9a6a', op: 'soft-light', a: 0.2 } };
  }
  if (b < 160) {
    const id = b < 156 ? 'H19_profile' : 'H19_smile';
    plate(warped(D(id), on(lf, 3) / FPS, 2, [1, 0]), cam({ z: lerp(1.0, 1.06, (b - 152) / 8) }), {});
    embers(t, { n: 60, seed: 67, rise: -0.5, size: 1.6 });
    return { grade: { col: '#ff9a6a', op: 'soft-light', a: 0.2 } };
  }
  // title over the dawn
  const c = cam({ z: 1.12, x: 1000 });
  plate(BG('BG09_dawn'), c, {});
  cel(warped(D('H19_stand'), on(lf, 3) / FPS, 3, [1, 0.1]), { x: 1280, y: 1150, h: 900 }, c, { shadow: 0.3, warm: 0.8, rim: '#ffd9a0', cool: 0 });
  embers(t, { n: 110, seed: 66, rise: -0.45, size: 1.2 });
  const e = ease.out(clamp((b - 160.5) / 2.5));
  X.save(); X.globalAlpha = e;
  X.font = '600 150px Futura'; X.fillStyle = '#2e1236';
  const word = 'EMBER', track = 60 * (1.3 - 0.3 * e); let x = 170;
  for (const ch of word) { X.fillText(ch, x, 330); x += X.measureText(ch).width + track; }
  X.fillStyle = '#b31d36'; X.fillRect(170, 360, (x - track - 170) * e, 5);
  X.font = '500 60px "Hiragino Sans"'; X.fillStyle = '#2e1236'; X.fillText('点火', 170, 445);
  X.font = '500 40px Futura'; X.fillText('I I I  ·  K I N D L E', 330, 437);
  X.restore();
  return { grade: { col: '#ff9a6a', op: 'soft-light', a: 0.2 } };
});

// memory frames (extracted once)
import { execFileSync } from 'child_process';
import fs from 'fs';
import { loadImage } from 'skia-canvas';
const memT = [23.3, 39.2, 40.2, 3.5];
for (let i = 0; i < 4; i++) {
  const out = `/tmp/claude-501/mem${i}.png`;
  if (!fs.existsSync(out)) execFileSync('ffmpeg', ['-y', '-loglevel', 'error', '-ss', String(memT[i]), '-i', MEM[i], '-frames:v', '1', '-vf', 'scale=1920:1080', out]);
  setImg('mem' + i, await loadImage(out));
}
