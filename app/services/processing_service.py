"""Source -> model prediction -> geocoding -> atomic persistence per request."""
import json
import re
from datetime import datetime, timedelta, timezone

from ai.features import normalize_record, nullable
from ai.inference import EnsemblePredictor
from app.models.rescue_request_model import RescueRequest
from app.models.prediction_model import RescuePrediction
from app.models.needs_model import Needs
from app.models.disaster_type_model import DisasterType
from app.repositories.rescue_request_repository import RescueRequestRepository
from app.schemas.rescue_request_schema import RescueRequestCreate
from app.services.transform_service import TransformService
from app.services.google_maps_service import GoogleMapsService, map_links
from app.services.location_service import resolve_location, coordinate_in_text
from sqlalchemy import func, select


def content_key(text):
    return re.sub(r"\s+", " ", text).strip().casefold()


def posted_datetime(value, collected_at=None):
    if not value:
        return None
    value = str(value).strip()
    relative = re.fullmatch(r"(\d+)([wdhm])", value)
    if relative:
        if collected_at is None:
            return None
        reference = datetime.fromisoformat(str(collected_at).replace("Z", "+00:00"))
        units = {"w": "weeks", "d": "days", "h": "hours", "m": "minutes"}
        return (reference - timedelta(**{units[relative[2]]: int(relative[1])})).isoformat()
    return datetime.fromisoformat(value.replace("Z", "+00:00")).isoformat()


class ProcessingService:
    @staticmethod
    def process(db, records, collected_at=None, geocode=True, commit=True):
        result = {"total": len(records), "created": 0, "duplicates": 0, "failed": 0,
                  "located": 0, "unlocated": 0, "results": []}
        existing = {content_key(content): id_ for id_, content in
                    db.query(RescueRequest.id, RescueRequest.content).all() if content}
        pending = []
        seen = set()
        for index, record in enumerate(records, 1):
            try:
                row = normalize_record(record)
                if not row["needs"] and row.get("needs_ids"):
                    row["needs"] = [item.name for item in db.query(Needs).filter(Needs.id.in_(row["needs_ids"])).all()]
                if not row["disaster_type"] and row.get("disaster_type_ids"):
                    row["disaster_type"] = [item.name for item in db.query(DisasterType).filter(DisasterType.id.in_(row["disaster_type_ids"])).all()]
                key = content_key(row["content"])
                if key in existing or key in seen:
                    result["duplicates"] += 1
                    result["results"].append({"row": index, "status": "duplicate", "id": existing.get(key)})
                    continue
                row["original_posted_time"] = row.get("posted_time")
                row["posted_time"] = posted_datetime(row.get("posted_time"), collected_at)
                if row.get("coordinate") is not None:
                    coordinate = json.loads(row["coordinate"]) if isinstance(row["coordinate"], str) else row["coordinate"]
                    row["coordinate"] = ProcessingService.valid_coordinate(coordinate)
                pending.append((index, row))
                seen.add(key)
            except (ValueError, TypeError, SyntaxError) as exc:
                result["failed"] += 1
                result["results"].append({"row": index, "status": "error", "error": str(exc)})
        predictions = EnsemblePredictor().predict([row for _, row in pending])
        for (index, row), prediction in zip(pending, predictions, strict=True):
            try:
                # Recheck under a namespaced transaction lock: separate jobs/API
                # workers may have normalized the same new post concurrently.
                key = content_key(row["content"])
                db.execute(select(func.pg_advisory_xact_lock(1414, func.hashtext(key))))
                duplicate = next((id_ for id_, content in db.query(RescueRequest.id, RescueRequest.content).all()
                                  if content and content_key(content) == key), None)
                if duplicate is not None:
                    result["duplicates"] += 1
                    result["results"].append({"row": index, "status": "duplicate", "id": duplicate})
                    if commit:
                        db.commit()
                    continue
                warnings = []
                if row.get("original_posted_time") and not row["posted_time"]:
                    warnings.append("Thời gian đăng tương đối chưa có ngày thu thập; chưa xác định ngày đăng.")
                if row["affected_people"] is None:
                    warnings.append("Chưa rõ số người bị ảnh hưởng; mô hình dùng giá trị thiếu theo cấu hình huấn luyện.")
                data = {key: row[key] for key in RescueRequestCreate.model_fields
                        if key in row and nullable(row[key]) is not None}
                data.update(urgency_score=prediction["urgency_score"],
                            reliability_score=prediction["reliability_score"],
                            status="unverified", posted_time=row["posted_time"])
                data["needs_ids"] = ProcessingService.catalog_ids(db, Needs, row["needs"])
                data["disaster_type_ids"] = ProcessingService.catalog_ids(db, DisasterType, row["disaster_type"])
                data.pop("needs_text", None)
                data.pop("disaster_type_text", None)
                location_result = resolve_location(row, network=geocode)
                coordinate = location_result["coordinate"]
                warnings.extend(location_result["warnings"])
                data["coordinate"] = coordinate
                item = RescueRequestRepository.create(db, RescueRequestCreate(**data), commit=False, geocode=False)
                details = {key: value for key, value in prediction.items() if key != "record"}
                details.update(method=prediction.get("method", "highest_probability"), source="ensemble",
                               predicted_at=datetime.now(timezone.utc).isoformat(),
                               original_posted_time=row.get("original_posted_time"),
                               collected_at=str(collected_at) if collected_at else None,
                               warnings=warnings, location_status="located" if coordinate else "unlocated",
                               coordinate_source=location_result["coordinate_source"],
                               source_map_link=location_result["source_map_link"], geocoding=location_result["geocoding"])
                details.update(source_url=row.get("source_url"), extraction_source=row.get("extraction_source", "structured"),
                               extraction_review_required=bool(row.get("extraction_review_required") or row.get("location_extracted")))
                db.add(RescuePrediction(rescue_request_id=item.id, details=details))
                if commit:
                    db.commit()
                else:
                    db.flush()
                result["created"] += 1
                result["located" if coordinate else "unlocated"] += 1
                result["results"].append({"row": index, "status": "created", "id": item.id, "prediction": details})
            except Exception as exc:
                db.rollback()
                if not commit:
                    raise
                result["failed"] += 1
                result["results"].append({"row": index, "status": "error", "error": str(exc)})
        result["results"].sort(key=lambda item: item["row"])
        return result

    @staticmethod
    def valid_coordinate(value):
        if not isinstance(value, dict) or value.get("type", "Point") != "Point":
            raise ValueError("coordinate must be a GeoJSON Point")
        coords = value.get("coordinates", [])
        if not isinstance(coords, (list, tuple)) or len(coords) != 2 or any(isinstance(v, bool) for v in coords):
            raise ValueError("coordinate must contain [longitude, latitude]")
        lng, lat = map(float, coords)
        if not (-180 <= lng <= 180 and -90 <= lat <= 90):
            raise ValueError("coordinate is outside valid longitude/latitude ranges")
        return {"type": "Point", "coordinates": [lng, lat]}

    @staticmethod
    def coordinate_in_text(*texts):
        return coordinate_in_text(*texts)

    @staticmethod
    def catalog_ids(db, model, names):
        ids = []
        for name in dict.fromkeys(names):
            name = name.strip().lower()
            if not name:
                continue
            item = db.query(model).filter(model.name.ilike(name)).first()
            if item is None:
                item = model(name=name)
                db.add(item)
                db.flush()
            ids.append(item.id)
        return ids

    @staticmethod
    def resolve_existing_map_links(db, limit=None):
        """Fill missing coordinates only; preserve saved model predictions and IDs."""
        candidates = db.query(RescueRequest).filter(RescueRequest.coordinate.is_(None)).all()
        result = {"with_links": 0, "updated": 0, "unresolved": 0, "failed": 0}
        for item in candidates:
            links = list(map_links(item.map_link, item.location, item.content))
            if not links:
                continue
            if limit is not None and result["with_links"] >= limit:
                break
            result["with_links"] += 1
            resolved = GoogleMapsService.resolve_record(*links)
            if not resolved:
                result["unresolved"] += 1
                continue
            try:
                lng, lat = resolved["coordinate"]["coordinates"]
                item.coordinate = func.ST_SetSRID(func.ST_MakePoint(lng, lat), 4326)
                item.map_link = TransformService.generate_map_link((lng, lat))
                if item.prediction_result:
                    details = dict(item.prediction_result.details)
                    details.update(location_status="located", coordinate_source="google_maps",
                                   source_map_link=resolved["source_url"],
                                   geocoding={"status": "located", "provider": "google_maps", "precision": "SOURCE_POINT"},
                                   location_resolved_at=datetime.now(timezone.utc).isoformat())
                    details["warnings"] = [warning for warning in details.get("warnings", [])
                                           if not warning.startswith("Chưa xác định được tọa độ")]
                    item.prediction_result.details = details
                db.commit()
                result["updated"] += 1
            except Exception:
                db.rollback()
                result["failed"] += 1
        return result
