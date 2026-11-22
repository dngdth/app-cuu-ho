"""Run Google address lookup on a small set of existing, unlocated requests."""
import argparse
import json
from app.db.database import SessionLocal
from app.services.geocode_maintenance import geocode_pending


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--limit", type=int, default=20)
    parser.add_argument("--id", type=int, action="append", dest="ids")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if not 1 <= args.limit <= 100:
        parser.error("limit must be between 1 and 100")
    with SessionLocal() as db:
        report = geocode_pending(db, args.limit, args.ids, args.dry_run)
    print(json.dumps(report, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
