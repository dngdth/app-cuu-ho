"""Additive tables for the prototype: no changes to existing rescue rows."""
from datetime import datetime, timezone
from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, JSON, String, Text
from app.db.database import Base


def utcnow():
    return datetime.now(timezone.utc)


class ApiCounter(Base):
    __tablename__ = "api_counter"
    service = Column(String(40), primary_key=True)
    period = Column(String(10), primary_key=True)
    period_key = Column(String(10), primary_key=True)
    count = Column(Integer, nullable=False, default=0)


class ProviderCache(Base):
    __tablename__ = "provider_cache"
    key = Column(String(64), primary_key=True)
    payload = Column(JSON, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)


class User(Base):
    __tablename__ = "app_user"
    id = Column(Integer, primary_key=True)
    email = Column(String(254), nullable=False, unique=True, index=True)
    name = Column(String(100), nullable=False)
    password_hash = Column(Text, nullable=False)
    role = Column(String(20), nullable=False, default="viewer")
    active = Column(Boolean, nullable=False, default=True)
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)


class UserSession(Base):
    __tablename__ = "user_session"
    token_hash = Column(String(64), primary_key=True)
    csrf_hash = Column(String(64), nullable=False)
    user_id = Column(Integer, ForeignKey("app_user.id", ondelete="CASCADE"), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)


class LoginThrottle(Base):
    __tablename__ = "login_throttle"
    key = Column(String(64), primary_key=True)
    attempts = Column(Integer, nullable=False, default=0)
    window_start = Column(DateTime(timezone=True), nullable=False, default=utcnow)


class ProcessingJob(Base):
    __tablename__ = "processing_job"
    id = Column(String(36), primary_key=True)
    kind = Column(String(30), nullable=False)
    owner_id = Column(Integer, ForeignKey("app_user.id"), nullable=False)
    status = Column(String(20), nullable=False, default="queued", index=True)
    payload = Column(JSON, nullable=False)
    progress = Column(Integer, nullable=False, default=0)
    total = Column(Integer, nullable=False)
    report = Column(JSON, nullable=False, default=dict)
    error = Column(Text)
    attempts = Column(Integer, nullable=False, default=0)
    worker_id = Column(String(36))
    lease_until = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=utcnow)
