# AM Risk Daily Briefing — Production Stack
**Built by IAM-ASI**

Multi-tenant daily aviation risk briefing platform. RSS → AI brief → synthetic presenter video → Telegram / WhatsApp / Email.

## Architecture

```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐
│  React Web  │────▶│  FastAPI     │────▶│  PostgreSQL │
│  (nginx)    │     │  (API)       │     │             │
└─────────────┘     └──────┬───────┘     └─────────────┘
                           │
                    ┌──────▼───────┐
                    │    Redis     │
                    │  (queue)     │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐     ┌─────────────┐
                    │Celery Worker │────▶│  GPU Server │
                    │(pipeline)    │     │(LivePortrait│
                    └──────────────┘     │/MuseTalk)   │
                                         └─────────────┘
```

## Quick Start (Docker)

```bash
cp .env.production .env
# edit .env — set DB_PASSWORD, SECRET_KEY, channel keys
docker compose up -d
# API: http://localhost:8000  (docs at /docs)
# Web: http://localhost:3000
# Default login: admin@amrisk.local / admin123  (change immediately)
```

## Production Checklist

- [ ] Change `SECRET_KEY` to `openssl rand -hex 32`
- [ ] Change `DB_PASSWORD`
- [ ] Change default admin password (first login → DB update)
- [ ] Set `SENTRY_DSN` for error tracking
- [ ] Configure at least one Telegram channel + Email
- [ ] WhatsApp: set `WHATSAPP_PROVIDER=twilio` or pair Green-API sender
- [ ] `APPROVAL_REQUIRED=true` — human approves every brief before send
- [ ] `GPU_ENABLED=true` on GPU worker for LivePortrait/MuseTalk lip-sync
- [ ] Backup: `pg_dump` + `data/` volume
- [ ] Reverse proxy (Caddy/Traefik) with TLS in front of web + api

## Multi-Tenancy

Each `Organization` has its own:
- Branding (name, colors, voice, logo)
- Users (admin/editor/viewer roles)
- Briefs, channels, feed sources
- Delivery history

All queries are scoped by `org_id`. Users only see their org's data.

## Approval Workflow

```
draft → pending_review → approved → published
                  ↘ rejected
```

- **Editor**: creates brief, edits script, submits for review
- **Admin**: approves/rejects, publishes to channels
- **Viewer**: read-only dashboard

## GPU Avatar (Tier 2)

Worker container requests 1 NVIDIA GPU. When `GPU_ENABLED=true`:

1. `pipeline/gpu_avatar.py` loads LivePortrait + MuseTalk models from `GPU_MODEL_PATH`
2. `make_talking_head(portrait, audio, out)` replaces Tier-1 Ken-Burns
3. Output format identical — no distribution changes

Model setup (first run):
```bash
# on GPU host
git clone https://github.com/KlingAIResearch/LivePortrait
# follow their install; symlink models into ./models
```

## API Overview

| Endpoint | Method | Role | Description |
|---|---|---|---|
| `/auth/login` | POST | — | Get JWT |
| `/auth/me` | GET | any | Current user |
| `/briefs` | GET | any | List briefs |
| `/briefs` | POST | editor+ | Create brief |
| `/briefs/{id}` | GET | any | Brief detail |
| `/briefs/{id}` | PATCH | editor+ | Update script/status |
| `/briefs/{id}/generate` | POST | editor+ | Queue video generation |
| `/briefs/{id}/approve` | POST | admin | Approve |
| `/briefs/{id}/reject` | POST | admin | Reject |
| `/briefs/{id}/publish` | POST | admin | Send to channels |
| `/channels/channels` | GET/POST | any/admin | Manage channels |
| `/channels/feeds` | GET/POST | any/editor+ | Manage RSS feeds |
| `/health` | GET | — | Health check |

## Scheduled Daily Brief

Celery Beat runs `daily_brief_task` at `DAILY_CRON_HOUR:MINUTE` UTC.
Creates a brief for every org and queues generation. Briefs land in
`pending_review` — an admin approves and publishes.

## File Map

```
api/            FastAPI app (models, auth, routers)
worker/         Celery tasks (generate, distribute, daily)
pipeline/       Ingest → summarize → voice → assemble → distribute
web/            React + Vite dashboard
config/         Default feeds + branding
data/           Runtime output (videos, audio, frames)
models/         GPU model weights (LivePortrait/MuseTalk)
```
