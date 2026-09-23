"""EMBER III — shot table: keyframe prompts, motion prompts, model tiers."""

STYLE = ("Top-tier Japanese TV anime key frame, cinematic 16:9 composition, crisp clean line art with variable line "
         "weight, cel shading, painterly background art, ufotable-style digital compositing with glow, light bloom "
         "and particles, dynamic camera angle, dramatic lighting. No text, no subtitles, no watermark.")
NIGHT = ("Palette: deep indigo and blue-black night, silver moonlight, snow; the ONLY warm colors are her crimson "
         "cloak, the ember-orange glow of her eyes and collar clasp, and floating embers.")
FIRE = ("Palette flipped to blazing orange, gold and hot magenta fire light against the black void; intense glow, "
        "heat haze, flying embers.")
HER = ("The heroine exactly as in the reference character sheet (silver-white hair with one red streak, ember-orange "
       "eyes, crimson hooded half-cloak with tattered hem, glowing ember clasp, black combat suit with leather straps, "
       "charcoal scarf, black knee boots) and the reference gun-scythe.")
CHAR = ['refs/char_sheet_v1.png', 'refs/weapon_sheet_v1.png']
WOLF = ['refs/wolf_sheet_v1.png']
KING = ['refs/king_keyvisual_v1.png']
NEG = ("text, subtitles, watermark, logo, 3D render, CGI, photorealistic, extra limbs, deformed hands, "
       "morphing face, blurry, low detail")

# id: (keyframe prompt, refs, motion prompt, tier, seconds)
SHOTS = {
    's01_clearing': (
        "Extreme wide shot at night: a quiet snowy clearing in a pine forest after a battle, a huge full moon low in "
        "the sky, glowing orange embers drifting slowly upward, trampled snow and scorch marks. A tiny lone figure "
        "in a red cloak holding a folded scythe stands in the center, seen from behind. Peaceful, melancholic. "
        + HER + ' ' + NIGHT, CHAR,
        "Very slow camera push in. Embers drift upward, light snow falls, her cloak moves gently in the wind. "
        "Calm, still, melancholic.", 'lite', 6),
    's02_eye': (
        "Extreme close-up of the heroine's face in profile-three-quarter view, eyes closed, snowflakes caught on her "
        "silver eyelashes and hair, soft breath vapor, moonlight rim light on her cheek, crimson hood edge in frame. "
        + HER + ' ' + NIGHT, CHAR,
        "Her eye slowly opens revealing a glowing ember-orange iris, she exhales a small cloud of breath vapor, "
        "then her eyes shift sharply to the side, alert. Snow drifts past. Subtle, tense.", 'lite', 4),
    's03_eclipse': (
        "Low angle shot of a huge full moon in a night sky above snowy pine treetops; a black shadow is taking a "
        "bite out of the moon's edge like an eclipse beginning; in the foreground snow, jagged black cracks glowing "
        "faint white-blue at the edges are spreading across the ground toward the viewer. Ominous. " + NIGHT, [],
        "The eclipse shadow creeps across the moon, black cracks race across the snow toward the camera, glowing "
        "faintly, snow trembles. Ominous.", 'lite', 4),
    's04_tide': (
        "Wide low-angle shot of the edge of a dark pine forest at night: black ink-like shadow wells out between the "
        "trees, and hundreds of pairs of glowing white-blue eyes open in the darkness; the first shadow wolves are "
        "pouring out onto the snow like a black flood. Menacing, epic scale. " + NIGHT, WOLF,
        "A tide of black shadow wolves pours out of the forest toward the camera like a flood, hundreds of glowing "
        "eyes, black smoke streaming, snow spraying. Fast and overwhelming.", 'fast', 6),
    's05a_unfold': (
        "Dynamic close-up insert shot of the gun-scythe mechanism: gloved hand gripping the black shaft as the "
        "telescoping shaft snaps outward, mechanical hinges and crimson stripes, sparks of motion, sharp speed lines. "
        + HER + ' ' + NIGHT, CHAR, None, 'still', 0),
    's05b_blade': (
        "Dynamic close-up insert shot: the curved scythe blade swinging out and locking into place on its hinge, "
        "a bright glint of moonlight along the steel edge and a thin ember-orange glow line on the cutting edge. "
        + NIGHT, CHAR, None, 'still', 0),
    's05c_chamber': (
        "Dynamic close-up insert shot: the rifle receiver on the scythe shaft, a gloved thumb racking the bolt, a large "
        "brass cartridge being chambered, tiny sparks, dramatic rim light. " + NIGHT, CHAR, None, 'still', 0),
    's06_launch': (
        "Dramatic low angle shot: the heroine crouched low in the snow in a coiled launch stance, gun-scythe drawn back "
        "behind her, cloak whipping violently, eyes glowing ember-orange, the snow beneath her boot cracking; in the "
        "background a black tide of shadow wolves charges toward her. " + HER + ' ' + NIGHT, CHAR + WOLF,
        "She explodes forward toward the wolves in a burst of speed, snow erupting behind her, cloak snapping, "
        "camera shakes. Anime action, fast.", 'fast', 4),
    's07a_run': (
        "Side-on tracking shot: the heroine sprinting at full speed across the snow alongside a stampede of black shadow "
        "wolves, background streaked with horizontal speed lines and motion blur, cloak streaming behind her, "
        "scythe held low, snow spray. " + HER + ' ' + NIGHT, CHAR + WOLF,
        "Fast side-tracking anime running shot, background streaks past, she cuts down a wolf mid-stride with the "
        "scythe, it bursts into black ink and smoke.", 'fast', 6),
    's07b_spin': (
        "Overhead three-quarter shot: the heroine mid 360-degree spin slash in the center of a ring of lunging shadow "
        "wolves, a glowing circular arc of light trails the scythe blade, wolves bursting into splashes of black ink "
        "and smoke. " + HER + ' ' + NIGHT, CHAR + WOLF,
        "She spins in a full circle, the scythe leaves a glowing arc, every wolf in the ring is cut and explodes into "
        "black ink splashes. Dynamic sakuga action.", 'fast', 4),
    's07c_recoil': (
        "Dynamic mid-air action shot: the heroine firing the rifle of her scythe backward, a huge muzzle flash and "
        "shockwave, the recoil hurling her forward through the air into a flying knee strike toward a leaping shadow "
        "wolf. " + HER + ' ' + NIGHT, CHAR + WOLF,
        "She fires backward, the recoil launches her forward, she smashes a knee into the wolf's jaw, it shatters "
        "into black smoke. Explosive anime action.", 'fast', 4),
    's07d_slide': (
        "Low ground-level shot: the heroine sliding on her knees across the snow beneath a leaping shadow wolf, her "
        "scythe raised to slice its belly, snow spraying, the wolf silhouetted against the moon above her. "
        + HER + ' ' + NIGHT, CHAR + WOLF,
        "She slides under the leaping wolf and slices upward, the wolf splits and dissolves into black ink behind "
        "her, snow sprays. Fast.", 'fast', 4),
    's07f_burst': (
        "Wide shot: a huge mound of shadow wolves piled on top of the heroine, dozens of glowing eyes, black smoke; "
        "cracks of orange light breaking through the pile from within. " + NIGHT, WOLF,
        "The pile of wolves bulges, then explodes outward in a shockwave of orange light as she bursts free, wolves "
        "flung in every direction dissolving into smoke.", 'fast', 4),
    's08_king': (
        "Epic extreme wide shot looking up: the black tide of shadow wolves flowing backward and upward into a single "
        "colossal wolf as tall as a mountain, dozens of glowing eyes, crown of broken spikes, the full moon behind its "
        "head almost completely eclipsed into a thin ring of light. The tiny heroine in red at the bottom of frame. "
        + NIGHT, KING + CHAR,
        "The shadow wolves stream upward and merge into the colossal wolf, it rises and opens dozens of glowing eyes, "
        "the eclipse closes into a ring of fire. Slow, enormous, terrifying.", 'fast', 8),
    's09_paw': (
        "Extreme low angle: a colossal black shadow paw the size of a building descending from the sky toward the "
        "heroine, who looks up with the scythe raised to block, snow blasting outward, shockwave. "
        + HER + ' ' + NIGHT, CHAR + KING,
        "The giant paw slams down on her, a massive shockwave of snow explodes outward, the screen shakes violently.",
        'fast', 4),
    's10_crater': (
        "Top-down shot: the heroine lying on her back at the bottom of a crater in the snow, hood torn, hair spread, "
        "eyes half-open and dim, the crimson cloak spread out like a pool of red, the ember clasp at her collar "
        "flickering faintly; the scythe lying out of reach; snow falling gently. Quiet, desperate. "
        + HER + ' ' + NIGHT, CHAR,
        "Very still. Snow falls onto her. The ember clasp flickers weakly, dimming. Her chest rises with a shallow "
        "breath. Slow.", 'lite', 6),
    's10b_hand': (
        "Extreme close-up: the heroine's gloved hand lying in the snow, fingers slowly beginning to curl into a fist, "
        "a faint orange glow starting between the fingers, snowflakes. " + NIGHT, CHAR,
        "Her fingers slowly close into a fist, gripping the snow, an orange glow grows between her fingers, "
        "the snow around her hand starts to melt and steam.", 'lite', 4),
    's11a_eyes': (
        "Extreme close-up of the heroine's face, eyes wide open and blazing with ember-orange fire, flames licking up "
        "from the irises, strands of silver hair lifting in a rising updraft, determined fierce expression. "
        + HER + ' ' + FIRE, CHAR,
        "Her eyes blaze brighter, fire pours from them, her hair whips upward in a rising heat wave, the frame "
        "floods with orange light.", 'fast', 4),
    's11b_ignite': (
        "Epic full-body shot: the heroine rising to her feet in the crater as her crimson cloak bursts into huge wings "
        "of fire, a ring of snow flash-evaporating into a wall of white steam around her, embers everywhere, "
        "gun-scythe held at her side, eyes blazing. " + HER + ' ' + FIRE, CHAR,
        "Her cloak erupts into roaring wings of fire, a shockwave ring of steam blasts outward, embers swirl, "
        "she stands tall. Explosive, triumphant.", 'fast', 6),
    's12a_ascend': (
        "Dynamic vertical shot: the heroine launching straight upward along the side of the colossal shadow wolf's "
        "body, trailing a comet tail of fire, the rifle blast beneath her, the giant's dark flank and glowing eyes "
        "rushing past. " + HER + ' ' + FIRE, CHAR + KING,
        "She rockets upward trailing fire, the camera spins around her as she ascends, the giant's dark body rushes "
        "past, speed lines.", 'fast', 6),
    's12b_tendrils': (
        "Mid-air action shot: dozens of whip-like black shadow tendrils lashing at the heroine as she flies upward "
        "through the air on wings of fire, she cuts through them with a glowing arc of her scythe, severed tendrils "
        "dissolving into black smoke. " + HER + ' ' + FIRE, CHAR + KING,
        "Black tendrils lash at her from all sides, she twists and slices through them in a burst of glowing arcs, "
        "they explode into smoke. Fast sakuga action.", 'fast', 4),
    's13_apex': (
        "Epic backlit shot: the heroine at the apex high above the colossal shadow wolf's head, silhouetted against "
        "the burning ring of the eclipsed moon, wings of fire spread wide, scythe raised overhead with both hands, "
        "time frozen, embers suspended in the air. " + HER + ' ' + FIRE, CHAR + KING,
        "Almost frozen in time: she slowly raises the scythe higher, embers hang in the air, her fire wings "
        "slowly unfurl. Silent, awe-inspiring slow motion.", 'lite', 4),
    's14_cut': (
        "Extreme wide shot of the night sky: a single brilliant line of white-gold light slashing diagonally across "
        "the entire sky, cutting the colossal shadow wolf cleanly in half, the eclipse ring cracking, light beginning "
        "to pour through. " + FIRE, KING,
        "The line of light blazes, the giant wolf splits along it and its halves slide apart and disintegrate into "
        "black ash, the eclipse shatters and brilliant light floods out.", 'fast', 6),
    's15_dawn': (
        "Wide shot at dawn: sunrise over a snowy pine forest, glowing embers falling gently from a pale gold and rose "
        "sky like snow, the heroine standing on a snowy ridge with her back half turned, cloak smoldering at the hem, "
        "gun-scythe resting on her shoulder, warm light on her face. Hopeful, beautiful. " + HER, CHAR,
        "Embers drift down like snow in the golden sunrise, her cloak and hair move in a gentle breeze, she turns "
        "her head toward the sun with a faint smile. Slow, peaceful.", 'lite', 8),
    's15b_smile': (
        "Close-up of the heroine's face lit by warm golden sunrise, a small tired genuine smile, embers drifting past, "
        "silver hair moving in a breeze, eyes soft ember-orange. " + HER, CHAR,
        "She closes her eyes and smiles softly as warm light washes over her, embers drift past. Gentle.", 'lite', 4),
}
