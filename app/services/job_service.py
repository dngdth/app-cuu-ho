"""PostgreSQL work queue with leases, transactional cursors and bounded retry."""
import asyncio
import logging
import uuid
from datetime import datetime, timedelta, timezone
from sqlalchemy import and_, or_, select
from app.db.database import SessionLocal
from app.models.operations_model import ProcessingJob, User
from app.models.rescue_request_model import RescueRequest
from app.services.processing_service import ProcessingService
from app.services.geocode_maintenance import geocode_pending

logger = logging.getLogger(__name__)
LEASE_SECONDS = 180


def utcnow():
    return datetime.now(timezone.utc)


def public_job(job):
    return {key: getattr(job, key) for key in ("id", "kind", "owner_id", "status", "progress", "total", "report", "error", "attempts", "created_at", "updated_at")}


def enqueue(db, kind, payload, owner_id):
    if db.query(ProcessingJob).filter(ProcessingJob.owner_id == owner_id,
            ProcessingJob.status.in_(("queued", "running"))).count() >= 3:
        raise ValueError("Mỗi tài khoản chỉ được có tối đa 3 tác vụ đang chờ/chạy")
    total = len(payload["records"] if kind == "import" else payload["ids"])
    job = ProcessingJob(id=str(uuid.uuid4()), kind=kind, payload=payload, owner_id=owner_id, total=total,
        status="queued", report={"created": 0, "duplicates": 0, "failed": 0, "located": 0, "unlocated": 0, "results": []})
    db.add(job)
    db.commit()
    return job


def claim(db, worker_id):
    now = utcnow()
    job = db.execute(select(ProcessingJob).where(or_(
        and_(ProcessingJob.status == "queued", or_(ProcessingJob.lease_until.is_(None), ProcessingJob.lease_until <= now)),
        and_(ProcessingJob.status == "running", ProcessingJob.lease_until <= now)
    )).order_by(ProcessingJob.created_at).with_for_update(skip_locked=True).limit(1)).scalar_one_or_none()
    if not job:
        return None
    if job.attempts >= 3:
        job.status, job.error = "failed", "Tác vụ đã vượt số lần thử lại; hãy kiểm tra cấu hình rồi thử lại."
        db.commit()
        return None
    job.status, job.worker_id = "running", worker_id
    job.attempts += 1
    job.lease_until = now + timedelta(seconds=LEASE_SECONDS)
    job.updated_at = now
    db.commit()
    return job.id


def run_step(db, job_id, worker_id):
    job = db.execute(select(ProcessingJob).where(ProcessingJob.id == job_id).with_for_update()).scalar_one_or_none()
    if not job or job.status != "running" or job.worker_id != worker_id:
        return False
    owner = db.get(User, job.owner_id)
    if not owner or not owner.active or owner.role not in ("operator", "admin"):
        job.status, job.payload = "cancelled", {}
        db.commit()
        return False
    if job.progress >= job.total:
        job.status, job.updated_at = "completed", utcnow()
        job.payload = {}  # Do not retain another raw source copy after completion.
        db.commit()
        return False
    report = dict(job.report)
    if job.kind == "import":
        result = ProcessingService.process(db, [job.payload["records"][job.progress]],
            collected_at=job.payload.get("collected_at"), geocode=job.payload.get("geocode", True), commit=False)
        for key in ("created", "duplicates", "failed", "located", "unlocated"):
            report[key] = report.get(key, 0) + result[key]
        row = result["results"][0]
        report["results"] = (report.get("results", []) + [{"row": job.progress + 1, "id": row.get("id"), "status": row["status"],
            "error": str(row["error"])[:500] if row.get("error") else None}])[-100:]
    elif job.kind == "geocode":
        result = geocode_pending(db, limit=1, ids=[job.payload["ids"][job.progress]], commit=False)
        status = result.get("status")
        row = (result.get("results") or [{}])[0]
        if status in ("disabled", "needs_api_key") or row.get("status") in ("quota_exceeded", "provider_error"):
            job.status = "blocked"
            job.error = result.get("message") or "Chưa định vị được do key, kết nối hoặc hạn mức. Kiểm tra cấu hình rồi thử lại."
            job.updated_at = utcnow()
            db.commit()
            return False
        report["located"] += result["updated"]
        report["unlocated"] += result["unresolved"]
        report["suggested"] = report.get("suggested", 0) + int(bool(row.get("has_suggestion")))
        report["results"] = (report.get("results", []) + [{"id": job.payload["ids"][job.progress], "status": row.get("status", "already_located")}])[-100:]
    else:
        raise ValueError("Unknown job kind")
    job.progress += 1
    job.report, job.updated_at = report, utcnow()
    job.lease_until = utcnow() + timedelta(seconds=LEASE_SECONDS)
    # ProcessingService uses flush, so source rows and this cursor commit together.
    db.commit()
    return True


def fail_job(db, job_id, worker_id):
    job = db.execute(select(ProcessingJob).where(ProcessingJob.id == job_id).with_for_update()).scalar_one_or_none()
    if job and job.status == "running" and job.worker_id == worker_id:
        job.status = "queued" if job.attempts < 3 else "failed"
        job.error = "Không xử lý được bản ghi; dữ liệu của bước lỗi đã rollback. Kiểm tra nội dung hoặc log backend."
        job.lease_until = utcnow() + timedelta(seconds=2 ** job.attempts)
        job.worker_id, job.updated_at = None, utcnow()
        db.commit()


async def worker_loop(session_factory=SessionLocal):
    worker_id = str(uuid.uuid4())
    def get_job():
        with session_factory() as db:
            return claim(db, worker_id)
    def step(job_id):
        with session_factory() as db:
            return run_step(db, job_id, worker_id)
    while True:
        try:
            job_id = await asyncio.to_thread(get_job)
            if job_id:
                try:
                    while await asyncio.to_thread(step, job_id):
                        await asyncio.sleep(0.6)
                except Exception:
                    logger.exception("Job step failed: %s", job_id)
                    with session_factory() as db:
                        fail_job(db, job_id, worker_id)
        except asyncio.CancelledError:
            raise
        except Exception:
            logger.exception("Worker unavailable")
        await asyncio.sleep(1)
