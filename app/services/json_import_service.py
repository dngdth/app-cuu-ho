"""Backward-compatible JSON import backed by the same production AI pipeline."""
from app.services.processing_service import ProcessingService


def import_json_data(data, db):
    result = ProcessingService.process(db, data)
    return {
        "success": True,
        "total": result["total"],
        "success_count": result["created"],
        "error_count": result["failed"],
        "errors": [f"Row {row['row']}: {row['error']}" for row in result["results"] if row["status"] == "error"],
        "duplicates": result["duplicates"],
        "results": result["results"],
    }
