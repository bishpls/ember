import sys, os, concurrent.futures as cf
import gen
from shots import SHOTS, NEG
SUFFIX = " 2D hand-drawn Japanese anime animation, dynamic sakuga, consistent character design, clean line art."
gen.gclient()
jobs = []
tiers = sys.argv[1].split(',') if len(sys.argv) > 1 else ['lite', 'fast']
only = sys.argv[2].split(',') if len(sys.argv) > 2 else None
M = {'lite': 'veo-3.1-lite-generate-preview', 'fast': 'veo-3.1-fast-generate-preview', 'std': 'veo-3.1-generate-preview'}
for k, (kp, refs, mp, tier, dur) in SHOTS.items():
    if mp is None or (only and k not in only):
        continue
    for t in tiers:
        out = f'clips/{k}_{t}.mp4'
        if not os.path.exists(out):
            jobs.append((k, mp + SUFFIX, out, M[t], dur))
print(len(jobs), 'jobs, est $', sum(gen.PRICE[m] * d for _, _, _, m, d in jobs))
def run(j):
    k, mp, out, m, d = j
    try:
        return gen.video(mp, out, first=f'keys/{k}.png', model=m, dur=d, negative=NEG, note=f'{k} {m}')
    except BaseException as e:
        return f'FAIL {out}: {str(e)[:160]}'
with cf.ThreadPoolExecutor(4) as ex:
    for r in ex.map(run, jobs):
        print(r, flush=True)
