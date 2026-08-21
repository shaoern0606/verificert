from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import current_user
from app.core.security import create_access_token, hash_password, verify_password
from app.db.session import get_db
from app.models.domain import Role, User
from app.schemas.domain import LoginRequest, RegisterRequest, TokenResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])


@router.post("/register", response_model=TokenResponse)
def register(payload: RegisterRequest, db: Session = Depends(get_db)) -> TokenResponse:
    if db.scalar(select(User).where(User.email == payload.email)):
        raise HTTPException(status_code=409, detail={"error": {"code": "EMAIL_EXISTS", "message": "An account already exists for this email."}})
    role = Role(payload.role) if payload.role in Role.__members__ else Role.RECIPIENT
    user = User(email=str(payload.email), password_hash=hash_password(payload.password), full_name=payload.full_name, role=role)
    db.add(user)
    db.commit()
    return TokenResponse(access_token=create_access_token(user.email, user.role.value), role=user.role.value)


@router.post("/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> TokenResponse:
    user = db.scalar(select(User).where(User.email == payload.email))
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail={"error": {"code": "BAD_CREDENTIALS", "message": "Email or password is incorrect."}})
    return TokenResponse(access_token=create_access_token(user.email, user.role.value), role=user.role.value)


@router.get("/me")
def me(user: User = Depends(current_user)) -> dict:
    return {"email": user.email, "full_name": user.full_name, "role": user.role.value}
