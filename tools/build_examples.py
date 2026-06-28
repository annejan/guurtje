#!/usr/bin/env python3
import math, os, sys, importlib.util, subprocess
from PIL import Image, ImageDraw, ImageFont
import numpy as np

REPO="/home/annejan/Projects/guurtje"
ICON=REPO+"/assets/icons"; DISC=REPO+"/assets/disc"
os.makedirs(ICON,exist_ok=True); os.makedirs(DISC,exist_ok=True)
spec=importlib.util.spec_from_file_location("dd",REPO+"/hardware/disc_driver.py")
dd=importlib.util.module_from_spec(spec); spec.loader.exec_module(dd)
M=dd.load_coords(REPO+"/data/coords_stopnu.csv")

S=256; C=S//2
FONT=ImageFont.truetype("/usr/share/fonts/texlive-dejavu/DejaVuSansMono-Bold.ttf",66)
def base(): return Image.new("RGB",(S,S),(0,0,0))

def pharmacy(on=True):
    im=base(); d=ImageDraw.Draw(im); g=(0,230,55) if on else (0,45,14)
    w,L=64,196
    d.rectangle([C-w//2,C-L//2,C+w//2,C+L//2],fill=g)
    d.rectangle([C-L//2,C-w//2,C+L//2,C+w//2],fill=g); return im
def stop():
    im=base(); d=ImageDraw.Draw(im); r=120
    pts=[(C+r*math.cos(math.pi/8+k*math.pi/4),C+r*math.sin(math.pi/8+k*math.pi/4)) for k in range(8)]
    d.polygon(pts,fill=(220,24,24)); d.polygon(pts,outline=(255,255,255),width=9)
    b=d.textbbox((0,0),"STOP",font=FONT)
    d.text((C-(b[2]-b[0])/2,C-(b[3]-b[1])/2-b[1]),"STOP",fill=(255,255,255),font=FONT); return im
def ampel_red():
    im=base(); d=ImageDraw.Draw(im); c=(235,40,30)
    d.ellipse([C-26,40,C+26,92],fill=c); d.rectangle([C-42,46,C+42,56],fill=c)
    d.rectangle([C-30,96,C+30,178],fill=c)
    d.rectangle([C-92,108,C-30,134],fill=c); d.rectangle([C+30,108,C+92,134],fill=c)
    d.rectangle([C-28,178,C-6,222],fill=c); d.rectangle([C+6,178,C+28,222],fill=c); return im
def ampel_green():
    im=base(); d=ImageDraw.Draw(im); c=(40,220,60)
    d.ellipse([C-22,40,C+30,92],fill=c); d.polygon([(C-38,54),(C+46,46),(C+46,56),(C-38,64)],fill=c)
    d.rectangle([C-24,96,C+32,166],fill=c)
    d.polygon([(C+8,158),(C+62,206),(C+46,222),(C-4,176)],fill=c)
    d.polygon([(C-6,158),(C-52,204),(C-36,220),(C+8,176)],fill=c)
    d.polygon([(C-18,104),(C-58,138),(C-46,150),(C-6,120)],fill=c)
    d.polygon([(C+24,104),(C+58,88),(C+68,100),(C+32,124)],fill=c); return im
def heart():
    im=base(); d=ImageDraw.Draw(im); c=(228,28,52)
    d.ellipse([C-72,68,C-2,150],fill=c); d.ellipse([C+2,68,C+72,150],fill=c)
    d.polygon([(C-68,116),(C+68,116),(C,208)],fill=c); return im
def smiley():
    im=base(); d=ImageDraw.Draw(im); y=(255,212,0)
    d.ellipse([C-112,C-112,C+112,C+112],fill=y)
    d.ellipse([C-52,C-46,C-22,C-6],fill=(25,25,25)); d.ellipse([C+22,C-46,C+52,C-6],fill=(25,25,25))
    d.arc([C-62,C-34,C+62,C+72],20,160,fill=(25,25,25),width=14); return im
def pacman():
    im=base(); d=ImageDraw.Draw(im); y=(255,228,0)
    d.pieslice([C-112,C-112,C+112,C+112],32,328,fill=y)
    d.ellipse([C+22,C-58,C+44,C-36],fill=(0,0,0)); return im
def owl():
    im=base(); d=ImageDraw.Draw(im); body=(122,86,52)
    d.polygon([(C-78,C-66),(C-44,C-98),(C-38,C-56)],fill=body)
    d.polygon([(C+78,C-66),(C+44,C-98),(C+38,C-56)],fill=body)
    d.ellipse([C-94,C-80,C+94,C+110],fill=body)
    for sx in (-46,46):
        d.ellipse([C+sx-36,C-60,C+sx+36,C+12],fill=(245,245,232))
        d.ellipse([C+sx-17,C-42,C+sx+17,C-8],fill=(20,20,20))
        d.ellipse([C+sx-6,C-38,C+sx+3,C-28],fill=(255,255,255))
    d.polygon([(C-13,C-4),(C+13,C-4),(C,C+24)],fill=(242,172,30)); return im
def yinyang():
    im=base(); d=ImageDraw.Draw(im); R=112; W=(245,245,245); B=(18,18,18)
    d.ellipse([C-R,C-R,C+R,C+R],fill=W); d.pieslice([C-R,C-R,C+R,C+R],-90,90,fill=B)
    d.ellipse([C-R//2,C-R,C+R//2,C],fill=W); d.ellipse([C-R//2,C,C+R//2,C+R],fill=B)
    d.ellipse([C-12,C-R//2-12,C+12,C-R//2+12],fill=B); d.ellipse([C-12,C+R//2-12,C+12,C+R//2+12],fill=W); return im
def radiation():
    im=base(); d=ImageDraw.Draw(im)
    d.ellipse([C-116,C-116,C+116,C+116],fill=(250,205,0))
    for k in range(3):
        a=-90+k*120; d.pieslice([C-92,C-92,C+92,C+92],a-30,a+30,fill=(18,18,18))
    d.ellipse([C-42,C-42,C+42,C+42],fill=(250,205,0)); d.ellipse([C-22,C-22,C+22,C+22],fill=(18,18,18)); return im

ICONS=[("pharmacy_cross",pharmacy(),"Groen apothekerskruis (FR/EU pharmacie)"),
       ("stop",stop(),"Letterlijke STOP (rood octagon)"),
       ("ampelmann_red",ampel_red(),"Ampelmännchen — rood (halt)"),
       ("ampelmann_green",ampel_green(),"Ampelmännchen — groen (loop)"),
       ("heart",heart(),"Hart"),("smiley",smiley(),"Smiley"),
       ("pacman",pacman(),"Pac-Man"),("owl",owl(),"NightOwl uil"),
       ("yinyang",yinyang(),"Yin-yang"),("radiation",radiation(),"Radioactief / trefoil")]

def render_disc(pil_img, out):                       # project a PIL image onto StopNu disc
    tmp=ICON+"/_tmp.png"; pil_img.save(tmp)
    rgb=dd.ImageSource(tmp).colours(M,0); dd.save_preview(M,rgb,out); os.remove(tmp)

for name,img,_ in ICONS:
    img.save(f"{ICON}/{name}.png"); render_disc(img,f"{DISC}/{name}_disc.png")
    print("icon+disc",name)

# animations: pharmacy blink + ampel switch -> icon GIF + disc GIF
def make_gif(frames, icon_gif, disc_gif, fps=4):
    frames[0].save(icon_gif,save_all=True,append_images=frames[1:],duration=int(1000/fps),loop=0,disposal=2)
    src=dd.ImageSource(icon_gif); FR="/tmp/_exfr"; os.makedirs(FR,exist_ok=True)
    for f in os.listdir(FR): os.remove(FR+"/"+f)
    n=src.frames
    for i in range(n):
        rgb=src.colours(M,i); dd.save_preview(M,rgb,f"{FR}/f{i:03d}.png")
    subprocess.run(f'ffmpeg -y -framerate {fps} -i {FR}/f%03d.png -vf '
        f'"scale=420:-1:flags=lanczos,split[s0][s1];[s0]palettegen=stats_mode=full[p];[s1][p]paletteuse" '
        f'-loop 0 {disc_gif}',shell=True,check=True,stderr=subprocess.DEVNULL)

make_gif([pharmacy(True),pharmacy(True),pharmacy(False)],
         f"{ICON}/pharmacy_blink.gif",f"{DISC}/pharmacy_blink_disc.gif",fps=3)
make_gif([ampel_red(),ampel_red(),ampel_red(),ampel_green(),ampel_green(),ampel_green()],
         f"{ICON}/ampelmann.gif",f"{DISC}/ampelmann_disc.gif",fps=4)
print("animations done; icons:",len(ICONS))
