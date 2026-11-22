from sqlalchemy.orm import Session
from app.models.disaster_type_model import DisasterType
from app.schemas.disaster_type_schema import DisasterTypeCreate, DisasterTypeUpdate

class DisasterTypeRepository:
    @staticmethod
    def get_all(db: Session):
        return db.query(DisasterType).all()

    @staticmethod
    def get_by_id(db: Session, id: int):
        return db.query(DisasterType).filter(DisasterType.id == id).first()

    @staticmethod
    def create(db: Session, data: DisasterTypeCreate):
        new = DisasterType(**data.model_dump())
        db.add(new)
        db.commit()
        db.refresh(new)
        return new

    @staticmethod
    def update(db: Session, id: int, data: DisasterTypeUpdate):
        item = DisasterTypeRepository.get_by_id(db, id)
        if not item:
            return None
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(item, key, value)
        db.commit()
        db.refresh(item)
        return item

    @staticmethod
    def delete(db: Session, id: int):
        item = DisasterTypeRepository.get_by_id(db, id)
        if not item:
            return None
        db.delete(item)
        db.commit()
        return item
