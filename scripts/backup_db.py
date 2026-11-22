"""Binary-safe PostgreSQL backup and restore to a NEW database via Docker Compose."""
import argparse
import json
import re
import subprocess
from datetime import datetime
from pathlib import Path
from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[1]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("action", choices=["backup", "restore"])
    parser.add_argument("--file", type=Path)
    parser.add_argument("--target-db")
    args = parser.parse_args()
    env = dotenv_values(ROOT / ".env")
    user, database = env.get("POSTGRES_USER", "rescue"), env.get("POSTGRES_DB", "rescue")
    base = ["docker", "compose", "exec", "-T", "postgres"]
    if args.action == "backup":
        path = (args.file or ROOT / "backups" / (datetime.now().strftime("rescue-%Y%m%d-%H%M%S") + ".dump")).resolve()
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as target:
            subprocess.run([*base, "pg_dump", "-U", user, "-d", database, "-Fc"], cwd=ROOT, stdout=target, check=True)
        print(json.dumps({"backup": str(path), "bytes": path.stat().st_size}))
    else:
        target = args.target_db or ""
        if not re.fullmatch(r"[a-z][a-z0-9_]{2,62}", target) or target == database:
            raise SystemExit("Choose a NEW target database name, different from the source database")
        if not args.file or not args.file.is_file():
            raise SystemExit("--file must be an existing pg_dump archive")
        # createdb refuses existing names; no --clean, DROP or overwrite of the live DB.
        subprocess.run([*base, "createdb", "-U", user, target], cwd=ROOT, check=True)
        with args.file.open("rb") as source:
            subprocess.run([*base, "pg_restore", "-U", user, "-d", target, "--no-owner", "--no-privileges", "--exit-on-error"], cwd=ROOT, stdin=source, check=True)
        count = subprocess.check_output([*base, "psql", "-U", user, "-d", target, "-Atc", "SELECT count(*) FROM rescue_request"], cwd=ROOT, text=True).strip()
        print(json.dumps({"restored_database": target, "rescue_requests": int(count)}))


if __name__ == "__main__":
    main()
