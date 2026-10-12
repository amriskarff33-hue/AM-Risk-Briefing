from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
import sentry_sdk
from .config import get_settings
from .db import engine, Base, get_db
from .models import User, UserRole, Organization, Brief, BriefStatus, Channel, Delivery, DeliveryStatus, FeedSource, AuditLog
from .routers import auth, briefs, channels

settings = get_settings()

if settings.SENTRY_DSN:
    sentry_sdk.init(dsn=settings.SENTRY_DSN, traces_sample_rate=0.1)

app = FastAPI(title="AM Risk Briefing API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(briefs.router)
app.include_router(channels.router)

@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    # seed default org + admin if empty
    db = next(get_db())
    if not db.query(Organization).first():
        org = Organization(name="AM Risk", slug="amrisk", brand_name="AM RISK",
                           brand_sub="Aviation Risk & Training", built_by="Built by IAM-ASI")
        db.add(org)
        db.commit()
        db.refresh(org)
        from .auth import get_password_hash
        admin = User(email="admin@amrisk.local", hashed_password=get_password_hash("admin123"),
                     full_name="System Admin", role=UserRole.admin, org_id=org.id)
        db.add(admin)
        db.commit()

@app.get("/health")
def health():
    return {"status": "ok", "version": "1.0.0"}

@app.get("/")
def root():
    return {"message": "AM Risk Briefing API", "docs": "/docs"}
