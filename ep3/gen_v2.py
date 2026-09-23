import concurrent.futures as cf, os
import gen
from shots import STYLE, NIGHT, FIRE, HER, CHAR, WOLF, KING, NEG, SHOTS
SUF = " 2D hand-drawn Japanese anime animation, dynamic sakuga, consistent character design, clean line art."
gen.gclient()
INSERTS = {
 'i1_cry': ("Extreme close-up of the heroine mid-battle, mouth open in a fierce battle cry, silver hair whipping "
            "sideways, ember-orange eyes blazing, snow and black ink droplets flying past, dutch angle. " + HER + ' ' + NIGHT,
            CHAR, "She screams a battle cry, hair whipping violently, camera shakes, ink droplets streak past. Intense.", 4),
 'i2_blade': ("Extreme close-up: the glowing-edged scythe blade slicing through the neck of a black shadow wolf, the "
              "wolf's body splitting into splashes of black ink, bright sparks and an arc of light along the edge. " + NIGHT,
              CHAR + WOLF, "The blade slices through in a blur, the wolf bursts into black ink splashes and sparks. Very fast.", 4),
 'i3_lunge': ("POV shot from the heroine's perspective: a black shadow wolf lunging straight at the camera, jaws wide open "
              "with white fangs, glowing white-blue eyes, black smoke trailing, the scythe blade entering the frame from "
              "the right about to cut it. " + NIGHT, WOLF + CHAR,
              "The wolf leaps directly at the camera jaws open, at the last instant the scythe blade sweeps across the "
              "frame and the wolf splits into ink. Fast.", 4),
 'i4_lookdown': ("High above, looking down past the heroine's boots as she flies upward on wings of fire: far below, the "
                 "colossal shadow wolf's head with dozens of glowing white-blue eyes looking up at her, the burning "
                 "forest tiny beneath, embers streaming past the camera. " + HER + ' ' + FIRE, CHAR + KING,
                 "The camera rockets upward with her, the giant wolf's head and eyes shrink below, embers streak past.", 4),
}
jobs = []
for k, (kp, refs, mp, d) in INSERTS.items():
    jobs.append(('ins', k, kp, refs, mp, d))
HERO = {'s11b_ignite': 8, 's13_apex': 8, 's14_cut': 8}
for k, d in HERO.items():
    jobs.append(('hero', k, None, None, SHOTS[k][2], d))
def run(j):
    typ, k, kp, refs, mp, d = j
    try:
        if typ == 'ins':
            if not os.path.exists(f'keys/{k}.png'):
                gen.image(kp + ' ' + STYLE, f'keys/{k}.png', refs=refs, note=f'key {k}')
            return gen.video(mp + SUF, f'clips/{k}_fast.mp4', first=f'keys/{k}.png',
                             model='veo-3.1-fast-generate-preview', dur=d, negative=NEG, note=f'{k} fast')
        else:
            return gen.video(mp + SUF, f'clips/{k}_std1080.mp4', first=f'keys/{k}.png',
                             model='veo-3.1-generate-preview', dur=d, res='1080p', negative=NEG, note=f'{k} std 1080p')
    except BaseException as e:
        return f'FAIL {k}: {str(e)[:200]}'
with cf.ThreadPoolExecutor(4) as ex:
    for r in ex.map(run, jobs): print(r, flush=True)
