from sqlalchemy.orm import Session
from app.models.region_model import Region
from app.schemas.region_schema import RegionCreate, RegionUpdate

class RegionRepository:
    @staticmethod
    def get_all(db: Session):
        return db.query(Region).all()

    @staticmethod
    def get_by_id(db: Session, id: int):
        return db.query(Region).filter(Region.id == id).first()

    @staticmethod
    def create(db: Session, data: RegionCreate):
        new = Region(**data.model_dump())
        db.add(new)
        db.commit()
        db.refresh(new)
        return new

    @staticmethod
    def update(db: Session, id: int, data: RegionUpdate):
        item = RegionRepository.get_by_id(db, id)
        if not item:
            return None
        for key, value in data.model_dump().items():
            setattr(item, key, value)
        db.commit()
        db.refresh(item)
        return item

    @staticmethod
    def delete(db: Session, id: int):
        item = RegionRepository.get_by_id(db, id)
        if not item:
            return None
        db.delete(item)
        db.commit()
        return item