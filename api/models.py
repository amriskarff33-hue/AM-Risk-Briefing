import enum
from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, Boolean, ForeignKey, Enum, JSON, Float
from sqlalchemy.orm import relationship
from .db import Base

class UserRole(str, enum.Enum):
    admin = "admin"
    editor = "editor"
    viewer = "viewer"

class BriefStatus(str, enum.Enum):
    draft = "draft"
    pending_review = "pending_review"
    approved = "approved"
    rejected = "rejected"
    published = "published"
    failed = "failed"

class DeliveryStatus(str, enum.Enum):
    pending = "pending"
    queued = "queued"
    sent = "sent"
    failed = "failed"
    retrying = "retrying"

class Organization(Base):
    __tablename__ = "organizations"
    id = Column(Integer, primary_key=True)
    name = Column(String(200), nullable=False)
    slug = Column(String(100), unique=True, nullable=False)
    brand_name = Column(String(200), default="AM RISK")
    brand_sub = Column(String(200), default="Aviation Risk & Training")
    built_by = Column(String(200), default="Built by IAM-ASI")
    logo_url = Column(String(500))
    primary_color = Column(String(7), default="#0A1628")
    accent_color = Column(String(7), default="#d6ff3d")
    voice = Column(String(100), default="en-ZA-LeahNeural")
    created_at = Column(DateTime, default=datetime.utcnow)
    users = relationship("User", back_populates="org")
    briefs = relationship("Brief", back_populates="org")
    channels = relationship("Channel", back_populates="org")

class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True)
    email = Column(String(200), unique=True, nullable=False)
    hashed_password = Column(String(200), nullable=False)
    full_name = Column(String(200))
    role = Column(Enum(UserRole), default=UserRole.viewer)
    org_id = Column(Integer, ForeignKey("organizations.id"))
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    org = relationship("Organization", back_populates="users")

class Brief(Base):
    __tablename__ = "briefs"
    id = Column(Integer, primary_key=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    title = Column(String(300))
    script = Column(Text)
    story = Column(Text)
    status = Column(Enum(BriefStatus), default=BriefStatus.draft)
    provider = Column(String(50), default="extractive")
    video_path_16 = Column(String(500))
    video_path_9 = Column(String(500))
    audio_path = Column(String(500))
    srt_path = Column(String(500))
    duration = Column(Float, default=0)
    items = Column(JSON, default=list)
    created_by = Column(Integer, ForeignKey("users.id"))
    approved_by = Column(Integer, ForeignKey("users.id"))
    approved_at = Column(DateTime)
    published_at = Column(DateTime)
    scheduled_for = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    org = relationship("Organization", back_populates="briefs")
    deliveries = relationship("Delivery", back_populates="brief", cascade="all, delete-orphan")

class Channel(Base):
    __tablename__ = "channels"
    id = Column(Integer, primary_key=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    name = Column(String(200), nullable=False)
    type = Column(String(50), nullable=False)  # telegram, whatsapp, email
    config = Column(JSON, default=dict)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    org = relationship("Organization", back_populates="channels")
    deliveries = relationship("Delivery", back_populates="channel")

class Delivery(Base):
    __tablename__ = "deliveries"
    id = Column(Integer, primary_key=True)
    brief_id = Column(Integer, ForeignKey("briefs.id"), nullable=False)
    channel_id = Column(Integer, ForeignKey("channels.id"), nullable=False)
    status = Column(Enum(DeliveryStatus), default=DeliveryStatus.pending)
    external_id = Column(String(200))
    error = Column(Text)
    attempts = Column(Integer, default=0)
    sent_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    brief = relationship("Brief", back_populates="deliveries")
    channel = relationship("Channel", back_populates="deliveries")

class FeedSource(Base):
    __tablename__ = "feed_sources"
    id = Column(Integer, primary_key=True)
    org_id = Column(Integer, ForeignKey("organizations.id"), nullable=False)
    url = Column(String(500), nullable=False)
    name = Column(String(200))
    keywords = Column(JSON, default=list)
    is_active = Column(Boolean, default=True)
    last_fetch = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)

class AuditLog(Base):
    __tablename__ = "audit_logs"
    id = Column(Integer, primary_key=True)
    org_id = Column(Integer, ForeignKey("organizations.id"))
    user_id = Column(Integer, ForeignKey("users.id"))
    action = Column(String(100), nullable=False)
    entity_type = Column(String(50))
    entity_id = Column(Integer)
    details = Column(JSON)
    created_at = Column(DateTime, default=datetime.utcnow)
