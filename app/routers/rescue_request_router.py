from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from app.services.rescue_request_service import RescueRequestService
from app.services import json_import_service
from app.schemas.rescue_request_schema import RescueRequestOut, RescueRequestCreate, RescueRequestUpdate
from sqlalchemy.orm import Session
from app.dependencies import get_db
from typing import Dict, Any, Optional
import shutil
import os
from pathlib import Path
from fastapi import Request

router = APIRouter(prefix="/rescue_request", tags=["rescue_request"])

# def serialize_geometry(item) -> RescueRequestOut:
#     """Convert ORM object location geometry to GeoJSON dict"""
#     if not item or not hasattr(item, 'location'):
#         return item

#     # Convert the ORM object to dict for processing
#     item_dict = {k: getattr(item, k) for k in item.__table__.columns.keys()}

#     # Convert geometry to GeoJSON if present
#     if item.location and hasattr(item.location, '__geo_interface__'):
#         geo = item.location.__geo_interface__
#         coords = geo.get('coordinates')
#         item_dict['location'] = {
#             'type': geo.get('type', 'Point'),
#             'coordinates': list(coords) if coords else None,
#             'address': item.address
#         }
#     elif item.location is None:
#         item_dict['location'] = None

#     # Create RescueRequestOut from dict
#     return RescueRequestOut(**item_dict)

@router.get("/", response_model=list[RescueRequestOut])
def get_all(
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of records to return"),
    status: Optional[str] = Query(None, description="Filter by status"),
    category_id: Optional[int] = Query(None, description="Filter by category ID"),
    region_id: Optional[int] = Query(None, description="Filter by region ID"),
    sort_by: str = Query("created_date", description="Field to sort by"),
    order: str = Query("desc", pattern="^(asc|desc)$", description="Sort order: asc or desc"),
    db: Session = Depends(get_db)
):
    """
    Get all rescue requests with pagination and filtering.
    """
    items = RescueRequestService.get_all(
        db,
        skip=skip,
        limit=limit,
        status=status,
        category_id=category_id,
        region_id=region_id,
        sort_by=sort_by,
        order=order
    )
    return items

@router.get("/{id}", response_model=RescueRequestOut)
def get_by_id(id: int, db: Session = Depends(get_db)):
    """Get a specific rescue request by ID"""
    item = RescueRequestService.get_by_id(db, id)
    if not item:
        raise HTTPException(status_code=404, detail=f"Rescue request with id {id} not found")
    return item

@router.post("/", response_model=RescueRequestOut, status_code=status.HTTP_201_CREATED)
def create(data: RescueRequestCreate, db: Session = Depends(get_db)):
    """
    Create a new rescue request with auto-transformation.

    **Auto-transformations applied:**
    - Title: Auto-generated from content + location if not provided
    - Coordinate: Auto-geocoded from location text if not provided
    - Map Link: Auto-generated from coordinates
    - Region ID: Auto-detected from location text
    - Needs/Disaster Types: Parse text to IDs if using *_text fields
    - Scores: Convert "CAO"/"TRUNG BÌNH"/"THẤP" to numeric
    - Posted Time: Parse "1w", "2d", "3h" to datetime

    **Examples:**
    - Minimal: `{"content": "Help!", "location": "Quận 2, HCM"}`
    - With text: `{"content": "...", "needs_text": "food, water"}`
    - Full control: `{"title": "...", "coordinate": {...}, "needs_ids": [1,2]}`
    """
    try:
        item = RescueRequestService.create(db, data)
        return item
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create rescue request: {str(e)}"
        )

@router.put("/{id}", response_model=RescueRequestOut)
def update(id: int, data: RescueRequestUpdate, request: Request, db: Session = Depends(get_db)):
    """
    Update a rescue request.

    **Note:** Only provided fields will be updated. Omitted fields remain unchanged.
    """
    try:
        user = getattr(request.state, "user", None)
        if user:
            data = data.model_copy(update={"actor": f"{user['name']} ({user['email']})"})
        item = RescueRequestService.update(db, id, data)
        if not item:
            raise HTTPException(status_code=404, detail=f"Rescue request with id {id} not found")
        return item
    except HTTPException:
        raise
    except ValueError as e:
        db.rollback()
        raise HTTPException(422, str(e)) from e
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update rescue request: {str(e)}"
        )

@router.delete("/{id}")
def delete(id: int, db: Session = Depends(get_db)):
    """Delete a rescue request by ID"""
    item = RescueRequestService.delete(db, id)
    if not item:
        raise HTTPException(404, "Rescue request not found")
    return {"message": "Deleted successfully"}

@router.get("/nearby/search", response_model=list[RescueRequestOut])
def get_nearby(
    longitude: float = Query(..., ge=-180, le=180, description="Longitude of the center point"),
    latitude: float = Query(..., ge=-90, le=90, description="Latitude of the center point"),
    radius_km: float = Query(5.0, gt=0, le=100, description="Search radius in kilometers (max 100km)"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of results"),
    db: Session = Depends(get_db)
):
    """
    Find rescue requests near a location.

    **Parameters:**
    - **longitude**: Longitude of the center point (-180 to 180)
    - **latitude**: Latitude of the center point (-90 to 90)
    - **radius_km**: Search radius in kilometers (default: 5km, max: 100km)
    - **limit**: Maximum number of results (1-500)

    **Returns:** List of rescue requests within the radius, sorted by distance (nearest first)

    **Example:** `/rescue_request/nearby/search?longitude=105.8342&latitude=21.0278&radius_km=10`
    """
    try:
        results = RescueRequestService.get_nearby(db, longitude, latitude, radius_km, limit)
        # results is list of tuples (RescueRequest, distance), extract just the requests
        return [result[0] for result in results]
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to search nearby requests: {str(e)}"
        )

@router.get("/region/{region_id}", response_model=list[RescueRequestOut])
def get_by_region(
    region_id: int,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=500, description="Maximum number of records"),
    db: Session = Depends(get_db)
):
    """
    Get all rescue requests in a specific region.

    **Parameters:**
    - **region_id**: ID of the region
    - **skip**: Number of records to skip (for pagination)
    - **limit**: Maximum number of records to return (1-500)

    **Returns:** List of rescue requests in the region, sorted by created_date (newest first)
    """
    try:
        items = RescueRequestService.get_by_region(db, region_id, skip, limit)
        return items
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get requests by region: {str(e)}"
        )

@router.post("/import-json-data")
def import_json_data(
    data: list[Dict[str, Any]],
    db: Session = Depends(get_db)
):
    """
    Import rescue requests from JSON data (direct in request body).

    **JSON Format:** Array of objects with fields:
    - title: Tiêu đề
    - content: Nội dung (required)
    - location: Địa chỉ (required)
    - contact: Liên hệ
    - posted_time: Thời gian đăng
    - disaster_type_text: Loại thiên tai (text)
    - needs_text: Nhu cầu (text)
    - affected_people: Số người bị ảnh hưởng
    - infrastructure_damage: Hư hại cơ sở hạ tầng (true/false)
    - is_isolated: Bị cô lập (true/false)
    - deathly: Có tử vong (true/false)
    - has_emergency: Khẩn cấp (true/false)
    - has_emotion: Cảm xúc mạnh (true/false)
    - has_emphasis: Nhấn mạnh (true/false)
    - reactions: Số lượt tương tác
    - replies: Số lượt phản hồi
    - urgency_score: Mức độ khẩn cấp (CAO/TRUNG BÌNH/THẤP)
    - reliability_score: Độ tin cậy (CAO/TRUNG BÌNH/THẤP)

    **Returns:** Import result with success/error statistics

    **Example request body:**
    ```json
    [
      {
        "content": "Nhà bị ngập sâu 2m, cần hỗ trợ gấp!",
        "location": "Quận 2, TP.HCM",
        "contact": "0901234567",
        "needs_text": "lương thực, nước uống",
        "urgency_score": "CAO"
      }
    ]
    ```
    """
    try:
        # Import JSON data directly
        result = json_import_service.import_json_data(data, db)

        if result.get("success"):
            return {
                "message": "Import completed",
                "total": result["total"],
                "success": result["success_count"],
                "errors": result["error_count"],
                "error_details": result.get("errors", []),
                "duplicates": result.get("duplicates", 0),
                "results": result.get("results", [])
            }
        else:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=result.get("error", "Import failed")
            )

    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to import JSON data: {str(e)}"
        )
