import sys, os, time, concurrent.futures as cf, threading
sys.path.insert(0, '../ep3')
import gen
from manifest import D, JN
from PIL import Image, ImageDraw
SHEET, WEAP, STYLEREF = 'refs/sheet_g2.png', 'props/WEAPON_sheet.png', 'keys/A1_guard.png'
STYLE = ("Japanese TV anime KEY FRAME drawing (genga, cleaned and colored), TRIGGER / ufotable production quality: confident tapered black "
         "line art, flat cel colors with one hard shadow tone and a thin cool rim highlight, no gradients, strong dynamic foreshortening. "
         "Character EXACTLY as the model sheet: silver-white choppy hair with ONE ember-red streak on her left, ember-orange eyes, crimson "
         "tattered hooded half-cloak with black lining, glowing orange diamond clasp, charcoal scarf, black bodysuit with brown leather straps, "
         "fingerless black gloves, black steel-toed knee boots. Weapon EXACTLY as the prop sheet: black shaft with thin red stripes, rifle receiver "
         "near the top, wide curved steel blade. Match the line and colour style of the style-reference drawing. No text.")
def guide_img(id_, j):
    im = Image.new('RGB', (1024, 1536), (235, 235, 240)); d = ImageDraw.Draw(im)
    R, L, C = (220, 40, 40), (40, 90, 220), (40, 40, 40)
    P = lambda k: tuple(map(int, j[k]))
    # torso as a quad (shoulders -> hips) so twist reads
    d.polygon([P('sL'), P('sR'), P('hipR'), P('hipL')], fill=(200, 200, 210), outline=C)
    d.line([P('neck'), P('pelvis')], fill=C, width=16)
    for s, c in (('R', R), ('L', L)):
        d.line([P('neck'), P('s' + s)], fill=c, width=18)
        d.line([P('s' + s), P('e' + s)], fill=c, width=24); d.line([P('e' + s), P('h' + s)], fill=c, width=22)
        d.line([P('hip' + s), P('k' + s)], fill=c, width=30); d.line([P('k' + s), P('f' + s)], fill=c, width=26)
        for q in ('h' + s, 'f' + s):
            x, y = P(q); d.ellipse([x - 18, y - 18, x + 18, y + 18], fill=c)
    x, y = P('head'); d.ellipse([x - 62, y - 76, x + 62, y + 76], outline=C, width=10)
    if j['nose'] != j['head']: d.line([P('head'), P('nose')], fill=C, width=12)
    d.line([P('wb'), P('wh')], fill=(120, 60, 20), width=14)
    d.line([P('wh'), P('bt')], fill=(150, 150, 150), width=26)
    out = f'guides2/{id_}.png'; im.save(out); return out
def path_of(r):
    return f'draw/{r}.png' if r in D else r
done = {k: os.path.exists(f'draw/{k}.png') for k in D}
lock = threading.Lock()
def run(id_):
    e = D[id_]
    out = f'draw/{id_}.png'
    if os.path.exists(out): return 'skip ' + id_
    refs = []
    if e['guide'] is not None: refs.append(guide_img(id_, e['guide']))
    refs += [SHEET]
    landscape_face = e['size'] == '1536x1024' and e['bg'] is None and 'INSERT' not in e['prompt']
    if 'INSERT' in e['prompt']: refs = [WEAP] + [path_of(r) for r in e['refs']]
    else:
        refs += [path_of(r) for r in e['refs']]
        if not landscape_face: refs += [WEAP, STYLEREF]
    lead = ("The FIRST image is a stick-figure layout guide (blue = her left limbs, red = her right limbs, grey quad = torso, brown = weapon shaft, "
            "grey thick line = blade): draw her in EXACTLY that pose, placement and scale. ") if e['guide'] is not None else ""
    bgtxt = " Transparent background, full body in frame unless stated otherwise." if e['bg'] == 'transparent' else ""
    prompt = lead + e['prompt'] + " " + STYLE + bgtxt
    try:
        return gen.oai_image(prompt, out, refs=refs[:10], model='gpt-image-2', size=e['size'], quality='high', background=e['bg'], note='ep4 ' + id_)
    except BaseException as ex:
        return f'FAIL {id_} {str(ex)[:200]}'
only = sys.argv[1].split(',') if len(sys.argv) > 1 and sys.argv[1] else None
todo = [k for k in D if (only is None or any(k.startswith(o) for o in only))]
# dependency waves
remaining = list(todo)
with cf.ThreadPoolExecutor(8) as ex:
    while remaining:
        ready = [k for k in remaining if all(os.path.exists(f'draw/{a}.png') for a in set(D[k]['after']) | {r for r in D[k]['refs'] if r in D})]
        if not ready: print('blocked:', remaining); break
        for r in ex.map(run, ready): print(r, flush=True)
        remaining = [k for k in remaining if k not in ready]
