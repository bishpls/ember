// The heroine: side-view 2D puppet.  Units: 1.0 = her full height.  Screen space, y down.
import { clamp, lerp, rot, add, sub, mul, len, norm, perp, ik2, capsule, taper, pathPoly, pathSmooth, cel,
  lagged, noise1, fbm, D2R, TAU, smooth } from './engine.js';
import { P } from './palette.js';

export const POSE0 = {
  lean: 4, head: 0, rot: 0, sq: 1, face: 1,
  wx: 0.10, wy: 0.10, wa: -80, g1: 0.30, g2: 0.55, two: 1, held: 1, unfold: 1, bside: 1,
  hx: 0.06, hy: 0.14,            // free far-hand target (rel. chest)
  h1x: 0.04, h1y: 0.16,          // free near-hand target when weapon not held
  fx1: 0.06, fy1: 0.50, fx2: -0.06, fy2: 0.50,   // feet rel. pelvis
  gnd: 1, eye: 1, mouth: 0, smile: 0, brow: 0, windx: -0.6, windy: 0, cloakAmt: 1, fire: 0,
};
const THIGH = 0.245, SHIN = 0.245, TORSO = 0.30, UARM = 0.16, FARM = 0.15, SHAFT = 0.98, BLADE = 0.52;

// pose(t) -> {p, root}; world: {S (px/unit), ground (y px)}
export function solve(p, root, S, ground = null) {
  const f = p.face >= 0 ? 1 : -1;
  const r = p.rot * D2R;
  const sq = p.sq, sx = 1 / Math.sqrt(sq);
  const Wp = (x, y) => { let q = [x * sx, y * sq]; q = rot(q, r); return [root[0] + f * q[0] * S, root[1] + q[1] * S]; };
  const L = p.lean * D2R;
  const chestL = [Math.sin(L) * TORSO, -Math.cos(L) * TORSO];
  const hd = L + p.head * D2R;
  const J = {};
  J.f = f; J.S = S; J.Wp = Wp; J.p = p; J.r = r;
  J.pelvis = Wp(0, 0);
  J.chest = Wp(...chestL);
  J.neck = Wp(chestL[0] + Math.sin(L) * 0.03, chestL[1] - Math.cos(L) * 0.03);
  J.headL = [chestL[0] + Math.sin(hd) * 0.1, chestL[1] - Math.cos(hd) * 0.1];
  J.head = Wp(...J.headL);
  J.hd = hd;
  J.sn = Wp(chestL[0] + 0.012, chestL[1] + 0.03);
  J.sf = Wp(chestL[0] - 0.02, chestL[1] + 0.02);
  J.hn = Wp(0.012, 0.005);
  J.hf = Wp(-0.012, 0.0);
  // weapon (local)
  const held = clamp(p.held);
  const ext = lerp(0.45, 1, smooth(p.unfold));
  const Ls = SHAFT * ext;
  const gL = [lerp(chestL[0] - 0.07, chestL[0] + p.wx, held), lerp(chestL[1] + 0.05, chestL[1] + p.wy, held)];
  const wa = lerp(-125, p.wa, held) * D2R;
  const u = [Math.cos(wa), Math.sin(wa)];
  const buttL = sub(gL, mul(u, p.g1 * Ls));
  const headL = add(buttL, mul(u, Ls));
  J.butt = Wp(...buttL); J.whead = Wp(...headL); J.grip = Wp(...gL);
  J.muzzle = Wp(...add(headL, mul(u, 0.05)));
  J.Ls = Ls * S;
  // blade polygon (local): from head, perpendicular (side = bside), curving back toward the butt
  const side = p.bside >= 0 ? 1 : -1;
  const ua = lerp(Math.PI * 0.95, Math.PI * 0.5, smooth(p.unfold));
  const bdir = rot(u, side * ua);
  const spine = [], edge = [];
  for (let i = 0; i <= 12; i++) {
    const s = i / 12;
    const c = add(add(headL, mul(bdir, BLADE * s)), mul(u, -0.13 * s * s * smooth(p.unfold)));
    const th = 0.062 * (1 - s ** 1.25) + 0.002;
    const nrm = norm(perp(bdir));
    const toward = (nrm[0] * -u[0] + nrm[1] * -u[1]) > 0 ? 1 : -1;
    spine.push(Wp(...add(c, mul(nrm, -toward * th * 0.38))));
    edge.push(Wp(...add(c, mul(nrm, toward * th * 0.62))));
  }
  J.bspine = spine; J.bedge = edge; J.btip = edge[12];
  // hands
  const g2L = add(buttL, mul(u, p.g2 * Ls));
  const hN = [lerp(chestL[0] + p.h1x, gL[0], held), lerp(chestL[1] + p.h1y, gL[1], held)];
  const two = clamp(p.two) * held;
  const hF = [lerp(chestL[0] + p.hx, g2L[0], two), lerp(chestL[1] + p.hy, g2L[1], two)];
  const bendA = f * (Math.cos(r) >= -0.2 ? 1 : -1);
  [J.en, J.handn] = ik2(J.sn, Wp(...hN), UARM * S, FARM * S, bendA);
  [J.ef, J.handf] = ik2(J.sf, Wp(...hF), UARM * S, FARM * S, bendA);
  // feet (+ ground clamp)
  let fn = Wp(p.fx1, p.fy1), ff = Wp(p.fx2, p.fy2);
  if (ground != null && p.gnd > 0) { fn[1] = lerp(fn[1], ground, p.gnd); ff[1] = lerp(ff[1], ground, p.gnd); }
  const bendL = -f * (Math.cos(r) >= -0.2 ? 1 : -1);
  [J.kn, J.footn] = ik2(J.hn, fn, THIGH * S, SHIN * S, bendL);
  [J.kf, J.footf] = ik2(J.hf, ff, THIGH * S, SHIN * S, bendL);
  // body frame vectors in world (for attaching things)
  J.up = norm(sub(J.chest, J.pelvis));
  J.fwd = [f * Math.cos(r), f * Math.sin(r) * 0 + Math.sin(r)];
  J.fwd = norm(rot([f, 0], f * r));
  return J;
}

// ------------------------------------------------------------------------------ drawing
const LW = (S) => Math.max(1.6, S * 0.0052);

// continuous limb silhouette through joints with a width profile (muscle shape, no joint circles)
export function limbPoly(ptsW) {
  // ptsW: [[x,y,w], ...]
  const n = ptsW.length, L = [], R = [];
  for (let i = 0; i < n; i++) {
    const a = ptsW[Math.max(0, i - 1)], b = ptsW[Math.min(n - 1, i + 1)];
    const d = norm([b[0] - a[0], b[1] - a[1]]), pp = perp(d);
    L.push([ptsW[i][0] + pp[0] * ptsW[i][2], ptsW[i][1] + pp[1] * ptsW[i][2]]);
    R.push([ptsW[i][0] - pp[0] * ptsW[i][2], ptsW[i][1] - pp[1] * ptsW[i][2]]);
  }
  // rounded caps
  const a0 = ptsW[0], an = ptsW[n - 1];
  const d0 = norm([ptsW[1][0] - a0[0], ptsW[1][1] - a0[1]]), dn = norm([an[0] - ptsW[n - 2][0], an[1] - ptsW[n - 2][1]]);
  const cap0 = [a0[0] - d0[0] * a0[2] * 0.8, a0[1] - d0[1] * a0[2] * 0.8];
  const capn = [an[0] + dn[0] * an[2] * 0.7, an[1] + dn[1] * an[2] * 0.7];
  return [cap0].concat(L, [capn], R.reverse());
}
function leg(ctx, hip, knee, ankle, base, shade, light, S) {
  const thigh = sub(knee, hip), shin = sub(ankle, knee);
  const q = (a, v, u) => add(a, mul(v, u));
  const pts = [[...hip, 0.05 * S], [...q(hip, thigh, 0.4), 0.047 * S], [...q(hip, thigh, 0.85), 0.034 * S],
    [...knee, 0.03 * S], [...q(knee, shin, 0.3), 0.032 * S], [...q(knee, shin, 0.7), 0.024 * S], [...ankle, 0.02 * S]];
  const poly = limbPoly(pts);
  cel(ctx, (c) => pathSmooth(c, poly, true, 0.7), base, shade, light, 0.45, 0.04 * S, P.line, LW(S));
}
function arm(ctx, sh, el, wr, base, shade, light, S) {
  const up = sub(el, sh), fo = sub(wr, el);
  const q = (a, v, u) => add(a, mul(v, u));
  const pts = [[...sh, 0.03 * S], [...q(sh, up, 0.45), 0.026 * S], [...el, 0.02 * S], [...q(el, fo, 0.35), 0.022 * S],
    [...wr, 0.016 * S]];
  const poly = limbPoly(pts);
  cel(ctx, (c) => pathSmooth(c, poly, true, 0.7), base, shade, light, 0.45, 0.025 * S, P.line, LW(S));
}
function limb(ctx, a, ra, b, rb, base, shade, light, S) {
  const pts = capsule(a, ra, b, rb, 6);
  cel(ctx, (c) => pathPoly(c, pts), base, shade, light, 0.5, ra, P.line, LW(S));
}

function boot(ctx, J, knee, foot, light, S) {
  // boot shaft from mid-shin + foot wedge pointing forward
  const d = norm(sub(foot, knee));
  const mid = add(knee, mul(sub(foot, knee), 0.35));
  const f = J.f;
  const toe = add(foot, [f * 0.075 * S, 0.004 * S]);
  const heel = add(foot, [-f * 0.028 * S, 0.012 * S]);
  const w1 = 0.034 * S, w2 = 0.03 * S;
  const pp = perp(d);
  const pts = [add(mid, mul(pp, w1)), add(foot, mul(pp, w2)), toe, add(toe, [0, 0.022 * S]),
    add(heel, [0, 0.012 * S]), heel, sub(foot, mul(pp, w2)), sub(mid, mul(pp, w1))];
  cel(ctx, (c) => pathPoly(c, pts), P.boot, P.bootS, light, 0.4, w1, P.line, LW(S));
  // steel toe cap
  const cap = [add(toe, [-f * 0.03 * S, -0.012 * S]), toe, add(toe, [0, 0.022 * S]), add(toe, [-f * 0.035 * S, 0.022 * S])];
  cel(ctx, (c) => pathPoly(c, cap), P.steel, P.steelS, light, 0.5, 0.02 * S, P.line, LW(S) * 0.8);
  // cuff strap
  const cuff = [add(mid, mul(pp, w1 * 1.05)), add(add(mid, mul(d, 0.03 * S)), mul(pp, w1 * 1.05)),
    sub(add(mid, mul(d, 0.03 * S)), mul(pp, w1 * 1.05)), sub(mid, mul(pp, w1 * 1.05))];
  cel(ctx, (c) => pathPoly(c, cuff), P.strap, P.strapS, light, 0.5, 0.02 * S, P.line, LW(S) * 0.7);
}

function torso(ctx, J, light, S) {
  const Wp = J.Wp;
  const L = J.p.lean * D2R;
  const c = [Math.sin(L) * TORSO, -Math.cos(L) * TORSO];
  const n = [Math.cos(L), Math.sin(L)];   // local forward normal of the spine
  const at = (u, w) => Wp(c[0] * u + n[0] * w, c[1] * u + n[1] * w);
  const pts = [at(-0.02, 0.07), at(0.25, 0.05), at(0.45, 0.047), at(0.62, 0.062), at(0.74, 0.078), at(0.86, 0.066),
    at(0.97, 0.05), at(1.06, 0.03), at(1.08, -0.02), at(1.02, -0.07), at(0.85, -0.062), at(0.6, -0.05), at(0.38, -0.052),
    at(0.15, -0.072), at(-0.05, -0.08), at(-0.14, -0.05), at(-0.15, 0.03), at(-0.1, 0.07)];
  cel(ctx, (cx) => pathSmooth(cx, pts), P.suit, P.suitS, light, 0.35, 0.06 * S, P.line, LW(S));
  // straps: belt + cross strap + buckle
  ctx.lineCap = 'round';
  const belt = [at(0.04, 0.07), at(0.02, -0.075)];
  const belt2 = [at(0.12, 0.066), at(0.1, -0.07)];
  for (const [a, b2] of [belt, belt2]) {
    ctx.beginPath(); ctx.moveTo(...a); ctx.lineTo(...b2);
    ctx.lineWidth = 0.022 * S; ctx.strokeStyle = P.line; ctx.stroke();
    ctx.lineWidth = 0.016 * S; ctx.strokeStyle = P.strap; ctx.stroke();
  }
  ctx.beginPath(); ctx.moveTo(...at(0.9, -0.05)); ctx.lineTo(...at(0.25, 0.06));
  ctx.lineWidth = 0.02 * S; ctx.strokeStyle = P.line; ctx.stroke();
  ctx.lineWidth = 0.013 * S; ctx.strokeStyle = P.strap; ctx.stroke();
  const bk = at(0.03, 0.035);
  ctx.fillStyle = P.buckle; ctx.fillRect(bk[0] - 0.012 * S, bk[1] - 0.01 * S, 0.024 * S, 0.02 * S);
  ctx.lineWidth = LW(S) * 0.6; ctx.strokeStyle = P.line; ctx.strokeRect(bk[0] - 0.012 * S, bk[1] - 0.01 * S, 0.024 * S, 0.02 * S);
}

function headDraw(ctx, J, light, S, t, hairLag) {
  const f = J.f, hd = J.hd + J.r;
  const hc = J.head;
  const R = 0.075 * S;
  const HS = 1.22;
  const loc = (x, y) => { const q = rot([x * f * HS, y * HS], f * hd); return [hc[0] + q[0] * S, hc[1] + q[1] * S]; };
  // --- back hair: ONE mass from the crown down past the nape, clumped jagged tips trailing with lag + wind
  const drag = hairLag;
  const wind = [J.p.windx * S * 0.05, J.p.windy * S * 0.05];
  const tr = (k) => add(mul(add(drag, wind), k), [0, fbm(t * 2.2 + k * 7) * 0.012 * S * k]);
  const hairBack = [loc(0.02, -0.088), loc(-0.04, -0.082), loc(-0.075, -0.05),
    add(loc(-0.11, -0.03), tr(0.35)), add(loc(-0.085, -0.005), tr(0.3)),
    add(loc(-0.13, 0.02), tr(0.55)), add(loc(-0.09, 0.03), tr(0.45)),
    add(loc(-0.12, 0.075), tr(0.7)), add(loc(-0.075, 0.06), tr(0.55)),
    add(loc(-0.085, 0.105), tr(0.8)), add(loc(-0.05, 0.075), tr(0.55)),
    add(loc(-0.04, 0.11), tr(0.6)), loc(-0.02, 0.06), loc(-0.03, 0.02), loc(0.0, -0.03)];
  cel(ctx, (cx) => pathPoly(cx, hairBack), P.hair, P.hairS, light, 0.35, 0.05 * S, P.line, LW(S));
  // --- neck + skull + face (profile)
  limb(ctx, J.neck, 0.022 * S, loc(-0.005, 0.045), 0.02 * S, P.skin, P.skinS, light, S);
  const face = [loc(-0.05, -0.02), loc(-0.045, -0.05), loc(-0.015, -0.07), loc(0.025, -0.066), loc(0.05, -0.04),
    loc(0.058, -0.01), loc(0.072, 0.012), loc(0.06, 0.02), loc(0.058, 0.032), loc(0.05, 0.036), loc(0.046, 0.046),
    loc(0.03, 0.062), loc(0.005, 0.06), loc(-0.02, 0.04), loc(-0.045, 0.012)];
  cel(ctx, (cx) => pathSmooth(cx, face, true, 0.8), P.skin, P.skinS, light, 0.25, R, P.line, LW(S));
  // eye (profile anime eye): thick upper lash + iris sliver + highlight; open amount p.eye
  const eo = clamp(J.p.eye);
  const ec = loc(0.03, -0.012);
  const eh = 0.024 * S * eo;
  const ew = 0.022 * S;
  const dirE = rot([f, 0], f * hd);
  const up = rot([0, -1], f * hd);
  if (eo > 0.08) {
    const irisPts = [add(ec, mul(up, eh * 0.6)), add(add(ec, mul(dirE, ew * 0.55)), mul(up, eh * 0.2)),
      add(add(ec, mul(dirE, ew * 0.4)), mul(up, -eh * 0.5)), add(ec, mul(up, -eh * 0.55)),
      add(add(ec, mul(dirE, -ew * 0.2)), mul(up, -eh * 0.2)), add(add(ec, mul(dirE, -ew * 0.2)), mul(up, eh * 0.4))];
    pathPoly(ctx, irisPts); ctx.fillStyle = J.p.fire > 0.5 ? P.yellow : P.iris; ctx.fill();
    ctx.beginPath(); ctx.arc(...add(add(ec, mul(dirE, ew * 0.05)), mul(up, eh * 0.25)), 0.0045 * S, 0, TAU);
    ctx.fillStyle = '#ffffff'; ctx.fill();
  }
  // upper lash line (always) — lowers to a closed-lid curve as eo -> 0
  const l0 = add(add(ec, mul(dirE, -ew * 0.35)), mul(up, eh * 0.55 + 0.004 * S));
  const l1 = add(add(ec, mul(dirE, ew * 0.75)), mul(up, eh * 0.3 + 0.002 * S));
  const lash = taper([l0, add(mix(l0, l1, 0.5), mul(up, 0.006 * S * (0.4 + eo))), l1], 0.004 * S, 0.012 * S, 0.011 * S);
  pathSmooth(ctx, lash); ctx.fillStyle = P.line; ctx.fill();
  // brow
  const bw = J.p.brow;   // + angry (inner end down)
  const b0 = loc(0.012, -0.046 - 0.004 * bw), b1 = loc(0.05, -0.042 + 0.008 * bw);
  pathSmooth(ctx, taper([b0, mix(b0, b1, 0.5), b1], 0.003 * S, 0.006 * S, 0.007 * S)); ctx.fillStyle = P.hairS; ctx.fill();
  // mouth: p.mouth 0 = closed line, 1 = open shout
  const mo = clamp(J.p.mouth);
  const m0 = loc(0.042, 0.036), m1 = loc(0.058, 0.034);
  if (mo < 0.1) {
    const sm = J.p.smile || 0;
    ctx.beginPath(); ctx.moveTo(...m0); ctx.quadraticCurveTo(...loc(0.05, 0.038 + 0.004 * sm), ...add(m1, rot([0, -0.008 * S * sm], f * hd)));
    ctx.lineWidth = LW(S) * 0.7; ctx.strokeStyle = P.line; ctx.stroke();
  } else {
    const mp = [loc(0.034, 0.033), loc(0.062, 0.03), loc(0.056, 0.03 + 0.03 * mo), loc(0.04, 0.034 + 0.024 * mo)];
    pathPoly(ctx, mp); ctx.fillStyle = '#5a1030'; ctx.fill(); ctx.lineWidth = LW(S) * 0.7; ctx.strokeStyle = P.line; ctx.stroke();
  }
  // --- front hair: bangs + crown spikes over the skull
  const crown = [loc(-0.07, 0.03), loc(-0.078, -0.02), loc(-0.06, -0.065), loc(-0.02, -0.088), loc(0.03, -0.084),
    loc(0.062, -0.06), loc(0.072, -0.03), loc(0.052, -0.035), loc(0.066, -0.004), loc(0.04, -0.028), loc(0.036, 0.004),
    loc(0.018, -0.03), loc(0.004, -0.02), loc(-0.012, -0.04), loc(-0.03, -0.01), loc(-0.035, 0.03)];
  // bangs sway with lag
  const bangs = crown.map((q, i) => (i >= 6 && i <= 12 ? add(q, mul(add(drag, wind), 0.12)) : q));
  cel(ctx, (cx) => pathPoly(cx, bangs), P.hair, P.hairS, light, 0.3, R, P.line, LW(S));
  // red streak clump on the near side
  const st = [loc(0.028, -0.082), loc(0.058, -0.06), loc(0.064, -0.028), loc(0.05, -0.006), loc(0.046, -0.04), loc(0.03, -0.05)];
  cel(ctx, (cx) => pathPoly(cx, st), P.streak, P.streakS, light, 0.3, 0.02 * S, P.line, LW(S) * 0.8);
  // ear peeking through
}

function mix(a, b, u) { return [lerp(a[0], b[0], u), lerp(a[1], b[1], u)]; }

function weapon(ctx, J, light, S, glow) {
  const lw = LW(S);
  // shaft
  const sh = capsule(J.butt, 0.011 * S, J.whead, 0.011 * S, 4);
  cel(ctx, (c) => pathPoly(c, sh), P.shaft, P.shaftS, light, 0.5, 0.01 * S, P.line, lw);
  // red stripe
  ctx.beginPath(); ctx.moveTo(...mix(J.butt, J.whead, 0.12)); ctx.lineTo(...mix(J.butt, J.whead, 0.7));
  ctx.lineWidth = 0.0045 * S; ctx.strokeStyle = P.stripe; ctx.stroke();
  // receiver block near the head
  const u = norm(sub(J.whead, J.butt)), v = perp(u);
  const c0 = add(J.whead, mul(u, -0.14 * S));
  const rb = [add(add(c0, mul(u, 0.1 * S)), mul(v, 0.02 * S)), add(add(c0, mul(u, -0.07 * S)), mul(v, 0.02 * S)),
    add(add(c0, mul(u, -0.07 * S)), mul(v, -0.024 * S)), add(add(c0, mul(u, -0.02 * S)), mul(v, -0.05 * S)),
    add(add(c0, mul(u, 0.0)), mul(v, -0.05 * S)), add(add(c0, mul(u, 0.02 * S)), mul(v, -0.024 * S)),
    add(add(c0, mul(u, 0.1 * S)), mul(v, -0.024 * S))];
  cel(ctx, (c) => pathPoly(c, rb), P.shaft, P.shaftS, light, 0.5, 0.02 * S, P.line, lw);
  const bar = capsule(J.whead, 0.008 * S, J.muzzle, 0.008 * S, 3);
  cel(ctx, (c) => pathPoly(c, bar), P.shaft, P.shaftS, light, 0.5, 0.01 * S, P.line, lw);
  // blade
  const poly = J.bspine.concat([...J.bedge].reverse());
  cel(ctx, (c) => pathSmooth(c, poly, true, 0.6), P.blade, P.bladeS, light, 0.6, 0.03 * S, P.line, lw);
  // hot edge line
  ctx.beginPath(); J.bedge.forEach((q, i) => (i ? ctx.lineTo(...q) : ctx.moveTo(...q)));
  ctx.lineWidth = 0.004 * S; ctx.strokeStyle = P.edge; ctx.stroke();
  if (glow) {
    glow.beginPath(); J.bedge.forEach((q, i) => (i ? glow.lineTo(...q) : glow.moveTo(...q)));
    glow.lineWidth = 0.012 * S; glow.strokeStyle = P.orange; glow.stroke();
  }
}

function hand(ctx, h, elbow, light, S) {
  const d = norm(sub(h, elbow));
  const pts = capsule(h, 0.021 * S, add(h, mul(d, 0.03 * S)), 0.017 * S, 5);
  cel(ctx, (c) => pathPoly(c, pts), P.suit, P.suitS, light, 0.4, 0.02 * S, P.line, LW(S) * 0.8);
}

// cloak: anchored across the shoulders, trailing by the lagged chest motion; tattered hem
function cloakPts(J, S, t, drag, wind) {
  const up = J.up, back = [-J.fwd[0], -J.fwd[1]], fw = J.fwd;
  const down = [-up[0], -up[1]];
  const collarF = add(add(J.neck, mul(fw, 0.028 * S)), mul(down, 0.01 * S));
  const shoulderF = add(add(J.sn, mul(fw, 0.03 * S)), mul(up, 0.012 * S));
  const collarB = add(add(J.neck, mul(back, 0.045 * S)), mul(down, 0.0 * S));
  const shoulderB = add(add(J.sf, mul(back, 0.07 * S)), mul(up, 0.005 * S));
  const n = 7, hem = [];
  const tr = (u) => add(mul(drag, 0.7 + 0.5 * u), mul(wind, 0.45 + 0.55 * u));
  for (let i = 0; i < n; i++) {
    const u = i / (n - 1);                      // 0 = front edge, 1 = back edge
    const anc = mix(shoulderF, shoulderB, u);
    const Lr = (0.34 + 0.12 * u) * S * J.p.cloakAmt;
    const dir = norm(add(mul(down, 1), mul(back, 0.1 + 0.35 * u)));
    let tip = add(add(anc, mul(dir, Lr)), tr(u));
    tip = add(tip, mul(perp(dir), fbm(t * 2.4 + i * 1.3) * 0.035 * S));
    const dv = sub(tip, anc);
    tip = add(anc, mul(norm(dv), Math.min(len(dv), Lr * 1.1)));
    hem.push(tip);
  }
  // bold triangular tears along the hem
  const hemT = [];
  for (let i = 0; i < n; i++) {
    hemT.push(hem[i]);
    if (i < n - 1) {
      const a = hem[i], b2 = hem[i + 1];
      const inward = mul(norm(sub(J.chest, mix(a, b2, 0.5))), (0.035 + 0.045 * hash01(i + 3)) * S);
      hemT.push(add(mix(a, b2, 0.5), inward));
    }
  }
  // front edge drapes from the collar over the near shoulder, back edge from the collar down the spine
  const frontMid = add(mix(shoulderF, hem[0], 0.45), mul(fw, 0.01 * S));
  const backMid = add(add(mix(shoulderB, hem[n - 1], 0.45), mul(back, 0.02 * S)), mul(tr(1), 0.25));
  const poly = [collarF, shoulderF, frontMid].concat(hemT, [backMid, shoulderB, collarB]);
  // lining: the inner face visible toward the back when it billows
  const lin = [shoulderB, backMid, hem[n - 1], hem[n - 2], mix(shoulderB, hem[n - 2], 0.5)];
  return { poly, lin, collarF, collarB };
}
function hash01(i) { const s = Math.sin(i * 91.7) * 43758.5; return s - Math.floor(s); }

// ------------------------------------------------------------------------------ public draw
// poseFn(t) -> {p, root}; draws at time t.  opts: {S, ground, light, glow, t}
export function drawHero(ctx, poseFn, t, { S, ground = null, light = [-0.55, -0.83], glow = null, tint = null } = {}) {
  const { p, root } = poseFn(t);
  const J = solve(p, root, S, ground);
  // follow-through: lagged chest & head vs now
  const chestAt = (tt) => { const q = poseFn(tt); return solve(q.p, q.root, S, ground).chest; };
  const headAt = (tt) => { const q = poseFn(tt); return solve(q.p, q.root, S, ground).head; };
  const lc = lagged(chestAt, t, { freq: 2.2, damp: 0.3, win: 0.8, n: 16 });
  const lh = lagged(headAt, t, { freq: 2.8, damp: 0.35, win: 0.6, n: 12 });
  const cdrag = sub(lc, J.chest), hdrag = sub(lh, J.head);
  const wind = [p.windx * S * 0.12, p.windy * S * 0.12];
  const cl = cloakPts(J, S, t, cdrag, wind);
  // cloak back (lining shows where it curls)
  cel(ctx, (c) => pathSmooth(c, cl.poly, true, 0.35), P.cloak, P.cloakS, light, 0.3, 0.12 * S, P.line, LW(S));
  pathSmooth(ctx, cl.lin, true, 0.4); ctx.fillStyle = P.lining; ctx.fill();
  // far leg + arm
  leg(ctx, J.hf, J.kf, J.footf, P.suitS, P.suitS, light, S);
  boot(ctx, J, J.kf, J.footf, light, S);
  const weaponBehind = p.held < 0.5;
  if (weaponBehind) weapon(ctx, J, light, S, glow);
  arm(ctx, J.sf, J.ef, J.handf, P.suitS, P.suitS, light, S);
  hand(ctx, J.handf, J.ef, light, S);
  // torso, near leg
  torso(ctx, J, light, S);
  leg(ctx, J.hn, J.kn, J.footn, P.suit, P.suitS, light, S);
  boot(ctx, J, J.kn, J.footn, light, S);
  // scarf wrap + head
  const sc = capsule(add(J.neck, mul(J.up, -0.012 * S)), 0.02 * S, add(J.neck, mul(J.up, 0.012 * S)), 0.019 * S, 5);
  headDraw(ctx, J, light, S, t, hdrag);
  cel(ctx, (c) => pathPoly(c, sc), P.scarf, P.scarfS, light, 0.4, 0.03 * S, P.line, LW(S));
  // scarf tail streaming
  for (const k of [0, 1]) {
    const st0 = add(add(J.neck, mul(J.fwd, -0.025 * S)), mul(J.up, -0.012 * S));
    const hang = norm(add([-J.fwd[0] * (0.5 + k * 0.3), -J.fwd[1] * (0.5 + k * 0.3)], [0, 1]));
    const st1 = add(add(st0, mul(hang, 0.05 * S)), mul(add(hdrag, wind), 0.3 + k * 0.1));
    const st2 = add(add(st1, mul(hang, 0.04 * S)), add(mul(add(hdrag, wind), 0.3), [fbm(t * 4 + k) * 0.015 * S, 0]));
    cel(ctx, (c) => pathSmooth(c, taper([st0, st1, st2], 0.02 * S, 0.012 * S, 0.018 * S)), P.scarf, P.scarfS, light, 0.3, 0.02 * S, P.line, LW(S) * 0.8);
  }
  // ember clasp
  const cc = add(J.chest, mul(J.fwd, 0.035 * S));
  ctx.beginPath(); ctx.moveTo(cc[0], cc[1] - 0.014 * S); ctx.lineTo(cc[0] + 0.009 * S, cc[1]); ctx.lineTo(cc[0], cc[1] + 0.014 * S); ctx.lineTo(cc[0] - 0.009 * S, cc[1]); ctx.closePath();
  ctx.fillStyle = P.clasp; ctx.fill(); ctx.lineWidth = LW(S) * 0.6; ctx.strokeStyle = P.line; ctx.stroke();
  if (glow) { glow.beginPath(); glow.arc(cc[0], cc[1], Math.min(0.03 * S, 30), 0, TAU); glow.fillStyle = P.orange; glow.fill(); }
  if (!weaponBehind) weapon(ctx, J, light, S, glow);
  // near arm on top
  arm(ctx, J.sn, J.en, J.handn, P.suit, P.suitS, light, S);
  hand(ctx, J.handn, J.en, light, S);
  return J;
}
