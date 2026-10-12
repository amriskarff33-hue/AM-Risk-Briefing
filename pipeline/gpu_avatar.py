"""GPU avatar: LivePortrait + MuseTalk lip-sync. Drop-in replacement for Tier-1 Ken-Burns."""
from __future__ import annotations
import os, subprocess
from pathlib import Path
from api.config import get_settings

settings = get_settings()

def make_talking_head(portrait: str, audio: str, out: str):
    """Generate lip-synced talking head from portrait image + TTS audio.
    
    Requires: LivePortrait + MuseTalk installed on GPU host.
    Models expected at GPU_MODEL_PATH (default /app/models).
    """
    if not settings.GPU_ENABLED:
        raise RuntimeError("GPU_ENABLED=false — use Tier-1 renderer")
    
    model_dir = Path(settings.GPU_MODEL_PATH)
    if not model_dir.exists():
        raise RuntimeError(f"Model dir {model_dir} not found — clone LivePortrait + MuseTalk")
    
    # TODO: implement LivePortrait inference + MuseTalk lip-sync
    # For now, fall back to Tier-1 by raising — worker catches and uses Ken-Burns
    raise NotImplementedError(
        "GPU avatar not yet wired. Set GPU_ENABLED=false for Tier-1, "
        "or implement LivePortrait+MuseTalk inference in pipeline/gpu_avatar.py"
    )
