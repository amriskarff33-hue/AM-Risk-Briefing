from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..db import get_db
from ..auth import get_current_user, require_role
from ..models import User, UserRole, Channel, FeedSource, AuditLog
from ..schemas import ChannelCreate, ChannelOut, FeedSourceCreate, FeedSourceOut

router = APIRouter(tags=["channels"])

@router.get("/channels", response_model=list[ChannelOut])
def list_channels(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(Channel).filter(Channel.org_id == user.org_id).all()

@router.post("/channels", response_model=ChannelOut)
def create_channel(data: ChannelCreate, db: Session = Depends(get_db),
                   user: User = Depends(require_role(UserRole.admin))):
    ch = Channel(org_id=user.org_id, **data.model_dump())
    db.add(ch)
    db.commit()
    db.refresh(ch)
    return ch

@router.delete("/channels/{channel_id}")
def delete_channel(channel_id: int, db: Session = Depends(get_db),
                   user: User = Depends(require_role(UserRole.admin))):
    ch = db.query(Channel).filter(Channel.id == channel_id, Channel.org_id == user.org_id).first()
    if not ch:
        raise HTTPException(status_code=404)
    db.delete(ch)
    db.commit()
    return {"ok": True}

@router.get("/feeds", response_model=list[FeedSourceOut])
def list_feeds(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    return db.query(FeedSource).filter(FeedSource.org_id == user.org_id).all()

@router.post("/feeds", response_model=FeedSourceOut)
def create_feed(data: FeedSourceCreate, db: Session = Depends(get_db),
                user: User = Depends(require_role(UserRole.admin, UserRole.editor))):
    fs = FeedSource(org_id=user.org_id, **data.model_dump())
    db.add(fs)
    db.commit()
    db.refresh(fs)
    return fs

@router.delete("/feeds/{feed_id}")
def delete_feed(feed_id: int, db: Session = Depends(get_db),
                user: User = Depends(require_role(UserRole.admin))):
    fs = db.query(FeedSource).filter(FeedSource.id == feed_id, FeedSource.org_id == user.org_id).first()
    if not fs:
        raise HTTPException(status_code=404)
    db.delete(fs)
    db.commit()
    return {"ok": True}
