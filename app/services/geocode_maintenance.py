"""Refresh missing positions and remove expired, API-derived Google content."""
from datetime import datetime, timezone
from sqlalchemy import func

from app.models.rescue_request_model import RescueRequest
from app.models.prediction_model import RescuePrediction
from app.services.location_service import resolve_location


def expired_geocode(details, now=None):
    geocoding = (details or {}).get("geocoding") or {}
    if geocoding.get("provider") not in ("google", "geoapify") or not geocoding.get("expires_at"):
        return False
    try:
        expiry = datetime.fromisoformat(geocoding["expires_at"].replace("Z", "+00:00"))
        if expiry.tzinfo is None:
            expiry = expiry.replace(tzinfo=timezone.utc)
        return expiry <= (now or datetime.now(timezone.utc))
    except (ValueError, TypeError):
        return True


def expired_details(details):
    old = (details or {}).get("geocoding") or {}
    return {**details, "location_status": "unlocated", "coordinate_source": None,
            "geocoding": {"provider": old.get("provider", "geoapify"), "status": "expired", "place_id": old.get("place_id"),
                          "message": "Vị trí từ dịch vụ bản đồ đã hết hạn lưu tạm; cần tra cứu lại."}}


def purge_expired_geocodes(db):
    count = 0
    for item in db.query(RescueRequest).join(RescueRequest.prediction_result).all():
        if expired_geocode(item.prediction):
            item.coordinate = None
            item.map_link = item.prediction.get("source_map_link")
            item.prediction_result.details = expired_details(item.prediction)
            count += 1
    if count:
        db.commit()
    return count


def geocode_pending(db, limit=20, ids=None, dry_run=False, commit=True):
    from app.services.geocode_service import GeocodeService
    if not GeocodeService().configured:
        return {"status": "needs_api_key", "checked": 0, "updated": 0, "unresolved": 0,
                "message": "Chưa cấu hình GEOAPIFY_API_KEY; chưa gọi API hoặc thay đổi dữ liệu."}
    if not GeocodeService().enabled:
        return {"status": "disabled", "checked": 0, "updated": 0, "unresolved": 0,
                "message": "Đang tắt dịch vụ định vị; chưa gọi API hoặc thay đổi dữ liệu."}
    if not dry_run and commit:
        purge_expired_geocodes(db)
    query = db.query(RescueRequest).outerjoin(RescueRequest.prediction_result).filter(RescueRequest.coordinate.is_(None)).order_by(
        RescuePrediction.details["geocoding"]["attempted_at"].as_string().asc().nullsfirst(), RescueRequest.id)
    if ids:
        query = query.filter(RescueRequest.id.in_(ids))
    items = query.limit(limit).all()
    report = {"status": "completed", "checked": 0, "updated": 0, "unresolved": 0, "dry_run": dry_run, "results": []}
    for item in items:
        location = resolve_location({"content": item.content, "location": item.location, "map_link": item.map_link})
        report["checked"] += 1
        report["updated" if location["coordinate"] else "unresolved"] += 1
        report["results"].append({"id": item.id, "status": location["geocoding"]["status"],
                                  "message": location["geocoding"].get("message"),
                                  "error_code": location["geocoding"].get("error_code"),
                                  "precision": location["geocoding"].get("precision"),
                                  "has_suggestion": bool(location["geocoding"].get("suggestions"))})
        if dry_run:
            continue
        if location["coordinate"]:
            lng, lat = location["coordinate"]["coordinates"]
            item.coordinate = func.ST_SetSRID(func.ST_MakePoint(lng, lat), 4326)
            item.map_link = f"https://maps.google.com/?q={lat},{lng}"
        if item.prediction_result:
            details = dict(item.prediction)
            old_location_message = (details.get("geocoding") or {}).get("message")
            warnings = [warning for warning in details.get("warnings", [])
                        if warning != old_location_message and not warning.startswith(("Chưa xác định được tọa độ", "Chờ cấu hình Google", "Chưa yêu cầu tìm tọa độ"))]
            details.update({key: value for key, value in location.items() if key not in ("coordinate", "warnings")})
            details.update(warnings=warnings + location["warnings"],
                           location_status="located" if location["coordinate"] else "unlocated")
            item.prediction_result.details = details
        if commit:
            db.commit()
        else:
            db.flush()
    return report
