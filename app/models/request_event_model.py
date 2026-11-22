from datetime import datetime, timezone
from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON, String
from app.db.database import Base


class RequestEvent(Base):
    __tablename__ = "rescue_request_event"
    id = Column(Integer, primary_key=True)
    rescue_request_id = Column(Integer, ForeignKey("rescue_request.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    actor = Column(String(100), nullable=False)
    note = Column(String(2000), nullable=False)
    changes = Column(JSON, nullable=False)
