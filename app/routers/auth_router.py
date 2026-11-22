import secrets
from datetime import datetime, timedelta, timezone
from typing import Literal
from fastapi import APIRouter, Depends, HTTPException, Request, Response
from pydantic import BaseModel, ConfigDict, Field, SecretStr, field_validator
from sqlalchemy.orm import Session
from app.dependencies import get_db
from app.core import config
from app.core.security import COOKIE, csrf_token, current_user, digest, enforce_login_rate, hash_password, public_user, require_admin, verify_password
from app.models.operations_model import User, UserSession

router = APIRouter(prefix="/auth", tags=["accounts"])


class LoginInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    email: str = Field(min_length=3, max_length=254)
    password: SecretStr = Field(min_length=1, max_length=128)


class UserInput(LoginInput):
    name: str = Field(min_length=1, max_length=100)
    role: Literal["viewer", "operator", "admin"] = "viewer"

    @field_validator("password")
    @classmethod
    def strong_password(cls, value):
        if len(value.get_secret_value()) < 12:
            raise ValueError("Mật khẩu cần ít nhất 12 ký tự")
        return value


@router.post("/login")
def login(data: LoginInput, request: Request, response: Response, db: Session = Depends(get_db)):
    enforce_login_rate(db, request.client.host if request.client else "unknown")
    user = db.query(User).filter(User.email == data.email.strip().lower()).first()
    # Hash even for unknown users, avoiding the fast account-existence branch.
    encoded = user.password_hash if user else hash_password("unused-password-check")
    valid = verify_password(data.password.get_secret_value(), encoded)
    if not user or not user.active or not valid:
        raise HTTPException(401, "Email hoặc mật khẩu không đúng")
    old = db.get(UserSession, digest(request.cookies.get(COOKIE, "")))
    if old:
        db.delete(old)
    token = secrets.token_urlsafe(32)
    csrf = csrf_token(token)
    db.add(UserSession(token_hash=digest(token), csrf_hash=digest(csrf), user_id=user.id,
                       expires_at=datetime.now(timezone.utc) + timedelta(hours=12)))
    db.commit()
    response.set_cookie(COOKIE, token, max_age=43200, httponly=True, secure=config.AUTH_COOKIE_SECURE, samesite="lax", path="/")
    return {"user": public_user(user), "csrf_token": csrf}


@router.get("/me")
def me(request: Request):
    user = getattr(request.state, "user", None)
    return {"user": user, "csrf_token": csrf_token(request.cookies[COOKIE]) if user else None}


@router.post("/logout")
def logout(request: Request, response: Response, db: Session = Depends(get_db)):
    current_user(request)
    session = db.get(UserSession, digest(request.cookies.get(COOKIE, "")))
    if session:
        db.delete(session)
        db.commit()
    response.delete_cookie(COOKIE, path="/", secure=config.AUTH_COOKIE_SECURE, httponly=True, samesite="lax")
    return {"message": "Đã đăng xuất"}


@router.get("/users")
def users(request: Request, db: Session = Depends(get_db)):
    require_admin(request)
    return [public_user(user) for user in db.query(User).order_by(User.id)]


@router.post("/users", status_code=201)
def create_user(data: UserInput, request: Request, db: Session = Depends(get_db)):
    require_admin(request)
    email = data.email.strip().lower()
    if "@" not in email or db.query(User).filter(User.email == email).first():
        raise HTTPException(422, "Email không hợp lệ hoặc đã tồn tại")
    user = User(email=email, name=data.name.strip(), role=data.role, password_hash=hash_password(data.password.get_secret_value()))
    db.add(user)
    db.commit()
    return public_user(user)


class AccessInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    active: bool


@router.patch("/users/{user_id}/access")
def access(user_id: int, data: AccessInput, request: Request, db: Session = Depends(get_db)):
    admin = require_admin(request)
    if user_id == admin["id"]:
        raise HTTPException(422, "Không tự khóa tài khoản đang dùng")
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(404, "Không tìm thấy tài khoản")
    user.active = data.active
    if not data.active:
        db.query(UserSession).filter(UserSession.user_id == user_id).delete()
    db.commit()
    return public_user(user)
