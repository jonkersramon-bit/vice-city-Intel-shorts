"""Create a short with free edge-tts, FFmpeg, and generated graphic slides.

Voice service requires internet and can rate-limit. This does not claim unlimited
service or original AI illustrations. Place up to 8 portrait images in assets/
to use custom scene art; otherwise graphic scenes are drawn locally.
"""
import asyncio
import os
import re
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import edge_tts

ROOT=Path(__file__).parent
OUT=ROOT/"output"
OUT.mkdir(exist_ok=True)
script=os.environ.get("SHORT_SCRIPT","").strip()
topic=os.environ.get("SHORT_TOPIC","Gaming tip").strip()
if not script:
    raise ValueError("SHORT_SCRIPT cannot be empty")
voice="en-US-AriaNeural"
async def speak():
    comm=edge_tts.Communicate(script,voice,rate="+7%")
    await comm.save(str(OUT/"voice.mp3"))
asyncio.run(speak())
def duration(path):
    r=subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","default=noprint_wrappers=1:nokey=1",str(path)],text=True)
    return float(r.strip())
seconds=duration(OUT/"voice.mp3")+0.5
sentences=[s.strip() for s in re.split(r"(?<=[.!?])\s+",script) if s.strip()]
if not sentences: sentences=[script]
images=sorted((ROOT/"assets").glob("*.png"))+sorted((ROOT/"assets").glob("*.jpg"))
W,H=720,1280
font_path="/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
font=ImageFont.truetype(font_path,43)
small=ImageFont.truetype(font_path,32)
def wrap(text,draw,f,maxw):
    words=text.split()
    lines=[];line=""
    for word in words:
        test=(line+" "+word).strip()
        if draw.textbbox((0,0),test,font=f)[2]>maxw and line:
            lines.append(line);line=word
        else:line=test
    if line:lines.append(line)
    return lines
frames=[]
for i,sentence in enumerate(sentences):
    if images:
        im=Image.open(images[i%len(images)]).convert("RGB")
        iw,ih=im.size
        scale=max(W/iw,H/ih)
        im=im.resize((round(iw*scale),round(ih*scale)),Image.Resampling.LANCZOS)
        x=(im.width-W)//2;y=(im.height-H)//2
        im=im.crop((x,y,x+W,y+H))
    else:
        im=Image.new("RGB",(W,H))
        pix=im.load()
        for y in range(H):
            for x in range(W):
                pix[x,y]=(int(19+20*y/H),int(9+20*x/W),int(48+38*y/H))
    d=ImageDraw.Draw(im,"RGBA")
    d.rectangle((0,0,W,150),fill=(9,5,30,215))
    d.text((W//2,67),"VICE CITY INTEL",font=font,anchor="mm",fill="#27e8ff",stroke_width=2,stroke_fill="#071022")
    d.rectangle((25,820,W-25,1125),fill=(9,5,30,225))
    d.rectangle((25,820,W-25,830),fill="#fc3cb7")
    lines=wrap(sentence,d,small,W-110)
    lineheight=49
    y=965-(len(lines)-1)*lineheight/2
    for line in lines:
        d.text((W//2,y),line,font=small,anchor="mm",fill="white",stroke_width=2,stroke_fill="#220b35")
        y+=lineheight
    d.text((W//2,1190),"GAMING TIPS  •  VICE CITY",font=small,anchor="mm",fill="#27e8ff")
    path=OUT/f"scene_{i:02}.jpg"
    im.save(path,quality=92)
    frames.append(path)
# Approximate captions timed by word count; for exact sync use TTS word boundaries.
weights=[max(1,len(s.split())) for s in sentences]
total=sum(weights)
with open(OUT/"frames.txt","w") as f:
    for path,w in zip(frames,weights):
        f.write(f"file '{path.resolve()}'\n")
        f.write(f"duration {seconds*w/total:.3f}\n")
    f.write(f"file '{frames[-1].resolve()}'\n")
subprocess.run(["ffmpeg","-y","-v","error","-safe","0","-f","concat","-i",str(OUT/"frames.txt"),"-i",str(OUT/"voice.mp3"),"-vf","fps=30,format=yuv420p","-c:v","libx264","-preset","veryfast","-crf","21","-c:a","aac","-b:a","160k","-shortest","-movflags","+faststart",str(OUT/"vice_city_intel.mp4")],check=True)
(OUT/"youtube.txt").write_text(f"{topic} | Vice City Intel #Shorts\n\n{script}\n\n#Gaming #PS5 #Shorts\n",encoding="utf-8")
print("Video created:",OUT/"vice_city_intel.mp4")
