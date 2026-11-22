"""Opaque server sessions, password hashing and role/CSRF enforcement."""
import hashlib
import hmac
import os
import secrets
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from app.core import config
from app.db.database import SessionLocal
from app.models.operations_model import User, UserSession, LoginThrottle

COOKIE = "rescue_session"
ROLES = {"viewer": 0, "operator": 1, "admin": 2}


def digest(value):
    return hashlib.sha256(value.encode()).hexdigest()


def hash_password(password):
    salt = secrets.token_hex(16)
    encoded = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), 600000).hex()
    return f"pbkdf2_sha256$600000${salt}${encoded}"


def verify_password(password, encoded):
    try:
        algorithm, rounds, salt, expected = encoded.split("$")
        if algorithm != "pbkdf2_sha256":
            return False
        actual = hashlib.pbkdf2_hmac("sha256", password.encode(), bytes.fromhex(salt), int(rounds)).hex()
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


def csrf_token(token):
    return hmac.new(token.encode(), b"rescue-csrf-v1", hashlib.sha256).hexdigest()


def public_user(user):
    return {"id": user.id, "email": user.email, "name": user.name, "role": user.role, "active": user.active}


def current_user(request: Request):
    user = getattr(request.state, "user", None)
    if not user:
        raise HTTPException(401, "Cần đăng nhập")
    return user


def require_admin(request: Request):
    user = current_user(request)
    if user["role"] != "admin":
        raise HTTPException(403, "Cần quyền quản trị")
    return user


def enforce_login_rate(db, ip):
    now = datetime.now(timezone.utc)
    key = digest("login:" + ip)
    db.execute(insert(LoginThrottle).values(key=key, attempts=0, window_start=now).on_conflict_do_nothing())
    row = db.execute(select(LoginThrottle).where(LoginThrottle.key == key).with_for_update()).scalar_one()
    if row.window_start < now - timedelta(minutes=15):
        row.attempts, row.window_start = 0, now
    if row.attempts >= 10:
        db.rollback()
        raise HTTPException(429, "Đã thử đăng nhập quá nhiều lần. Vui lòng chờ 15 phút.")
    row.attempts += 1
    db.commit()


def bootstrap_admin(db):
    email = os.getenv("INITIAL_ADMIN_EMAIL", "").strip().lower()
    password = os.getenv("INITIAL_ADMIN_PASSWORD", "")
    if not email or not password or db.query(User).filter(User.email == email).first():
        return
    if len(password) < 12:
        raise RuntimeError("INITIAL_ADMIN_PASSWORD must be at least 12 characters")
    db.add(User(email=email, name="Quản trị demo", role="admin", password_hash=hash_password(password)))
    db.commit()


class AccessMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, session_factory=SessionLocal):
        super().__init__(app)
        self.session_factory = session_factory

    async def dispatch(self, request, call_next):
        if request.method == "OPTIONS":
            return await call_next(request)
        path = request.url.path.rstrip("/") or "/"
        writing = request.method not in ("GET", "HEAD")
        if writing:
            origin = request.headers.get("origin")
            if origin and origin not in config.ALLOWED_ORIGINS:
                return JSONResponse({"detail": "Nguồn yêu cầu không được phép"}, 403)
        request.state.user = None
        token = request.cookies.get(COOKIE, "")
        session = None
        if token:
            with self.session_factory() as db:
                session = db.get(UserSession, digest(token))
                if session and session.expires_at > datetime.now(timezone.utc):
                    user = db.get(User, session.user_id)
                    if user and user.active:
                        request.state.user = public_user(user)
                csrf_hash = session.csrf_hash if request.state.user else None
        else:
            csrf_hash = None
        protected = ((writing and path != "/auth/login") or path.startswith(("/jobs", "/auth/users"))
                     or path in ("/geocode/forward", "/operations/export") or (path.startswith("/operations/requests/") and path.endswith("/events")))
        if protected:
            if not request.state.user:
                return JSONResponse({"detail": "Cần đăng nhập để thay đổi dữ liệu hoặc dùng dịch vụ định vị"}, 401)
            needed = 0 if path == "/auth/logout" else 1
            if path.startswith(("/auth/users", "/needs", "/disaster_type", "/region")) or request.method == "DELETE":
                needed = 2
            if ROLES.get(request.state.user["role"], -1) < needed:
                return JSONResponse({"detail": "Tài khoản không có quyền thực hiện thao tác này"}, 403)
            if writing and (not csrf_hash or not hmac.compare_digest(digest(request.headers.get("X-CSRF-Token", "")), csrf_hash)):
                return JSONResponse({"detail": "Phiên xác thực thay đổi. Hãy tải lại trang và thử lại."}, 403)
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        if path.startswith(("/auth", "/jobs", "/rescue_request", "/operations")):
            response.headers["Cache-Control"] = "no-store"
        return response
