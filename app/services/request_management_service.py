"""Atomic human edits, model refresh and an append-only review history."""
from datetime import datetime, timezone
from sqlalchemy import func
from sqlalchemy.orm import selectinload
from ai.inference import EnsemblePredictor
from app.core.workflow import canonical_status, next_statuses
from app.models import RescueRequest, RescuePrediction, Needs, DisasterType, Region
from app.models.request_event_model import RequestEvent
from app.schemas.rescue_request_schema import RescueRequestOut
from app.services.location_service import resolve_location
from app.services.region_catalog import find_region
from app.services.transform_service import TransformService

AI_FIELDS = {"location", "contact", "affected_people", "infrastructure_damage", "is_isolated",
             "deathly", "has_emergency", "has_emotion", "has_emphasis", "needs_ids", "disaster_type_ids"}


def request_query(db):
    return db.query(RescueRequest).options(selectinload(RescueRequest.needs),
        selectinload(RescueRequest.disaster_types), selectinload(RescueRequest.prediction_result))


def review_request(db, request_id, payload):
    item = request_query(db).filter(RescueRequest.id == request_id).with_for_update().first()
    if item is None:
        return None
    values = payload.model_dump(exclude_unset=True)
    actor, note = payload.actor, payload.note
    values.pop("actor", None)
    values.pop("note", None)
    before = RescueRequestOut.model_validate(item).model_dump()
    old_status = canonical_status(item.status)
    target = values.get("status", old_status)
    if target != old_status and target not in next_statuses(old_status):
        raise ValueError("Chuyển trạng thái không hợp lệ. Hãy tải lại yêu cầu.")
    changes = {}
    for field, value in values.items():
        old = before.get(field)
        if field == "location":
            old = item.location
        if field == "map_link":
            old = (item.prediction or {}).get("source_map_link")
        if field in ("needs_ids", "disaster_type_ids"):
            relation, model = ("needs", Needs) if field == "needs_ids" else ("disaster_types", DisasterType)
            old = sorted(row.id for row in getattr(item, relation))
            value = sorted(set(value))
            rows = db.query(model).filter(model.id.in_(value)).all()
            if len(rows) != len(value):
                raise ValueError("Danh mục nhu cầu hoặc thiên tai không tồn tại")
            if old != value:
                setattr(item, relation, rows)
        else:
            if field == "region_id" and value is not None and db.get(Region, value) is None:
                raise ValueError("Khu vực không tồn tại")
            if field != "coordinate" and old != value:
                setattr(item, field, value)
        if old != value:
            changes[field] = {"before": old, "after": value}
    if not changes:
        return item
    details = dict(item.prediction or {})
    location_changed = bool({"location", "map_link"} & changes.keys())
    if "location" in changes and "region_id" not in values:
        old_region = item.region_id
        item.region_id = find_region(db, item.location)
        if old_region != item.region_id:
            changes["region_id"] = {"before": old_region, "after": item.region_id}
    if location_changed or "coordinate" in changes:
        if "coordinate" in values:
            coordinate = values["coordinate"]
            result = {"coordinate": coordinate, "coordinate_source": "manual" if coordinate else None,
                      "source_map_link": values.get("map_link", details.get("source_map_link")),
                      "geocoding": {"status": "located" if coordinate else "not_requested", "provider": "manual"}}
        else:
            # Never reuse an old generated map link or coordinates after an address edit.
            result = resolve_location({"location": item.location,
                "map_link": values.get("map_link"), "content": ""})
        coordinate = result["coordinate"]
        item.coordinate = (func.ST_SetSRID(func.ST_MakePoint(*coordinate["coordinates"]), 4326)
                           if coordinate else None)
        item.map_link = (TransformService.generate_map_link(tuple(coordinate["coordinates"]))
                         if coordinate else result["source_map_link"])
        details.update({key: result[key] for key in ("coordinate_source", "source_map_link", "geocoding")})
        old_message = (before.get("prediction") or {}).get("geocoding", {}).get("message")
        details["warnings"] = [warning for warning in details.get("warnings", []) if warning != old_message]
        details["warnings"].extend(warning for warning in result.get("warnings", []) if warning not in details["warnings"])
        details["location_status"] = "located" if coordinate else "unlocated"
        details["location_resolved_at"] = datetime.now(timezone.utc).isoformat()
        # Audit the action without keeping another permanent copy of provider coordinates.
        changes["coordinate"] = {"before": bool(before["coordinate"]), "after": bool(coordinate),
                                 "source": result["coordinate_source"]}
        changes.pop("map_link", None)
    if AI_FIELDS & changes.keys():
        details["warnings"] = [warning for warning in details.get("warnings", [])
                               if not warning.startswith("Chưa rõ số người bị ảnh hưởng")]
        if item.affected_people is None:
            details["warnings"].append("Chưa rõ số người bị ảnh hưởng; mô hình dùng giá trị thiếu theo cấu hình huấn luyện.")
        row = {key: getattr(item, key) for key in AI_FIELDS - {"needs_ids", "disaster_type_ids"}}
        row.update(content=item.content or item.title, needs=[r.name for r in item.needs],
                   disaster_type=[r.name for r in item.disaster_types], reactions=item.reactions or 0,
                   replies=item.replies or 0)
        prediction = EnsemblePredictor().predict([row])[0]
        details.update({key: value for key, value in prediction.items() if key != "record"})
        details.update(source="ensemble", method=prediction.get("method", "highest_probability"), predicted_at=datetime.now(timezone.utc).isoformat())
        item.urgency_score = prediction["urgency_score"]
        item.reliability_score = prediction["reliability_score"]
        changes["ai"] = {"recalculated": True, "urgency_score": item.urgency_score,
                         "reliability_score": item.reliability_score}
    if details:
        if item.prediction_result is None:
            item.prediction_result = RescuePrediction(details=details)
        else:
            item.prediction_result.details = details
    db.add(RequestEvent(rescue_request_id=item.id, actor=actor, note=note, changes=changes))
    db.commit()
    db.refresh(item)
    return item


def quality_summary(db):
    counts = {"total": 0, "located": 0, "missing_coordinates": 0, "missing_address": 0,
              "missing_region": 0, "missing_prediction": 0, "missing_posted_time": 0,
              "statuses": {}, "urgencies": {"high": 0, "medium": 0, "low": 0, "unknown": 0}}
    for item in request_query(db).all():
        row = RescueRequestOut.model_validate(item)
        counts["total"] += 1
        counts["located" if row.coordinate else "missing_coordinates"] += 1
        address = (row.location or "").strip()
        counts["missing_address"] += int(not address or address.startswith(("http://", "https://")))
        counts["missing_region"] += int(row.region_id is None)
        counts["missing_prediction"] += int(not (row.prediction or {}).get("models"))
        counts["missing_posted_time"] += int(not row.posted_time)
        counts["statuses"][row.status] = counts["statuses"].get(row.status, 0) + 1
        score = row.urgency_score or 0
        urgency = ("unknown" if score <= 0 else ("high" if score >= 3 else "medium" if score >= 2 else "low")) if score <= 3 else ("high" if score >= 6 else "medium" if score >= 4 else "low")
        counts["urgencies"][urgency] += 1
    return counts
