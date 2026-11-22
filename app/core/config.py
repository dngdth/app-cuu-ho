import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "").strip()
# Keep paid provider calls off until Cloud quotas have been checked.
GOOGLE_MAPS_ENABLED = os.getenv("GOOGLE_MAPS_ENABLED", "false").strip().lower() == "true"

GEOAPIFY_API_KEY = os.getenv("GEOAPIFY_API_KEY", "").strip()
GEOCODING_ENABLED = os.getenv("GEOCODING_ENABLED", "true").lower() == "true"
GEOCODING_DAILY_LIMIT = int(os.getenv("GEOCODING_DAILY_LIMIT", "200"))
GEOCODING_MONTHLY_LIMIT = int(os.getenv("GEOCODING_MONTHLY_LIMIT", "4000"))
ROUTING_DAILY_LIMIT = int(os.getenv("ROUTING_DAILY_LIMIT", "50"))
ROUTING_MONTHLY_LIMIT = int(os.getenv("ROUTING_MONTHLY_LIMIT", "1000"))
AUTH_COOKIE_SECURE = os.getenv("AUTH_COOKIE_SECURE", "false").lower() == "true"
ALLOWED_ORIGINS = [value.strip() for value in os.getenv("ALLOWED_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173,http://localhost:8098").split(",") if value.strip()]
