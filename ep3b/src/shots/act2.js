// S7b spin, S7c recoil knee, S7d pile & burst.
import { W, H, b2t, t2b, lerp, clamp, ease, onN, TAU, rng, add, mul, rot, sub, norm, len, pathPoly, pathSmooth, taper, fbm } from '../engine.js';
import { P } from '../palette.js';
import { shot, hit } from '../film.js';
import { Actor } from '../actor.js';
import { drawHero, solve } from '../hero.js';
import { drawWolf } from '../wolf.js';
import { night } from '../scene.js';
import { inkBurst, smearArc, puffs, ring, radialLines, streakLines, embers, snowfall, muzzle, flame, cracks } from '../fx.js';

function arcPos(p0, p1, u, h) { return [lerp(p0[0], p1[0], u), lerp(p0[1], p1[1], u) - Math.sin(u * Math.PI) * h]; }
function shakeXY(t, amt, s = 0) { return [amt * fbm(t * 40 + s), amt * fbm(t * 40 + s + 7)]; }
const hitDecay = (t, tb, k = 7) => (t >= b2t(tb) ? Math.exp(-(t - b2t(tb)) * k) : 0);

// ---------------------------------------------------------------- S7b  ring spin (52-58)
{
  const S = 600, G = 1000, CX = 960;
  const hero = new Actor({ face: 1, lean: 18, wa: 170, wx: -0.05, wy: 0.14, g1: 0.5, two: 0, bside: -1, brow: 1,
    fx1: 0.28, fy1: 0.44, fx2: -0.3, fy2: 0.46, windx: -0.8, head: -6 });
  hero.key(52, 'io', {});
  hero.key(54.2, 'io', { lean: 36, sq: 0.88, fx1: 0.36, fy1: 0.34, fx2: -0.4, fy2: 0.36, wa: 195, head: -12 });  // coil
  // the spin: facing flips twice across the turn, blade angle sweeps continuously
  hero.key(54.8, 'in2', { wa: 150, lean: 24, sq: 1.0, mouth: 0.9 });
  hero.key(54.95, 'step', { face: -1 });
  hero.key(55.3, 'lin', { wa: 20 });
  hero.key(55.45, 'step', { face: 1 });
  hero.key(55.8, 'outx', { wa: -40, lean: 30, sq: 0.92, fx1: 0.42, fy1: 0.36, fx2: -0.46, fy2: 0.38, mouth: 0.2 });
  hero.key(57.5, 'io', { lean: 26, sq: 1.0, wa: -30, mouth: 0 });
  hero.over((t, p, root) => { root[0] = CX; root[1] = G - 0.47 * S + (1 - p.sq) * 0.5 * S; });
  const pose = hero.fn();
  const pack = [];
  { const r = rng(71); const n = 6;
    for (let i = 0; i < n; i++) {
      const side = i % 2 ? 1 : -1, d = 0.5 + 0.5 * r();
      pack.push({ side, s: lerp(240, 360, d), from: [CX + side * (1100 + r() * 300), G - 120 - r() * 60],
        to: [CX + side * (120 + r() * 120), G - 330 - r() * 140], t0: b2t(53 + r() * 0.8), tHit: b2t(55 + (i / n) * 0.45), seed: 80 + i, behind: i % 3 === 0 });
    } }
  const burstT = b2t(55.5);
  shot(52, 58, 's07b_spin', (E) => {
    const { ctx, glow, t } = E;
    const b = t2b(t), tq = onN(t, 2);
    const sh = shakeXY(t, 22 * hitDecay(t, 55.5, 6));
    const zoom = lerp(1.0, 1.12, ease.io(clamp((b - 52) / 2.8))) - 0.1 * ease.outx(clamp((b - 55.5) / 1.5));
    ctx.save(); ctx.translate(W / 2 + sh[0], H / 2 + sh[1]); ctx.scale(zoom, zoom); ctx.translate(-W / 2, -H / 2);
    glow.save(); glow.translate(W / 2 + sh[0], H / 2 + sh[1]); glow.scale(zoom, zoom); glow.translate(-W / 2, -H / 2);
    night(ctx, glow, t, { moonXY: [1560, 220], moonR: 150, bite: 0.62, drain: 0.5, horizon: 620, snowY: 880 });
    const wolfAt = (w) => {
      if (t < w.t0) return { pos: [w.from[0] - w.side * (w.t0 - t) * 0, w.from[1]], mode: 'run' };
      const u = clamp((t - w.t0) / (w.tHit - w.t0));
      return { pos: arcPos(w.from, w.to, ease.in2(u), 260), mode: 'leap', u };
    };
    const drawPack = (behind) => {
      for (const w of pack) {
        if (w.behind !== behind) continue;
        if (t < burstT) {
          const st = wolfAt(w);
          if (t > w.tHit) st.pos = add(w.to, [0, -20 * (t - w.tHit)]);
          drawWolf(ctx, { x: st.pos[0], y: st.pos[1], s: w.s, face: -w.side, phase: tq * 2.6, mode: st.mode, jaw: 1, pitch: st.mode === 'leap' ? -18 : 0, t: tq, seed: w.seed }, glow);
          // hit seam appears at contact, held until the burst
          if (t > w.tHit) { ctx.save(); ctx.translate(...w.to); ctx.rotate(0.1 * w.side); ctx.fillStyle = '#fff'; ctx.fillRect(-w.s * 0.6, -5, w.s * 1.2, 10); ctx.restore(); }
        } else {
          inkBurst(ctx, w.to[0], w.to[1], t - burstT, w.seed, 1.4, glow, [w.side * 0.8, -0.5]);
        }
      }
    };
    drawPack(true);
    // spin smear: a flat ellipse ring around her waist; back half drawn behind her
    const spinU = clamp((b - 54.8) / 0.9);
    const J = solve(pose(t).p, pose(t).root, S, G);
    const ringC = [J.pelvis[0], J.pelvis[1] - 0.12 * S];
    const smearAlpha = (spinU > 0 && spinU < 1) ? 1 : (b >= 55.7 && b < 56.2 ? 1 - (b - 55.7) / 0.5 : 0);
    if (smearAlpha > 0) {
      ctx.save(); ctx.translate(...ringC); ctx.scale(1, 0.32);
      glow.save(); glow.translate(...ringC); glow.scale(1, 0.32);
      const a1 = lerp(-Math.PI / 2, Math.PI * 1.5, ease.io(clamp(spinU)));
      smearArc(ctx, 0, 0, 0.62 * S, 0.9 * S, Math.max(-Math.PI / 2, a1 - Math.PI * 1.6), a1, glow, smearAlpha);
      ctx.restore(); glow.restore();
    }
    drawHero(ctx, pose, (b > 54.7 && b < 56) ? onN(t, 1) : tq, { S, ground: G, glow });
    drawPack(false);
    if (b > 55.5) {
      ring(ctx, ringC[0], G - 10, (t - burstT) / 0.8, 1300, '#ffffff', 0.18, 40, glow);
      puffs(ctx, CX, G, (t - burstT) / 1.1, 55, 2.2, P.snow, P.snowS, [0, -1], 2.2);
    }
    ctx.restore(); glow.restore();
    if (b > 55.4 && b < 56.3) radialLines(ctx, W / 2, H * 0.55, onN(t, 1), 1, '#ffffff', 9, 0.3, 0.55);
    snowfall(ctx, t, { n: 60, speed: 40, wind: -80 });
  });
  hit(55.5, 'impact', 2); hit(55.5, 'flash', 3);
}

// ---------------------------------------------------------------- S7c  recoil shot -> flying knee (58-62)
{
  const S = 680, G = 1010;
  const hero = new Actor({ face: 1, lean: 20, wa: 190, wx: -0.1, wy: 0.05, g1: 0.25, g2: 0.5, two: 1, bside: 1, brow: 1,
    fx1: 0.3, fy1: 0.44, fx2: -0.34, fy2: 0.46, windx: -0.6, head: -5 });
  // aim the barrel back (muzzle left), brace
  hero.key(58, 'io', {});
  hero.key(58.8, 'io', { wa: 182, lean: 30, sq: 0.9, fx1: 0.34, fy1: 0.38, fx2: -0.4, fy2: 0.4 });
  // BANG at 59: thrown forward, knee drives up
  hero.key(59.0, 'lin', { sq: 0.9 });
  hero.key(59.12, 'outx', { lean: 48, sq: 1.1, fx1: 0.2, fy1: 0.18, fx2: -0.32, fy2: 0.42, gnd: 0, mouth: 1, wa: 200 });
  hero.key(59.5, 'io', { lean: 30, fx1: 0.26, fy1: 0.12, fx2: -0.2, fy2: 0.44, sq: 1 });
  hero.key(59.6, 'outx', { lean: 38 });
  hero.key(60.6, 'io', { lean: 10, fx1: 0.22, fy1: 0.38, fx2: -0.24, fy2: 0.42, mouth: 0, wa: 160 });
  hero.key(61.2, 'out', { gnd: 1, lean: 26, sq: 0.9, fx1: 0.34, fy1: 0.4, fx2: -0.36, fy2: 0.42 });
  hero.key(61.8, 'io', { sq: 1 });
  const X0 = 520;
  const rootX = (t) => {
    const tt = t - b2t(59);
    if (tt < 0) return X0;
    // recoil impulse: fast then decelerating (drag), stopped by the knee impact at 59.5, then drift
    const k = 5.5, v0 = 2600;
    const flight = X0 + v0 / k * (1 - Math.exp(-k * Math.min(tt, 0.2)));
    if (tt < 0.2) return flight;
    return flight + 260 * (1 - Math.exp(-(tt - 0.2) * 2.5));
  };
  hero.over((t, p, root) => {
    const tt = t - b2t(59);
    root[0] = rootX(t);
    root[1] = G - 0.47 * S;
    if (tt > 0 && tt < 0.88) root[1] -= Math.sin(clamp(tt / 0.88) * Math.PI) * 0.5 * S;
  });
  const pose = hero.fn();
  const knee = (t) => solve(pose(t).p, pose(t).root, S, G).kn;
  const K = knee(b2t(59.2));
  const wolf = { s: 420, t0: b2t(58.2), tHit: b2t(59.2), from: [1900, G - 150], to: [K[0] + 0.45 * 420, K[1] - 0.05 * 420] };
  shot(58, 62, 's07c_recoil', (E) => {
    const { ctx, glow, t } = E;
    const b = t2b(t), tq = onN(t, 2);
    const camx = lerp(0, 380, ease.io(clamp((b - 59) / 1.2)));
    const sh = shakeXY(t, 26 * hitDecay(t, 59, 8) + 20 * hitDecay(t, 59.5, 8));
    ctx.save(); ctx.translate(-camx + sh[0], sh[1]);
    glow.save(); glow.translate(-camx + sh[0], sh[1]);
    night(ctx, glow, t, { moonXY: [1500 + camx * 0.9, 230], moonR: 150, bite: 0.62, drain: 0.5, horizon: 620, snowY: 890, camx: camx });
    // the wolf lunge -> knee to the jaw at 59.5 -> launched up and away, bursts at 60.2
    const tBurst = b2t(60.2);
    if (t < wolf.tHit) {
      const u = clamp((t - wolf.t0) / (wolf.tHit - wolf.t0));
      const pos = t < wolf.t0 ? wolf.from : arcPos(wolf.from, wolf.to, ease.in2(u), 180);
      drawWolf(ctx, { x: pos[0], y: pos[1], s: wolf.s, face: -1, phase: tq * 2.6, mode: t < wolf.t0 ? 'run' : 'leap', jaw: 1, pitch: -10, t: tq, seed: 91 }, glow);
    } else if (t < tBurst) {
      const tt = t - wolf.tHit;
      const pos = [wolf.to[0] + 1400 * tt, wolf.to[1] - 1500 * tt + 1800 * tt * tt];
      ctx.save(); ctx.translate(...pos); ctx.rotate(-tt * 9); ctx.translate(-pos[0], -pos[1]);
      drawWolf(ctx, { x: pos[0], y: pos[1], s: wolf.s, face: -1, phase: 0, mode: 'hurt', jaw: 1, t: tq, seed: 91 }, glow);
      ctx.restore();
    } else {
      const tt = tBurst - wolf.tHit;
      inkBurst(ctx, wolf.to[0] + 1400 * tt, wolf.to[1] - 1500 * tt + 1800 * tt * tt, t - tBurst, 91, 1.8, glow, [0.6, -0.4]);
    }
    // afterimages during the recoil flight
    if (b > 59 && b < 59.6) for (let k = 3; k >= 1; k--) { ctx.globalAlpha = 0.22; drawHero(ctx, pose, t - k * 0.035, { S, ground: G }); }
    ctx.globalAlpha = 1;
    const J = drawHero(ctx, pose, (b > 58.9 && b < 59.7) ? onN(t, 1) : tq, { S, ground: G, glow });
    // muzzle blast (pointing back) + recoil shockwave + snow blown back
    if (b >= 59 && b < 59.7) {
      const Js = solve(pose(b2t(59)).p, pose(b2t(59)).root, S, G);
      const d = norm(sub(Js.muzzle, Js.grip));
      muzzle(ctx, Js.muzzle[0], Js.muzzle[1], d, t - b2t(59), 2.4, glow);
      ring(ctx, Js.muzzle[0], Js.muzzle[1], (t - b2t(59)) / 0.4, 420, '#ffffff', 1.0, 22, glow);
      puffs(ctx, X0 - 60, G, (t - b2t(59)) / 1.0, 61, 1.8, P.snow, P.snowS, [-1, -0.3], 0.8);
    }
    // knee impact star
    if (b >= 59.5 && b < 59.9) {
      const k = knee(b2t(59.5)); const a = 1 - (b - 59.5) / 0.4;
      ctx.save(); ctx.translate(k[0] + 40, k[1] - 20); ctx.fillStyle = '#fff'; ctx.globalAlpha = a;
      pathPoly(ctx, [[0, -160], [22, -22], [200, 0], [22, 22], [0, 160], [-22, 22], [-120, 0], [-22, -22]]); ctx.fill();
      ctx.restore(); ctx.globalAlpha = 1;
    }
    ctx.restore(); glow.restore();
    if (b > 59 && b < 59.6) streakLines(ctx, onN(t, 1), [-1, 0], 1.3, '#ffffff', 12, 0.55);
    snowfall(ctx, t, { n: 60, speed: 40, wind: -200 });
  });
  hit(59, 'flash', 3); hit(59.5, 'impact', 2);
}

// ---------------------------------------------------------------- S7d  the pile, and the burst (62-68)
{
  const S = 520, G = 1000, CX = 960;
  const hero = new Actor({ face: -1, lean: 30, wa: -30, wx: 0.2, wy: 0.02, g1: 0.35, two: 0, bside: -1, brow: 1,
    fx1: 0.34, fy1: 0.4, fx2: -0.36, fy2: 0.42, windx: 0.4 });
  hero.key(62, 'io', {});
  hero.key(63.5, 'io', { lean: 50, sq: 0.8, head: 20, fx1: 0.3, fy1: 0.3, fx2: -0.3, fy2: 0.34 });     // buried, crouching
  hero.key(66, 'lin', { lean: 50, sq: 0.8 });
  hero.key(66.15, 'outx', { lean: -12, sq: 1.08, head: -18, wa: -110, wx: 0.05, wy: -0.25, mouth: 1, fx1: 0.28, fy1: 0.48, fx2: -0.32, fy2: 0.48, fire: 1 });
  hero.key(67.5, 'io', { lean: 6, sq: 1, mouth: 0.2, wa: -95 });
  hero.over((t, p, root) => { root[0] = CX; root[1] = G - 0.48 * S + (1 - p.sq) * 0.5 * S; });
  const pose = hero.fn();
  const pilers = [];
  { const r = rng(123);
    for (let i = 0; i < 12; i++) {
      const a = lerp(-2.7, -0.45, r()), dist = 900 + r() * 500;
      pilers.push({ from: [CX + Math.cos(a) * dist * 1.4, G + Math.sin(a) * dist * 0.5 - 60], to: [CX + (r() - 0.5) * 360, G - 120 - r() * 300],
        t0: b2t(62 + r() * 1.2), t1: b2t(63.2 + r() * 1.0), s: 240 + r() * 150, seed: 130 + i, face: Math.cos(a) > 0 ? -1 : 1, rot: (r() - 0.5) * 0.8 });
    } }
  const tB = b2t(66);
  shot(62, 68, 's07d_pile', (E) => {
    const { ctx, glow, t } = E;
    const b = t2b(t), tq = onN(t, 2);
    const tension = clamp((b - 64.2) / 1.8);
    const sh = shakeXY(t, 5 * tension + 34 * hitDecay(t, 66, 5));
    ctx.save(); ctx.translate(sh[0], sh[1]);
    glow.save(); glow.translate(sh[0], sh[1]);
    night(ctx, glow, t, { moonXY: [1540, 220], moonR: 150, bite: 0.62, drain: 0.6, horizon: 620, snowY: 880 });
    if (b < 66) {
      drawHero(ctx, pose, tq, { S, ground: G, glow });
      for (const w of pilers) {
        if (t < w.t0) continue;
        const u = clamp((t - w.t0) / (w.t1 - w.t0));
        let pos = arcPos(w.from, w.to, ease.in2(u), 220);
        if (u >= 1) pos = add(w.to, [3 * Math.sin(t * 30 + w.seed) * tension, 2 * Math.cos(t * 27 + w.seed) * tension]);
        ctx.save(); ctx.translate(...pos); ctx.rotate(u >= 1 ? w.rot : 0); ctx.translate(-pos[0], -pos[1]);
        drawWolf(ctx, { x: pos[0], y: pos[1], s: w.s, face: w.face, phase: tq * 2.6, mode: u < 1 ? 'leap' : 'crouch', jaw: 0.8, t: tq, seed: w.seed }, glow);
        ctx.restore();
      }
      // light cracks leaking through the mound
      if (tension > 0) {
        const r = rng(Math.floor(t * 12));
        for (let i = 0; i < Math.floor(4 + tension * 14); i++) {
          const a = -Math.PI / 2 + (r() - 0.5) * 2.6, L = (160 + r() * 360) * tension;
          const c0 = [CX + (r() - 0.5) * 80, G - 250];
          const pts = [c0, add(c0, [Math.cos(a) * L * 0.5 + (r() - 0.5) * 60, Math.sin(a) * L * 0.5]), add(c0, [Math.cos(a) * L, Math.sin(a) * L])];
          pathPoly(ctx, taper(pts, 14 * tension, 1, 10 * tension)); ctx.fillStyle = r() > 0.5 ? P.yellow : P.orange; ctx.fill();
          pathPoly(glow, taper(pts, 40 * tension, 4, 30 * tension)); glow.fillStyle = P.orange; glow.fill();
        }
      }
    } else {
      const age = t - tB;
      // explosion: layered triangle fire burst + radial light blades
      const R = 1500 * ease.outx(clamp(age / 0.6));
      if (age < 0.9) {
        const r = rng(7);
        for (let i = 0; i < 26; i++) {
          const a = r() * TAU, w = 0.05 + r() * 0.08, L = R * (0.6 + r() * 0.6);
          const c = [P.pink, P.orange, P.yellow][i % 3];
          ctx.globalAlpha = 1 - clamp((age - 0.35) / 0.55);
          pathPoly(ctx, [[CX, G - 260], [CX + Math.cos(a - w) * L, G - 260 + Math.sin(a - w) * L], [CX + Math.cos(a + w) * L, G - 260 + Math.sin(a + w) * L]]);
          ctx.fillStyle = c; ctx.fill();
        }
        ctx.globalAlpha = 1;
      }
      // wolves flung outward, spinning, dissolving
      for (const w of pilers) {
        const d = norm(sub(w.to, [CX, G - 260]));
        const v = 1700 + (w.seed % 5) * 250;
        const pos = [w.to[0] + d[0] * v * age, w.to[1] + (d[1] * v - 500) * age + 1500 * age * age];
        if (age < 0.55) {
          ctx.save(); ctx.translate(...pos); ctx.rotate(w.rot + age * (w.seed % 2 ? 8 : -8)); ctx.translate(-pos[0], -pos[1]);
          drawWolf(ctx, { x: pos[0], y: pos[1], s: w.s, face: w.face, phase: 0, mode: 'hurt', jaw: 1, t: tq, seed: w.seed, alpha: 1 - age * 1.5 }, glow);
          ctx.restore();
        }
        inkBurst(ctx, pos[0], pos[1], age - 0.3, w.seed, 1.0, glow, d);
      }
      ring(ctx, CX, G - 10, age / 0.9, 1800, P.yellow, 0.2, 60, glow);
      ring(ctx, CX, G - 260, age / 0.6, 900, '#ffffff', 1.0, 30, glow);
      puffs(ctx, CX, G, age / 1.2, 77, 2.6, P.snow, P.snowS, [0, -1], 2.6);
      // her: standing tall in the crater, embers and fire licking up
      for (let i = 0; i < 6; i++) flame(ctx, CX - 180 + i * 72, G + 6, 90, 150 + 60 * Math.sin(i * 2 + t * 9), onN(t, 2), i, -Math.PI / 2, glow);
      drawHero(ctx, pose, onN(t, 2), { S, ground: G, glow });
    }
    ctx.restore(); glow.restore();
    if (b > 66 && b < 67) radialLines(ctx, CX, G - 260, onN(t, 1), 1.2, P.yellow, 3, 0.25, 0.7);
    embers(ctx, t, { n: b > 66 ? 90 : 20, seed: 12, glow, alpha: 0.9, size: 1.3 });
  });
  hit(66, 'impact', 3); hit(66, 'flash', 5);
}
