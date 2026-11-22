from sqlalchemy.orm import Session
from app.repositories.needs_repository import NeedsRepository
from app.schemas.needs_schema import NeedsCreate, NeedsUpdate

class NeedsService:
    def __init__(self):
        self.repository = NeedsRepository()

    def get_all(self, db: Session):
        return self.repository.get_all(db)

    def get_by_id(self, db: Session, id: int):
        return self.repository.get_by_id(db, id)

    def create(self, db: Session, data: NeedsCreate):
        return self.repository.create(db, data)

    def update(self, db: Session, id: int, data: NeedsUpdate):
        return self.repository.update(db, id, data)

    def delete(self, db: Session, id: int):
        return self.repository.delete(db, id)
