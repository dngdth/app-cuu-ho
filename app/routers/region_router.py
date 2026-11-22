from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session
from app.dependencies import get_db
from app.schemas.region_schema import RegionCreate, RegionUpdate, RegionResponse
from app.services.region_service import RegionService
from app.services import region_import_service
import shutil
import os
from pathlib import Path

router = APIRouter(prefix="/region", tags=["Region"])
region_service = RegionService()

@router.get("/", response_model=list[RegionResponse])
def get_all(db: Session = Depends(get_db)):
    return region_service.get_all(db)

@router.get("/{id}", response_model=RegionResponse)
def get_by_id(id: int, db: Session = Depends(get_db)):
    item = region_service.get_by_id(db, id)
    if not item:
        raise HTTPException(404, "Region not found")
    return item

@router.post("/", response_model=RegionResponse)
def create(data: RegionCreate, db: Session = Depends(get_db)):
    return region_service.create(db, data)

@router.put("/{id}", response_model=RegionResponse)
def update(id: int, data: RegionUpdate, db: Session = Depends(get_db)):
    item = region_service.update(db, id, data)
    if not item:
        raise HTTPException(404, "Region not found")
    return item

@router.delete("/{id}")
def delete(id: int, db: Session = Depends(get_db)):
    item = region_service.delete(db, id)
    if not item:
        raise HTTPException(404, "Region not found")
    return {"message": "Deleted successfully"}

@router.post("/import-csv", 
             summary="Import regions from CSV file",
             description="Upload a CSV file with columns: name, parent_id (optional)")
async def import_csv(
    file: UploadFile = File(..., description="CSV file containing region data"),
    db: Session = Depends(get_db)
):
    """
    Import regions from CSV file.
    
    CSV format:
    - name: Region name (required)
    - parent_id: Parent region ID (optional)
    
    Example:
    ```
    name,parent_id
    Hà Nội,
    Ba Đình,1
    ```
    """
    # Check file extension
    if not file.filename.endswith('.csv'):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="File must be CSV format"
        )
    
    # Save uploaded file temporarily
    upload_dir = Path("uploads")
    upload_dir.mkdir(exist_ok=True)
    file_path = upload_dir / file.filename
    
    try:
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
        
        # Import CSV
        result = region_import_service.import_csv(str(file_path), db)
        
        # Clean up
        os.remove(file_path)
        
        if result.get("success"):
            return {
                "message": "Import completed",
                "total": result["total"],
                "success": result["success_count"],
                "errors": result["error_count"],
                "error_details": result.get("errors", [])
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "Import failed")
            )
            
    except Exception as e:
        # Clean up on error
        if file_path.exists():
            os.remove(file_path)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to import CSV: {str(e)}"
        )