if __name__ == "__main__":
    import socket

    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        probe.settimeout(1)
        if probe.connect_ex(("127.0.0.1", 8099)) == 0:
            raise SystemExit("Port 8099 is already in use. Stop the other backend before starting this project.")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import rescue_request_router, needs_router, disaster_type_router, region_router, geocode_router
from app.routers import processing_router, operations_router, auth_router, jobs_router
from app.db.database import Base, engine
import uvicorn
import logging
import asyncio
from contextlib import asynccontextmanager, suppress
from app.db.database import SessionLocal
from app.services.geocode_maintenance import purge_expired_geocodes
from app.core.security import AccessMiddleware, bootstrap_admin
from app.services.job_service import worker_loop
from app.core.config import ALLOWED_ORIGINS
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

def cleanup_geocoding():
    with SessionLocal() as db:
        purge_expired_geocodes(db)
        from datetime import datetime, timedelta, timezone
        import time
        from app.models.operations_model import ProviderCache, UserSession, LoginThrottle, ApiCounter, ProcessingJob
        now = datetime.now(timezone.utc)
        db.query(ProviderCache).filter(ProviderCache.expires_at < now).delete()
        db.query(UserSession).filter(UserSession.expires_at < now).delete()
        db.query(LoginThrottle).filter(LoginThrottle.window_start < now - timedelta(days=1)).delete()
        db.query(ApiCounter).filter(ApiCounter.period == "second", ApiCounter.period_key < str(int(time.time()) - 86400)).delete()
        db.query(ProcessingJob).filter(ProcessingJob.status.in_(("completed", "failed", "cancelled")),
                                      ProcessingJob.updated_at < now - timedelta(days=7)).delete(synchronize_session=False)
        db.commit()


async def cleanup_loop():
    while True:
        try:
            await asyncio.to_thread(cleanup_geocoding)
        except Exception:
            logging.exception("Could not clean expired Google geocoding data")
        await asyncio.sleep(3600)


@asynccontextmanager
async def lifespan(app):
    from app.services.region_catalog import ensure_catalog
    with SessionLocal() as db:
        ensure_catalog(db)
        bootstrap_admin(db)
        db.commit()
    cleanup_task = asyncio.create_task(cleanup_loop())
    worker_task = asyncio.create_task(worker_loop())
    yield
    cleanup_task.cancel()
    worker_task.cancel()
    with suppress(asyncio.CancelledError):
        await cleanup_task
    with suppress(asyncio.CancelledError):
        await worker_task


app = FastAPI(lifespan=lifespan)
app.add_middleware(AccessMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

Base.metadata.create_all(bind=engine)
app.include_router(rescue_request_router.router)
app.include_router(needs_router.router)
app.include_router(disaster_type_router.router)
app.include_router(region_router.router)
app.include_router(geocode_router.router)
app.include_router(processing_router.router)
app.include_router(operations_router.router)
app.include_router(auth_router.router)
app.include_router(jobs_router.router)


@app.exception_handler(RequestValidationError)
async def validation_error(request, exc):
    # Do not echo submitted passwords, source posts or other input values.
    return JSONResponse(status_code=422, content={"detail": [
        {"loc": list(error["loc"]), "msg": error["msg"], "type": error["type"]} for error in exc.errors()]})


@app.get("/ready")
def readiness():
    from sqlalchemy import text
    from pathlib import Path
    from ai.inference import EnsemblePredictor, MODEL_FILES
    try:
        with SessionLocal() as db:
            db.execute(text("SELECT 1"))
        directory = EnsemblePredictor().model_dir
        missing = [name for name, file in MODEL_FILES.items() if not (Path(directory) / file).is_file()]
        if missing:
            return JSONResponse({"ready": False, "database": True, "models": False}, 503)
        return {"ready": True, "database": True, "models": True}
    except Exception:
        return JSONResponse({"ready": False}, 503)
@app.get("/")
def read_root():
    return {"message": "Welcome to the FastAPI app!"}

@app.get("/health")
def health_check():
    """Health check endpoint for monitoring"""
    return {"status": "healthy"}

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8099)
