from __future__ import annotations
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageOps, ImageFilter
import math
import random

NAVY_DEEP = "#070a11"
NAVY = "#0A1628"
NAVY_MID = "#122244"
YELLOW = "#d6ff3d"
WHITE = "#FFFFFF"
BLUE = "#4fd6ff"

def _font(size):
    for p in (
        "/System/Library/Fonts/Supplemental/HelveticaNeue-Bold.otf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
    ):
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            pass
    return ImageFont.load_default()

def _grid(img):
    base = Image.new("RGB", img.size, NAVY_DEEP)
    g = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(g)
    sx = img.width // 40
    sy = img.height // 40
    for i in range(0, img.width, sx):
        alpha = 24 if i % (sx * 4) == 0 else 10
        d.line([(i, 0), (i, img.height)], fill=(255, 255, 255, alpha), width=1)
    for i in range(0, img.height, sy):
        alpha = 24 if i % (sy * 4) == 0 else 10
        d.line([(0, i), (img.width, i)], fill=(255, 255, 255, alpha), width=1)
    d.polygon([(img.width * 0.55, 0), (img.width, 0), (img.width, img.height * 0.45)], fill=(255, 255, 255, 18))
    d.polygon([(0, img.height * 0.65), (img.width * 0.35, img.height), (0, img.height)], fill=(95, 140, 255, 14))
    if g.mode != "RGBA": g = g.convert("RGBA")
    base = base.convert("RGBA")
    return Image.alpha_composite(base, g).convert("RGB")

def _logo(icon_path):
    try:
        lg = Image.open(icon_path).convert("RGBA").resize((72, 72), Image.LANCZOS)
        return lg
    except Exception:
        return None

def _heading_bg(w):
    g = Image.new("RGBA", (w, 68), (0, 0, 0, 0))
    d = ImageDraw.Draw(g)
    d.rectangle([0, 0, w, 68], fill=(10, 22, 40, 220))
    d.rectangle([0, 0, 6, 68], fill=YELLOW)
    d.rectangle([0, 64, w, 68], fill=(245, 197, 24, 255))
    return g

def presenter_card(path, brand="AM RISK", sub="DAILY AVIATION RISK BRIEFING", by="Built by IAM-ASI", size=(1280, 720), headline=None, date="12-10-2026"):
    base = _grid(Image.new("RGB", size, NAVY_DEEP))
    draw = ImageDraw.Draw(base)
    icon = _logo(Path(__file__).resolve().parent.parent.parent / "icon.svg")
    if icon:
        base.paste(icon, (40, 20), icon)
    hb = _heading_bg(size[0])
    base.paste(hb, (0, 0), hb)
    draw.text((130, 14), brand, font=_font(40), fill=YELLOW)
    draw.text((130, 36), sub, font=_font(20), fill=WHITE)
    draw.text((size[0]-160, 22), date, font=_font(22), fill=WHITE)
    head_txt = headline or "Aviation safety update"
    wrap = head_txt[:80]
    if len(head_txt) > 80:
        wrap = head_txt[:77] + "..."
    hp = Image.new("RGBA", (520, 190), (0, 0, 0, 0))
    hd = ImageDraw.Draw(hp)
    hd.rectangle([0, 0, 520, 190], fill=(10, 22, 40, 232))
    hd.rounded_rectangle([0, 0, 6, 190], radius=0, fill=YELLOW)
    hd.text((28, 24), "TOP STORY", font=_font(16), fill=BLUE)
    for i, ln in enumerate([wrap[i:i+40] for i in range(0, len(wrap), 40)]):
        hd.text((28, 58 + i*30), ln, font=_font(24), fill=WHITE)
    hp = hp.filter(ImageFilter.GaussianBlur(0.5))
    base.paste(hp, (40, 240), hp)
    cx, cy = size[0] // 2 + 240, size[1] // 2 + 40
    for r, c, a in ((200, (20,40,70), 40), (170, (30,60,110), 60), (140, (45,80,150), 90)):
        glow = Image.new("RGBA", (r*2+20, r*2+20), (0,0,0,0))
        gd = ImageDraw.Draw(glow)
        gd.ellipse([10,10,r*2+10,r*2+10], fill=(c[0],c[1],c[2],a), outline=None)
        glow = glow.filter(ImageFilter.GaussianBlur(6))
        base.paste(glow, (cx-r-10, cy-r-10), glow)
    draw.ellipse([cx-70, cy-100, cx+70, cy+40], fill="#e6c89c")
    draw.arc([cx-70, cy-100, cx+70, cy+40], 20, 160, fill="#2a2118", width=16)
    draw.rectangle([cx-120, cy+40, cx+120, size[1]-40], fill=BLUE, width=0)
    draw.rectangle([cx-120, cy+40, cx+120, cy+60], fill=YELLOW)
    draw.rectangle([cx-120, cy+40, cx-114, size[1]-40], fill=YELLOW)
    draw.rectangle([cx+114, cy+40, cx+120, size[1]-40], fill=YELLOW)
    lt = Image.new("RGBA", (size[0], 80), (0,0,0,0))
    ldt = ImageDraw.Draw(lt)
    ldt.rectangle([0, 0, size[0], 80], fill=(0,0,0,190))
    ldt.rectangle([0, 0, size[0], 4], fill=YELLOW)
    ldt.text((40, 24), by, font=_font(20), fill=YELLOW)
    ldt.text((40, 46), "AVIATION SAFETY • ARFF • RISK INTELLIGENCE", font=_font(16), fill=WHITE)
    ldt.text((size[0]-340, 30), "AM RISK • BUILT BY IAM-ASI", font=_font(16), fill=WHITE)
    base.paste(lt, (0, size[1]-80), lt)
    base.save(path)
    return path
