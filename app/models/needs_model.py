from sqlalchemy import Column, Integer, String
from app.db.database import Base

class Needs(Base):
    __tablename__ = "needs"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=True)