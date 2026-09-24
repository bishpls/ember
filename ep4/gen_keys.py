import sys, os, concurrent.futures as cf
sys.path.insert(0, '../ep3')
import gen
SHEET = 'refs/sheet_g2.png'
STYLE = ("Japanese TV anime KEY FRAME drawing (genga, cleaned and colored), TRIGGER / ufotable production quality: "
         "confident tapered black line art, flat cel colors with one hard shadow tone and a thin rim highlight, no gradients, "
         "dynamic foreshortening. Character EXACTLY as the model sheet (silver-white hair with one red streak, ember-orange eyes, "
         "crimson tattered hooded half-cloak with black lining, glowing orange diamond clasp, charcoal scarf, black bodysuit with brown straps, "
         "fingerless gloves, black steel-toed knee boots). Weapon: a large folding gun-scythe with a black shaft with thin red stripes, a rifle receiver "
         "near the top, and a wide curved steel blade. Transparent background, full body in frame, no text.")
HERO = {
 'A1_guard': "Pose exactly like the stick-figure guide (blue = her left side, red = her right side, brown line = weapon shaft, grey = blade): a low wide battle stance seen from a three-quarter front angle, knees bent, weight low, the gun-scythe gripped two-handed and angled low behind her with the blade trailing near the ground, cloak and hair blown back by wind, fierce focused eyes looking toward the left.",
 'C1_coil': "Pose exactly like the stick-figure guide: ANTICIPATION before a spin attack. A deep coiled crouch, torso twisted hard away from the direction of the swing, the scythe pulled back horizontally at hip height with both hands, weight on the back foot, cloak wrapped tight around her from the twist, eyes locked forward.",
 'C2_twist': "Pose exactly like the stick-figure guide: MID-SPIN, seen from behind at a three-quarter back angle, pivoting on one foot, the scythe sweeping horizontally at waist height with the blade leading, cloak flaring out horizontally in a spiral from the spin, hair whipping sideways. Extreme motion.",
 'C3_extend': "Pose exactly like the stick-figure guide: FULL EXTENSION of a spinning slash, three-quarter front view, both arms fully extended to the side, the scythe horizontal at maximum reach, body leaning hard into the swing, cloak spiraling around her, mouth open in a battle cry. Extreme dynamic foreshortening on the blade.",
 'C4_follow': "Pose exactly like the stick-figure guide: FOLLOW-THROUGH after a spinning slash: dropped low onto one knee, the scythe swept around past her side and trailing behind with the blade low, head down, cloak settling around her in a spiral, hair falling forward over her eyes.",
 'D2_rise': "Pose exactly like the stick-figure guide: standing up straight after the fight, the gun-scythe held vertically at her side with the blade down near her feet, calm fierce expression, turning her head to look over her shoulder toward the viewer, cloak and hair drifting in the wind.",
}
OTHER = {
 'W1_leap': ("Japanese TV anime key frame, flat cel style, transparent background: a monstrous 'void wolf' made of living black shadow, leaping through the air toward the right, jaws wide open showing white fangs, glowing cyan-white slit eyes, a jagged torn-shadow mane of sharp spikes, wisps of black smoke peeling off its edges, thin cold blue rim light on its back. Pure black body with one dark blue-grey shadow tone. Full body, dynamic foreshortening, no text.", ['../ep3/refs/wolf_sheet_v1.png'], '1536x1024', 'transparent'),
 'W2_leap_front': ("Japanese TV anime key frame, flat cel style, transparent background: a monstrous 'void wolf' made of living black shadow lunging straight toward the viewer, extreme foreshortening, huge open jaws with white fangs filling the center, glowing cyan-white slit eyes, jagged spiky shadow mane flaring, black smoke wisps. Pure black body, thin cold blue rim light. No text.", ['../ep3/refs/wolf_sheet_v1.png'], '1024x1024', 'transparent'),
 'BG_clearing': ("Japanese anime background art (hand-painted BG, like a ufotable or Makoto Shinkai production background), wide 16:9 landscape, NO characters: a snowy clearing in a dark pine forest at night, low camera angle, fresh deep snow in the foreground with blue shadows, tall snow-laden pines framing both sides, fog between the trees, and in the sky a large moon mostly eclipsed by a black disk with a thin burning silver-white ring. Deep indigo and blue palette, silver moonlight on the snow. Painterly, detailed, cinematic. No text.", [], '1536x1024', None),
 'B1_eyes': ("Japanese TV anime extreme close-up key frame, full frame 16:9, flat cel colors with hard shadow: the heroine's face from the model sheet in a tight three-quarter close-up cropped from brow to mouth, both ember-orange eyes narrowed in fierce battle focus, a thin line of orange light reflecting in her irises, silver-white hair with the red streak whipping across the frame in the wind, snowflakes and small black ink droplets streaking past, cold blue night rim light on one side and warm orange light on the other. Clean line art. No text.", [SHEET], '1536x1024', None),
}
jobs = []
for k, v in HERO.items():
    jobs.append((k, v + ' ' + STYLE, [f'guides/{k}.png', SHEET], '1024x1536', 'transparent'))
for k, (p, refs, size, bg) in OTHER.items():
    jobs.append((k, p, refs, size, bg))
only = sys.argv[1].split(',') if len(sys.argv) > 1 else None
def run(j):
    k, p, refs, size, bg = j
    if only and k not in only: return 'skip ' + k
    out = f'keys/{k}.png' if not k.startswith('BG') else f'bg/{k}.png'
    try: return gen.oai_image(p, out, refs=refs, model='gpt-image-2', size=size, quality='high', background=bg, note='ep4 ' + k)
    except BaseException as e: return f'FAIL {k} {str(e)[:300]}'
with cf.ThreadPoolExecutor(5) as ex:
    for r in ex.map(run, jobs): print(r, flush=True)
