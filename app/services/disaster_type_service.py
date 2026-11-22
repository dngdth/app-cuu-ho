from sqlalchemy.orm import Session
from app.repositories.disaster_type_repository import DisasterTypeRepository
from app.schemas.disaster_type_schema import DisasterTypeCreate, DisasterTypeUpdate

class DisasterTypeService:
    def __init__(self):
        self.repository = DisasterTypeRepository()

    def get_all(self, db: Session):
        return self.repository.get_all(db)

    def get_by_id(self, db: Session, id: int):
        return self.repository.get_by_id(db, id)

    def create(self, db: Session, data: DisasterTypeCreate):
        return self.repository.create(db, data)

    def update(self, db: Session, id: int, data: DisasterTypeUpdate):
        return self.repository.update(db, id, data)

    def delete(self, db: Session, id: int):
        return self.repository.delete(db, id)
