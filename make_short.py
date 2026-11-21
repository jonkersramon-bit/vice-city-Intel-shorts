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
    """Retry transient TTS failures; never render a silent Short."""
    import tempfile
    import time
    voices=["en-US-AriaNeural","en-US-JennyNeural"]
    errors=[]
    for attempt in range(4):
        word_events.clear()
        voice=voices[min(attempt//2,len(voices)-1)]
        target=OUT/"voice.mp3"
        temp=OUT/"voice.partial.mp3"
        if temp.exists():
            temp.unlink()
        try:
            communicate=edge_tts.Communicate(script,voice,rate="+8%")
            with temp.open("wb") as f:
                async for part in communicate.stream():
                    if part["type"]=="audio":
                        f.write(part["data"])
                    elif part["type"]=="WordBoundary":
                        word_events.append((part["offset"]/10_000_000,part["duration"]/10_000_000,part["text"]))
            if not temp.exists() or temp.stat().st_size<2000:
                raise RuntimeError("TTS produced no usable audio")
            subprocess.run(["ffprobe","-v","error","-show_entries","format=duration",
                "-of","default=noprint_wrappers=1:nokey=1",str(temp)],
                check=True,capture_output=True,text=True)
            temp.replace(target)
            return
        except Exception as exc:
            errors.append(f"{voice}: {type(exc).__name__}: {exc}")
            if temp.exists():
                temp.unlink()
            if attempt<3:
                await asyncio.sleep(2*(attempt+1))
    raise RuntimeError("Voice generation failed after retries: "+" | ".join(errors[-2:]))
asyncio.run(narrate())
duration=float(subprocess.check_output(["ffprobe","-v","error","-show_entries","format=duration","-of","default=noprint_wrappers=1:nokey=1",str(OUT/"voice.mp3")],text=True).strip())
if duration<=0: raise RuntimeError("Voice-over has zero duration")
duration+=0.35

# Mission walkthroughs need real TTS word boundaries for reliable subtitles.
# Approximate captions can drift and must not silently pass quality checks.
if os.getenv("MISSION_MODE","1")=="1":
    if len(word_events)<max(5,len(script.split())//3):
        raise RuntimeError("Voice service did not provide enough word timestamps for accurate captions")
    last_time=max(start+length for start,length,_ in word_events)
    if last_time>duration+0.25:
        raise RuntimeError("Voice word timings exceed audio duration")

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


def draw_mission_diagram(im,i):
    """Illustrative neon gaming scene with visual subjects tied to the Short topic."""
    d=ImageDraw.Draw(im,"RGBA")
    cyan=(34,235,255,230); pink=(255,56,182,235)
    text=(topic+" "+script).lower()
    if any(t in text for t in ("storage","ps5","console","update","download","settings","pc")):
        subjects=["console","controller","screen","console","screen","controller"]
    elif any(t in text for t in ("mission","escape","police","car","driving","vehicle","heist")):
        subjects=["car","road","car","road","car","road"]
    else:
        subjects=["city","car","screen","city","controller","car"]
    subject=subjects[i%6]
    if subject=="car":
        d.polygon([(125,625),(235,530),(480,530),(605,625)],fill=(25,43,85,255))
        d.rounded_rectangle((110,610,610,755),radius=40,fill=(20,25,61,255),outline=pink,width=10)
        d.polygon([(245,548),(310,495),(447,495),(490,548)],fill=(16,80,122,240))
        for x in (235,495):
            d.ellipse((x-48,720,x+48,816),fill=(8,8,22,255),outline=cyan,width=10)
        for x in (155,550):
            d.ellipse((x-24,660,x+24,690),fill=(255,235,235,240))
    elif subject=="road":
        d.polygon([(300,520),(425,520),(660,1100),(70,1100)],fill=(16,20,51,240))
        for y in (640,765,920):
            d.line((350,y,375,y+70),fill=cyan if i%2 else pink,width=15)
        for x in (90,590):
            d.line((x,460,x,950),fill=pink,width=7)
    elif subject=="console":
        d.rounded_rectangle((185,440,525,865),radius=45,fill=(236,238,255,255),outline=cyan,width=9)
        d.rounded_rectangle((275,445,435,850),radius=20,fill=(16,19,51,255))
        d.line((270,470,270,840),fill=pink,width=12)
    elif subject=="controller":
        d.rounded_rectangle((105,565,615,830),radius=95,fill=(224,230,252,255),outline=cyan,width=10)
        d.ellipse((225,660,315,750),fill=(21,25,65,255))
        d.ellipse((425,660,515,750),fill=(21,25,65,255))
        d.line((175,650,175,715),fill=pink,width=12)
        d.line((145,685,205,685),fill=pink,width=12)
    elif subject=="screen":
        d.rounded_rectangle((95,420,625,800),radius=25,fill=(15,18,54,255),outline=cyan,width=12)
        d.rectangle((135,460,585,745),fill=(35,20,88,255))
        for j in range(5):
            d.rounded_rectangle((170,510+j*43,480-j*17,530+j*43),radius=6,fill=pink if j%2 else cyan)
        d.line((360,800,360,885),fill=pink,width=14)
    else:
        for j in range(8):
            x=75+j*75
            h=230+(j*71)%260
            d.rectangle((x,850-h,x+60,850),fill=(13,18,56,255),outline=cyan if j%2 else pink,width=5)
    return im


def fetch_licensed_city_photos():
    """Strictly vetted CC photographs; never reuse or silently substitute bad images."""
    import json
    import urllib.parse
    import urllib.request
    import html
    import hashlib
    from io import BytesIO
    context=(topic+" "+script).lower()
    if any(k in context for k in ("console","ps5","xbox","storage","download","update","pc","settings")):
        searches=[
            "gaming console neon light photography",
            "video game controller rgb lighting",
            "gaming computer neon led room",
            "gaming setup RGB monitor",
            "PlayStation controller dark photography",
            "gaming keyboard RGB desk",
            "gaming console LED light",
            "computer gaming setup neon",
        ]
        relevant=("gaming","controller","console","playstation","computer","keyboard",
                  "monitor","xbox","rgb","gamepad","pc")
        irrelevant=("hotel","resort","facade","architecture","building","skyline","beach")
    else:
        searches=[
            "Miami night cars street traffic",
            "Miami police car road at night",
            "Miami sports car downtown street",
            "Miami city highway driving dusk",
            "Miami parking garage automobiles",
            "Miami car headlights street at night",
            "Miami downtown intersection traffic",
            "Miami night road palm trees",
            "Miami street vehicles evening",
            "Miami city traffic night photography",
        ]
        relevant=("car","vehicle","traffic","road","street","highway","drive","driving",
                  "police","parking","intersection","automobile","motor","truck","taxi")
        irrelevant=("hotel","resort","facade","architecture","building","skyline",
                    "beach","sunset","ocean drive hotel","art deco hotel")
    forbidden=("satellite","aerial","map","diagram","drawing","illustration","painting",
               "poster","logo","screenshot","render","generated","skyview","bird's eye",
               "topographic","google earth","nude","nudity","naked","beachgoers",
               "newspaper","new york times","magazine","archive","pdf","scanned","scan",
               "document","manuscript","book page","journal","article","text page","facsimile")
    # Persist reviewed, licensed downloads between GitHub Actions runs.
    # Cache key is topic-specific, so a PC Short never inherits car photos.
    import hashlib
    cache_id=hashlib.sha256((" ".join(searches)).encode()).hexdigest()[:16]
    directory=ROOT/"photo_library"/cache_id
    directory.mkdir(parents=True,exist_ok=True)
    manifest=directory/"credits.txt"
    existing=sorted(directory.glob("photo_*.jpg"))
    if len(existing)>=2 and manifest.exists():
        (OUT/"IMAGE_CREDITS.txt").write_text(manifest.read_text(encoding="utf-8"),encoding="utf-8")
        print("Reusing six cached, licensed photographs from",directory)
        return existing[:6]
    seen_hashes=set()
    seen_pixels=[]
    credits=[]
    # Do not trust incomplete cached sets: rebuild to avoid mixed provenance.
    for old in directory.glob("photo_*.jpg"):
        old.unlink()
    def fingerprint(im):
        # 16x16 grayscale difference hash to catch resizes and near duplicates.
        gray=im.convert("L").resize((17,16),Image.Resampling.LANCZOS)
        pixels=list(gray.get_flattened_data())
        return tuple(pixels[y*17+x]>pixels[y*17+x+1] for y in range(16) for x in range(16))
    for idx,term in enumerate(searches):
        if len(credits)>=6:
            break
        try:
            params=urllib.parse.urlencode({
                "action":"query","generator":"search","gsrsearch":term,
                "gsrnamespace":"6","gsrlimit":"40","prop":"imageinfo",
                "iiprop":"url|extmetadata|size|sha1","iiurlwidth":"1200","format":"json"
            })
            request=urllib.request.Request(
                "https://commons.wikimedia.org/w/api.php?"+params,
                headers={"User-Agent":"ViceCityIntelShorts/1.0 (licensed-image montage)"})
            with urllib.request.urlopen(request,timeout=20) as response:
                pages=json.load(response).get("query",{}).get("pages",{})
            candidates=[]
            for page in pages.values():
                info=(page.get("imageinfo") or [{}])[0]
                meta=info.get("extmetadata",{})
                license_name=html.unescape(meta.get("LicenseShortName",{}).get("value",""))
                name=page.get("title","").lower()
                if not name.endswith((".jpg",".jpeg",".png",".webp")):
                    continue
                desc=re.sub("<[^>]+>"," ",meta.get("ImageDescription",{}).get("value","")).lower()
                if any(bad in name+" "+desc for bad in forbidden):
                    continue
                context=name+" "+desc
                if not any(term in context for term in relevant):
                    continue
                if any(term in context for term in irrelevant):
                    continue
                if any(bad in name+" "+desc for bad in ("daytime","daylight","sunny day","broad daylight","morning","midday","noon")):
                    continue
                if not (license_name.startswith("CC BY") or license_name in ("CC0","Public domain")):
                    continue
                if info.get("width",0)<1000 or info.get("height",0)<700:
                    continue
                # Prefer landscape/portrait street photos, never panoramic aerials.
                if info.get("width",1)/max(1,info.get("height",1))>2.3:
                    continue
                url=info.get("thumburl") or info.get("url")
                if not url or not url.lower().split("?")[0].endswith((".jpg",".jpeg",".png",".webp")):
                    continue
                if info.get("sha1") in seen_hashes:
                    continue
                candidates.append((page,info,license_name,url))
            for page,info,license_name,url in candidates:
                try:
                    req=urllib.request.Request(url,headers={"User-Agent":"ViceCityIntelShorts/1.0"})
                    with urllib.request.urlopen(req,timeout=20) as response:
                        data=response.read(9_000_000)
                    photo=Image.open(BytesIO(data)).convert("RGB")
                    if photo.width<650 or photo.height<400:
                        continue
                    fp=fingerprint(photo)
                    if any(sum(a!=b for a,b in zip(fp,prev))<32 for prev in seen_pixels):
                        continue
                    target=directory/f"photo_{len(credits):02}.jpg"
                    photo.save(target,quality=92)
                    seen_pixels.append(fp)
                    seen_hashes.add(info.get("sha1"))
                    artist=html.unescape(re.sub("<[^>]+>","",info.get("extmetadata",{}).get("Artist",{}).get("value","Unknown")))
                    credits.append(f"{target.name}: {page.get('title')} | {artist} | {license_name} | {info.get('descriptionurl','')}")
                    if len(credits)>=6:
                        break
                except Exception as error:
                    print("Skipped candidate:",type(error).__name__)
        except Exception as error:
            print("Commons search unavailable:",term,type(error).__name__,str(error)[:100])
    if credits:
        credit_text="\n".join(credits)+"\n"
        (OUT/"IMAGE_CREDITS.txt").write_text(credit_text,encoding="utf-8")
        if len(credits)>=2:
            manifest.write_text(credit_text,encoding="utf-8")
    return sorted(directory.glob("photo_*.jpg"))

# Extract six representative frames from creator-owned or explicitly licensed gameplay.
# Place a single authorized MP4 in assets/gameplay.mp4. Never scrape third-party videos.
gameplay_file=ROOT/"assets"/"gameplay.mp4"
scene_times=[]
raw_scene_times=os.getenv("SCENE_TIMES","").strip()
if raw_scene_times:
    try:
        scene_times=[float(v.strip()) for v in raw_scene_times.split(",")]
    except ValueError as exc:
        raise RuntimeError("SCENE_TIMES must be comma-separated seconds") from exc
    if len(scene_times)!=6 or any(v<0 for v in scene_times):
        raise RuntimeError("SCENE_TIMES requires six nonnegative timestamps")

if gameplay_file.is_file():
    source_duration=float(subprocess.check_output([
        "ffprobe","-v","error","-show_entries","format=duration",
        "-of","default=noprint_wrappers=1:nokey=1",str(gameplay_file)
    ],text=True).strip())
    if source_duration<12:
        raise RuntimeError("Gameplay clip must be at least 12 seconds.")
    if scene_times and max(scene_times)>source_duration-2:
        raise RuntimeError("A selected scene timestamp exceeds the playable video duration")
    if scene_times and any(scene_times[i+1] <= scene_times[i] for i in range(5)):
        raise RuntimeError("SCENE_TIMES must be six strictly increasing timestamps")
    if os.getenv("MISSION_MODE","1")=="1" and not scene_times:
        raise RuntimeError("Mission guide requires six reviewed SCENE_TIMES. Automatic random excerpts can misrepresent mission steps.")
    for idx in range(6):
        position=scene_times[idx] if scene_times else source_duration*(idx+0.5)/6
        target=ROOT/"assets"/f"gameplay_frame_{idx:02}.jpg"
        subprocess.run(["ffmpeg","-y","-loglevel","error","-ss",f"{position:.2f}",
            "-i",str(gameplay_file),"-frames:v","1","-q:v","2",str(target)],check=True)
assets=([ROOT/"assets"/f"gameplay_frame_{idx:02}.jpg" for idx in range(6)] if gameplay_file.is_file() else sorted([p for p in (ROOT/"assets").glob("*") if p.suffix.lower() in (".png",".jpg",".jpeg",".webp")]) if (ROOT/"assets").exists() else [])
# Mission guides must show actual relevant footage or deliberately selected screenshots.
# Do not silently substitute unrelated Miami photography.
mission_mode=os.getenv("MISSION_MODE","0")=="1"
if not assets and mission_mode:
    raise RuntimeError(
        "MISSION ASSETS REQUIRED: Add 4-6 relevant, rights-cleared mission screenshots "
        "to assets/ before building. Generic Miami stock images are not valid mission guidance. "
        "Also verify mission name and steps against gameplay before publishing."
    )
if not assets:
    assets=fetch_licensed_city_photos()
    if len(assets)<2:
        raise RuntimeError(
            "PHOTO ASSETS NEEDED: Fewer than two distinct licensed, topic-matched "
            "photographs were available. Add approved photos to assets/."
        )
    if len(assets)<6:
        print(f"Using {len(assets)} verified photos with different motion scenes.")

# Reject duplicate images even when manually supplied in assets/.
# A simple pixel signature also catches byte-identical images in different formats.
seen_visuals=set()
for visual in assets[:6]:
    with Image.open(visual) as probe:
        signature=tuple(probe.convert("RGB").resize((24,24)).tobytes())
    if signature in seen_visuals:
        raise RuntimeError("Duplicate image detected: "+str(visual))
    seen_visuals.add(signature)
if len(assets)<2:
    raise RuntimeError("At least two distinct visual sources are required.")
sentences=[s.strip() for s in re.split(r"(?<=[.!?])\s+",script) if s.strip()]
n=6
if not gameplay_file.is_file() and len(assets)<6:
    assets=[assets[i%len(assets)] for i in range(6)]
scene_duration=(duration+0.35*(n-1))/n
for i in range(n):
    if assets:
        im=Image.open(assets[i]).convert("RGB")
        sw,sh=im.size
        if gameplay_file.is_file():
            # Storyboard must show the same full-frame composition as the MP4.
            background=im.resize((W,H),Image.Resampling.LANCZOS).filter(ImageFilter.GaussianBlur(24))
            scale=min(W/sw,H/sh)
            foreground=im.resize((max(1,round(sw*scale)),max(1,round(sh*scale))),Image.Resampling.LANCZOS)
            background.paste(foreground,((W-foreground.width)//2,(H-foreground.height)//2))
            im=background
        else:
            scale=max(W/sw,H/sh)
            im=im.resize((math.ceil(sw*scale),math.ceil(sh*scale)),Image.Resampling.LANCZOS)
            x=(im.width-W)//2;y=(im.height-H)//2
            im=im.crop((x,y,x+W,y+H))
    else:
        raise RuntimeError("Missing visual assets")
    im.save(OUT/f"scene_{i:02}.png")

# A visual review sheet helps catch mismatched or duplicate mission moments.
preview_w,preview_h=240,426
sheet=Image.new("RGB",(preview_w*3,preview_h*2),(8,8,25))
for idx in range(n):
    with Image.open(OUT/f"scene_{idx:02}.png") as source:
        tile=source.convert("RGB").resize((preview_w,preview_h),Image.Resampling.LANCZOS)
        sheet.paste(tile,((idx%3)*preview_w,(idx//3)*preview_h))
    d=ImageDraw.Draw(sheet)
    d.rectangle(((idx%3)*preview_w,(idx//3)*preview_h,(idx%3)*preview_w+95,(idx//3)*preview_h+30),fill=(10,10,35))
    d.text(((idx%3)*preview_w+8,(idx//3)*preview_h+4),f"SCENE {idx+1}",fill="white")
sheet.save(OUT/"scene_review.jpg",quality=90)

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
Style: Captions,DejaVu Sans,39,&H00FFFFFF,&H000000FF,&H004B1545,&H950A0622,1,0,0,0,100,100,0,0,1,3,1,2,55,55,270,1
Style: Brand,DejaVu Sans,31,&H00FFE829,&H000000FF,&H00300B25,&H00000000,1,0,0,0,100,100,0,0,1,2,0,8,30,30,70,1
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
"""
with ass.open("w",encoding="utf-8") as f:
    f.write(header)
    f.write(f"Dialogue: 0,{stamp(0)},{stamp(duration)},Brand,,0,0,0,,VICE CITY INTEL\n")
    if word_events:
        # Use actual word timestamps from synthesis, not estimates.
        for j in range(0,len(word_events),4):
            group=word_events[j:j+4]
            start=group[0][0]
            end=word_events[j+4][0] if j+4<len(word_events) else duration
            # Break only between words; keep captions within 2 lines and safe margins.
            words=[w[2].upper().replace("{","").replace("}","") for w in group]
            rows=[]
            line=""
            for word in words:
                test=(line+" "+word).strip()
                if len(test)>17 and line:
                    rows.append(line)
                    line=word
                else:
                    line=test
            if line:
                rows.append(line)
            caption=r"\N".join(rows)
            f.write(f"Dialogue: 1,{stamp(start)},{stamp(end)},Captions,,0,0,0,,{caption}\n")
    else:
        # Provider sometimes omits WordBoundary events. Never truncate text.
        # Split the complete narration into short, word-safe captions.
        tokens=script.split()
        groups=[tokens[i:i+3] for i in range(0,len(tokens),3)]
        total=sum(len(g) for g in groups)
        cursor=0.0
        for group in groups:
            span=duration*len(group)/total
            text=" ".join(group).upper().replace("{","").replace("}","")
            rows=[]
            row=""
            for word in text.split():
                candidate=(row+" "+word).strip()
                if len(candidate)>17 and row:
                    rows.append(row)
                    row=word
                else:
                    row=candidate
            if row:
                rows.append(row)
            caption=r"\N".join(rows)
            f.write(f"Dialogue: 1,{stamp(cursor)},{stamp(cursor+span)},Captions,,0,0,0,,{caption}\n")
            cursor+=span

# Each scene is gently zoomed; transitions are short crossfades.
cmd=["ffmpeg","-y","-loglevel","error"]
for i in range(n):
    if gameplay_file.is_file():
        excerpt=scene_times[i] if scene_times else source_duration*(i+0.25)/n
        if excerpt+scene_duration+0.35>source_duration:
            raise RuntimeError(f"Scene {i+1} starts too late for its narration; choose an earlier timestamp")
        cmd+=["-ss",f"{excerpt:.3f}","-t",str(scene_duration+0.5),"-i",str(gameplay_file)]
    else:
        cmd+=["-loop","1","-framerate","30","-t",str(scene_duration+.4),"-i",str(OUT/f"scene_{i:02}.png")]
cmd+=["-i",str(OUT/"voice.mp3")]
filters=[]
for i in range(n):
    if gameplay_file.is_file():
        filters.append(f"[{i}:v]fps=30,split=2[bg{i}][fg{i}]")
        filters.append(f"[bg{i}]scale=720:1280:force_original_aspect_ratio=increase,crop=720:1280,boxblur=20:2[blur{i}]")
        filters.append(f"[fg{i}]scale=720:1280:force_original_aspect_ratio=decrease,setsar=1[front{i}]")
        filters.append(f"[blur{i}][front{i}]overlay=(W-w)/2:(H-h)/2:shortest=1,trim=duration={scene_duration+.35:.3f},setpts=PTS-STARTPTS,format=yuv420p[v{i}]")
    else:
        filters.append(f"[{i}:v]scale=900:1600,crop=720:1280:x='90+65*sin(n/85+{i}*1.3)':y='160+95*cos(n/105+{i}*0.9)',setsar=1,trim=duration={scene_duration+.35:.3f},setpts=PTS-STARTPTS,format=yuv420p[v{i}]")
last="v0"
for i in range(1,n):
    nextname=f"xf{i}"
    filters.append(f"[{last}][v{i}]xfade=transition=fade:duration=0.35:offset={(scene_duration-.35)*i:.3f}[{nextname}]")
    last=nextname
filters.append(f"[{last}]ass={ass.as_posix()},drawbox=x=0:y=0:w=720:h=8:color=0xff39be:t=fill,drawbox=x=0:y=1272:w=720:h=8:color=0x23e6ff:t=fill,scale=1080:1920:flags=lanczos,format=yuv420p[vout]")
cmd+=["-filter_complex",";".join(filters),"-map","[vout]","-map",f"{n}:a:0","-t",str(duration),"-c:v","libx264","-preset","veryfast","-crf","21","-r","30","-c:a","aac","-b:a","160k","-movflags","+faststart",str(OUT/"vice_city_intel.mp4")]
subprocess.run(cmd,check=True)
credit=os.getenv("GAMEPLAY_CREDIT","").strip()
credit_line=f"Gameplay: {credit}\n" if credit else ""
description=f"{topic} 🎮 #Shorts\n\n{script}\n\n{credit_line}Visuals are illustrative, not gameplay footage.\n#GTA6 #ViceCityIntel #GamingTips #Shorts\n"
(OUT/"youtube.txt").write_text(description,encoding="utf-8")
actual_dimensions=subprocess.check_output(["ffprobe","-v","error","-select_streams","v:0","-show_entries","stream=width,height","-of","csv=p=0",str(OUT/"vice_city_intel.mp4")],text=True).strip()
if actual_dimensions!="1080,1920":
    raise RuntimeError("Unexpected final MP4 resolution: "+actual_dimensions)
print("Created",OUT/"vice_city_intel.mp4",f"duration={duration:.1f}s",f"words={len(word_events)}",f"images={len(assets)}")
