import subprocess, glob, os, sys
from PIL import Image, ImageDraw
from shots import SHOTS
os.makedirs('board/dailies', exist_ok=True)
keys = [k for k, v in SHOTS.items() if v[2] is not None]
per_page = 4
for pg in range(0, len(keys), per_page):
    rows = []
    for k in keys[pg:pg + per_page]:
        for t in ('lite', 'fast'):
            f = f'clips/{k}_{t}.mp4'
            if not os.path.exists(f):
                continue
            tmp = f'/tmp/claude-501/d_{k}_{t}.png'
            dur = float(subprocess.check_output(['ffprobe', '-v', 'error', '-show_entries', 'format=duration', '-of', 'csv=p=0', f]))
            n = 8
            subprocess.run(['ffmpeg', '-y', '-loglevel', 'error', '-i', f, '-vf',
                            f'fps={n / dur:.4f},scale=300:-1,tile={n}x1', '-frames:v', '1', tmp], check=True)
            im = Image.open(tmp).convert('RGB')
            ImageDraw.Draw(im).rectangle((0, 0, 150, 16), fill=(0, 0, 0))
            ImageDraw.Draw(im).text((4, 2), f'{k} {t}', fill=(255, 220, 0))
            rows.append(im)
    W = max(r.width for r in rows)
    S = Image.new('RGB', (W, sum(r.height for r in rows)))
    y = 0
    for r in rows:
        S.paste(r, (0, y)); y += r.height
    S.save(f'board/dailies/p{pg // per_page:02d}.jpg', quality=85)
print('pages', (len(keys) + per_page - 1) // per_page)
