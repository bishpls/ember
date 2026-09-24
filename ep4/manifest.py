"""EMBER III (studio pipeline) — drawing manifest: every key + in-between, its layout guide and acting note.
Joint order (pixels on a 1024x1536 portrait page):
 head nose neck pelvis | sR eR hR | sL eL hL | hipR kR fR | hipL kL fL | wb wh bt   (her right = red, left = blue)
"""
JN = ['head', 'nose', 'neck', 'pelvis', 'sR', 'eR', 'hR', 'sL', 'eL', 'hL', 'hipR', 'kR', 'fR', 'hipL', 'kL', 'fL', 'wb', 'wh', 'bt']


def J(*pts):
    assert len(pts) == 19, len(pts)
    return dict(zip(JN, pts))


def lerpJ(a, b, u, arc=None):
    """in-between guide: joints interpolated (optionally bowed along an arc for the weapon tip)"""
    out = {}
    for k in JN:
        x = a[k][0] + (b[k][0] - a[k][0]) * u
        y = a[k][1] + (b[k][1] - a[k][1]) * u
        if arc and k in ('wh', 'bt', 'hR', 'hL'):
            import math
            bow = math.sin(u * math.pi) * arc
            x += bow[0] if isinstance(bow, tuple) else 0
            y -= arc * math.sin(u * math.pi) if not isinstance(arc, tuple) else 0
        out[k] = (x, y)
    return out


def shift(j, dx=0, dy=0, s=1.0, cx=512, cy=768):
    return {k: ((x - cx) * s + cx + dx, (y - cy) * s + cy + dy) for k, (x, y) in j.items()}


def mirror(j):   # mirror horizontally AND swap sides so colours stay anatomically correct
    m = {k: (1024 - x, y) for k, (x, y) in j.items()}
    sw = {}
    for k, v in m.items():
        if k[-1] in 'RL' and k not in ('head',):
            o = k[:-1] + ('L' if k[-1] == 'R' else 'R')
            sw[o] = v
        else:
            sw[k] = v
    return sw


D = {}    # id -> dict(guide, prompt, refs, size, bg, after)


def add(id_, prompt, guide=None, refs=(), size='1024x1536', bg='transparent', after=()):
    D[id_] = dict(guide=guide, prompt=prompt, refs=list(refs), size=size, bg=bg, after=list(after))


# ============================================================================ S01 establishing
add('H01_back', "Seen from directly BEHIND and slightly above, full body, small and still: she stands alone facing away from the viewer, feet together, arms loose at her sides, the folded gun-scythe strapped diagonally across her back, the crimson hood down, cloak and hair stirring in a light wind, head slightly bowed.",
    J((512, 240), (512, 240), (512, 340), (512, 730), (600, 380), (630, 560), (640, 720), (424, 380), (394, 560), (384, 720),
      (560, 740), (570, 1030), (575, 1340), (464, 740), (454, 1030), (450, 1340), (380, 300), (660, 700), (700, 640)))

# ============================================================================ S02 face MCU (landscape bust)
BUST = "Medium close-up, landscape framing from the chest up, three-quarter view facing screen-left, snow falling, cold blue moonlight rim on her hair and cheek, a warm faint orange glow from the clasp under her chin."
add('H02_open', BUST + " Her ember-orange eyes are OPEN, alert and piercing, glancing sharply toward screen-left; lips closed. Breath vapour at her mouth.", size='1536x1024', bg=None, refs=['keys/B1_eyes.png'])
add('H02_closed', BUST + " Exactly the same drawing, framing and lighting as the reference, but her eyes are fully CLOSED, peaceful, snowflakes on her lashes, head a few degrees lower.", size='1536x1024', bg=None, refs=['H02_open'], after=['H02_open'])
add('H02_half', BUST + " Exactly the same drawing, framing and lighting as the references, the in-between: eyes HALF-open, lids heavy, just starting to look up.", size='1536x1024', bg=None, refs=['H02_open', 'H02_closed'], after=['H02_open', 'H02_closed'])

# ============================================================================ S05 over the shoulder
add('H05_shoulder', "Over-the-shoulder foreground element: seen from behind her right shoulder, cropped from the waist up and very large in frame on the RIGHT side, her head turned in three-quarter back view looking toward screen-left into the distance, hood down, silver hair and crimson cloak whipping toward screen-right in a strong wind, the folded gun-scythe on her back.", size='1024x1536')

# ============================================================================ S06 weapon inserts (landscape, full frame)
INS = ("Extreme close-up anime INSERT shot of a MECHANISM ONLY (no face, no person visible except at most one gloved hand), landscape full frame, "
       "dramatic dutch angle, dark navy background with radial speed lines, cel-shaded metal with sharp white specular glints. The weapon exactly as the prop sheet.")
add('H06_grip', INS + " A black fingerless-gloved hand SLAMS closed around the folded gun-scythe's black shaft (red stripes), seen from the side, fingers tight, a tiny spark at the hinge.", size='1536x1024', bg=None, refs=['props/WEAPON_sheet.png'])
add('H06_extend', INS + " Only the black telescoping shaft segments SHOOTING outward along a diagonal toward the upper right, heavy motion lines streaking behind the segments, a red stripe running along it, steel collars clicking into place.", size='1536x1024', bg=None, refs=['props/WEAPON_sheet.png'])
add('H06_lock', INS + " Only the head of the weapon: the wide curved steel scythe blade swinging open on its hinge and LOCKING, a brilliant white glint flashing along the razor edge, a thin glowing orange line on the cutting edge, the rifle receiver beside the hinge.", size='1536x1024', bg=None, refs=['props/WEAPON_sheet.png'])

# ============================================================================ S07 launch
COIL7 = J((600, 560), (650, 590), (560, 640), (470, 920), (610, 670), (680, 800), (620, 900), (500, 680), (440, 820), (400, 930),
          (520, 930), (690, 1060), (740, 1360), (430, 940), (300, 1120), (180, 1360), (330, 960), (820, 820), (900, 1010))
SPRING7 = J((720, 380), (780, 400), (670, 460), (500, 780), (720, 500), (800, 620), (880, 700), (620, 520), (560, 660), (500, 760),
            (540, 790), (700, 900), (820, 1000), (460, 800), (330, 1030), (120, 1300), (420, 820), (60, 900), (20, 1120))
add('H07_coil', "ANTICIPATION: she sinks into a deep coiled crouch facing screen-right, weight low on her back leg, torso folded forward, the gun-scythe held low along her body, eyes blazing with focus, cloak pooled around her, snow cracking under her boots.", COIL7)
add('H07_mid', "In-between from the coil to the launch: legs beginning to extend, body rising and tipping forward toward screen-right, cloak starting to lift.", lerpJ(COIL7, SPRING7, 0.45), refs=['H07_coil'], after=['H07_coil'])
add('H07_spring', "LAUNCH: she explodes forward toward screen-right, her back leg fully extended pushing off the ground, body a straight diagonal line, front knee driving, the scythe trailing low behind her, cloak and hair streaming straight back, snow bursting from her back foot.", SPRING7, refs=['H07_coil'], after=['H07_coil'])

# ============================================================================ S08 sprint cycle (side view, running RIGHT, scythe trailing behind in her right hand)
def runpose(front_leg, phase):
    # phase: 0 contact, 1 down, 2 pass/up ; front_leg: 'L' or 'R' (which leg is reaching forward)
    base = dict(head=(640, 300), nose=(690, 318), neck=(610, 390), pelvis=(500, 760))
    bob = {0: 0, 1: 40, 2: -30}[phase]
    j = {k: (v[0], v[1] + bob) for k, v in base.items()}
    # weapon arm (right) trails low behind; left arm pumps
    j['sR'] = (590, 430 + bob); j['eR'] = (520, 600 + bob); j['hR'] = (430, 740 + bob)
    j['wb'] = (520, 690 + bob); j['wh'] = (110, 900 + bob); j['bt'] = (40, 1150 + bob)
    arm = {('L', 0): (740, 520), ('L', 1): (700, 580), ('L', 2): (600, 620), ('R', 0): (500, 640), ('R', 1): (560, 600), ('R', 2): (680, 540)}[(front_leg, phase)]
    j['sL'] = (650, 420 + bob); j['eL'] = ((650 + arm[0]) / 2 + 10, 530 + bob); j['hL'] = (arm[0], arm[1] + bob)
    front = {0: ((640, 980), (770, 1340)), 1: ((600, 1010), (560, 1350)), 2: ((540, 1060), (500, 1350))}[phase]
    back = {0: ((400, 1010), (250, 1250)), 1: ((380, 1020), (280, 1160)), 2: ((620, 950), (480, 1110))}[phase]
    fl, bl = (front_leg, 'R' if front_leg == 'L' else 'L')
    j['hip' + fl] = (512, 770 + bob); j['k' + fl] = (front[0][0], front[0][1] + bob * 0.5); j['f' + fl] = front[1]
    j['hip' + bl] = (490, 770 + bob); j['k' + bl] = (back[0][0], back[0][1] + bob * 0.5); j['f' + bl] = (back[1][0], back[1][1] + bob * 0.3)
    return J(*[j[k] for k in JN])


RUNP = "Side view running at full sprint toward screen-RIGHT, body leaning hard forward, the gun-scythe held in her right hand trailing low behind her with the blade near the snow (like Ruby Rose), cloak streaming straight back, hair whipping back, fierce eyes. Frame {n} of a 6-drawing run cycle: "
RUN_NOTES = ['CONTACT: left heel just striking the snow far ahead, right leg extended behind.',
             'DOWN: weight dropping onto the bent left leg, right heel kicking up behind.',
             'PASSING: right knee driving forward past the left leg, body rising.',
             'CONTACT: right heel striking the snow far ahead, left leg extended behind.',
             'DOWN: weight dropping onto the bent right leg, left heel kicking up behind.',
             'PASSING: left knee driving forward past the right leg, body rising.']
RUN_GUIDES = [runpose('L', 0), runpose('L', 1), runpose('L', 2), runpose('R', 0), runpose('R', 1), runpose('R', 2)]
for i in range(6):
    add(f'H08_run{i}', RUNP.format(n=i + 1) + RUN_NOTES[i] + " Keep the design, scale and the weapon position identical to the reference run-cycle drawings.",
        RUN_GUIDES[i], refs=([f'H08_run0'] if i else []), after=(['H08_run0'] if i else []))
# kill 1: wind-back -> slash through -> follow
SW1 = J((620, 340), (670, 360), (590, 430), (500, 790), (560, 460), (440, 520), (330, 560), (640, 470), (560, 560), (420, 580),
        (520, 800), (660, 1000), (780, 1330), (470, 810), (360, 1050), (220, 1300), (500, 560), (40, 520), (20, 280))
SH1 = J((640, 360), (690, 380), (610, 450), (500, 800), (660, 470), (800, 500), (930, 480), (560, 490), (700, 520), (860, 500),
        (530, 810), (680, 1010), (800, 1340), (470, 820), (360, 1060), (220, 1310), (620, 520), (1010, 440), (1000, 180))
SF1 = J((660, 400), (700, 430), (630, 480), (520, 820), (680, 500), (760, 400), (800, 300), (580, 520), (680, 420), (760, 320),
        (540, 830), (690, 1030), (800, 1350), (480, 840), (370, 1070), (230, 1320), (840, 360), (700, -40), (400, -60))
add('H08_windup', "Mid-sprint facing screen-right, twisting her torso to wind the gun-scythe back behind her for a big rising slash, blade trailing far behind, both hands on the shaft, eyes locked on a target ahead.", SW1, refs=['H08_run0'])
add('H08_slash_a', "In-between: the scythe whipping forward in a low horizontal arc, body untwisting, a motion blur on the blade.", lerpJ(SW1, SH1, 0.5), refs=['H08_windup'], after=['H08_windup'])
add('H08_slash', "IMPACT: the scythe fully swung forward at full extension toward screen-right, arms extended, body twisted into the swing, mouth open in a shout, cloak flaring, the blade edge blazing.", SH1, refs=['H08_windup'], after=['H08_windup'])
add('H08_follow', "FOLLOW-THROUGH: the scythe carried up and over past her head after the slash, body opening up, still running, hair and cloak whipping.", SF1, refs=['H08_slash'], after=['H08_slash'])
# kill 2: hop + backhand spin (turning to face screen-left)
HOP = J((560, 260), (520, 280), (560, 360), (540, 700), (640, 400), (700, 540), (620, 640), (480, 400), (420, 540), (460, 660),
        (580, 700), (700, 860), (620, 1020), (500, 710), (440, 900), (560, 1060), (520, 620), (900, 820), (980, 1060))
BACK = J((440, 300), (390, 320), (460, 390), (520, 740), (380, 430), (260, 460), (130, 470), (540, 420), (400, 470), (240, 480),
         (560, 750), (660, 960), (620, 1200), (480, 760), (400, 980), (300, 1180), (420, 470), (0, 460), (20, 220))
add('H08_hop', "She hops into the air, knees tucked, twisting her whole body around to spin and face BACKWARD (screen-left), the scythe swinging around behind her, cloak wrapping around her from the spin.", HOP, refs=['H08_windup'])
add('H08_backhand', "Mid-air spinning BACKHAND slash toward screen-LEFT, the scythe extended at full reach, body horizontal-ish in the spin, cloak spiraling around her, a fierce shout.", BACK, refs=['H08_hop'], after=['H08_hop'])

# ============================================================================ S09 spin slash (pilot keys + breakdowns)
import json
PILOT = {
 'C1': J((430, 470), (390, 500), (460, 560), (560, 900), (530, 590), (640, 720), (740, 800), (390, 610), (470, 760), (600, 810),
         (610, 900), (760, 1080), (820, 1360), (500, 910), (330, 1100), (220, 1360), (400, 820), (990, 780), (960, 560)),
 'C2': J((520, 420), (560, 440), (520, 510), (500, 860), (400, 560), (300, 660), (220, 700), (640, 560), (720, 650), (640, 700),
         (440, 870), (380, 1100), (340, 1370), (560, 870), (660, 1080), (720, 1360), (760, 700), (60, 720), (20, 960)),
 'C3': J((430, 420), (470, 440), (460, 510), (520, 860), (560, 550), (720, 560), (860, 580), (390, 560), (520, 600), (700, 590),
         (580, 870), (700, 1080), (820, 1360), (470, 870), (360, 1090), (240, 1360), (420, 600), (1010, 560), (980, 300)),
 'C4': J((430, 700), (400, 740), (470, 780), (560, 1060), (530, 810), (430, 900), (330, 960), (410, 830), (330, 930), (260, 970),
         (610, 1060), (760, 1200), (760, 1400), (520, 1070), (420, 1300), (650, 1400), (620, 900), (40, 1040), (120, 1330)),
}
add('H09_b12', "Breakdown drawing between the coil and the mid-spin: she is unwinding explosively, torso turning away from the viewer, the scythe starting its horizontal sweep, cloak beginning to flare outward, weight shifting onto the pivot foot.",
    lerpJ(PILOT['C1'], PILOT['C2'], 0.5), refs=['keys/C1_coil.png', 'keys/C2_twist.png'])
add('H09_b23', "Breakdown drawing between the back-view mid-spin and the full extension: she is coming around to face three-quarter front, arms swinging out to full reach, the scythe blade whipping around horizontally at waist height, cloak spiraling.",
    lerpJ(PILOT['C2'], PILOT['C3'], 0.5), refs=['keys/C2_twist.png', 'keys/C3_extend.png'])
add('H09_b34', "Breakdown drawing between the full extension and the low follow-through: the swing carrying her body down and around, dropping toward one knee, the scythe continuing its arc low behind her, cloak wrapping around.",
    lerpJ(PILOT['C3'], PILOT['C4'], 0.5), refs=['keys/C3_extend.png', 'keys/C4_follow.png'])

# ============================================================================ S10 recoil -> flying knee
AIM = J((600, 380), (560, 400), (620, 470), (560, 820), (560, 500), (460, 580), (360, 620), (680, 500), (580, 580), (460, 600),
        (600, 830), (740, 1020), (820, 1340), (520, 840), (400, 1060), (260, 1330), (560, 620), (40, 580), (10, 820))
KNEE = J((560, 360), (600, 380), (540, 450), (470, 760), (560, 490), (460, 600), (380, 680), (500, 500), (400, 610), (320, 690),
         (500, 760), (650, 700), (620, 900), (440, 780), (380, 1000), (240, 1150), (400, 700), (20, 820), (10, 1060))
add('H10_aim', "Braced sideways, facing screen-right, she aims the gun-scythe's barrel BACKWARD past her own hip toward screen-left, both hands on the weapon, knees bent, bracing for the recoil, a cold confident look.", AIM)
add('H10_fire', "The shot fires backward: the recoil hurls her forward off her feet toward screen-right, body tipping forward into the air, knee starting to drive up, cloak blown forward, a muzzle flash behind her.", lerpJ(AIM, KNEE, 0.5), refs=['H10_aim'], after=['H10_aim'])
add('H10_knee', "FLYING KNEE STRIKE: airborne, launched toward screen-right, her right knee driven up and forward like a battering ram, the scythe trailing behind her, cloak and hair streaming back, a savage shout.", KNEE, refs=['H10_aim'], after=['H10_aim'])
add('H10_land', "Landing: she skids to a stop in a low wide stance, one hand touching the snow, the scythe held out behind her, snow spraying from her boots, head up.",
    J((540, 620), (590, 640), (520, 700), (520, 1000), (580, 730), (660, 880), (720, 1060), (470, 730), (380, 860), (300, 980),
      (560, 1000), (720, 1130), (830, 1380), (480, 1010), (330, 1180), (200, 1380), (330, 970), (40, 880), (20, 1100)), refs=['H10_aim'])

# ============================================================================ S11 the pile / burst
add('H11_buried', "Crouched low under a crushing weight, arms crossed over her head, the scythe clutched against her body, eyes squeezed shut, cloak torn; black shadow claws and fur pressing in at the edges of the drawing.", refs=['keys/C4_follow.png'])
add('H11_burst', "EXPLOSIVE RELEASE: she bursts upward standing tall, arms flung wide, head thrown back in a roaring battle cry, the scythe held high in one hand, her cloak blasting outward, fire and light erupting around her body, eyes blazing orange.",
    J((512, 280), (512, 250), (512, 380), (512, 760), (610, 400), (760, 330), (880, 200), (414, 400), (270, 330), (150, 230),
      (570, 770), (640, 1040), (700, 1360), (454, 770), (390, 1040), (320, 1360), (880, 400), (880, -60), (620, -80)))
add('H11_stand', "Standing in the middle of a ring of fire, scythe planted beside her, cloak smouldering at the hem, breathing hard, embers rising, a fierce glare at the viewer.", refs=['keys/D2_rise.png'])

# ============================================================================ S12/13 the King, the paw
add('H12_lookup', "Seen from behind and far below scale: tiny full-body figure standing in the snow looking UP at something enormous above, head tilted far back, the scythe hanging from one hand, cloak blown forward.", refs=['H01_back'])
add('H13_brace', "Extreme LOW ANGLE from below: she braces with the gun-scythe held horizontally over her head with both hands to block something huge coming down from above, knees bent, teeth gritted, snow blasting outward around her, hair whipped by the downdraft.",
    J((512, 520), (512, 500), (512, 610), (512, 960), (600, 620), (700, 470), (760, 300), (424, 620), (330, 470), (270, 300),
      (570, 970), (690, 1170), (760, 1420), (454, 970), (340, 1170), (270, 1420), (130, 300), (900, 300), (1000, 450)))

# ============================================================================ S14 the crater (top-down)
add('H14_lying', "View from DIRECTLY ABOVE: she lies on her back in the snow, arms flung out, legs slightly bent, hair and crimson cloak spread around her like a pool, eyes half-open and dim, a trickle of blood at her lip, the scythe lying out of reach above her head, snow settling on her. The orange clasp at her collar barely glowing.", size='1536x1024')
add('H14_closed', "The exact same drawing as the reference (view from directly above, lying in the snow), but her eyes are fully CLOSED.", size='1536x1024', refs=['H14_lying'], after=['H14_lying'])

# ============================================================================ S15 ignition
add('H15_fireeye', "Anime extreme close-up, landscape full frame: her eyes snapping WIDE open, the irises ablaze with fire, flames licking up out of her pupils, silver hair lifting in an updraft of heat, sparks, lit hot orange from below, intense.", size='1536x1024', bg=None, refs=['keys/B1_eyes.png'])
RISE1 = J((512, 520), (540, 540), (512, 610), (512, 930), (590, 630), (640, 780), (600, 930), (430, 630), (380, 780), (400, 930),
          (560, 940), (640, 1170), (620, 1400), (460, 940), (360, 1120), (300, 1400), (700, 700), (720, 1400), (560, 1420))
RISE2 = J((512, 250), (512, 230), (512, 350), (512, 740), (610, 380), (730, 420), (850, 460), (414, 380), (300, 420), (180, 470),
          (570, 750), (620, 1030), (660, 1360), (454, 750), (400, 1030), (360, 1360), (860, 300), (870, 1400), (700, 1420))
add('H15_rise1', "Rising from the crater: on one knee pushing herself up, head bowed, the scythe gripped upright as a support, her cloak beginning to glow at the edges like embers catching fire.", RISE1)
add('H15_rise2', "Standing up tall with her arms spread wide from her sides, head lifting, eyes closed, the scythe in her right hand, her crimson cloak erupting into flame from the hem upward, heat distortion around her.", RISE2, refs=['H15_rise1'], after=['H15_rise1'])
add('H15_roar', "IGNITION: full body, standing, head thrown back in a roar, fists clenched, the scythe held high, eyes blazing fire, her whole cloak transformed into roaring fire flaring out like wings behind her, embers everywhere, lit hot orange-gold.", RISE2, refs=['H15_rise2'], after=['H15_rise2'])

# ============================================================================ S16 ascent (flying up, wings of fire)
FLY = "Flying straight UPWARD through the air on wings of fire, seen from below and to the side, body arched, hair and the burning cloak streaming downward, trailing fire and embers."
add('H16_fly1', FLY + " The scythe held low trailing below her, eyes locked upward on her target.",
    J((520, 280), (560, 250), (520, 380), (520, 760), (610, 420), (700, 560), (720, 700), (430, 420), (360, 560), (360, 700),
      (570, 770), (620, 1050), (600, 1340), (470, 770), (430, 1060), (470, 1330), (700, 640), (760, 1380), (900, 1300)))
add('H16_cutL', FLY + " She twists and slashes the scythe hard across toward screen-LEFT, a huge horizontal cut, blade trailing light.",
    J((560, 300), (520, 290), (560, 390), (560, 760), (480, 420), (340, 420), (180, 430), (640, 420), (520, 470), (360, 470),
      (600, 770), (650, 1040), (620, 1330), (510, 770), (480, 1050), (520, 1330), (560, 440), (0, 440), (30, 200)), refs=['H16_fly1'], after=['H16_fly1'])
add('H16_cutR', FLY + " She twists the other way and slashes the scythe hard across toward screen-RIGHT, a huge backhand cut, blade trailing light.",
    mirror(J((560, 300), (520, 290), (560, 390), (560, 760), (480, 420), (340, 420), (180, 430), (640, 420), (520, 470), (360, 470),
             (600, 770), (650, 1040), (620, 1330), (510, 770), (480, 1050), (520, 1330), (560, 440), (0, 440), (30, 200))), refs=['H16_fly1'], after=['H16_fly1'])
add('H16_spin', FLY + " She spins head over heels in mid-air, the scythe whirling around her in a full circle, a ring of fire around her.",
    J((512, 1100), (512, 1140), (512, 1000), (512, 640), (600, 980), (700, 900), (800, 780), (424, 980), (330, 900), (220, 780),
      (560, 630), (620, 380), (600, 150), (464, 630), (420, 370), (450, 140), (800, 780), (220, 780), (180, 1000)), refs=['H16_fly1'], after=['H16_fly1'])

# ============================================================================ S17 apex
add('H17_raise', "Seen from BELOW, strongly backlit against a blazing eclipse: at the apex of her flight she raises the gun-scythe high over her head with both hands, body arched back, great wings of fire spread wide, her form mostly a dark silhouette with a burning rim of light, embers frozen in the air around her.",
    J((512, 440), (512, 420), (512, 540), (512, 900), (600, 560), (650, 400), (600, 240), (424, 560), (380, 400), (430, 240),
      (560, 910), (600, 1180), (560, 1440), (464, 910), (430, 1180), (480, 1440), (560, 300), (430, 20), (180, 60)))

# ============================================================================ S18 the cut
DS1 = J((512, 380), (540, 400), (512, 480), (512, 840), (600, 500), (660, 360), (620, 200), (424, 500), (380, 360), (440, 200),
        (560, 850), (600, 1120), (560, 1400), (464, 850), (430, 1120), (480, 1400), (560, 240), (380, -40), (120, -20))
DS2 = J((560, 520), (600, 560), (540, 600), (480, 920), (600, 620), (700, 760), (780, 900), (500, 620), (600, 780), (720, 920),
        (520, 930), (640, 1150), (560, 1420), (440, 940), (320, 1130), (240, 1380), (660, 820), (1000, 1300), (1010, 1500))
add('H18_down1', "The DOWNSWING begins: from high overhead she whips the gun-scythe forward and down with her whole body, back arched, wings of fire flaring, the blade starting to trail white-gold light.", lerpJ(DS1, DS2, 0.35), refs=['H17_raise'])
add('H18_down2', "FULL DOWNSWING: body folded forward completing a colossal diagonal cut, arms fully extended downward, the scythe at the end of its arc, a line of white-gold light trailing from the blade across the whole frame, hair and fire-cloak whipping upward, eyes blazing.", DS2, refs=['H18_down1'], after=['H18_down1'])

# ============================================================================ S19 dawn
add('H19_land', "LANDING in fresh snow at dawn: she drops into a deep crouch on one knee, one hand planted in the snow, the scythe held out to the side, her cloak (now crimson cloth again, smouldering with small embers at the torn hem) settling around her, head down, warm golden light.",
    J((520, 640), (560, 680), (520, 720), (540, 1020), (590, 750), (680, 900), (720, 1080), (460, 750), (380, 900), (330, 1060),
      (580, 1020), (720, 1150), (720, 1400), (500, 1030), (400, 1250), (620, 1400), (760, 900), (1000, 700), (1010, 1000)))
add('H19_stand', "Standing on a snowy ridge at dawn seen from behind in three-quarter back view, looking toward the sunrise on the left, the gun-scythe resting on her right shoulder, cloak and hair drifting in a gentle breeze, warm golden rim light on her silhouette, small embers falling around her, a sense of peace.",
    refs=['H01_back', 'keys/D2_rise.png'])
add('H19_profile', "Close-up, landscape framing, her face in PROFILE facing screen-left toward the rising sun, warm golden light on her face, silver hair with the red streak glowing at the edges, eyes open and soft, a few embers drifting past, gentle expression.", size='1536x1024', bg=None)
add('H19_smile', "Exactly the same drawing and framing as the reference, but she closes her eyes and gives a small, tired, genuine smile.", size='1536x1024', bg=None, refs=['H19_profile'], after=['H19_profile'])

if __name__ == '__main__':
    print(len(D), 'drawings')
