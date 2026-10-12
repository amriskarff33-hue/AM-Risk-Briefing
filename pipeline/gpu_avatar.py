"""GPU avatar: LivePortrait + MuseTalk lip-sync pipeline.

Requires:
  - NVIDIA GPU with CUDA 11.8+
  - LivePortrait cloned to /app/models/LivePortrait
  - MuseTalk cloned to /app/models/MuseTalk
  - Python deps: torch, opencv-python, librosa, etc.

This module provides make_talking_head(portrait, audio, out) that
replaces the Tier-1 Ken-Burns renderer when GPU_ENABLED=true.
"""
from __future__ import annotations
import os, sys, subprocess, tempfile
from pathlib import Path
from api.config import get_settings

settings = get_settings()

LIVEPORTRAIT_DIR = Path(settings.GPU_MODEL_PATH) / "LivePortrait"
MUSETALK_DIR = Path(settings.GPU_MODEL_PATH) / "MuseTalk"

def _check_gpu():
    try:
        import torch
        if not torch.cuda.is_available():
            raise RuntimeError("CUDA not available")
        return torch.cuda.get_device_name(0)
    except ImportError:
        raise RuntimeError("PyTorch not installed on worker")

def _check_models():
    if not LIVEPORTRAIT_DIR.exists():
        raise RuntimeError(f"LivePortrait not found at {LIVEPORTRAIT_DIR}")
    if not MUSETALK_DIR.exists():
        raise RuntimeError(f"MuseTalk not found at {MUSETALK_DIR}")

def make_talking_head(portrait: str, audio: str, out: str, voice: str = "en-ZA-LeahNeural"):
    """Generate lip-synced talking head video.
    
    Args:
        portrait: Path to presenter portrait image (PNG/JPG)
        audio: Path to TTS audio (WAV)
        out: Output video path (MP4)
        voice: Voice identifier (for metadata)
    
    Returns:
        Path to output video
    """
    if not settings.GPU_ENABLED:
        raise RuntimeError("GPU_ENABLED=false — use Tier-1 renderer")
    
    gpu = _check_gpu()
    _check_models()
    
    out = Path(out)
    out.parent.mkdir(parents=True, exist_ok=True)
    
    # Step 1: LivePortrait — animate portrait from audio-driven landmarks
    # This uses the audio to generate facial landmarks, then reenacts the portrait
    lp_out = out.parent / "lp_animated.mp4"
    
    # Add LivePortrait to path
    sys.path.insert(0, str(LIVEPORTRAIT_DIR))
    
    try:
        from LivePortrait.src.live_portrait_pipeline import LivePortraitPipeline
        from LivePortrait.src.utils.io import load_image
        
        # Initialize pipeline
        pipeline = LivePortraitPipeline(
            checkpoint_dir=str(LIVEPORTRAIT_DIR / "checkpoints"),
            device="cuda",
        )
        
        # Load portrait
        source_image = load_image(portrait)
        
        # Generate audio-driven animation
        # LivePortrait uses audio2landmark to drive facial motion
        pipeline.render(
            source=source_image,
            audio=audio,
            output=str(lp_out),
            fps=25,
        )
    except Exception as e:
        raise RuntimeError(f"LivePortrait inference failed: {e}")
    
    # Step 2: MuseTalk — refine lip-sync quality
    mt_out = out.parent / "mt_refined.mp4"
    
    sys.path.insert(0, str(MUSETALK_DIR))
    try:
        from musetalk import MuseTalkPipeline
        
        mt_pipeline = MuseTalkPipeline(
            checkpoint_dir=str(MUSETALK_DIR / "checkpoints"),
            device="cuda",
        )
        mt_pipeline.refine(
            video=str(lp_out),
            audio=audio,
            output=str(mt_out),
        )
    except Exception as e:
        # MuseTalk is optional — fall back to LivePortrait output
        print(f"[gpu_avatar] MuseTalk refinement failed ({e}), using LivePortrait output")
        mt_out = lp_out
    
    # Step 3: Final encode with audio mux
    subprocess.run([
        "ffmpeg", "-y", "-loglevel", "error",
        "-i", str(mt_out), "-i", str(audio),
        "-c:v", "libx264", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-shortest",
        str(out),
    ], check=True)
    
    # Cleanup intermediates
    lp_out.unlink(missing_ok=True)
    if mt_out != lp_out:
        mt_out.unlink(missing_ok=True)
    
    return str(out)

def setup_models():
    """Clone + setup LivePortrait and MuseTalk. Run once on GPU host."""
    import subprocess
    
    model_dir = Path(settings.GPU_MODEL_PATH)
    model_dir.mkdir(parents=True, exist_ok=True)
    
    repos = [
        ("LivePortrait", "https://github.com/KlingAIResearch/LivePortrait.git"),
        ("MuseTalk", "https://github.com/TMElyralab/MuseTalk.git"),
    ]
    
    for name, url in repos:
        dest = model_dir / name
        if dest.exists():
            print(f"[setup] {name} already exists")
            continue
        print(f"[setup] Cloning {name}...")
        subprocess.run(["git", "clone", url, str(dest)], check=True)
    
    # Install deps
    for name, _ in repos:
        req = model_dir / name / "requirements.txt"
        if req.exists():
            print(f"[setup] Installing {name} deps...")
            subprocess.run([sys.executable, "-m", "pip", "install", "-r", str(req)], check=True)
    
    # Download checkpoints (follow each repo's instructions)
    print("[setup] Download model checkpoints:")
    print(f"  LivePortrait: see {LIVEPORTRAIT_DIR}/README.md")
    print(f"  MuseTalk: see {MUSETALK_DIR}/README.md")
    print("[setup] Done. Set GPU_ENABLED=true to use.")
