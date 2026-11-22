from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.dependencies import get_db
from app.schemas.needs_schema import NeedsCreate, NeedsUpdate, NeedsResponse
from app.services.needs_service import NeedsService

router = APIRouter(prefix="/needs", tags=["Needs"])
needs_service = NeedsService()

@router.get("/", response_model=list[NeedsResponse])
def get_all(db: Session = Depends(get_db)):
    return needs_service.get_all(db)

@router.get("/{id}", response_model=NeedsResponse)
def get_by_id(id: int, db: Session = Depends(get_db)):
    item = needs_service.get_by_id(db, id)
    if not item:
        raise HTTPException(404, "Needs not found")
    return item

@router.post("/", response_model=NeedsResponse)
def create(data: NeedsCreate, db: Session = Depends(get_db)):
    return needs_service.create(db, data)

@router.put("/{id}", response_model=NeedsResponse)
def update(id: int, data: NeedsUpdate, db: Session = Depends(get_db)):
    item = needs_service.update(db, id, data)
    if not item:
        raise HTTPException(404, "Needs not found")
    return item

@router.delete("/{id}")
def delete(id: int, db: Session = Depends(get_db)):
    item = needs_service.delete(db, id)
    if not item:
        raise HTTPException(404, "Needs not found")
    return {"message": "Deleted successfully"}
