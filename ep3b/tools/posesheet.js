import { Canvas } from 'skia-canvas';
import fs from 'fs';
import { drawHero, POSE0 } from '../src/hero.js';
import { P } from '../src/palette.js';
const c = new Canvas(1920, 1080), ctx = c.getContext('2d');
ctx.fillStyle = '#9ea4ea'; ctx.fillRect(0, 0, 1920, 1080);
ctx.fillStyle = P.snow; ctx.fillRect(0, 900, 1920, 180);
const poses = [
  {},
  { lean: 25, wa: 170, wx: -0.05, wy: 0.14, fx1: 0.2, fy1: 0.45, fx2: -0.22, fy2: 0.46, bside: 1 },
  { lean: 40, wa: 10, wx: 0.2, wy: 0.05, fx1: 0.25, fy1: 0.38, fx2: -0.25, fy2: 0.44, mouth: 1, brow: 1 },
  { lean: -10, wa: -120, wx: 0.0, wy: -0.1, fx1: 0.12, fy1: 0.48, fx2: -0.12, fy2: 0.48, eye: 0.2, face: -1 },
  { held: 0, unfold: 0, lean: 3, head: 20, h1x: 0.03, h1y: 0.17, two: 0, hx: -0.02, hy: 0.17 },
];
poses.forEach((q, i) => {
  const S = 520, x = 200 + i * 380, y = 900 - 0.5 * S;
  drawHero(ctx, (t) => ({ p: { ...POSE0, ...q }, root: [x, y] }), 0.5, { S, ground: 900 });
});
fs.writeFileSync('board/posesheet.png', await c.toBuffer('png'));
console.log('ok');
