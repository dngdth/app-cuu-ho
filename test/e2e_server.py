"""Real API/worker for browser tests in a NEW isolated PostgreSQL schema."""
import asyncio
import hashlib
import json
import re
import sys
import uuid
from contextlib import asynccontextmanager, suppress
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from fastapi import FastAPI
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.core.config import DATABASE_URL
from app.core.security import AccessMiddleware, hash_password
from app.db.database import Base
from app.dependencies import get_db
from app.models.operations_model import User
from app.routers import auth_router, jobs_router, operations_router, processing_router, rescue_request_router, needs_router, region_router, disaster_type_router, geocode_router
from app.services.job_service import worker_loop
from app.services.processing_service import ProcessingService
from app.services.region_catalog import ensure_catalog

MARKER = Path(__file__).resolve().parents[1] / ".e2e-schema"


def cleanup():
    if not MARKER.exists():
        return
    data = json.loads(MARKER.read_text())
    schema = data["schema"]
    if not re.fullmatch(r"e2e_[a-f0-9]{32}", schema) or data["database_fingerprint"] != hashlib.sha256(DATABASE_URL.encode()).hexdigest():
        raise RuntimeError("Refusing to clean an unverified test schema")
    engine = create_engine(DATABASE_URL)
    with engine.begin() as db:
        db.execute(text(f'DROP SCHEMA IF EXISTS "{schema}" CASCADE'))
    engine.dispose()
    MARKER.unlink()
    print("Removed isolated E2E schema; public data untouched")


if __name__ == "__main__" and "--cleanup" in sys.argv:
    cleanup()
    raise SystemExit(0)

schema = "e2e_" + uuid.uuid4().hex
with MARKER.open("x") as marker:
    json.dump({"schema": schema, "database_fingerprint": hashlib.sha256(DATABASE_URL.encode()).hexdigest()}, marker)
engine = create_engine(DATABASE_URL, connect_args={"options": f"-csearch_path={schema},public"}).execution_options(schema_translate_map={None: schema})
with engine.begin() as db:
    db.execute(text(f'CREATE SCHEMA "{schema}"'))
Base.metadata.create_all(engine)
Factory = sessionmaker(bind=engine, autoflush=False)
with Factory() as db:
    ensure_catalog(db)
    db.add(User(email="e2e@example.test", name="E2E Operator", role="admin", password_hash=hash_password("E2E-only-password-2026")))
    db.commit()
    ProcessingService.process(db, [{"content": "Điểm demo E2E", "location": "Huế", "affected_people": 3,
        "coordinate": {"type": "Point", "coordinates": [107.58, 16.46]}}], geocode=False)


@asynccontextmanager
async def lifespan(app):
    worker = asyncio.create_task(worker_loop(Factory))
    yield
    worker.cancel()
    with suppress(asyncio.CancelledError):
        await worker
    engine.dispose()


app = FastAPI(lifespan=lifespan)
app.add_middleware(AccessMiddleware, session_factory=Factory)
for module in (auth_router, jobs_router, operations_router, processing_router, rescue_request_router, needs_router, region_router, disaster_type_router, geocode_router):
    app.include_router(module.router)


def db_session():
    with Factory() as db:
        yield db


app.dependency_overrides[get_db] = db_session


@app.get("/health")
def health():
    return {"status": "test"}
