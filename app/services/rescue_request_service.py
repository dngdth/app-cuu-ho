from sqlalchemy.orm import Session
from app.repositories.rescue_request_repository import RescueRequestRepository
from app.schemas.rescue_request_schema import RescueRequestCreate, RescueRequestUpdate
from typing import Optional

class RescueRequestService:
    def __init__(self):
        self.repository = RescueRequestRepository()

    @staticmethod
    def convert_location_to_geom(location_data):
        return RescueRequestRepository.convert_location_to_geom(location_data)

    @staticmethod
    def get_all(
        db: Session,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None,
        category_id: Optional[int] = None,
        region_id: Optional[int] = None,
        sort_by: str = "created_date",
        order: str = "desc"
    ):
        return RescueRequestRepository.get_all(
            db,
            skip,
            limit,
            status,
            category_id,
            region_id,
            sort_by,
            order
        )

    @staticmethod
    def get_by_id(db: Session, request_id: int):
        return RescueRequestRepository.get_by_id(db, request_id)

    @staticmethod
    def create(db: Session, data: RescueRequestCreate):
        data = data.model_copy(update={"status": "unverified"})
        if data.urgency_score is None or data.reliability_score is None:
            from app.services.processing_service import ProcessingService
            result = ProcessingService.process(db, [data.model_dump(exclude_unset=True)])
            row = result["results"][0]
            if row["status"] == "error":
                raise ValueError(row["error"])
            return RescueRequestRepository.get_by_id(db, row["id"])
        return RescueRequestRepository.create(db, data)

    @staticmethod
    def update(db: Session, request_id: int, data: RescueRequestUpdate):
        return RescueRequestRepository.update(db, request_id, data)

    @staticmethod
    def delete(db: Session, request_id: int):
        return RescueRequestRepository.delete(db, request_id)

    @staticmethod
    def get_nearby(
        db: Session,
        longitude: float,
        latitude: float,
        radius_km: float = 5.0,
        limit: int = 100
    ):
        return RescueRequestRepository.get_nearby(
            db,
            longitude,
            latitude,
            radius_km,
            limit
        )

    @staticmethod
    def get_by_region(
        db: Session,
        region_id: int,
        skip: int = 0,
        limit: int = 100
    ):
        return RescueRequestRepository.get_by_region(
            db,
            region_id,
            skip,
            limit
        )


