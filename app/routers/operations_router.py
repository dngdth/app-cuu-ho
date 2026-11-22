from fastapi import APIRouter, Depends, HTTPException, Request
from sqlalchemy.orm import Session
from app.dependencies import get_db
from app.models.request_event_model import RequestEvent
from app.models.rescue_request_model import RescueRequest
from app.schemas.review_schema import ReviewInput
from app.schemas.rescue_request_schema import RescueRequestOut
from app.services.request_management_service import quality_summary, review_request
from fastapi.responses import FileResponse, Response
from pathlib import Path
import csv
import io
import json
from ai.inference import EnsemblePredictor

router = APIRouter(prefix="/operations", tags=["operations"])


@router.get("/summary")
def summary(db: Session = Depends(get_db)):
    return quality_summary(db)


@router.get("/model-report")
def model_report():
    path = EnsemblePredictor().model_dir / "evaluation.json"
    if not path.is_file():
        raise HTTPException(404, "Bộ model hiện tại chưa có báo cáo holdout; chạy scripts/train_evaluate.py trước")
    report = json.loads(path.read_text(encoding="utf-8"))
    report["split"].pop("test_group_hashes", None)
    return report


@router.get("/model-figure/{target}")
def model_figure(target: str):
    if target not in ("urgency", "reliability"):
        raise HTTPException(404, "Không có biểu đồ")
    path = EnsemblePredictor().model_dir / f"{target}_evaluation.png"
    if not path.is_file():
        raise HTTPException(404, "Chưa tạo biểu đồ đánh giá")
    return FileResponse(path, media_type="image/png")


@router.get("/export")
def export_csv(db: Session = Depends(get_db)):
    from app.services.request_management_service import request_query
    stream = io.StringIO()
    writer = csv.writer(stream)
    fields = ["id", "title", "content", "location", "contact", "status", "urgency_score", "reliability_score", "posted_time", "longitude", "latitude"]
    writer.writerow(fields)
    def safe(value):
        text = "" if value is None else str(value)
        return "'" + text if text.lstrip().startswith(("=", "+", "-", "@", "\t", "\r")) else text
    for item in request_query(db).order_by(RescueRequest.id):
        row = RescueRequestOut.model_validate(item)
        point = (row.coordinate or {}).get("coordinates", [None, None])
        values = row.model_dump()
        values.update(longitude=point[0], latitude=point[1])
        writer.writerow([safe(values.get(field)) for field in fields])
    return Response("\ufeff" + stream.getvalue(), media_type="text/csv; charset=utf-8",
                    headers={"Content-Disposition": 'attachment; filename="rescue-requests.csv"'})


@router.get("/requests/{request_id}/events")
def events(request_id: int, db: Session = Depends(get_db)):
    if db.get(RescueRequest, request_id) is None:
        raise HTTPException(404, "Không tìm thấy yêu cầu")
    rows = db.query(RequestEvent).filter(RequestEvent.rescue_request_id == request_id).order_by(RequestEvent.id.desc()).limit(200).all()
    return [{"id": r.id, "created_at": r.created_at, "actor": r.actor, "note": r.note, "changes": r.changes} for r in rows]


@router.patch("/requests/{request_id}/review", response_model=RescueRequestOut)
def review(request_id: int, data: ReviewInput, request: Request, db: Session = Depends(get_db)):
    try:
        user = getattr(request.state, "user", None)
        if user:
            data = data.model_copy(update={"actor": f"{user['name']} ({user['email']})"})
        item = review_request(db, request_id, data)
        if item is None:
            raise HTTPException(404, "Không tìm thấy yêu cầu")
        return item
    except ValueError as exc:
        db.rollback()
        raise HTTPException(422, str(exc)) from exc
    except (FileNotFoundError, RuntimeError) as exc:
        db.rollback()
        raise HTTPException(503, "Chưa thể chạy mô hình. Thay đổi chưa được lưu.") from exc
    except Exception:
        db.rollback()
        raise
