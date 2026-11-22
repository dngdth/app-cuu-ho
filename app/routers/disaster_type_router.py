from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.dependencies import get_db
from app.schemas.disaster_type_schema import DisasterTypeCreate, DisasterTypeUpdate, DisasterTypeResponse
from app.services.disaster_type_service import DisasterTypeService

router = APIRouter(prefix="/disaster-type", tags=["DisasterType"])
disaster_type_service = DisasterTypeService()

@router.get("/", response_model=list[DisasterTypeResponse])
def get_all(db: Session = Depends(get_db)):
    return disaster_type_service.get_all(db)

@router.get("/{id}", response_model=DisasterTypeResponse)
def get_by_id(id: int, db: Session = Depends(get_db)):
    item = disaster_type_service.get_by_id(db, id)
    if not item:
        raise HTTPException(404, "DisasterType not found")
    return item

@router.post("/", response_model=DisasterTypeResponse)
def create(data: DisasterTypeCreate, db: Session = Depends(get_db)):
    return disaster_type_service.create(db, data)

@router.put("/{id}", response_model=DisasterTypeResponse)
def update(id: int, data: DisasterTypeUpdate, db: Session = Depends(get_db)):
    item = disaster_type_service.update(db, id, data)
    if not item:
        raise HTTPException(404, "DisasterType not found")
    return item

@router.delete("/{id}")
def delete(id: int, db: Session = Depends(get_db)):
    item = disaster_type_service.delete(db, id)
    if not item:
        raise HTTPException(404, "DisasterType not found")
    return {"message": "Deleted successfully"}
