"""Resolve Maps links on saved, unlocated requests without rerunning models."""
import argparse
import json
from app.db.database import SessionLocal
from app.services.processing_service import ProcessingService


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int)
    args = parser.parse_args()
    with SessionLocal() as db:
        report = ProcessingService.resolve_existing_map_links(db, args.limit)
    print(json.dumps(report), flush=True)
    if report["failed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
