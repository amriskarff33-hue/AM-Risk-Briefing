"""TTS: edge-tts (free, no key) default. Piper local = offline upgrade. Coqui XTTS avoided (non-commercial)."""
from __future__ import annotations
import asyncio, os, shutil, subprocess

async def _edge(text, voice, mp3):
    import edge_tts
    await edge_tts.Communicate(text, voice).save(mp3)

def synth(text, out_wav, voice="en-ZA-LeahNeural"):
    out_wav = str(out_wav)
    mp3 = out_wav + ".mp3"
    try:
        asyncio.run(_edge(text, voice, mp3))
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", mp3, "-ar", "22050", "-ac", "1", out_wav],
                       check=True)
        return out_wav
    except Exception as e:
        print(f"[voice] edge-tts unavailable ({e}); trying macOS say")
    # macOS offline fallback — real spoken voice, no key needed
    try:
        aiff = out_wav + ".aiff"
        subprocess.run(["say", "-v", "Daniel", "-o", aiff, text[:4000]],
                       check=True, timeout=300)
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", aiff, "-ar", "22050", "-ac", "1", out_wav],
                       check=True)
        return out_wav
    except Exception as e:
        # last resort: silent-track so video still builds
        print(f"[voice] say unavailable ({e}); writing silent placeholder")
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "lavfi",
                        "-i", "anullsrc=r=22050:cl=mono", "-t", str(max(8, len(text) // 14)),
                        out_wav], check=True)
        return out_wav

def duration(path):
    r = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                        "-of", "default=nw=1:nk=1", str(path)], capture_output=True, text=True)
    try:
        return float(r.stdout.strip())
    except Exception:
        return 20.0
