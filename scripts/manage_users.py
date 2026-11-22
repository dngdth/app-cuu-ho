"""Local admin password recovery; does not expose passwords on the command line."""
import argparse
import getpass
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.db.database import SessionLocal
from app.models.operations_model import User, UserSession
from app.core.security import hash_password

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--email", required=True)
    args = parser.parse_args()
    password = getpass.getpass("New password (at least 12 characters): ")
    if len(password) < 12:
        raise SystemExit("Password too short")
    with SessionLocal() as db:
        user = db.query(User).filter(User.email == args.email.strip().lower()).first()
        if not user:
            raise SystemExit("User not found")
        user.password_hash = hash_password(password)
        db.query(UserSession).filter(UserSession.user_id == user.id).delete()
        db.commit()
        print("Password updated; existing sessions revoked.")
