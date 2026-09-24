// 7a — the tracking run: two kills at speed.  Beats 44-52.
import { W, H, b2t, lerp, clamp, ease, onN, sub, add, mul, norm, len, TAU } from '../engine.js';
import { P } from '../palette.js';
import { shot, hit } from '../film.js';
import { Actor, runCycle } from '../actor.js';
import { drawHero, solve } from '../hero.js';
import { drawWolf } from '../wolf.js';
import { Forest, sky, stars, snowField } from '../bg.js';
import { inkBurst, smearTrail, streakLines, puffs, embers, snowfall } from '../fx.js';

const B0 = 44, B1 = 52;
const S = 760, GROUND = 1010, SPEED = 1500;          // px/s in world
const far = new Forest(11, 60, [-2000, 12000], 610, 150, 260, { base: P.pineFar, shade: P.pineFarS, snow: '#c9cdf6' }, 0.25);
const mid = new Forest(12, 44, [-2000, 16000], 720, 260, 420, { base: P.pine, shade: P.pineS, snow: P.pineSnow, line: P.line, lw: 2 }, 0.55);

const X0 = 0;
const hero = new Actor({ lean: 32, wa: 158, wx: -0.04, wy: 0.16, g1: 0.62, two: 0, bside: -1, run: 1, __S: S, windx: -1.4 });
hero.key(B0, 'lin', { lean: 32, wa: 158 });
// kill 1: wind back, sweep through (contact at 48), overshoot, recover
hero.key(47.2, 'io', { wa: 158, lean: 32, run: 1, g1: 0.62 });
hero.key(47.75, 'io', { wa: 190, lean: 38, wx: -0.1, wy: 0.14, g1: 0.4, run: 0.3, brow: 1 });
hero.key(48.0, 'in2', { wa: 338, lean: 14, wx: 0.12, wy: 0.02, mouth: 0.8 });
hero.key(48.35, 'outx', { wa: 405, lean: 8, wx: 0.08, wy: -0.02, mouth: 0.2 });
hero.key(49.3, 'io', { wa: 518, lean: 32, wx: -0.04, wy: 0.16, g1: 0.62, run: 1, mouth: 0, brow: 0 });
// kill 2: hop + full spin backhand at 50.5 (rot -360, blade sweeps a circle)
hero.key(49.9, 'io', { rot: 0, run: 1, wa: 518 });
hero.key(50.15, 'io', { run: 0, fx1: 0.12, fy1: 0.36, fx2: -0.1, fy2: 0.4, gnd: 0 });
hero.key(50.5, 'in2', { rot: -250, wa: 518 - 200, g1: 0.4 });
hero.key(50.85, 'out', { rot: -360, wa: 518 - 360 });
hero.key(51.3, 'io', { g1: 0.62 });
hero.key(50.86, 'step', { rot: 0 });
hero.key(51.2, 'io', { run: 1, gnd: 0 });
hero.over(runCycle);
// root: runs right at SPEED; hop between 50.0 and 50.9
hero.over((t, p, root) => {
  const x = X0 + SPEED * (t - b2t(B0));
  let y = GROUND - 0.49 * S;
  const h0 = b2t(50.0), h1 = b2t(50.9);
  if (t > h0 && t < h1) { const u = (t - h0) / (h1 - h0); y -= Math.sin(u * Math.PI) * 0.35 * S; }
  root[0] = x; root[1] = y + (root[1] - (hero.tr.get('ry', t) || 0));
});
const pose = hero.fn();
const tip = (t) => { const q = pose(t); return solve(q.p, q.root, S, GROUND).btip; };

// wolves (world coords): two pacers + two attackers solved backward from the blade
const heroX = (t) => X0 + SPEED * (t - b2t(B0));
const pacers = [
  { off: 520, dy: 40, s: 330, seed: 3, ph: 0.2 },
  { off: -620, dy: -110, s: 260, seed: 4, ph: 0.6, far: true },
];
const C1 = tip(b2t(48.0));
const leap1 = { t0: b2t(46.9), t1: b2t(48.0), p0: [heroX(b2t(46.9)) + 780, GROUND - 0.36 * 360], p1: [C1[0] + 0.32 * 360, C1[1] + 0.14 * 360], s: 360, seed: 5 };
const C2 = tip(b2t(50.5));
const leap2 = { t0: b2t(49.6), t1: b2t(50.5), p0: [heroX(b2t(49.6)) - 700, GROUND - 0.36 * 340], p1: [C2[0] - 0.3 * 340, C2[1] + 0.1 * 340], s: 340, seed: 6 };
function arc(L, t, g = 2600) {
  const T = L.t1 - L.t0, tau = t - L.t0;
  const vy = (L.p1[1] - L.p0[1] - 0.5 * g * T * T) / T;
  return [lerp(L.p0[0], L.p1[0], tau / T), L.p0[1] + vy * tau + 0.5 * g * tau * tau];
}

shot(B0, B1, 's07a_run', (E) => {
  const { ctx, glow, t } = E;
  const tq = onN(t, 2);
  const camx = heroX(t) - 900 + 50 * Math.sin(t * 1.3), camy = 0;
  // --- background (screen space parallax)
  ctx.setTransform(1, 0, 0, 1, 0, 0);
  const g = ctx.createLinearGradient(0, 0, 0, 700); g.addColorStop(0, P.sky0); g.addColorStop(1, P.sky1);
  ctx.fillStyle = g; ctx.fillRect(0, 0, W, H);
  stars(ctx, t, 5, 90, 0.7);
  ctx.fillStyle = '#8f96dc'; ctx.fillRect(0, 600, W, 300);
  far.draw(ctx, camx, 0);
  ctx.fillStyle = '#b4b9f0'; ctx.fillRect(0, 700, W, 400);
  mid.draw(ctx, camx, 0);
  snowField(ctx, GROUND - 20, camx * 1.0);
  // ground speed streaks
  streakLines(ctx, tq, [-1, 0], 0.7, '#ffffff', 3, 0.35);
  // --- world layer
  ctx.save(); ctx.translate(-camx, 0);
  glow.save(); glow.translate(-camx, 0);
  const wt = t;
  // far pacer behind
  for (const pc of pacers.filter((q) => q.far)) {
    drawWolf(ctx, { x: heroX(t) + pc.off, y: GROUND + pc.dy - 0.4 * pc.s, s: pc.s, face: 1, phase: onN(t, 2) * 2.8 + pc.ph, mode: 'run', t: tq, seed: pc.seed, alpha: 0.9 }, glow);
  }
  // attackers
  for (const [L, burstAt, dir] of [[leap1, b2t(48.0), [0.6, -0.4]], [leap2, b2t(50.5), [-0.6, -0.3]]]) {
    if (t < L.t0 - 0.6) continue;
    if (t < L.t1) {
      const pos = t < L.t0 ? [L.p0[0] + (t - L.t0) * (L.p0[0] > heroX(t) ? -200 : 900), L.p0[1]] : arc(L, t);
      const mode = t < L.t0 ? 'run' : 'leap';
      const vx = L.p1[0] - L.p0[0];
      drawWolf(ctx, { x: pos[0], y: pos[1], s: L.s, face: vx < 0 ? -1 : 1, phase: onN(t, 2) * 2.8, mode, jaw: t > L.t0 ? 1 : 0.3, pitch: mode === 'leap' ? -12 : 0, t: tq, seed: L.seed }, glow);
    } else {
      const age = t - burstAt;
      // the wolf splits along the cut and the halves tumble apart before dissolving
      if (age < 0.5) {
        const cut = -0.6 * (dir[0] > 0 ? 1 : -1);
        for (const side of [1, -1]) {
          ctx.save();
          const cx = L.p1[0], cy = L.p1[1];
          ctx.translate(cx, cy); ctx.rotate(cut);
          ctx.beginPath(); ctx.rect(-2000, side > 0 ? -2000 : 0, 4000, 2000); ctx.clip();
          ctx.rotate(-cut); ctx.translate(-cx, -cy);
          const drift = [dir[0] * 500 * age + side * 60 * age, side * 220 * age + 900 * age * age];
          ctx.translate(drift[0], drift[1]);
          ctx.translate(cx, cy); ctx.rotate(side * age * 2.5); ctx.translate(-cx, -cy);
          drawWolf(ctx, { x: cx, y: cy, s: L.s, face: (L.p1[0] - L.p0[0]) < 0 ? -1 : 1, phase: 0, mode: 'leap', jaw: 1, pitch: -12, t: tq, seed: L.seed, alpha: 1 - age * 1.6 }, null);
          ctx.restore();
        }
        // hot seam
        ctx.save(); ctx.translate(L.p1[0], L.p1[1]); ctx.rotate(-0.6 * (dir[0] > 0 ? 1 : -1));
        ctx.fillStyle = '#fff'; ctx.globalAlpha = 1 - age * 2; ctx.fillRect(-L.s * 0.7, -6, L.s * 1.4, 12); ctx.restore(); ctx.globalAlpha = 1;
      }
      inkBurst(ctx, L.p1[0], L.p1[1], age, L.seed, 1.7, glow, dir);
    }
  }
  // blade smear (tip history)
  const hist = [];
  for (let k = 0; k < 8; k++) hist.push(tip(t - k / 60));
  const sp = len(sub(hist[0], hist[2])) * 30;
  if (sp > 1800) smearTrail(ctx, hist, 0.06 * S, glow, clamp((sp - 1800) / 3000));
  // hero
  drawHero(ctx, pose, tq, { S, ground: GROUND, glow, light: [-0.55, -0.83] });
  // kick-up snow at the feet
  const J = solve(pose(t).p, pose(t).root, S, GROUND);
  puffs(ctx, J.footn[0] - 40, GROUND, (t * 2.6) % 1, Math.floor(t * 2.6), 0.5, P.snow, P.snowS, [-1, -0.4], 0.6);
  // near pacer in front (foreground, bigger, slightly lower)
  for (const pc of pacers.filter((q) => !q.far)) {
    drawWolf(ctx, { x: heroX(t) + pc.off + 40 * Math.sin(t * 2), y: GROUND + pc.dy - 0.4 * pc.s, s: pc.s, face: 1, phase: onN(t, 2) * 2.8 + pc.ph, mode: 'run', t: tq, seed: pc.seed }, glow);
  }
  ctx.restore(); glow.restore();
  embers(ctx, t, { n: 30, seed: 7, region: [0, 200, W, 800], glow, alpha: 0.8 });
  snowfall(ctx, t * 3, { n: 80, speed: 40, wind: -900, size: 1.1 });
});
hit(48.0, 'impact', 2); hit(48.0, 'flash', 4);
hit(50.5, 'flash', 3);
