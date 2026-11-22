from sqlalchemy import Column, Integer, String
from app.db.database import Base

class DisasterType(Base):
    __tablename__ = "disaster_type"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)
