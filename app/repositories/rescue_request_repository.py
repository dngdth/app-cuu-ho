from sqlalchemy.orm import Session
from typing import Optional
from sqlalchemy import func, desc, asc, cast
from geoalchemy2 import Geography
from app.models.rescue_request_model import RescueRequest
from app.schemas.rescue_request_schema import RescueRequestCreate, RescueRequestUpdate
import logging

logger = logging.getLogger(__name__)

class RescueRequestRepository:
    @staticmethod
    def convert_location_to_geom(location_data):
        """Convert GeoJSON location to PostGIS geometry"""
        if not location_data:
            return None
        # location_data = {"type": "Point", "coordinates": [longitude, latitude], "address": "..."}
        coords = location_data.get("coordinates")
        if coords and len(coords) == 2:
            return f"POINT({coords[0]} {coords[1]})"
        return None

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
        """Get all rescue requests with pagination and filtering"""
        from app.services.request_management_service import request_query
        query = request_query(db)

        # Apply filters
        if status:
            from sqlalchemy import or_
            from app.core.workflow import TRANSITIONS
            query = query.filter(or_(RescueRequest.status == status, RescueRequest.status.is_(None), RescueRequest.status.notin_(tuple(TRANSITIONS)))) if status == "unverified" else query.filter(RescueRequest.status == status)
        if category_id:
            query = query.filter(RescueRequest.disaster_types.any(id=category_id))
        if region_id:
            query = query.filter(RescueRequest.region_id == region_id)

        # Apply sorting
        order_func = desc if order == "desc" else asc
        if hasattr(RescueRequest, sort_by):
            query = query.order_by(order_func(getattr(RescueRequest, sort_by)))

        # Apply pagination
        return query.offset(skip).limit(limit).all()

    @staticmethod
    def get_by_id(db: Session, request_id: int):
        return db.query(RescueRequest).filter(RescueRequest.id == request_id).first()

    @staticmethod
    def create(db: Session, data: RescueRequestCreate, commit: bool = True, geocode: bool = True):
        data_dict = data.model_dump()
        
        # Auto-transform logic - apply transforms for missing fields
        from app.services.transform_service import TransformService
        transform_service = TransformService()
        
        # 1. Parse posted_time if it's in text format (e.g., "1w", "2d")
        if data_dict.get("posted_time"):
            try:
                parsed_time = TransformService.parse_posted_time(data_dict["posted_time"])
                if parsed_time:
                    data_dict["posted_time"] = parsed_time.isoformat()
            except Exception as e:
                logger.warning(f"Failed to parse posted_time: {e}")
        
        # 2. Auto-generate title if not provided
        if not data_dict.get("title"):
            content = data_dict.get("content", "")
            location = data_dict.get("location", "")
            data_dict["title"] = TransformService.generate_title(content, location)
            logger.info(f"Auto-generated title: {data_dict['title']}")
        
        # 3. Geocode location if coordinate not provided
        coordinate_dict = data_dict.get("coordinate")
        if geocode and (not coordinate_dict or not coordinate_dict.get("coordinates")):
            location_text = data_dict.get("location", "")
            if location_text:
                try:
                    coords = transform_service.geocode_location(location_text)
                    if coords:
                        data_dict["coordinate"] = {"type": "Point", "coordinates": list(coords)}
                        logger.info(f"Geocoded location '{location_text}' to {coords}")
                except Exception as e:
                    logger.error(f"Geocoding failed for '{location_text}': {e}")
        
        # 4. Generate map link if coordinate exists
        if data_dict.get("coordinate") and data_dict["coordinate"].get("coordinates"):
            coords = data_dict["coordinate"]["coordinates"]
            if coords and len(coords) == 2:
                # coords is [lng, lat], pass as tuple
                data_dict["map_link"] = TransformService.generate_map_link((coords[0], coords[1]))
        
        # 5. Find region_id from location text if not provided
        if not data_dict.get("region_id") and data_dict.get("location"):
            try:
                region_id = TransformService.find_region_id(db, data_dict["location"])
                if region_id:
                    data_dict["region_id"] = region_id
                    logger.info(f"Found region_id {region_id} for location '{data_dict['location']}'")
            except Exception as e:
                logger.warning(f"Failed to find region_id: {e}")
        
        # 6. Parse needs text to IDs
        needs_text = data_dict.pop("needs_text", None)
        if needs_text:
            try:
                needs_ids_parsed = TransformService.parse_needs_text(db, needs_text)
                if needs_ids_parsed:
                    data_dict["needs_ids"] = needs_ids_parsed
                    logger.info(f"Parsed needs '{needs_text}' to IDs: {needs_ids_parsed}")
            except Exception as e:
                logger.warning(f"Failed to parse needs: {e}")
        
        # 7. Parse disaster type text to IDs
        disaster_type_text = data_dict.pop("disaster_type_text", None)
        if disaster_type_text:
            try:
                disaster_type_ids_parsed = TransformService.parse_disaster_type_text(db, disaster_type_text)
                if disaster_type_ids_parsed:
                    data_dict["disaster_type_ids"] = disaster_type_ids_parsed
                    logger.info(f"Parsed disaster_type '{disaster_type_text}' to IDs: {disaster_type_ids_parsed}")
            except Exception as e:
                logger.warning(f"Failed to parse disaster_type: {e}")
        
        # 8. Map score text to numeric values
        if data_dict.get("urgency_score") and isinstance(data_dict["urgency_score"], str):
            data_dict["urgency_score"] = TransformService.map_text_to_score(data_dict["urgency_score"])
        
        if data_dict.get("reliability_score") and isinstance(data_dict["reliability_score"], str):
            data_dict["reliability_score"] = TransformService.map_text_to_score(data_dict["reliability_score"])
        
        # Handle many-to-many relationships
        needs_ids = data_dict.pop("needs_ids", [])
        disaster_type_ids = data_dict.pop("disaster_type_ids", [])
        
        # Handle coordinate: convert to PostGIS geometry
        coordinate_data = data_dict.pop("coordinate", None)
        if coordinate_data and coordinate_data.get("coordinates"):
            coords = coordinate_data["coordinates"]
            if len(coords) == 2:
                data_dict["coordinate"] = func.ST_GeomFromText(f"POINT({coords[0]} {coords[1]})", 4326)
        
        # Create the rescue request
        new = RescueRequest(**data_dict)
        db.add(new)
        
        # Add many-to-many relationships
        if needs_ids:
            from app.models.needs_model import Needs
            needs = db.query(Needs).filter(Needs.id.in_(needs_ids)).all()
            new.needs = needs
        
        if disaster_type_ids:
            from app.models.disaster_type_model import DisasterType
            disaster_types = db.query(DisasterType).filter(DisasterType.id.in_(disaster_type_ids)).all()
            new.disaster_types = disaster_types
        
        if commit:
            db.commit()
            db.refresh(new)
        else:
            db.flush()
        return new

    @staticmethod
    def update(db: Session, request_id: int, data: RescueRequestUpdate):
        from app.schemas.review_schema import ReviewInput
        from app.services.request_management_service import review_request
        return review_request(db, request_id, ReviewInput.model_validate(data.model_dump(exclude_unset=True)))

    @staticmethod
    def delete(db: Session, request_id: int):
        item = db.query(RescueRequest).filter(RescueRequest.id == request_id).first()
        if not item:
            return None
        db.delete(item)
        db.commit()
        return item

    @staticmethod
    def get_nearby(
        db: Session,
        longitude: float,
        latitude: float,
        radius_km: float = 5.0,
        limit: int = 100
    ):
        """Find rescue requests within radius (km) of a point"""
        point = func.ST_SetSRID(func.ST_MakePoint(longitude, latitude), 4326)

        # Use geography for accurate distance in meters
        query = db.query(
            RescueRequest,
            func.ST_Distance(
                cast(RescueRequest.coordinate, Geography),
                cast(point, Geography)
            ).label('distance')
        ).filter(
            func.ST_DWithin(
                cast(RescueRequest.coordinate, Geography),
                cast(point, Geography),
                radius_km * 1000  # Convert km to meters
            )
        ).order_by('distance').limit(limit)

        # Return list of tuples (RescueRequest, distance_in_meters)
        return query.all()

    @staticmethod
    def get_by_region(db: Session, region_id: int, skip: int = 0, limit: int = 100):
        """Get all rescue requests in a specific region"""
        return db.query(RescueRequest).filter(
            RescueRequest.region_id == region_id
        ).order_by(desc(RescueRequest.created_date)).offset(skip).limit(limit).all()
