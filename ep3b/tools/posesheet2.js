import { Canvas } from 'skia-canvas';
import fs from 'fs';
import { drawHero, POSE0 } from '../src/hero.js';
const c = new Canvas(1920, 1080), ctx = c.getContext('2d');
ctx.fillStyle = '#7a7eb6'; ctx.fillRect(0, 0, 1920, 1080);
const base = { held: 1, two: 0, g1: 0.5, gnd: 0, eye: 0.15, windx: 0.2, hx: 0.05, hy: 0.2 };
const tests = [
  { rot: -90, face: 1, wa: 40, wx: 0.25, wy: 0.1 },
  { rot: 90, face: 1, wa: 40, wx: 0.25, wy: 0.1 },
  { rot: 90, face: -1, wa: 200, wx: 0.3, wy: 0.0, fx1: 0.1, fy1: 0.48, fx2: -0.05, fy2: 0.5 },
  { rot: -90, face: -1, wa: 0, wx: 0.3, wy: -0.05, fx1: 0.1, fy1: 0.48, fx2: -0.05, fy2: 0.5, lean: -10 },
];
tests.forEach((q, i) => {
  const x = 300 + (i % 2) * 900, y = 300 + Math.floor(i / 2) * 480;
  drawHero(ctx, () => ({ p: { ...POSE0, ...base, ...q }, root: [x, y] }), 0.5, { S: 420 });
  ctx.fillStyle = '#ff0'; ctx.font = '30px sans-serif'; ctx.fillText(JSON.stringify(q).slice(0, 60), x - 250, y - 200);
});
fs.writeFileSync('board/lying.png', await c.toBuffer('png'));
