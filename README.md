# AM Risk Daily Briefing + Video Generator
**Built by IAM-ASI**

Daily aviation-safety / ARFF / risk feeds → synthetic presenter video → Telegram groups + WhatsApp groups + Email.

Open-source stack (commercial-safe licenses only):

| Stage | Pick | GitHub inspiration | Why |
|---|---|---|---|
| Ingest | `feedparser` RSS + GDELT | `giftedunicorn/ai-news-bot`, `viochris/daily-ai-news-digest`, `yktsnet/tg-dev-digest` | No scraping paywalls, RSS-first, dedup by hash |
| Summarize | Extractive fallback, optional Groq/Claude/DeepSeek | `money-printer-pro` (Groq Llama3) | Runs with zero API key today, upgrades with key |
| TTS | `edge-tts` default, `Piper` (MIT) local fallback | `rhasspy/piper`, `money-printer-pro` (Kokoro) | Avoid Coqui XTTS-v2 (non-commercial license) |
| Avatar SYN (presenter) | Tier1 CPU: Ken-Burns portrait + waveform (today). Tier2 GPU: LivePortrait + MuseTalk/Wav2Lip drop-in | `KlingAIResearch/LivePortrait` 19k★, `OpenTalker/SadTalker`, `numz/sd-wav2lip-uhq`, `antgroup/echomimic_v2` | SadTalker needs CUDA; Tier1 ships on Mac CPU |
| Avatar B (trainer) | Rig-style card render via PIL, reuses `signals.js` messaging | existing `rig.js` | On-brand, authoritative for procedures |
| Assemble | FFmpeg 9, 16:9 + 9:16, burned captions, bumper/outro | `ahmadhozien/money-printer-pro`, `kharkilirov1/Ytpipe` (Remotion) | No cloud render bill |
| Distribute | Telegram Bot API, WhatsApp via Twilio/Green-API, Email SMTP/Resend | `ArthurSekhian/news-digest-agent` | Telegram = groups first-class; WhatsApp groups need provider |

## Quick start

```sh
cd "am-risk-generator"
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # fill TELEGRAM_* etc (optional for dry-run)
python3 -m pipeline.daily --dry-run        # ingest + script + preview, no sends
python3 -m pipeline.daily --with-audio --with-video   # needs network (edge-tts) + ffmpeg
```

Outputs go to `out/YYYY-MM-DD/`:
- `briefing.json`, `script.txt`, `captions.srt`
- `briefing-16x9.mp4`, `briefing-9x16.mp4` (synthetic presenter)
- `email.html`, `telegram.txt`, `whatsapp.txt`
- `send-log.json` (dry-run safe)

## Daily automation

```sh
# cron 06:00 SAST daily
0 6 * * * cd /path/am-risk-generator && .venv/bin/python -m pipeline.daily --with-audio --with-video --send >> logs/cron.log 2>&1
```
Or GitHub Actions (see `.github/workflows/daily.yml` pattern from `ai-news-bot`).

## WhatsApp groups — honest note

- Telegram groups: native, 1 bot token, works today.
- WhatsApp groups: no free official group API. Supported paths in `distribute.py`:
  1. Twilio WhatsApp (official, best for 1:1 + broadcast lists, limited groups)
  2. Green-API / Whapi / Baileys (`whatsapp-web.js`) for true group post — needs a paired number, self-host.
- Default: Telegram + Email live day 1, WhatsApp via provider key when you add it. Queue file ensures no brief is lost.

## Upgrade to GPU lip-sync later

`pipeline/avatar.py` exposes `make_talking_head(portrait, audio, out)` — point it at LivePortrait + MuseTalk when you have CUDA. Tier1 video layout stays identical so Telegram/WhatsApp consumers see no break.
