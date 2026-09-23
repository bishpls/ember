import sys, glob
from PIL import Image, ImageDraw
d=sys.argv[1]; out=sys.argv[2]; cols=int(sys.argv[3]) if len(sys.argv)>3 else 3
fs=sorted(glob.glob(d+'/f*.png'))
w,h=640,360
rows=(len(fs)+cols-1)//cols
S=Image.new('RGB',(cols*w,rows*h))
for i,f in enumerate(fs):
    im=Image.open(f).convert('RGB').resize((w,h))
    fr=int(f.split('/f')[-1][:4])
    ImageDraw.Draw(im).text((8,8),f"f{fr} {(fr-1)/24:.2f}s",fill=(255,255,0))
    S.paste(im,((i%cols)*w,(i//cols)*h))
S.save(out)
