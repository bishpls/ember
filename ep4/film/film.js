// shot registry + renderer.  node film/film.js --sheet NAME | --beats b,b | --range B0 B1 --out f.mp4
import fs from 'fs';
import { spawn } from 'child_process';
import { Canvas } from 'skia-canvas';
import { W, H, FPS, BEAT, bf, fb, main, clearFrame, post } from './lib.js';

export const SHOTS = [];
export const TOTAL = 168;
export function shot(b0, b1, name, draw) { SHOTS.push({ b0, b1, name, draw }); SHOTS.sort((a, b) => a.b0 - b.b0); }

export function renderFrame(fi) {
  const b = fb(fi);
  let sh = SHOTS[0];
  for (const s of SHOTS) if (b >= s.b0) sh = s;
  clearFrame();
  const f0 = Math.round(bf(sh.b0));
  const E = { fi, lf: fi - f0, t: fi / FPS, lt: (fi - f0) / FPS, b, u: (b - sh.b0) / (sh.b1 - sh.b0), nf: Math.round(bf(sh.b1)) - f0 };
  const po = sh.draw(E) || {};
  const T = TOTAL * BEAT;
  const fade = Math.min(1, E.t / 0.6) * Math.min(1, (T - E.t) / 1.2);
  post({ ...po, fade: (po.fade ?? 1) * fade, fi });
  return main;
}

async function sheetOut(frames, out, cols = 4) {
  const w = 480, h = 270, rows = Math.ceil(frames.length / cols);
  const S = new Canvas(cols * w, rows * h), x = S.getContext('2d');
  for (let i = 0; i < frames.length; i++) {
    x.drawImage(renderFrame(frames[i]), (i % cols) * w, Math.floor(i / cols) * h, w, h);
    x.fillStyle = '#ff0'; x.font = '14px sans-serif';
    x.fillText(`f${frames[i]} b${fb(frames[i]).toFixed(1)}`, (i % cols) * w + 6, Math.floor(i / cols) * h + 16);
  }
  fs.writeFileSync(out, await S.toBuffer('jpg', { quality: 0.85 }));
  console.log('wrote', out);
}

export async function cli() {
  const A = process.argv.slice(2);
  const arg = (k, d = null) => { const i = A.indexOf(k); return i >= 0 ? A[i + 1] : d; };
  fs.mkdirSync('board', { recursive: true });
  if (arg('--sheet')) {
    const sh = SHOTS.find((s) => s.name === arg('--sheet'));
    const n = +arg('--n', 16), f0 = Math.ceil(bf(sh.b0)), f1 = Math.floor(bf(sh.b1)) - 1;
    await sheetOut(Array.from({ length: n }, (_, i) => Math.round(f0 + (f1 - f0) * i / (n - 1))), `board/sheet_${sh.name}.jpg`, +arg('--cols', 4));
  } else if (arg('--frames')) {
    const [a, z] = arg('--frames').split(':').map(Number);
    await sheetOut(Array.from({ length: z - a }, (_, i) => a + i), arg('--out', 'board/frames.jpg'), +arg('--cols', 8));
  } else if (arg('--beats')) {
    await sheetOut(arg('--beats').split(',').map((b) => Math.round(bf(+b))), arg('--out', 'board/beats.jpg'), +arg('--cols', 4));
  } else if (arg('--range')) {
    const i = A.indexOf('--range'), b0 = +A[i + 1], b1 = +A[i + 2];
    const out = arg('--out', 'out/part.mp4');
    fs.mkdirSync('out', { recursive: true });
    const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgba', '-s', `${W}x${H}`, '-r', String(FPS), '-i', '-',
      '-c:v', 'libx264', '-preset', 'medium', '-crf', '14', '-pix_fmt', 'yuv420p', out]);
    const f0 = Math.round(bf(b0)), f1 = Math.round(bf(b1));
    for (let f = f0; f < f1; f++) {
      const buf = await renderFrame(f).toBuffer('raw');
      if (!ff.stdin.write(buf)) await new Promise((r) => ff.stdin.once('drain', r));
    }
    ff.stdin.end(); await new Promise((r) => ff.on('close', r));
    console.log('wrote', out);
  }
}
