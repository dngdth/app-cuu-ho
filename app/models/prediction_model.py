from datetime import datetime
from sqlalchemy import Column, DateTime, ForeignKey, Integer, JSON
from app.db.database import Base


class RescuePrediction(Base):
    __tablename__ = "rescue_prediction"
    rescue_request_id = Column(Integer, ForeignKey("rescue_request.id", ondelete="CASCADE"), primary_key=True)
    details = Column(JSON, nullable=False)
    created_date = Column(DateTime, default=datetime.utcnow)
