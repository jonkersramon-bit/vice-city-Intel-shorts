"""Vice City Intel: vertical neon short with timed captions and natural Edge TTS.

Original artwork: add your OWN unique portrait PNG/JPG files to assets/.
Without images, procedural neon Miami scenes are rendered locally. No credits.
Edge TTS uses an unofficial online service; availability is not guaranteed.
"""
import asyncio
import math
import os
import random
import re
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
import edge_tts

ROOT=Path(__file__).resolve().parent
OUT=ROOT/"output"
OUT.mkdir(exist_ok=True)
script=os.getenv("SHORT_SCRIPT","").strip()
topic=os.getenv("SHORT_TOPIC","GTA 6 gaming tip").strip()
if not script:
    raise SystemExit("Missing SHORT_SCRIPT")
W,H=720,1280
fontpath="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
font=ImageFont.truetype(fontpath,42)
fontsmall=ImageFont.truetype(fontpath,31)
word_events=[]

async def narrate():
    communicate=edge_tts.Communicate(script,"en-US-AriaNeural",rate="+8%")
    with (OUT/"voice.mp3").open("wb") as f:
        async for part in communicate.stream():
            if part["type"]=="audio":
                f.write(part["data"])
            elif part["type"]=="WordBoundary":
                word_events.append((part["offset"]/10_000_000,part["duration"]/10_000_000,part["text"]))
asyncio.run(narrate())
duration=float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","default=noprint_wrappers=1:nokey=1",str(OUT/"voice.mp3")],text=True).strip())
if duration<=0: raise RuntimeError("Voice-over has zero duration")
duration+=0.35

def draw_procedural(i):
    """Original neon city scenes, NOT generated gameplay or AI photos."""
    rng=random.Random(84591+i*391)
    im=Image.new("RGB",(W,H))
    pix=im.load()
    for y in range(H):
        p=y/H
        for x in range(W):
            glow=max(0,1-abs(x-W*.5)/(W*.7))
            pix[x,y]=(int(45+105*(1-p)*glow),int(13+25*p),int(75+52*p))
    d=ImageDraw.Draw(im,"RGBA")
    horizon=690+rng.randint(-75,65)
    d.ellipse((100,150,630,680),fill=(255,58,175,35))
    d.ellipse((200,220,570,590),fill=(255,96,171,38))
    for j in range(20):
        bw=rng.randint(32,95);bx=j*44-50
        bh=rng.randint(120,430)
        d.rectangle((bx,horizon-bh,bx+bw,horizon),fill=(17,9,44,255))
        for yy in range(horizon-bh+18,horizon-15,31):
            for xx in range(bx+9,bx+bw-5,20):
                if rng.random()>.45:
                    d.rectangle((xx,yy,xx+6,yy+12),fill=(24,225,255,150) if rng.random()>.5 else (255,60,184,190))
    d.polygon([(0,H),(W,H),(W,horizon),(0,horizon)],fill=(10,8,36,255))
    for j in range(13):
        y=horizon+int(((j+1)/13)**1.8*(H-horizon))
        d.line((0,y,W,y),fill=(255,40,165,30+j*8),width=2)
    for k in range(4):
        x=rng.choice([60,130,590,665])
        d.line((x,horizon-210,x+(-20 if x<W/2 else 20),horizon+100),fill=(8,7,31,255),width=17)
        for a in range(10):
            angle=a*math.pi/5
            d.line((x,horizon-210,x+int(105*math.cos(angle)),horizon-210+int(60*math.sin(angle))),fill=(10,11,36,255),width=12)
    return im.filter(ImageFilter.GaussianBlur(.5))

assets=sorted([p for p in (ROOT/"assets").glob("*") if p.suffix.lower() in (".png",".jpg",".jpeg",".webp")]) if (ROOT/"assets").exists() else []
sentences=[s.strip() for s in re.split(r"(?<=[.!?])\s+",script) if s.strip()]
n=max(4,min(6,len(sentences)))
scene_duration=duration/n
for i in range(n):
    if assets:
        im=Image.open(assets[i%len(assets)]).convert("RGB")
        sw,sh=im.size
        scale=max(W/sw,H/sh)
        im=im.resize((math.ceil(sw*scale),math.ceil(sh*scale)),Image.Resampling.LANCZOS)
        x=(im.width-W)//2;y=(im.height-H)//2
        im=im.crop((x,y,x+W,y+H))
    else:
        im=draw_procedural(i)
    im.save(OUT/f"scene_{i:02}.png")

def stamp(sec):
    cs=round(max(0,sec)*100)
    return f"{cs//360000}:{cs//6000%60:02}:{cs//100%60:02}.{cs%100:02}"

ass=OUT/"captions.ass"
header="""[Script Info]
ScriptType: v4.00+
PlayResX: 720
PlayResY: 1280
WrapStyle: 2
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Captions,DejaVu Sans,36,&H00FFFFFF,&H000000FF,&H004B1545,&H950A0622,1,0,0,0,100,100,0,0,1,3,1,2,45,45,225,1
Style: Brand,DejaVu Sans,35,&H00FFE829,&H000000FF,&H00300B25,&H00000000,1,0,0,0,100,100,0,0,1,2,0,8,30,30,70,1
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
with ass.open("w",encoding="utf-8") as f:
    f.write(header)
    f.write(f"Dialogue: 0,{stamp(0)},{stamp(duration)},Brand,,0,0,0,,VICE CITY INTEL\n")
    if word_events:
        # Use actual word timestamps from synthesis, not estimates.
        for j in range(0,len(word_events),5):
            group=word_events[j:j+5]
            start=group[0][0]
            end=word_events[j+5][0] if j+5<len(word_events) else duration
            caption=" ".join(w[2] for w in group).upper().replace("{","").replace("}","")
            f.write(f"Dialogue: 1,{stamp(start)},{stamp(end)},Captions,,0,0,0,,{caption}\n")
    else:
        # Rare fallback if provider does not send word boundaries.
        for i,s in enumerate(sentences):
            f.write(f"Dialogue: 1,{stamp(duration*i/len(sentences))},{stamp(duration*(i+1)/len(sentences))},Captions,,0,0,0,,{s.upper()}\n")

# Each scene is gently zoomed; transitions are short crossfades.
cmd=["ffmpeg","-y","-loglevel","error"]
for i in range(n):
    cmd+=["-loop","1","-framerate","30","-t",str(scene_duration+.3),"-i",str(OUT/f"scene_{i:02}.png")]
cmd+=["-i",str(OUT/"voice.mp3")]
filters=[]
for i in range(n):
    filters.append(f"[{i}:v]scale=800:1423,crop=720:1280:x='40+20*sin(n/60)':y='70+20*cos(n/75)',setsar=1,trim=duration={scene_duration+.25:.3f},setpts=PTS-STARTPTS,format=yuv420p[v{i}]")
last="v0"
for i in range(1,n):
    nextname=f"xf{i}"
    filters.append(f"[{last}][v{i}]xfade=transition=fade:duration=0.25:offset={scene_duration*i:.3f}[{nextname}]")
    last=nextname
filters.append(f"[{last}]ass={ass.as_posix()},drawbox=x=0:y=0:w=720:h=8:color=0xff39be:t=fill,drawbox=x=0:y=1272:w=720:h=8:color=0x23e6ff:t=fill[vout]")
cmd+=["-filter_complex",";".join(filters),"-map","[vout]","-map",f"{n}:a:0","-t",str(duration),"-c:v","libx264","-preset","veryfast","-crf","21","-r","30","-c:a","aac","-b:a","160k","-movflags","+faststart",str(OUT/"vice_city_intel.mp4")]
subprocess.run(cmd,check=True)
(OUT/"youtube.txt").write_text(f"{topic} 🎮 #Shorts\n\n{script}\n\nIllustrative visuals; not gameplay footage.\n#GTA6 #ViceCityIntel #GamingTips #Shorts\n",encoding="utf-8")
print("Created",OUT/"vice_city_intel.mp4",f"duration={duration:.1f}s",f"words={len(word_events)}",f"images={len(assets)}")
