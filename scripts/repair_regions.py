"""Preview or fill only missing region IDs from explicit source addresses."""
import argparse
import json
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.db.database import SessionLocal
from app.models import RescueRequest
from app.models.request_event_model import RequestEvent
from app.services.region_catalog import ensure_catalog, find_region


def repair(db, apply=False):
    ensure_catalog(db)
    changes = []
    for item in db.query(RescueRequest).filter(RescueRequest.region_id.is_(None)).all():
        region_id = find_region(db, item.location)
        if region_id:
            changes.append({"id": item.id, "region_id": region_id})
            if apply:
                item.region_id = region_id
                db.add(RequestEvent(rescue_request_id=item.id, actor="repair_regions", note="Bổ sung khu vực từ tên tỉnh/thành ghi trong địa chỉ nguồn.",
                    changes={"region_id": {"before": None, "after": region_id}}))
    if apply:
        db.commit()
    else:
        db.rollback()
    return {"mode": "apply" if apply else "dry_run", "matched": len(changes), "changes": changes}


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args()
    with SessionLocal() as db:
        print(json.dumps(repair(db, args.apply), ensure_ascii=False))
