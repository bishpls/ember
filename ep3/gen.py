"""EMBER III — generation client with a hard budget guard.

Every paid call is estimated up front, refused if it would cross the cap, and logged to ledger.jsonl.
Keys are read from ~/stratos-ai/.env and never printed.
"""
import os
import sys
import json
import time
import pathlib
import argparse

HERE = pathlib.Path(__file__).resolve().parent
LEDGER = HERE / 'ledger.jsonl'
CAP = 200.0
WARN = 170.0

PRICE = {
    'gemini-3-pro-image-preview': 0.134,       # per image (1K/2K)
    'gemini-3.1-flash-image-preview': 0.067,   # per 1K image
    'veo-3.1-lite-generate-preview': 0.05,     # per second, 720p
    'veo-3.1-fast-generate-preview': 0.10,
    'veo-3.1-generate-preview': 0.40,
    'sora-2': 0.10,
    'sora-2-pro': 0.30,
}


def _keys():
    env = {}
    for line in (pathlib.Path.home() / 'stratos-ai' / '.env').read_text().splitlines():
        if '=' in line and not line.strip().startswith('#'):
            k, v = line.split('=', 1)
            env[k.strip()] = v.strip().strip('"').strip("'")
    return env


def spent():
    if not LEDGER.exists():
        return 0.0
    return sum(json.loads(l)['cost'] for l in LEDGER.read_text().splitlines() if l.strip())


def charge(kind, model, cost, note):
    s = spent()
    if s + cost > CAP:
        raise SystemExit(f'BUDGET GUARD: ${s:.2f} spent + ${cost:.2f} would exceed ${CAP:.0f} cap')
    return s


def log(kind, model, cost, note, out):
    with LEDGER.open('a') as f:
        f.write(json.dumps(dict(t=time.time(), kind=kind, model=model, cost=round(cost, 4), note=note,
                                out=str(out))) + '\n')
    s = spent()
    flag = '  <-- over 80% of cap' if s >= WARN else ''
    print(f'[ledger] +${cost:.3f} {kind} {model} -> total ${s:.2f} / ${CAP:.0f}{flag}')


_client = None


def gclient():
    global _client
    if _client is None:
        from google import genai
        _client = genai.Client(api_key=_keys()['GEMINI_API_KEY'])
    return _client


def image(prompt, out, refs=(), model='gemini-3-pro-image-preview', aspect='16:9', size='2K', note=''):
    from google.genai import types
    from PIL import Image
    cost = PRICE[model]
    charge('image', model, cost, note)
    parts = [prompt] + [Image.open(r) for r in refs]
    cfg = types.GenerateContentConfig(response_modalities=['IMAGE'],
                                      image_config=types.ImageConfig(aspect_ratio=aspect, image_size=size))
    for attempt in range(3):
        try:
            r = gclient().models.generate_content(model=model, contents=parts, config=cfg)
            break
        except Exception as e:
            print('retry', attempt, str(e)[:200])
            time.sleep(4 * (attempt + 1))
    else:
        raise SystemExit('image failed')
    saved = False
    for part in r.candidates[0].content.parts:
        if getattr(part, 'inline_data', None) and part.inline_data.data:
            pathlib.Path(out).parent.mkdir(parents=True, exist_ok=True)
            pathlib.Path(out).write_bytes(part.inline_data.data)
            saved = True
            break
    log('image', model, cost, note or prompt[:80], out)
    if not saved:
        txt = ' '.join(getattr(p, 'text', '') or '' for p in r.candidates[0].content.parts)
        raise SystemExit(f'no image returned: {txt[:300]}')
    return out


def video(prompt, out, first=None, last=None, refs=(), model='veo-3.1-fast-generate-preview', dur=8,
          aspect='16:9', res='720p', negative='', note=''):
    from google.genai import types
    if os.path.exists(out) and not os.environ.get('FORCE'):
        print('skip existing', out)
        return out
    cost = PRICE[model] * dur
    charge('video', model, cost, note)
    kw = dict(aspect_ratio=aspect, resolution=res, duration_seconds=dur, number_of_videos=1)
    if negative and 'lite' not in model:
        kw['negative_prompt'] = negative
    if last:
        kw['last_frame'] = types.Image.from_file(location=str(last))
    if refs:
        kw['reference_images'] = [types.VideoGenerationReferenceImage(
            image=types.Image.from_file(location=str(r)), reference_type='asset') for r in refs]
    img = types.Image.from_file(location=str(first)) if first else None
    op = gclient().models.generate_videos(model=model, prompt=prompt, image=img,
                                          config=types.GenerateVideosConfig(**kw))
    t0 = time.time()
    while not op.done:
        time.sleep(8)
        op = gclient().operations.get(op)
        if time.time() - t0 > 900:
            raise SystemExit('video timeout')
    if op.error:
        log('video-failed', model, 0.0, note, out)
        raise SystemExit(f'video error: {op.error}')
    vids = op.response.generated_videos if op.response else []
    if not vids:
        log('video-filtered', model, 0.0, note, out)
        raise SystemExit(f'no video (filtered?): {op.response}')
    v = vids[0].video
    gclient().files.download(file=v)
    pathlib.Path(out).parent.mkdir(parents=True, exist_ok=True)
    v.save(str(out))
    log('video', model, cost, note or prompt[:80], out)
    print(f'video {out} in {time.time() - t0:.0f}s')
    return out


_oai = None


def oclient():
    global _oai
    if _oai is None:
        from openai import OpenAI
        _oai = OpenAI(api_key=_keys()['OPENAI_API_KEY'])
    return _oai


def oai_image(prompt, out, refs=(), model='gpt-image-2', size='1536x1024', quality='high', background=None, note=''):
    """GPT Image generate/edit. Cost is computed from returned token usage."""
    import base64
    charge('image', model, 0.40, note)      # pre-check with a conservative estimate
    kw = dict(model=model, prompt=prompt, size=size, quality=quality)
    if background:
        kw['background'] = background
    for attempt in range(3):
        try:
            if refs:
                files = [open(r, 'rb') for r in refs]
                r = oclient().images.edit(image=files, **kw)
                for f in files:
                    f.close()
            else:
                r = oclient().images.generate(**kw)
            break
        except Exception as e:
            print('retry', attempt, str(e)[:300])
            time.sleep(5 * (attempt + 1))
    else:
        raise SystemExit('oai image failed')
    u = getattr(r, 'usage', None)
    cost = 0.25
    if u is not None:
        it = getattr(u, 'input_tokens', 0) or 0
        ot = getattr(u, 'output_tokens', 0) or 0
        det = getattr(u, 'input_tokens_details', None)
        img_in = getattr(det, 'image_tokens', 0) if det else 0
        cost = (it - img_in) * 5e-6 + img_in * 8e-6 + ot * 30e-6
    pathlib.Path(out).parent.mkdir(parents=True, exist_ok=True)
    pathlib.Path(out).write_bytes(base64.b64decode(r.data[0].b64_json))
    log('image', model, cost, note or prompt[:80], out)
    return out


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('cmd', choices=['spent'])
    a = ap.parse_args()
    print(f'${spent():.2f} of ${CAP:.0f}')
