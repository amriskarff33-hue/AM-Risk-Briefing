"""Celery tasks: ingest -> brief -> video -> distribute. GPU avatar hook included."""
from __future__ import annotations
import os, json, shutil, subprocess
from pathlib import Path
from datetime import datetime
from sqlalchemy.orm import Session
from celery import shared_task
from api.config import get_settings
from api.db import SessionLocal
from api.models import Brief, BriefStatus, Channel, Delivery, DeliveryStatus, FeedSource, Organization, AuditLog
from pipeline.ingest import load_feeds, fetch
from pipeline.summarize import build_brief
from pipeline.voice import synth
from pipeline.assemble import build_video
from pipeline.distribute import distribute

settings = get_settings()
DATA = Path(settings.DATA_DIR)
DATA.mkdir(parents=True, exist_ok=True)

def _org_config(db: Session, org_id: int) -> dict:
    org = db.query(Organization).filter(Organization.id == org_id).first()
    if not org:
        return {}
    return {
        "brand": org.brand_name, "sub": org.brand_sub, "by": org.built_by,
        "voice": org.voice, "accent": org.accent_color, "primary": org.primary_color,
    }

def _feeds_for_org(db: Session, org_id: int) -> list:
    rows = db.query(FeedSource).filter(FeedSource.org_id == org_id, FeedSource.is_active == True).all()
    if not rows:
        cfg = load_feeds(str(Path(__file__).resolve().parent.parent / "config" / "feeds.yaml"))
        return cfg.get("feeds", [])
    return [r.url for r in rows]

@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def generate_brief_task(self, brief_id: int):
    db = SessionLocal()
    try:
        brief = db.query(Brief).filter(Brief.id == brief_id).first()
        if not brief:
            return {"error": "brief not found"}
        org = db.query(Organization).filter(Organization.id == brief.org_id).first()
        cfg = _org_config(db, brief.org_id)
        outdir = DATA / str(brief.org_id) / str(brief_id)
        outdir.mkdir(parents=True, exist_ok=True)

        # 1. ingest
        feeds = _feeds_for_org(db, brief.org_id)
        if feeds:
            items = fetch({"feeds": feeds, "keywords": ["ARFF", "runway", "ground", "safety", "ICAO"],
                           "lookback_hours": 30, "max_items": 12})
        else:
            items = []
        brief.items = items
        db.commit()

        # 2. brief
        result = build_brief(items)
        brief.story = result["story"]
        brief.script = result["script"]
        brief.provider = result["provider"]
        db.commit()

        # 3. voice
        audio = outdir / "voice.wav"
        synth(brief.script, audio, voice=cfg.get("voice", "en-ZA-LeahNeural"))
        brief.audio_path = str(audio)
        db.commit()

        # 4. video — GPU avatar if available, else Tier-1
        if settings.GPU_ENABLED:
            try:
                from pipeline.gpu_avatar import make_talking_head
                portrait = outdir / "presenter.png"
                from pipeline.avatar_new import presenter_card
                presenter_card(str(portrait), brand=cfg.get("brand", "AM RISK"),
                               by=cfg.get("by", "Built by IAM-ASI"),
                               headline=brief.script.split(".")[0] if brief.script else None)
                video_path = outdir / "briefing-gpu.mp4"
                make_talking_head(str(portrait), str(audio), str(video_path))
                # GPU output is 16:9; derive 9:16
                v9 = outdir / "briefing-9x16.mp4"
                subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(video_path),
                                "-vf", "crop=720:720:(in_w-720)/2:(in_h-720)/2,scale=720:1280:flags=lanczos",
                                "-c:a", "copy", str(v9)], check=True)
                brief.video_path_16 = str(video_path)
                brief.video_path_9 = str(v9)
                brief.duration = videos["duration"] if 'videos' in dir() else 0
                db.commit()
            except Exception as e:
                print(f"[worker] GPU avatar failed ({e}), falling back to Tier-1")
                brief.status = BriefStatus.failed
                db.commit()
                raise self.retry(exc=e)
        
        # Tier-1 fallback (or if GPU disabled)
        if not brief.video_path_16:
            videos = build_video(brief.script, audio, outdir,
                                 brand=cfg.get("brand", "AM RISK"), by=cfg.get("by", "Built by IAM-ASI"))
            brief.video_path_16 = videos["16x9"]
            brief.video_path_9 = videos["9x16"]
            brief.srt_path = videos["srt"]
            brief.duration = videos["duration"]
        
        brief.status = BriefStatus.pending_review
        db.commit()
        return {"status": "pending_review", "brief_id": brief_id}
    except Exception as exc:
        brief.status = BriefStatus.failed
        db.commit()
        raise self.retry(exc=exc)
    finally:
        db.close()

@shared_task(bind=True, max_retries=3, default_retry_delay=30)
def distribute_brief_task(self, brief_id: int):
    db = SessionLocal()
    try:
        brief = db.query(Brief).filter(Brief.id == brief_id).first()
        if not brief:
            return {"error": "brief not found"}
        channels = db.query(Channel).filter(Channel.org_id == brief.org_id, Channel.is_active == True).all()
        for ch in channels:
            d = Delivery(brief_id=brief.id, channel_id=ch.id, status=DeliveryStatus.queued)
            db.add(d)
            db.commit()
            db.refresh(d)
            try:
                if ch.type == "telegram":
                    from pipeline.distribute import telegram
                    telegram(ch.config.get("bot_token", os.getenv("TELEGRAM_BOT_TOKEN", "")),
                             ch.config.get("chat_ids", []), _tg_text(brief), brief.video_path_9)
                    d.status = DeliveryStatus.sent
                    d.sent_at = datetime.utcnow()
                elif ch.type == "email":
                    from pipeline.distribute import email_smtp, email_resend
                    if ch.config.get("mode") == "smtp":
                        email_smtp(ch.config.get("host"), ch.config.get("port", 587),
                                   ch.config.get("user"), ch.config.get("pass"),
                                   ch.config.get("from"), ch.config.get("to"),
                                   "AM Risk Daily Brief", _email_html(brief))
                    elif ch.config.get("mode") == "resend":
                        email_resend(ch.config.get("api_key"), ch.config.get("from"),
                                     ch.config.get("to"), "AM Risk Daily Brief", _email_html(brief))
                    d.status = DeliveryStatus.sent
                    d.sent_at = datetime.utcnow()
                elif ch.type == "whatsapp":
                    from pipeline.distribute import whatsapp_twilio
                    if ch.config.get("provider") == "twilio":
                        sid = whatsapp_twilio(ch.config.get("sid"), ch.config.get("token"),
                                              ch.config.get("from"), ch.config.get("to"),
                                              _wa_text(brief), brief.video_path_9)
                        d.external_id = sid
                        d.status = DeliveryStatus.sent
                        d.sent_at = datetime.utcnow()
                    else:
                        d.status = DeliveryStatus.failed
                        d.error = "WhatsApp groups need Green-API/Baileys sender — see README"
            except Exception as e:
                d.status = DeliveryStatus.failed
                d.error = str(e)[:500]
                d.attempts += 1
            db.commit()
        return {"status": "distributed", "brief_id": brief_id}
    except Exception as exc:
        raise self.retry(exc=exc)
    finally:
        db.close()

@shared_task
def daily_brief_task():
    """Create + generate a brief for every org. Runs via Celery Beat."""
    db = SessionLocal()
    try:
        orgs = db.query(Organization).all()
        for org in orgs:
            brief = Brief(org_id=org.id, title=f"Daily Brief {datetime.utcnow().strftime('%Y-%m-%d')}",
                         status=BriefStatus.draft, created_by=None)
            db.add(brief)
            db.commit()
            db.refresh(brief)
            generate_brief_task.delay(brief.id)
        return {"orgs": len(orgs)}
    finally:
        db.close()

def _tg_text(brief):
    return f"✈️ AM RISK DAILY BRIEF\n\n{brief.story[:3000]}\n\n— Built by IAM-ASI"

def _wa_text(brief):
    return f"*AM RISK DAILY BRIEF*\n\n{brief.story[:1200]}\n\n_Built by IAM-ASI_"

def _email_html(brief):
    items = "".join(f"<li><b>{i.get('title','')}</b><br><span style='color:#555'>{i.get('source','')}</span> — "
                    f"<a href='{i.get('link','')}'>source</a></li>" for i in (brief.items or [])[:8])
    return f"""<div style="font-family:Arial;max-width:640px">
<div style="background:#0A1628;color:#d6ff3d;padding:16px 20px;font-size:22px;font-weight:bold">AM RISK — Daily Brief</div>
<div style="padding:16px 20px;white-space:pre-wrap">{brief.story}</div>
<h3>Sources</h3><ul>{items or '<li>No fresh items</li>'}</ul>
<p style="color:#666;font-size:12px">Training aid only. Verify against ICAO Annex, AIP and operator manuals.<br>Built by IAM-ASI</p></div>"""
