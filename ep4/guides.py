# Layout: pose guides for each key drawing (1024x1536 portrait). Joint positions authored by hand.
from PIL import Image, ImageDraw
W, H = 1024, 1536
# joints: head(c), neck, pelvis, shoulders L/R, elbows, hands, hips, knees, feet; weapon butt->head, blade tip
# L = her left (blue), R = her right (red). Coordinates in pixels.
K = {
 'A1_guard': dict(head=(470,260), nose=(430,270), neck=(480,360), pelvis=(500,760),
   sR=(560,400), eR=(640,560), hR=(690,700), sL=(410,400), eL=(360,560), hL=(430,690),
   hipR=(560,760), kR=(690,1010), fR=(760,1330), hipL=(440,770), kL=(350,1020), fL=(250,1320),
   wb=(300,560), wh=(900,860), bt=(990,1180)),
 'C1_coil': dict(head=(430,470), nose=(390,500), neck=(460,560), pelvis=(560,900),
   sR=(530,590), eR=(640,720), hR=(740,800), sL=(390,610), eL=(470,760), hL=(600,810),
   hipR=(610,900), kR=(760,1080), fR=(820,1360), hipL=(500,910), kL=(330,1100), fL=(220,1360),
   wb=(400,820), wh=(990,780), bt=(960,560)),
 'C2_twist': dict(head=(520,420), nose=(560,440), neck=(520,510), pelvis=(500,860),
   sR=(400,560), eR=(300,660), hR=(220,700), sL=(640,560), eL=(720,650), hL=(640,700),
   hipR=(440,870), kR=(380,1100), fR=(340,1370), hipL=(560,870), kL=(660,1080), fL=(720,1360),
   wb=(760,700), wh=(60,720), bt=(20,960)),
 'C3_extend': dict(head=(430,420), nose=(470,440), neck=(460,510), pelvis=(520,860),
   sR=(560,550), eR=(720,560), hR=(860,580), sL=(390,560), eL=(520,600), hL=(700,590),
   hipR=(580,870), kR=(700,1080), fR=(820,1360), hipL=(470,870), kL=(360,1090), fL=(240,1360),
   wb=(420,600), wh=(1010,560), bt=(980,300)),
 'C4_follow': dict(head=(430,700), nose=(400,740), neck=(470,780), pelvis=(560,1060),
   sR=(530,810), eR=(430,900), hR=(330,960), sL=(410,830), eL=(330,930), hL=(260,970),
   hipR=(610,1060), kR=(760,1200), fR=(760,1400), hipL=(520,1070), kL=(420,1300), fL=(650,1400),
   wb=(620,900), wh=(40,1040), bt=(120,1330)),
 'D2_rise': dict(head=(520,250), nose=(560,260), neck=(510,350), pelvis=(500,760),
   sR=(430,400), eR=(380,560), hR=(370,700), sL=(590,400), eL=(620,560), hL=(600,700),
   hipR=(450,770), kR=(430,1030), fR=(420,1330), hipL=(560,770), kL=(600,1030), fL=(640,1330),
   wb=(360,420), wh=(380,1250), bt=(640,1330)),
}
def draw(name, j):
    im = Image.new('RGB', (W, H), (235, 235, 240)); d = ImageDraw.Draw(im)
    R, L, C = (220, 40, 40), (40, 90, 220), (40, 40, 40)
    seg = lambda a, b, c, w=26: d.line([j[a], j[b]], fill=c, width=w)
    seg('neck', 'pelvis', C, 40)
    for s in 'RL':
        c = R if s == 'R' else L
        seg('neck', 's'+s, c, 22); seg('s'+s, 'e'+s, c); seg('e'+s, 'h'+s, c)
        seg('pelvis', 'hip'+s, c, 22); seg('hip'+s, 'k'+s, c, 30); seg('k'+s, 'f'+s, c, 26)
        for q in ('h'+s, 'f'+s): x, y = j[q]; d.ellipse([x-20, y-20, x+20, y+20], fill=c)
    x, y = j['head']; d.ellipse([x-70, y-85, x+70, y+85], outline=C, width=10)
    d.line([j['head'], j['nose']], fill=C, width=10)
    d.line([j['wb'], j['wh']], fill=(120, 60, 20), width=14)
    d.line([j['wh'], j['bt']], fill=(150, 150, 150), width=24)
    im.save(f'guides/{name}.png')
for k, v in K.items(): draw(k, v)
# contact sheet
ims = [Image.open(f'guides/{k}.png').resize((256, 384)) for k in K]
S = Image.new('RGB', (256 * len(ims), 384)); [S.paste(im, (i * 256, 0)) for i, im in enumerate(ims)]
S.save('guides/_sheet.png')
