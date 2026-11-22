from sqlalchemy import Column, Integer, String, ForeignKey, Float, DateTime, Boolean, Table
from sqlalchemy.orm import relationship
from geoalchemy2 import Geometry
from app.db.database import Base
from datetime import datetime

# Association table for many-to-many relationship between rescue_request and needs
rescue_request_needs = Table(
    'rescue_request_needs',
    Base.metadata,
    Column('rescue_request_id', Integer, ForeignKey('rescue_request.id'), primary_key=True),
    Column('needs_id', Integer, ForeignKey('needs.id'), primary_key=True)
)

# Association table for many-to-many relationship between rescue_request and disaster_types
rescue_request_disaster_types = Table(
    'rescue_request_disaster_types',
    Base.metadata,
    Column('rescue_request_id', Integer, ForeignKey('rescue_request.id'), primary_key=True),
    Column('disaster_type_id', Integer, ForeignKey('disaster_type.id'), primary_key=True)
)

class RescueRequest(Base):
    __tablename__ = "rescue_request"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String, nullable=False)
    # GeoJSON Point: [longitude, latitude]
    coordinate = Column(Geometry(geometry_type='POINT', srid=4326), nullable=True)
    location = Column(String, nullable=True)
    content = Column(String, nullable=True)
    map_link = Column(String, nullable=True)
    status = Column(String, nullable=True)
    posted_time = Column(String, nullable=True)
    created_date = Column(DateTime, default=datetime.utcnow)
    image = Column(String, nullable=True)
    urgency_score = Column(Float, nullable=True)
    reliability_score = Column(Float, nullable=True)
    contact = Column(String, nullable=True)
    region_id = Column(Integer, ForeignKey("region.id"))
    
    # New columns
    affected_people = Column(Integer, nullable=True)
    infrastructure_damage = Column(Boolean, default=False)
    is_isolated = Column(Boolean, default=False)
    deathly = Column(Boolean, default=False)
    has_emergency = Column(Boolean, default=False)
    has_emotion = Column(Boolean, default=False)
    has_emphasis = Column(Boolean, default=False)
    reactions = Column(Integer, default=0)
    replies = Column(Integer, default=0)

    region = relationship("Region")
    needs = relationship("Needs", secondary=rescue_request_needs, backref="rescue_requests")
    disaster_types = relationship("DisasterType", secondary=rescue_request_disaster_types, backref="rescue_requests")
    prediction_result = relationship("RescuePrediction", uselist=False, cascade="all, delete-orphan")

    @property
    def prediction(self):
        return self.prediction_result.details if self.prediction_result else None
