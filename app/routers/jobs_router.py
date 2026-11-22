import json
from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.orm import Session
from app.core.security import current_user
from app.dependencies import get_db
from app.models.operations_model import ProcessingJob
from app.models.rescue_request_model import RescueRequest
from app.models.prediction_model import RescuePrediction
from app.routers.processing_router import ProcessingInput, GeocodePendingInput
from app.services.job_service import enqueue, public_job, utcnow

router = APIRouter(prefix="/jobs", tags=["background jobs"])


def owned(db, id_, user, lock=False):
    query = select(ProcessingJob).where(ProcessingJob.id == id_)
    job = db.execute(query.with_for_update() if lock else query).scalar_one_or_none()
    if not job or (job.owner_id != user["id"] and user["role"] != "admin"):
        raise HTTPException(404, "Không tìm thấy tác vụ")
    return job


@router.get("")
def list_jobs(request: Request, db: Session = Depends(get_db)):
    user = current_user(request)
    query = db.query(ProcessingJob)
    if user["role"] != "admin":
        query = query.filter(ProcessingJob.owner_id == user["id"])
    return [public_job(job) for job in query.order_by(ProcessingJob.created_at.desc()).limit(30)]


@router.post("/import", status_code=202)
def queue_import(data: ProcessingInput, request: Request, db: Session = Depends(get_db)):
    user = current_user(request)
    payload = data.model_dump(mode="json")
    if len(json.dumps(payload).encode()) > 3 * 1024 * 1024:
        raise HTTPException(413, "Mỗi tác vụ tối đa 3 MB")
    try:
        return public_job(enqueue(db, "import", payload, user["id"]))
    except ValueError as exc:
        raise HTTPException(429, str(exc)) from exc


class GeocodeJobInput(GeocodePendingInput):
    region_id: int | None = Field(default=None, ge=1)


@router.post("/geocode", status_code=202)
def queue_geocode(data: GeocodeJobInput, request: Request, db: Session = Depends(get_db)):
    if data.dry_run:
        raise HTTPException(422, "Dùng /processing/geocode-pending với dry_run để xem trước; tác vụ nền dùng dry_run=false")
    from app.services.geocode_service import GeocodeService
    service = GeocodeService()
    if not service.configured or not service.enabled:
        raise HTTPException(503, "Chưa cấu hình Geoapify key hoặc định vị đang tắt")
    query = db.query(RescueRequest.id).outerjoin(RescueRequest.prediction_result).filter(RescueRequest.coordinate.is_(None))
    if data.region_id is not None:
        query = query.filter(RescueRequest.region_id == data.region_id)
    if data.ids:
        query = query.filter(RescueRequest.id.in_(data.ids))
    ids = [row.id for row in query.order_by(
        RescuePrediction.details["geocoding"]["attempted_at"].as_string().asc().nullsfirst(),
        RescueRequest.id).limit(data.limit)]
    if not ids:
        raise HTTPException(404, "Không còn yêu cầu chưa có tọa độ trong khu vực đã chọn.")
    try:
        return public_job(enqueue(db, "geocode", {"ids": ids}, current_user(request)["id"]))
    except ValueError as exc:
        raise HTTPException(429, str(exc)) from exc


@router.get("/{job_id}")
def get_job(job_id: str, request: Request, db: Session = Depends(get_db)):
    return public_job(owned(db, job_id, current_user(request)))


@router.post("/{job_id}/cancel")
def cancel(job_id: str, request: Request, db: Session = Depends(get_db)):
    job = owned(db, job_id, current_user(request), lock=True)
    if job.status in ("queued", "running", "blocked"):
        job.status, job.updated_at = "cancelled", utcnow()
        job.payload = {}
        db.commit()
    return public_job(job)


@router.post("/{job_id}/retry")
def retry(job_id: str, request: Request, db: Session = Depends(get_db)):
    job = owned(db, job_id, current_user(request), lock=True)
    if job.status not in ("failed", "blocked"):
        raise HTTPException(422, "Chỉ thử lại tác vụ lỗi hoặc đang bị chặn")
    job.status, job.error, job.worker_id, job.lease_until, job.attempts = "queued", None, None, None, 0
    job.updated_at = utcnow()
    db.commit()
    return public_job(job)
