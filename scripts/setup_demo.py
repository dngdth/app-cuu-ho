"""Fill missing local settings without printing secrets or replacing existing keys."""
import argparse
import re
import secrets
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dotenv import dotenv_values

ROOT = Path(__file__).resolve().parents[1]


def set_value(path, key, value):
    content = path.read_text(encoding="utf-8-sig") if path.exists() else ""
    pattern = r"(?m)^" + re.escape(key) + r"\s*=.*$"
    content = re.sub(pattern, lambda m: key + "=" + value, content) if re.search(pattern, content) else content.rstrip() + "\n" + key + "=" + value + "\n"
    path.write_text(content, encoding="utf-8")


def setup():
    backend, frontend = ROOT / ".env", ROOT / "fe/.env.local"
    if not backend.exists():
        content = (ROOT / ".env.example").read_text(encoding="utf-8")
        password = secrets.token_urlsafe(24)
        backend.write_text(content.replace("change_me", password), encoding="utf-8")
    values = dotenv_values(backend)
    defaults = {"GEOAPIFY_API_KEY": "", "GEOCODING_ENABLED": "true", "GEOCODING_DAILY_LIMIT": "200",
        "GEOCODING_MONTHLY_LIMIT": "4000", "ROUTING_DAILY_LIMIT": "50", "ROUTING_MONTHLY_LIMIT": "1000",
        "AUTH_COOKIE_SECURE": "false", "ALLOWED_ORIGINS": "http://localhost:5173,http://127.0.0.1:5173,http://localhost:8098",
        "RESCUE_MODEL_DIR": "ai/artifacts/prototype", "INITIAL_ADMIN_EMAIL": "admin@rescue.local"}
    for key, value in defaults.items():
        if key not in values:
            set_value(backend, key, value)
    if not values.get("INITIAL_ADMIN_PASSWORD"):
        set_value(backend, "INITIAL_ADMIN_PASSWORD", secrets.token_urlsafe(24))
    if not frontend.exists():
        frontend.write_text((ROOT / "fe/.env.example").read_text(encoding="utf-8"), encoding="utf-8")
    print("Local settings ready. Admin email/password are in .env (INITIAL_ADMIN_EMAIL / INITIAL_ADMIN_PASSWORD).")
    print("Google keys, if retained from earlier setup, are no longer used by the application.")


if __name__ == "__main__":
    setup()
