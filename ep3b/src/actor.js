// Helpers to build a hero pose function from sparse tracks + procedural cycles.
import { Track, b2t, TAU, lerp, clamp, onN, ease } from './engine.js';
import { POSE0, solve } from './hero.js';

export class Actor {
  constructor(base = {}) {
    this.tr = new Track({ ...POSE0, ...base, rx: 0, ry: 0, run: 0, runPh: 0 });
    this.fns = [];     // procedural overlays: (t, p) => void (mutates p)
    this.rootFns = []; // [t0, t1, fn(t) -> [x,y]]
  }
  key(b, ez, vals) { this.tr.key(b2t(b), ez, vals); return this; }
  over(fn) { this.fns.push(fn); return this; }
  rootFn(b0, b1, fn) { this.rootFns.push([b2t(b0), b2t(b1), fn]); return this; }
  pose(t) {
    const p = this.tr.eval(t);
    let root = [p.rx, p.ry];
    for (const [a, b, fn] of this.rootFns) if (t >= a && t < b) root = fn(t);
    for (const fn of this.fns) fn(t, p, root);
    return { p, root };
  }
  fn() { return (t) => this.pose(t); }
}

// run cycle overlay: blends in with p.run (0..1); phase advances with p.runPh (cycles/s)
// Sprint cycle authored as 4 key poses per step (contact, down, passing, up), interpolated, held on twos.
// Foot targets are relative to the pelvis (units of height).  Right leg = near.
const RUN_KEYS = [
  // [near foot x,y], [far foot x,y], bob, lean+, far-arm x,y
  { n: [0.24, 0.46], f: [-0.2, 0.3], bob: 0.00, lean: 0, arm: [0.14, 0.04] },     // contact (near heel strikes ahead)
  { n: [0.08, 0.44], f: [-0.08, 0.2], bob: 0.035, lean: 3, arm: [0.08, 0.1] },    // down (weight on near, far heel up behind)
  { n: [-0.14, 0.46], f: [0.14, 0.26], bob: 0.0, lean: 2, arm: [-0.02, 0.14] },   // passing (far knee drives forward)
  { n: [-0.3, 0.36], f: [0.26, 0.3], bob: -0.045, lean: -1, arm: [-0.1, 0.13] },  // up (push-off, airborne)
];
function runSample(ph) {       // ph in [0,1) over one full stride (2 steps)
  const half = ph < 0.5 ? 0 : 1;
  const u = (ph % 0.5) / 0.5 * 4;
  const i = Math.floor(u), f = u - i;
  const a = RUN_KEYS[i], b = RUN_KEYS[(i + 1) % 4];
  const L = (x, y) => [lerp(x[0], y[0], f), lerp(x[1], y[1], f)];
  let n = L(a.n, b.n), fa = L(a.f, b.f);
  if (i === 3) { n = L(a.n, RUN_KEYS[0].f); fa = L(a.f, RUN_KEYS[0].n); }
  let arm = L(a.arm, b.arm);
  if (half) { [n, fa] = [fa, n]; arm = [-arm[0] + 0.04, arm[1]]; }
  return { n, f: fa, bob: lerp(a.bob, b.bob, f), lean: lerp(a.lean, b.lean, f), arm };
}
export function runCycle(t, p, root) {
  if (p.run <= 0.001) return;
  const k = p.run;
  const ph = ((onN(t, 2) * 2.3) % 1 + 1) % 1;       // 2.3 strides/s = 4.6 steps/s: a sprint
  const r = runSample(ph);
  p.fx1 = lerp(p.fx1, r.n[0], k); p.fy1 = lerp(p.fy1, r.n[1], k);
  p.fx2 = lerp(p.fx2, r.f[0], k); p.fy2 = lerp(p.fy2, r.f[1], k);
  p.hx = lerp(p.hx, r.arm[0], k); p.hy = lerp(p.hy, r.arm[1], k);
  p.lean += k * r.lean;
  root[1] += k * p.__S * r.bob;
  p.gnd = lerp(p.gnd, 0.0, k);
}
