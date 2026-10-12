"""FFmpeg assemble WITHOUT text filters (this FFmpeg has no libass/drawtext).
All branding + captions are burned with PIL, then encoded as PNG sequence.
Works on any stock macOS FFmpeg build."""
from __future__ import annotations
import subprocess
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
from .avatar_new import presenter_card as presenter_card_new

def presenter_card(*a, **k):
    return presenter_card_new(*a, **k, headline=k.pop("headline", None))
from .voice import duration

W, H, FPS = 1280, 720, 12

def _font(size):
    for p in ("/System/Library/Fonts/Helvetica.ttc",
              "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
              "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"):
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            continue
    return ImageFont.load_default()

def write_srt(script, path, total):
    words = script.split()
    n = max(1, len(words) // 7)
    per = total / n
    with open(path, "w") as f:
        for i in range(n):
            chunk = " ".join(words[i*7:(i+1)*7])
            f.write(f"{i+1}\n00:00:{int(i*per)//60:02d}:{int(i*per)%60:02d},000 --> "
                    f"00:00:{int((i+1)*per)//60:02d}:{int((i+1)*per)%60:02d},000\n{chunk}\n\n")
    return [" ".join(words[i*7:(i+1)*7]) for i in range(n)]

def _frame(base, caption, brand, by, zoom):
    # Ken-Burns: crop center by zoom then resize back
    z = 1.0 + zoom
    cw, ch = int(W / z), int(H / z)
    x, y = (base.width - cw)//2, (base.height - ch)//2
    fr = base.crop((x, y, x+cw, y+ch)).resize((W, H), Image.BILINEAR)
    d = ImageDraw.Draw(fr, "RGBA")
    d.rectangle([0, H-150, W, H], fill=(0, 0, 0, 160))
    d.rectangle([0, H-150, W, H-146], fill=(245, 197, 24, 255))
    d.text((40, H-132), brand + " DAILY BRIEF", font=_font(30), fill=(245, 197, 24, 255))
    d.text((W-330, H-128), by, font=_font(22), fill=(255, 255, 255, 255))
    # caption wrapped to 2 lines
    words, lines, cur = caption.split(), [], ""
    for w in words:
        if len(cur) + len(w) + 1 > 64:
            lines.append(cur); cur = w
        else:
            cur = (cur + " " + w).strip()
    lines.append(cur)
    for i, ln in enumerate(lines[:2]):
        d.text((40, H-92 + i*34), ln, font=_font(28), fill=(255, 255, 255, 255))
    return fr

def build_video(script, audio, outdir, brand="AM RISK", by="Built by IAM-ASI"):
    outdir = Path(outdir); outdir.mkdir(parents=True, exist_ok=True)
    headline = None
    try:
        if script:
            headline = script.splitlines()[0][:100]
    except Exception:
        pass
    card = Image.open(presenter_card(outdir / "presenter.png", brand=brand, by=by, headline=headline)).convert("RGB")
    dur = duration(audio) if Path(audio).exists() else 20.0
    dur = max(8.0, min(dur, 120.0))
    srt = outdir / "captions.srt"
    caps = write_srt(script, srt, dur)
    frames = outdir / "frames"; frames.mkdir(exist_ok=True)
    total = int(dur * FPS)
    per_cap = total / max(1, len(caps))
    for i in range(total):
        cap = caps[min(len(caps)-1, int(i // per_cap))]
        _frame(card, cap, brand, by, 0.08 * i / total).save(frames / f"f{i:05d}.png")
        if i % 240 == 0:
            print(f"[assemble] frame {i}/{total}")
    v16 = outdir / "briefing-16x9.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(FPS),
                    "-i", str(frames / "f%05d.png"), "-i", str(audio),
                    "-t", str(dur), "-c:v", "libx264", "-pix_fmt", "yuv420p",
                    "-c:a", "aac", "-shortest", str(v16)], check=True)
    v9 = outdir / "briefing-9x16.mp4"
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(v16),
                    "-vf", "crop=720:720:(in_w-720)/2:(in_h-720)/2,scale=720:1280:flags=lanczos,"
                           "crop=720:1280:0:0",
                    "-c:a", "copy", str(v9)], check=True)
    return {"16x9": str(v16), "9x16": str(v9), "srt": str(srt), "duration": dur}
