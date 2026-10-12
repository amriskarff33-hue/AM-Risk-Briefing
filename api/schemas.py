from pydantic import BaseModel, EmailStr
from typing import Optional, List, Dict, Any
from datetime import datetime
from .models import UserRole, BriefStatus, DeliveryStatus

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"

class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: Optional[str] = None
    role: UserRole = UserRole.viewer

class UserOut(BaseModel):
    id: int
    email: str
    full_name: Optional[str]
    role: UserRole
    org_id: int
    is_active: bool
    class Config:
        from_attributes = True

class OrgCreate(BaseModel):
    name: str
    slug: str
    brand_name: Optional[str] = "AM RISK"
    brand_sub: Optional[str] = "Aviation Risk & Training"
    built_by: Optional[str] = "Built by IAM-ASI"

class OrgOut(BaseModel):
    id: int
    name: str
    slug: str
    brand_name: str
    brand_sub: str
    built_by: str
    class Config:
        from_attributes = True

class BriefCreate(BaseModel):
    title: Optional[str] = None
    script: Optional[str] = None
    scheduled_for: Optional[datetime] = None

class BriefUpdate(BaseModel):
    title: Optional[str] = None
    script: Optional[str] = None
    status: Optional[BriefStatus] = None
    scheduled_for: Optional[datetime] = None

class BriefOut(BaseModel):
    id: int
    org_id: int
    title: Optional[str]
    script: Optional[str]
    story: Optional[str]
    status: BriefStatus
    provider: str
    video_path_16: Optional[str]
    video_path_9: Optional[str]
    audio_path: Optional[str]
    duration: float
    items: List[Dict[str, Any]]
    created_by: Optional[int]
    approved_by: Optional[int]
    approved_at: Optional[datetime]
    published_at: Optional[datetime]
    scheduled_for: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True

class ChannelCreate(BaseModel):
    name: str
    type: str
    config: Dict[str, Any] = {}

class ChannelOut(BaseModel):
    id: int
    org_id: int
    name: str
    type: str
    config: Dict[str, Any]
    is_active: bool
    class Config:
        from_attributes = True

class DeliveryOut(BaseModel):
    id: int
    brief_id: int
    channel_id: int
    status: DeliveryStatus
    external_id: Optional[str]
    error: Optional[str]
    attempts: int
    sent_at: Optional[datetime]
    class Config:
        from_attributes = True

class FeedSourceCreate(BaseModel):
    url: str
    name: Optional[str] = None
    keywords: List[str] = []

class FeedSourceOut(BaseModel):
    id: int
    org_id: int
    url: str
    name: Optional[str]
    keywords: List[str]
    is_active: bool
    last_fetch: Optional[datetime]
    class Config:
        from_attributes = True

class JobStatus(BaseModel):
    job_id: str
    status: str
    progress: Optional[float] = None
    message: Optional[str] = None
