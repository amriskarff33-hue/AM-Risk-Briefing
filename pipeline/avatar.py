"""Synthetic presenter (Tier 1 CPU, ships today) + GPU hook (Tier 2).

Tier 1: branded portrait card (PIL) with subtle Ken-Burns zoom + audio waveform bar.
Looks like a news presenter frame, runs on any Mac CPU.
Tier 2 hook: make_talking_head() — point at LivePortrait + MuseTalk/Wav2Lip when CUDA exists.
  - LivePortrait: https://github.com/KlingAIResearch/LivePortrait (19k stars)
  - MuseTalk/Wav2Lip-UHQ: real-time lip-sync
Layout is identical so distribution doesn't break on upgrade.
"""
from __future__ import annotations
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

NAVY, YELLOW, WHITE = "#0A1628", "#F5C518", "#FFFFFF"

def _font(size):
    for p in ("/System/Library/Fonts/Helvetica.ttc", "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"):
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            continue
    return ImageFont.load_default()

def presenter_card(path, brand="AM RISK", sub="Aviation Risk & Training", by="Built by IAM-ASI", size=(1280, 720)):
    img = Image.new("RGB", size, NAVY)
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, size[0], 90], fill="#060D1A")
    d.rectangle([0, 90, size[0], 96], fill=YELLOW)
    d.text((60, 22), brand, font=_font(44), fill=YELLOW)
    d.text((300, 34), sub, font=_font(24), fill=WHITE)
    # synthetic presenter silhouette: circle head + shoulders on gradient panel
    cx, cy = size[0] // 2, size[1] // 2 + 40
    for r, c in ((170, "#16294a"), (150, "#1E3A66"), (110, "#2B4E89")):
        d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=c)
    d.ellipse([cx - 62, cy - 92, cx + 62, cy + 32], fill="#D9B48F")          # head
    d.arc([cx - 62, cy - 92, cx + 62, cy + 32], 20, 160, fill="#3A2A1E", width=14)  # hair
    d.rectangle([cx - 110, cy + 60, cx + 110, size[1]], fill="#101F38")      # shoulders/uniform
    d.rectangle([cx - 110, cy + 60, cx + 110, cy + 78], fill=YELLOW)         # epaulette strip
    d.text((60, size[1] - 110), "ASI PRESENTER — SYNTHETIC", font=_font(28), fill=WHITE)
    d.text((60, size[1] - 70), by, font=_font(22), fill=YELLOW)
    d.text((size[0] - 420, size[1] - 70), "AM RISK • DAILY BRIEF", font=_font(20), fill="#8FA0BD")
    img.save(path)
    return path

def make_talking_head(portrait, audio, out):
    """GPU upgrade hook. Today: raise with instructions; Tier1 path used instead."""
    raise NotImplementedError(
        "Plug LivePortrait (portrait animation) + MuseTalk/Wav2Lip (lip-sync) here when CUDA is available. "
        "See README table. Tier-1 Ken-Burns video is used until then.")
