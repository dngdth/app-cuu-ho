"""Import a source CSV through the running API, with real ensemble predictions."""
import argparse
import csv
import json
import getpass
from pathlib import Path

import requests


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("file", nargs="?", default="crawl/data_clean.csv")
    parser.add_argument("--api-url", default="http://localhost:8099")
    parser.add_argument("--email", required=True, help="Operator/admin email. Password is entered privately.")
    parser.add_argument("--batch-size", type=int, default=20)
    parser.add_argument("--limit", type=int)
    parser.add_argument("--collected-at", help="Actual collection timestamp, ISO format. Omit if unknown.")
    parser.add_argument("--no-geocode", action="store_true")
    args = parser.parse_args()
    if not 1 <= args.batch_size <= 500:
        parser.error("--batch-size must be between 1 and 500")
    with Path(args.file).open(encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        if not reader.fieldnames or "content" not in reader.fieldnames:
            parser.error("CSV must contain a content column")
        rows = list(reader)
    if args.limit:
        rows = rows[:args.limit]
    totals = {key: 0 for key in ("created", "duplicates", "failed", "located", "unlocated")}
    with requests.Session() as session:
        login = session.post(args.api_url.rstrip("/") + "/auth/login", json={"email": args.email, "password": getpass.getpass("Password: ")}, timeout=20)
        login.raise_for_status()
        session.headers["X-CSRF-Token"] = login.json()["csrf_token"]
        for start in range(0, len(rows), args.batch_size):
            payload = {"records": rows[start:start + args.batch_size], "geocode": not args.no_geocode}
            if args.collected_at:
                payload["collected_at"] = args.collected_at
            response = session.post(args.api_url.rstrip("/") + "/processing/import", json=payload, timeout=180)
            response.raise_for_status()
            report = response.json()
            for key in totals:
                totals[key] += report[key]
            print(json.dumps({"processed": min(start + args.batch_size, len(rows)), "total": len(rows), **totals}), flush=True)
            for row in report["results"]:
                if row["status"] == "error":
                    print(f"Row {start + row['row']}: {row['error']}", flush=True)
    if totals["failed"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
