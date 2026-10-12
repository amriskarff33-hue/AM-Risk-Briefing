"""Daily entrypoint: ingest -> brief -> audio -> video -> distribute."""
from __future__ import annotations
import argparse, json
from datetime import date
from pathlib import Path
from dotenv import load_dotenv

from .ingest import load_feeds, fetch
from .summarize import build_brief
from .voice import synth
from .assemble import build_video
from .distribute import distribute

ROOT = Path(__file__).resolve().parent.parent

def email_html(brief, brand="AM RISK", by="Built by IAM-ASI"):
    items = "".join(f"<li><b>{i['title']}</b><br><span style='color:#555'>{i['source']}</span> — "
                    f"<a href='{i['link']}'>source</a></li>" for i in brief["items"][:8])
    return f"""<div style="font-family:Arial;max-width:640px">
<div style="background:#0A1628;color:#F5C518;padding:16px 20px;font-size:22px;font-weight:bold">{brand} — Daily Brief</div>
<div style="padding:16px 20px;white-space:pre-wrap">{brief['story']}</div>
<h3>Sources</h3><ul>{items or '<li>No fresh items</li>'}</ul>
<p style="color:#666;font-size:12px">{brief['disclaimer']}<br>{by}</p></div>"""

def main():
    load_dotenv(ROOT / ".env")
    ap = argparse.ArgumentParser()
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--with-audio", action="store_true")
    ap.add_argument("--with-video", action="store_true")
    ap.add_argument("--send", action="store_true")
    a = ap.parse_args()

    outdir = ROOT / "out" / str(date.today())
    outdir.mkdir(parents=True, exist_ok=True)

    cfg = load_feeds(str(ROOT / "config" / "feeds.yaml"))
    items = fetch(cfg)
    (outdir / "items.json").write_text(json.dumps(items, indent=2))
    brief = build_brief(items)
    (outdir / "briefing.json").write_text(json.dumps({k: v for k, v in brief.items() if k != "items"}, indent=2))
    (outdir / "script.txt").write_text(brief["script"])
    print(f"[ingest] {len(items)} items, provider={brief['provider']}")

    audio = outdir / "voice.wav"
    videos = {}
    if a.with_audio or a.with_video:
        synth(brief["script"], audio)
        print(f"[voice] {audio}")
    if a.with_video:
        videos = build_video(brief["script"], audio, outdir)
        print(f"[video] {videos}")

    tg = f"✈️ AM RISK DAILY BRIEF\n\n{brief['story'][:3000]}\n\n— Built by IAM-ASI"
    wa = f"*AM RISK DAILY BRIEF*\n\n{brief['story'][:1200]}\n\n_Built by IAM-ASI_"
    (outdir / "telegram.txt").write_text(tg)
    (outdir / "whatsapp.txt").write_text(wa)
    (outdir / "email.html").write_text(email_html(brief))

    if a.send and not a.dry_run:
        log = distribute(outdir, brief, videos, (outdir / "email.html").read_text(), tg, wa)
        print("[send]", log)
    else:
        print(f"[dry-run] preview in {outdir} (pass --send to deliver)")

if __name__ == "__main__":
    main()
