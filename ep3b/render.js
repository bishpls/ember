// node render.js --sheet NAME [--n 12] | --frames f1,f2 | --beats b1,b2 | --range B0 B1 --out file.mp4
import fs from 'fs';
import { spawn } from 'child_process';
import { Canvas } from 'skia-canvas';
import { W, H, FPS, BEAT } from './src/engine.js';
import { SHOTS, renderFrame, TOTAL_BEATS } from './src/film.js';
import './src/shots/index.js';

const A = process.argv.slice(2);
const arg = (k, d = null) => { const i = A.indexOf(k); return i >= 0 ? A[i + 1] : d; };
fs.mkdirSync('board', { recursive: true });

async function sheet(frames, out, cols = 4) {
  const w = 480, h = 270, rows = Math.ceil(frames.length / cols);
  const S = new Canvas(cols * w, rows * h), x = S.getContext('2d');
  for (let i = 0; i < frames.length; i++) {
    const c = renderFrame(frames[i]);
    x.drawImage(c, (i % cols) * w, Math.floor(i / cols) * h, w, h);
    x.fillStyle = '#ff0'; x.font = '14px sans-serif';
    x.fillText(`f${frames[i]} b${(frames[i] / FPS / BEAT).toFixed(1)}`, (i % cols) * w + 6, Math.floor(i / cols) * h + 16);
  }
  fs.writeFileSync(out, await S.toBuffer('jpg', { quality: 0.85 }));
  console.log('wrote', out);
}

if (arg('--sheet')) {
  const name = arg('--sheet'), n = +arg('--n', 12);
  const sh = SHOTS.find((s) => s.name === name);
  const f0 = Math.ceil(sh.b0 * BEAT * FPS), f1 = Math.floor(sh.b1 * BEAT * FPS) - 1;
  const frames = Array.from({ length: n }, (_, i) => Math.round(f0 + (f1 - f0) * i / (n - 1)));
  await sheet(frames, `board/sheet_${name}.jpg`, +arg('--cols', 4));
} else if (arg('--beats')) {
  const frames = arg('--beats').split(',').map((b) => Math.round(+b * BEAT * FPS));
  await sheet(frames, arg('--out', 'board/beats.jpg'), +arg('--cols', 4));
} else if (arg('--frames')) {
  for (const f of arg('--frames').split(',').map(Number)) {
    fs.writeFileSync(`board/f${String(f).padStart(4, '0')}.png`, await renderFrame(f).toBuffer('png'));
  }
} else if (arg('--range')) {
  const b0 = +A[A.indexOf('--range') + 1], b1 = +A[A.indexOf('--range') + 2];
  const out = arg('--out', 'out/part.mp4');
  fs.mkdirSync('out', { recursive: true });
  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgba', '-s', `${W}x${H}`, '-r', String(FPS),
    '-i', '-', '-c:v', 'libx264', '-preset', 'medium', '-crf', '14', '-pix_fmt', 'yuv420p', out]);
  const f0 = Math.round(b0 * BEAT * FPS), f1 = Math.round(b1 * BEAT * FPS);
  const t0 = Date.now();
  for (let f = f0; f < f1; f++) {
    const c = renderFrame(f);
    const buf = await c.toBuffer('raw');
    if (!ff.stdin.write(buf)) await new Promise((r) => ff.stdin.once('drain', r));
    if ((f - f0) % 48 === 0) console.log(`frame ${f}/${f1} ${((Date.now() - t0) / 1000).toFixed(0)}s`);
  }
  ff.stdin.end();
  await new Promise((r) => ff.on('close', r));
  console.log('wrote', out);
}
