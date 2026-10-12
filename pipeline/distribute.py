"""Distribution: Telegram (live day 1) + Email (SMTP/Resend) + WhatsApp (provider).
All sends are dry-run safe: without keys we write queue files instead of failing."""
from __future__ import annotations
import json, os, smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path

def telegram(bot_token, chat_ids, text, video=None):
    import asyncio
    from telegram import Bot
    async def _go():
        async with Bot(bot_token) as b:
            for cid in chat_ids:
                if video and Path(video).exists():
                    await b.send_video(cid, open(video, "rb"), caption=text[:1000], supports_streaming=True)
                else:
                    await b.send_message(cid, text[:4000])
    asyncio.run(_go())

def email_smtp(host, port, user, pw, frm, to, subject, html):
    m = MIMEMultipart("alternative")
    m["From"], m["To"], m["Subject"] = frm, to, subject
    m.attach(MIMEText(html, "html"))
    with smtplib.SMTP(host, int(port)) as s:
        s.starttls(); s.login(user, pw); s.sendmail(frm, to.split(","), m.as_string())

def email_resend(key, frm, to, subject, html):
    import resend
    resend.api_key = key
    resend.Emails.send({"from": frm, "to": to.split(","), "subject": subject, "html": html})

def whatsapp_twilio(sid, token, frm, to, body, media=None):
    from twilio.rest import Client
    c = Client(sid, token)
    kwargs = {"from_": frm, "to": to, "body": body[:1500]}
    if media:
        kwargs["media_url"] = [media]
    return c.messages.create(**kwargs).sid

def distribute(outdir, brief, videos, email_html, tg_text, wa_text):
    outdir = Path(outdir)
    log = {"telegram": "skipped", "email": "skipped", "whatsapp": "skipped"}
    # Telegram
    tok = os.getenv("TELEGRAM_BOT_TOKEN")
    chats = [c.strip() for c in os.getenv("TELEGRAM_CHAT_IDS", "").split(",") if c.strip()]
    if tok and chats:
        try:
            telegram(tok, chats, tg_text, videos.get("9x16"))
            log["telegram"] = f"sent to {len(chats)} chat(s)"
        except Exception as e:
            log["telegram"] = f"error: {e}"
            (outdir / "telegram_retry.txt").write_text(tg_text)
    else:
        (outdir / "telegram.txt").write_text(tg_text)
        log["telegram"] = "queued (no token)"
    # Email
    mode = os.getenv("EMAIL_MODE", "none")
    try:
        if mode == "smtp" and os.getenv("SMTP_HOST"):
            email_smtp(os.getenv("SMTP_HOST"), os.getenv("SMTP_PORT", 587), os.getenv("SMTP_USER"),
                       os.getenv("SMTP_PASS"), os.getenv("EMAIL_FROM"), os.getenv("EMAIL_TO"),
                       "AM Risk Daily Brief", email_html)
            log["email"] = "sent via smtp"
        elif mode == "resend" and os.getenv("RESEND_API_KEY"):
            email_resend(os.getenv("RESEND_API_KEY"), os.getenv("EMAIL_FROM"), os.getenv("EMAIL_TO"),
                         "AM Risk Daily Brief", email_html)
            log["email"] = "sent via resend"
        else:
            (outdir / "email.html").write_text(email_html)
            log["email"] = "queued (no smtp)"
    except Exception as e:
        log["email"] = f"error: {e}"
    # WhatsApp
    prov = os.getenv("WHATSAPP_PROVIDER", "none")
    try:
        if prov == "twilio" and os.getenv("TWILIO_SID"):
            sid = whatsapp_twilio(os.getenv("TWILIO_SID"), os.getenv("TWILIO_TOKEN"),
                                  os.getenv("TWILIO_WHATSAPP_FROM"), os.getenv("WHATSAPP_TO"), wa_text)
            log["whatsapp"] = f"sent via twilio {sid}"
        else:
            (outdir / "whatsapp.txt").write_text(
                wa_text + "\n\n[Attach: briefing-9x16.mp4 — post to group via Green-API/Baileys number, see README]")
            log["whatsapp"] = "queued (pair a Green-API/Baileys sender for groups)"
    except Exception as e:
        log["whatsapp"] = f"error: {e}"
    (outdir / "send-log.json").write_text(json.dumps(log, indent=2))
    return log
