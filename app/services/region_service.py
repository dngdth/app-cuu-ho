from sqlalchemy.orm import Session
from app.repositories.region_repository import RegionRepository

class RegionService:
    def __init__(self):
        self.repository = RegionRepository()
    def get_all(self, db: Session):
        return self.repository.get_all(db)

    def get_by_id(self, db: Session, id: int):
        return self.repository.get_by_id(db, id)

    def create(self, db: Session, data):
        return self.repository.create(db, data)

    def update(self, db: Session, id: int, data):
        return self.repository.update(db, id, data)

    def delete(self, db: Session, id: int):
        return self.repository.delete(db, id)
