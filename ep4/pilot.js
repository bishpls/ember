// EMBER — Round 4 pilot: the spin slash, studio pipeline.
// Keys drawn by the image model into MY layouts; timing, in-betweens (smears/slides/holds), FX and compositing here.
import { Canvas, loadImage } from 'skia-canvas';
import fs from 'fs';
import { spawn } from 'child_process';
import { clamp, lerp, ease, rng, TAU, fbm, noise1, pathPoly, taper, add, rot } from '../ep3b/src/engine.js';
import { inkBurst, radialLines, streakLines, ring, embers, snowfall, puffs } from '../ep3b/src/fx.js';
// anime blade smear: a few thin concentric light streaks + one sharp crescent, bright core, additive glow
function smearArc(ctx, cx, cy, r0, r1, a0, a1, glow, alpha = 1) {
  ctx.save(); ctx.globalAlpha = alpha; ctx.lineCap = 'round';
  for (let i = 0; i < 6; i++) {
    const r = r0 + (r1 - r0) * (0.35 + i * 0.13), a = a0 + (a1 - a0) * (0.25 + i * 0.08);
    ctx.beginPath(); ctx.arc(cx, cy, r, a, a1); ctx.lineWidth = 2 + i * 1.5; ctx.strokeStyle = i > 3 ? '#ffffff' : 'rgba(210,230,255,0.8)'; ctx.stroke();
  }
  const n = 24, pts = [];
  for (let i = 0; i <= n; i++) { const u = i / n, a = a0 + (a1 - a0) * u; pts.push([cx + Math.cos(a) * r1, cy + Math.sin(a) * r1]); }
  for (let i = n; i >= 0; i--) { const u = i / n, a = a0 + (a1 - a0) * u; const r = r1 - (r1 - r0) * 0.22 * u * u; pts.push([cx + Math.cos(a) * r, cy + Math.sin(a) * r]); }
  ctx.beginPath(); pts.forEach((q, i) => (i ? ctx.lineTo(...q) : ctx.moveTo(...q))); ctx.closePath();
  ctx.fillStyle = 'rgba(255,255,255,0.92)'; ctx.fill();
  ctx.restore();
  if (glow) { glow.save(); glow.globalAlpha = 0.5 * alpha; glow.beginPath(); pts.forEach((q, i) => (i ? glow.lineTo(...q) : glow.moveTo(...q))); glow.closePath(); glow.fillStyle = '#9fd0ff'; glow.fill(); glow.restore(); }
}

const W = 1920, H = 1080, FPS = 24, BEAT = 0.4;
const F = (beat) => Math.round(beat * BEAT * FPS);      // beat -> frame
const NF = F(12);

const I = {};
for (const k of ['A1_guard', 'C1_coil', 'C2_twist', 'C3_extend', 'C4_follow', 'D2_rise', 'W1_leap', 'W2_leap_front', 'B1_eyes'])
  I[k] = await loadImage(`keys/${k}.png`);
I.BG = await loadImage('bg/BG_clearing.png');

// ---------------------------------------------------------------- layers
const main = new Canvas(W, H), glowC = new Canvas(W, H), cel = new Canvas(W, H), tmp = new Canvas(W, H);
const X = main.getContext('2d'), G = glowC.getContext('2d');

// background plate: painted BG, cover-fit, with camera (zoom about a point), optional depth blur
function bgPlate(zoom = 1, cx = 0.5, cy = 0.5, blur = 0, dx = 0, dy = 0) {
  const s = Math.max(W / I.BG.width, H / I.BG.height) * zoom;
  const w = I.BG.width * s, h = I.BG.height * s;
  X.save(); X.filter = blur ? `blur(${blur}px)` : 'none';
  X.drawImage(I.BG, W * cx - w * cx + dx, H * cy - h * cy + dy, w, h);
  X.restore(); X.filter = 'none';
}

// a cel: the key drawing composited with a rim light, a light-side gradient (satsuei) and a contact shadow
// place: {x, y (feet/anchor at bottom-centre), h (px height), rot, flip, alpha, sx}
function drawCel(img, place, { rim = '#8fb6ff', rimOff = [-6, -4], warm = 0, shadow = true } = {}) {
  const h = place.h, w = img.width * (h / img.height) * (place.sx || 1);
  const c = cel.getContext('2d');
  c.setTransform(1, 0, 0, 1, 0, 0); c.globalCompositeOperation = 'source-over'; c.globalAlpha = 1;
  c.clearRect(0, 0, W, H);
  c.save();
  c.translate(place.x, place.y); c.rotate(place.rot || 0); c.scale(place.flip ? -1 : 1, 1);
  c.drawImage(img, -w / 2, -h, w, h);
  c.restore();
  // rim silhouette
  const t = tmp.getContext('2d');
  t.setTransform(1, 0, 0, 1, 0, 0); t.globalCompositeOperation = 'source-over'; t.clearRect(0, 0, W, H);
  t.drawImage(cel, 0, 0);
  t.globalCompositeOperation = 'source-in'; t.fillStyle = rim; t.fillRect(0, 0, W, H);
  // satsuei gradient: cool from top-left, warm from the bottom-right when lit by fire
  c.globalCompositeOperation = 'source-atop';
  const g = c.createLinearGradient(place.x - h * 0.5, place.y - h, place.x + h * 0.4, place.y);
  g.addColorStop(0, 'rgba(150,180,255,0.18)'); g.addColorStop(0.55, 'rgba(0,0,0,0)'); g.addColorStop(1, `rgba(255,120,40,${0.3 * warm})`);
  c.fillStyle = g; c.fillRect(0, 0, W, H);
  c.globalCompositeOperation = 'source-over';
  if (shadow) {
    X.save(); X.globalAlpha = 0.45 * (place.alpha ?? 1); X.fillStyle = '#0a0c24';
    X.beginPath(); X.ellipse(place.x, place.y - 4, w * 0.36, h * 0.03, 0, 0, TAU); X.fill(); X.restore();
  }
  X.save(); X.globalAlpha = 0.9 * (place.alpha ?? 1); X.drawImage(tmp, rimOff[0], rimOff[1]); X.restore();
  X.save(); X.globalAlpha = place.alpha ?? 1; X.drawImage(cel, 0, 0); X.restore();
}

// smear frame between two keys: the outgoing key dragged along an arc in several ghosted, stretched copies
function smearCel(img, place, n, spread, dir = 1) {
  for (let i = n; i >= 1; i--) {
    const a = i / n;
    drawCel(img, { ...place, rot: (place.rot || 0) + dir * spread * a, x: place.x - dir * 40 * a, sx: 1 + 0.25 * a, alpha: 0.18 * (1 - a) + 0.05 }, { shadow: false });
  }
  drawCel(img, { ...place, sx: 1.12 }, { shadow: false });
}

const _rims = new Map();
function rimOf(img) {           // cached cold-cyan silhouette of a drawing, used as a rim light behind it
  if (_rims.has(img)) return _rims.get(img);
  const c = new Canvas(img.width, img.height), x = c.getContext('2d');
  x.drawImage(img, 0, 0); x.globalCompositeOperation = 'source-in'; x.fillStyle = '#7fe7ff'; x.fillRect(0, 0, img.width, img.height);
  _rims.set(img, c); return c;
}
// a wolf cel with optional split along a line (for the delayed kill)
function drawWolfCel(img, x, y, h, { flip = false, rot = 0, split = 0, splitA = 0.3, alpha = 1, halfDrift = [0, 0] } = {}) {
  const w = img.width * (h / img.height);
  const drawHalf = (side) => {
    X.save(); X.globalAlpha = alpha;
    X.translate(x, y); X.rotate(splitA);
    X.beginPath(); X.rect(-3000, side > 0 ? -3000 : 0, 6000, 3000); X.clip();
    X.rotate(-splitA);
    X.translate(side * halfDrift[0] * split, side * halfDrift[1] * split + (side < 0 ? 400 * split * split : 0));
    X.rotate(rot + side * split * 0.6); X.scale(flip ? -1 : 1, 1);
    X.drawImage(rimOf(img), -w / 2 - 5, -h / 2 - 4, w, h);
    X.drawImage(img, -w / 2, -h / 2, w, h);
    X.restore();
  };
  if (split <= 0) { drawHalf(1); drawHalf(-1); return; }
  drawHalf(1); drawHalf(-1);
  // burning seam
  X.save(); X.translate(x, y); X.rotate(splitA); X.fillStyle = '#fff4d8'; X.globalAlpha = clamp(1 - split * 1.5);
  X.fillRect(-w * 0.55, -5, w * 1.1, 10); X.restore();
  G.save(); G.translate(x, y); G.rotate(splitA); G.fillStyle = '#ff8a1f'; G.globalAlpha = clamp(1 - split * 1.2);
  G.fillRect(-w * 0.6, -24, w * 1.2, 48); G.restore();
}

function post(f, { impact = false, flash = 0, shake = [0, 0], grade = 'night', bars = 0 } = {}) {
  // bloom
  X.save(); X.globalCompositeOperation = 'lighter';
  X.filter = 'blur(12px)'; X.globalAlpha = 0.8; X.drawImage(glowC, 0, 0);
  X.filter = 'blur(40px)'; X.globalAlpha = 0.7; X.drawImage(glowC, 0, 0);
  X.restore(); X.filter = 'none';
  if (impact) {
    const img = X.getImageData(0, 0, W, H), d = img.data;
    for (let i = 0; i < d.length; i += 4) {
      const l = 0.3 * d[i] + 0.59 * d[i + 1] + 0.11 * d[i + 2], warm = d[i] - d[i + 2] > 50 && d[i] > 110;
      const v = l > 105 ? 10 : 248;
      d[i] = warm ? 235 : v; d[i + 1] = warm ? 25 : v; d[i + 2] = warm ? 30 : v;
    }
    X.putImageData(img, 0, 0);
  }
  if (flash > 0) { X.fillStyle = `rgba(255,250,240,${flash})`; X.fillRect(0, 0, W, H); }
  // grade + vignette
  const vg = X.createRadialGradient(W / 2, H / 2, H * 0.4, W / 2, H / 2, H * 1.0);
  vg.addColorStop(0, 'rgba(0,0,0,0)'); vg.addColorStop(1, 'rgba(4,4,20,0.6)');
  X.fillStyle = vg; X.fillRect(0, 0, W, H);
  if (bars) { X.fillStyle = '#000'; X.fillRect(0, 0, W, bars); X.fillRect(0, H - bars, W, bars); }
}

const hold = (f, n) => Math.floor(f / n) * n;           // animate on twos / threes

// ---------------------------------------------------------------- the cut
function frame(f) {
  const t = f / FPS;
  X.setTransform(1, 0, 0, 1, 0, 0); X.globalAlpha = 1; X.globalCompositeOperation = 'source-over'; X.filter = 'none';
  G.setTransform(1, 0, 0, 1, 0, 0); G.clearRect(0, 0, W, H);
  X.fillStyle = '#000'; X.fillRect(0, 0, W, H);
  let opts = {};
  const tq = hold(f, 2) / FPS;

  if (f < F(3)) {
    // ---- A: guard.  Slow push; wolves cross the far clearing; wind in the cloak.
    const u = f / F(3);
    bgPlate(lerp(1.0, 1.05, u), 0.5, 0.55, 3);
    const far = [[-0.2, 640, 150, false, 0], [1.15, 655, 130, true, 0.4], [0.05, 690, 190, false, 0.7]];
    for (const [x0, y, h, fl, ph] of far) {
      const x = W * (x0 + (fl ? -1 : 1) * (0.35 * u + 0.05 * ph));
      drawWolfCel(I.W1_leap, x, y + 8 * Math.sin(tq * 14 + ph * 6), h, { flip: fl, alpha: 0.85 });
    }
    const sway = Math.sin(tq * 3.2) * 0.006;
    drawCel(I.A1_guard, { x: 820, y: 1120, h: 1000 * lerp(1.0, 1.03, u), rot: sway }, {});
    snowfall(X, t, { n: 90, speed: 50, wind: -60, size: 1.4, alpha: 0.8 });
    embers(X, t, { n: 25, seed: 4, glow: G, alpha: 0.7 });
    opts = { shake: [0, 0] };
  } else if (f < F(4.5)) {
    // ---- B: eyes.  Snap push on the beat.
    const lf = f - F(3);
    const z = lf < 5 ? lerp(1.0, 1.02, lf / 5) : lerp(1.1, 1.13, (lf - 5) / 10);
    const w = W * z, h = w * I.B1_eyes.height / I.B1_eyes.width;
    X.drawImage(I.B1_eyes, (W - w) / 2 + (lf >= 5 ? 30 : 0), (H - h) / 2, w, h);
    if (lf >= 5) radialLines(X, W * 0.62, H * 0.52, hold(f, 1) / FPS, 0.9, '#ffffff', 3, 0.3, 0.55);
    if (lf >= 5 && lf < 8) G.fillStyle = 'rgba(255,138,31,0.35)', G.fillRect(0, 0, W, H);
    snowfall(X, t * 2, { n: 40, speed: 80, wind: -900, size: 3, alpha: 0.9 });
    opts = { flash: lf === 5 ? 0.5 : 0 };
  } else if (f < F(9)) {
    // ---- C: the spin.
    const lf = f - F(4.5);
    const cam = lerp(1.08, 1.0, clamp(lf / 30));
    bgPlate(cam, 0.5, 0.6, 5);
    const P0 = { x: 960, y: 1110, h: 900 };
    const kHit = F(6.5) - F(4.5);                 // contact frame (local)
    // wolves: two leaping in from the sides, one from depth; arrive at kHit; split, burst on beat 7
    const kBurst = F(7) - F(4.5);
    const arrive = (from, to, k0) => { const u = clamp((lf - k0) / (kHit - k0)); return [lerp(from[0], to[0], ease.in2(u)), lerp(from[1], to[1], ease.in2(u)) - Math.sin(u * Math.PI) * 180]; };
    const wolves = [
      { img: I.W1_leap, from: [-700, 560], to: [520, 640], k0: 2, h: 560, flip: true, a: -0.5 },
      { img: I.W1_leap, from: [2600, 520], to: [1420, 600], k0: 5, h: 560, flip: false, a: 0.5 },
      { img: I.W2_leap_front, from: [1500, 470], to: [1380, 380], k0: 0, h: 160, grow: 520, a: 0.1, behind: true },
    ];
    const drawWolves = (behind = null) => {
      for (const w of wolves) {
        if (behind !== null && !!w.behind !== behind) continue;
        if (lf < kBurst) {
          const p = arrive(w.from, w.to, w.k0);
          const hh = w.grow ? lerp(w.h, w.grow, clamp((lf - w.k0) / (kHit - w.k0))) : w.h;
          const split = lf > kHit ? (lf - kHit) / (kBurst - kHit) * 0.25 : 0;
          drawWolfCel(w.img, p[0], p[1], hh, { flip: w.flip, split, splitA: w.a, halfDrift: [30, 40] });
        } else {
          inkBurst(X, w.to[0], w.to[1], (lf - kBurst) / FPS, w.k0 + 3, 2.0, null, [w.to[0] < 960 ? -0.6 : 0.6, -0.4]);
        }
      }
    };
    // back wolf first (it's behind her), side wolves in front
    // key sequence (local frames):  C1 hold 0..kHit-6 | C2 2f | smear 2f | C3 contact + hit-stop | C4 follow
    const kC2 = kHit - 6, kSm = kHit - 4, kC3 = kHit - 2;
    if (lf < kC2) {
      const tension = clamp(lf / kC2);
      drawWolves(true);
      drawCel(I.C1_coil, { ...P0, x: P0.x + 3 * Math.sin(lf * 2.1) * tension, h: P0.h * lerp(1, 0.97, tension) });
      drawWolves(false);
    } else if (lf < kSm) {
      drawWolves(true);
      drawCel(I.C2_twist, { ...P0, rot: -0.03 });
      drawWolves(false);
      smearArc(X, 960, 700, 250, 620, Math.PI * 0.9, Math.PI * 1.7, G, 0.9);
    } else if (lf < kC3) {
      drawWolves(true);
      smearArc(X, 960, 700, 240, 700, Math.PI * 0.85, Math.PI * 2.25, G, 1);
      smearCel(I.C3_extend, { ...P0 }, 5, 0.18, -1);
      drawWolves(false);
    } else if (lf < kHit + 8) {                       // contact: extend, hit-stop hold
      drawWolves(true);
      drawCel(I.C3_extend, { ...P0, x: P0.x + (lf < kHit + 4 ? 6 * Math.sin(lf * 3) : 0) }, { warm: 0.4 });
      drawWolves(false);
      smearArc(X, 960, 700, 240, 700, Math.PI * 1.4, Math.PI * 2.3, G, 0.9 * clamp(1 - (lf - kC3) / 8));
      if (lf >= kHit) radialLines(X, 960, 640, hold(f, 1) / FPS, 1.1, '#ffffff', 5, 0.28, 0.6);
    } else {                                          // follow-through: drop, settle
      const s = lf - (kHit + 8);
      drawWolves();
      const drop = ease.outx(clamp(s / 6)) * 40;
      drawCel(I.C4_follow, { ...P0, y: P0.y + drop * 0.2, h: P0.h * 0.98 }, { warm: 0.3 });
      ring(X, 960, 1040, s / 16, 1500, '#ffffff', 0.16, 36, G);
      puffs(X, 960, 1060, s / 20, 44, 2.2, '#e6ebff', '#9aa6e0', [0, -1], 2.0);
    }
    snowfall(X, t, { n: 70, speed: 60, wind: -120, size: 1.5, alpha: 0.8 });
    embers(X, t, { n: 40, seed: 9, glow: G, alpha: 0.8 });
    const hitF = F(6.5), burstF = F(7);
    opts = {
      impact: f === hitF || f === hitF + 1 || f === burstF,
      flash: f === hitF + 2 ? 0.6 : f === burstF + 1 ? 0.4 : 0,
      shake: f >= hitF ? [22 * Math.exp(-(f - hitF) / 5) * fbm(t * 40), 22 * Math.exp(-(f - hitF) / 5) * fbm(t * 40 + 7)] : [0, 0],
    };
  } else {
    // ---- D: aftermath.  She rises and looks back at us; ink burns away into embers.
    const lf = f - F(9), u = lf / (NF - F(9));
    bgPlate(lerp(1.12, 1.16, u), 0.45, 0.6, 7);
    drawCel(I.D2_rise, { x: 1150, y: 1180, h: 1150 * lerp(1.0, 1.03, u) }, { warm: 0.2 });
    const r = rng(12);
    for (let i = 0; i < 70; i++) {
      const x = r() * W, y0 = r() * H, fall = 60 + r() * 120, s = 4 + r() * 10;
      const y = (y0 + fall * lf / FPS) % H;
      const burn = clamp(lf / 20 - r() * 0.5);
      X.fillStyle = burn > 0.5 ? '#ff8a1f' : '#07060f'; X.fillRect(x, y, s, s * 0.6);
      if (burn > 0.5) { G.fillStyle = '#ff8a1f'; G.globalAlpha = 0.6; G.beginPath(); G.arc(x, y, s * 2, 0, TAU); G.fill(); G.globalAlpha = 1; }
    }
    snowfall(X, t, { n: 60, speed: 40, wind: -40, size: 1.4, alpha: 0.7 });
    embers(X, t, { n: 45, seed: 14, glow: G, alpha: 0.9, rise: 1.2 });
  }
  if (opts.shake && (opts.shake[0] || opts.shake[1])) {
    const s = new Canvas(W, H); s.getContext('2d').drawImage(main, 0, 0);
    X.fillStyle = '#000'; X.fillRect(0, 0, W, H); X.drawImage(s, opts.shake[0], opts.shake[1]);
  }
  post(f, opts);
  return main;
}

// ---------------------------------------------------------------- render
const A = process.argv.slice(2);
if (A[0] === '--sheet') {
  const n = 24, cols = 6, w = 320, h = 180;
  const S = new Canvas(cols * w, Math.ceil(n / cols) * h), x = S.getContext('2d');
  for (let i = 0; i < n; i++) {
    const f = Math.round(i * (NF - 1) / (n - 1));
    x.drawImage(frame(f), (i % cols) * w, Math.floor(i / cols) * h, w, h);
    x.fillStyle = '#ff0'; x.font = '13px sans-serif'; x.fillText(`f${f}`, (i % cols) * w + 4, Math.floor(i / cols) * h + 14);
  }
  fs.writeFileSync('pilot_sheet.jpg', await S.toBuffer('jpg', { quality: 0.85 }));
} else if (A[0] === '--frames') {
  for (const f of A[1].split(',').map(Number)) fs.writeFileSync(`pf_${f}.png`, await frame(f).toBuffer('png'));
} else {
  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgba', '-s', `${W}x${H}`, '-r', String(FPS),
    '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '15', '-pix_fmt', 'yuv420p', 'pilot_picture.mp4']);
  for (let f = 0; f < NF; f++) {
    const buf = await frame(f).toBuffer('raw');
    if (!ff.stdin.write(buf)) await new Promise((r) => ff.stdin.once('drain', r));
  }
  ff.stdin.end(); await new Promise((r) => ff.on('close', r));
  console.log('wrote pilot_picture.mp4', NF, 'frames');
}
