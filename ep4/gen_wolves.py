import sys, os, concurrent.futures as cf
sys.path.insert(0, '../ep3')
import gen
WS = "Pure black living-shadow body with one dark blue-grey shadow tone, jagged torn-shadow mane of sharp spikes, glowing cyan-white slit eyes, faint cold cyan rim light, black smoke wisps. Japanese TV anime flat cel style, clean line art, transparent background, no text, no grid lines."
J = [
 ('props/WOLF_cycle3x2.png', "Anime animation model sheet: a 6-drawing gallop cycle of the SAME shadow wolf running toward screen-RIGHT, laid out in a 3 by 2 grid (3 drawings per row, 2 rows), each drawing the same size and centered in its cell, in order left-to-right then top-to-bottom: contact, collect, push-off, extended flight, reach, landing. " + WS, ['keys/W1_leap.png'], '1536x1024'),
 ('keys/W3_hurt.png', "Anime key frame: a shadow wolf knocked backward through the air, tumbling, body twisted, jaws gaping, legs flailing, smoke bursting off it. " + WS, ['keys/W1_leap.png'], '1536x1024'),
 ('keys/W4_pounce.png', "Anime key frame: a shadow wolf pouncing DOWNWARD from above onto its prey, seen from below, jaws open, claws spread, body diving. " + WS, ['keys/W1_leap.png'], '1024x1024'),
]
def run(j):
    out, p, refs, size = j
    if os.path.exists(out): return 'skip ' + out
    return gen.oai_image(p, out, refs=refs, model='gpt-image-2', size=size, quality='high', background='transparent', note='ep4 ' + out)
with cf.ThreadPoolExecutor(3) as ex:
    for r in ex.map(run, J): print(r)
