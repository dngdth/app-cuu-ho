from sqlalchemy.orm import Session
from app.models.needs_model import Needs
from app.schemas.needs_schema import NeedsCreate, NeedsUpdate

class NeedsRepository:
    @staticmethod
    def get_all(db: Session):
        return db.query(Needs).all()

    @staticmethod
    def get_by_id(db: Session, id: int):
        return db.query(Needs).filter(Needs.id == id).first()

    @staticmethod
    def create(db: Session, data: NeedsCreate):
        new = Needs(**data.model_dump())
        db.add(new)
        db.commit()
        db.refresh(new)
        return new

    @staticmethod
    def update(db: Session, id: int, data: NeedsUpdate):
        item = NeedsRepository.get_by_id(db, id)
        if not item:
            return None
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(item, key, value)
        db.commit()
        db.refresh(item)
        return item

    @staticmethod
    def delete(db: Session, id: int):
        item = NeedsRepository.get_by_id(db, id)
        if not item:
            return None
        db.delete(item)
        db.commit()
        return item
