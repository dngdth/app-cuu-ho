import asyncio
import csv
import io
import logging
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from ai.inference import EnsemblePredictor
from app.dependencies import get_db
from app.services.processing_service import ProcessingService

router = APIRouter(prefix="/processing", tags=["AI processing"])
logger = logging.getLogger(__name__)


class ProcessingInput(BaseModel):
    records: list[dict[str, Any]] = Field(min_length=1, max_length=500)
    collected_at: datetime | None = None
    geocode: bool = True


def process_records(db, data):
    try:
        return ProcessingService.process(db, data.records, data.collected_at, data.geocode)
    except (FileNotFoundError, ImportError) as exc:
        db.rollback()
        logger.exception("Model unavailable")
        raise HTTPException(503, "Không đọc được bộ model. Kiểm tra thư viện và RESCUE_MODEL_DIR.") from exc
    except Exception as exc:
        db.rollback()
        logger.exception("Prediction failed")
        raise HTTPException(500, "Dự đoán thất bại; chưa lưu dữ liệu của lô này. Xem log backend.") from exc


@router.post("/predict")
def predict(data: ProcessingInput):
    """Preview all three predictions without geocoding or writing to the database."""
    try:
        return [{k: v for k, v in item.items() if k != "record"}
                for item in EnsemblePredictor().predict(data.records)]
    except (ValueError, TypeError, SyntaxError) as exc:
        raise HTTPException(422, str(exc)) from exc
    except Exception as exc:
        logger.exception("Prediction failed")
        raise HTTPException(503, "Không chạy được bộ model; xem log backend.") from exc


@router.post("/import")
def import_records(data: ProcessingInput, db: Session = Depends(get_db)):
    """Predict, deduplicate, geocode, and save every valid source record."""
    return process_records(db, data)


class GeocodePendingInput(BaseModel):
    ids: list[int] | None = Field(default=None, min_length=1, max_length=100)
    limit: int = Field(default=20, ge=1, le=100)
    dry_run: bool = False


@router.post("/geocode-pending")
def geocode_pending_records(data: GeocodePendingInput, db: Session = Depends(get_db)):
    """Locate saved requests without rerunning AI or creating duplicate requests."""
    from app.services.geocode_maintenance import geocode_pending
    return geocode_pending(db, limit=data.limit, ids=data.ids, dry_run=data.dry_run)


def read_csv_upload(file):
    raw = file.file.read(3 * 1024 * 1024 + 1)
    if len(raw) > 3 * 1024 * 1024:
        raise HTTPException(413, "File CSV vượt quá 3 MB.")
    try:
        reader = csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))
        if not reader.fieldnames or "content" not in reader.fieldnames:
            raise ValueError("CSV phải có cột content.")
        records = []
        for row in reader:
            if None in row:
                raise ValueError("CSV có dòng không khớp số cột.")
            records.append(row)
            if len(records) > 500:
                raise ValueError("Mỗi lần nhập tối đa 500 dòng.")
        if not records:
            raise ValueError("CSV không có bản ghi.")
    except (UnicodeDecodeError, csv.Error, ValueError) as exc:
        raise HTTPException(422, str(exc)) from exc
    return records


@router.post("/read-csv")
def read_csv(file: UploadFile = File(...)):
    """Validate a CSV so the UI can submit small batches and show progress."""
    return {"records": read_csv_upload(file)}


@router.post("/import-csv")
def import_csv(file: UploadFile = File(...), collected_at: datetime | None = Form(None),
               geocode: bool = Form(True), db: Session = Depends(get_db)):
    records = read_csv_upload(file)
    return process_records(db, ProcessingInput(records=records, collected_at=collected_at, geocode=geocode))


class TextInput(BaseModel):
    content: str = Field(min_length=1, max_length=20000)
    location: str | None = None
    coordinate: dict[str, Any] | None = None
    source_url: str | None = Field(default=None, max_length=2000)
    use_llm: bool = False


@router.post("/extract")
def extract_preview(data: TextInput):
    from ai.extraction import extract_post
    row = extract_post(data.content, data.source_url)
    if data.location:
        row["location"] = data.location
    return {"record": row, "review_required": True,
            "message": "Bóc tách theo quy tắc local; kiểm tra lại địa chỉ, số người và nhu cầu trước khi nhập."}


@router.post("/text")
def process_text(data: TextInput, db: Session = Depends(get_db)):
    """Optional LLM extraction for an unstructured post, followed by the same pipeline."""
    try:
        if data.use_llm:
            from ai.src.extract_utils import extract_emergency_info
            record = asyncio.run(extract_emergency_info(data.content))
            record.update(extraction_source="llm", extraction_review_required=True)
        else:
            from ai.extraction import extract_post
            record = extract_post(data.content, data.source_url)
    except RuntimeError as exc:
        raise HTTPException(503, "Chưa cấu hình BASE_URL/API_KEY cho bước trích xuất bài viết. Bạn có thể nhập CSV hoặc các trường đã bóc tách.") from exc
    except Exception as exc:
        logger.exception("Extraction failed")
        raise HTTPException(502, "Không trích xuất được bài viết; chưa tạo yêu cầu cứu hộ.") from exc
    record["content"] = data.content
    if data.location:
        record["location"] = data.location
    if data.coordinate:
        record["coordinate"] = data.coordinate
    return process_records(db, ProcessingInput(records=[record]))
