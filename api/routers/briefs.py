from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from typing import Optional
from datetime import datetime
from ..db import get_db
from ..auth import get_current_user, require_role
from ..models import User, UserRole, Brief, BriefStatus, Channel, Delivery, DeliveryStatus, AuditLog, Organization
from ..schemas import BriefCreate, BriefUpdate, BriefOut, ChannelCreate, ChannelOut, DeliveryOut, JobStatus
from ..config import get_settings

router = APIRouter(prefix="/briefs", tags=["briefs"])
settings = get_settings()

def audit(db: Session, user: User, action: str, entity_type: str, entity_id: int, details: dict = None):
    db.add(AuditLog(org_id=user.org_id, user_id=user.id, action=action,
                     entity_type=entity_type, entity_id=entity_id, details=details or {}))
    db.commit()

@router.get("", response_model=list[BriefOut])
def list_briefs(status: Optional[BriefStatus] = None, db: Session = Depends(get_db),
                user: User = Depends(get_current_user)):
    q = db.query(Brief).filter(Brief.org_id == user.org_id)
    if status:
        q = q.filter(Brief.status == status)
    return q.order_by(Brief.created_at.desc()).all()

@router.post("", response_model=BriefOut)
def create_brief(data: BriefCreate, background: BackgroundTasks,
                 db: Session = Depends(get_db), user: User = Depends(require_role(UserRole.admin, UserRole.editor))):
    brief = Brief(org_id=user.org_id, title=data.title, script=data.script,
                  status=BriefStatus.draft, created_by=user.id)
    db.add(brief)
    db.commit()
    db.refresh(brief)
    audit(db, user, "create", "brief", brief.id)
    return brief

@router.get("/{brief_id}", response_model=BriefOut)
def get_brief(brief_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    brief = db.query(Brief).filter(Brief.id == brief_id, Brief.org_id == user.org_id).first()
    if not brief:
        raise HTTPException(status_code=404, detail="Brief not found")
    return brief

@router.patch("/{brief_id}", response_model=BriefOut)
def update_brief(brief_id: int, data: BriefUpdate, db: Session = Depends(get_db),
                 user: User = Depends(require_role(UserRole.admin, UserRole.editor))):
    brief = db.query(Brief).filter(Brief.id == brief_id, Brief.org_id == user.org_id).first()
    if not brief:
        raise HTTPException(status_code=404, detail="Brief not found")
    for k, v in data.model_dump(exclude_unset=True).items():
        setattr(brief, k, v)
    if data.status == BriefStatus.pending_review:
        audit(db, user, "submit_for_review", "brief", brief.id)
    db.commit()
    db.refresh(brief)
    return brief

@router.post("/{brief_id}/approve", response_model=BriefOut)
def approve_brief(brief_id: int, db: Session = Depends(get_db),
                  user: User = Depends(require_role(UserRole.admin))):
    brief = db.query(Brief).filter(Brief.id == brief_id, Brief.org_id == user.org_id).first()
    if not brief:
        raise HTTPException(status_code=404, detail="Brief not found")
    if brief.status != BriefStatus.pending_review:
        raise HTTPException(status_code=400, detail="Brief must be pending review")
    brief.status = BriefStatus.approved
    brief.approved_by = user.id
    brief.approved_at = datetime.utcnow()
    db.commit()
    audit(db, user, "approve", "brief", brief.id)
    return brief

@router.post("/{brief_id}/reject", response_model=BriefOut)
def reject_brief(brief_id: int, db: Session = Depends(get_db),
                 user: User = Depends(require_role(UserRole.admin))):
    brief = db.query(Brief).filter(Brief.id == brief_id, Brief.org_id == user.org_id).first()
    if not brief:
        raise HTTPException(status_code=404, detail="Brief not found")
    brief.status = BriefStatus.rejected
    db.commit()
    audit(db, user, "reject", "brief", brief.id)
    return brief

@router.post("/{brief_id}/generate", response_model=JobStatus)
def generate_brief(brief_id: int, background: BackgroundTasks,
                    db: Session = Depends(get_db), user: User = Depends(require_role(UserRole.admin, UserRole.editor))):
    from worker.tasks import generate_brief_task
    brief = db.query(Brief).filter(Brief.id == brief_id, Brief.org_id == user.org_id).first()
    if not brief:
        raise HTTPException(status_code=404, detail="Brief not found")
    task = generate_brief_task.delay(brief_id)
    return {"job_id": task.id, "status": "queued", "message": "Brief generation queued"}

@router.post("/{brief_id}/publish", response_model=BriefOut)
def publish_brief(brief_id: int, db: Session = Depends(get_db),
                  user: User = Depends(require_role(UserRole.admin))):
    from worker.tasks import distribute_brief_task
    brief = db.query(Brief).filter(Brief.id == brief_id, Brief.org_id == user.org_id).first()
    if not brief:
        raise HTTPException(status_code=404, detail="Brief not found")
    if settings.APPROVAL_REQUIRED and brief.status != BriefStatus.approved:
        raise HTTPException(status_code=400, detail="Brief must be approved before publishing")
    if not brief.video_path_16:
        raise HTTPException(status_code=400, detail="Brief has no video yet — generate first")
    brief.status = BriefStatus.published
    brief.published_at = datetime.utcnow()
    db.commit()
    distribute_brief_task.delay(brief_id)
    audit(db, user, "publish", "brief", brief.id)
    return brief

@router.get("/{brief_id}/deliveries", response_model=list[DeliveryOut])
def list_deliveries(brief_id: int, db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(Delivery).filter(Delivery.brief_id == brief_id).all()
