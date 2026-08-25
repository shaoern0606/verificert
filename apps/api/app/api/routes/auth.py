from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import current_user, require_role
from app.core.config import get_settings
from app.core.rate_limit import limiter
from app.core.security import create_access_token, hash_password, verify_password
from app.db.session import get_db
from app.models.domain import Role, User
from app.schemas.domain import LoginRequest, RegisterRequest, RoleUpdateRequest, TokenResponse

router = APIRouter(prefix="/api/auth", tags=["auth"])


def _issue_session(response: Response, user: User) -> TokenResponse:
    settings = get_settings()
    token = create_access_token(user.email, user.role.value)
    response.set_cookie(
        key=settings.access_token_cookie_name,
        value=token,
        httponly=True,
        secure=settings.cookie_secure,
        samesite="none",
        max_age=settings.jwt_minutes * 60,
        path="/",
    )
    return TokenResponse(role=user.role.value, email=user.email, full_name=user.full_name)


@router.post("/register", response_model=TokenResponse)
@limiter.limit("5/minute")
def register(request: Request, payload: RegisterRequest, response: Response, db: Session = Depends(get_db)) -> TokenResponse:
    if db.scalar(select(User).where(User.email == payload.email)):
        raise HTTPException(status_code=409, detail={"error": {"code": "EMAIL_EXISTS", "message": "An account already exists for this email."}})
    user = User(email=str(payload.email), password_hash=hash_password(payload.password), full_name=payload.full_name, role=Role.RECIPIENT)
    db.add(user)
    db.commit()
    return _issue_session(response, user)


@router.post("/login", response_model=TokenResponse)
@limiter.limit("10/minute")
def login(request: Request, payload: LoginRequest, response: Response, db: Session = Depends(get_db)) -> TokenResponse:
    email = payload.email.strip().lower()
    user = db.scalar(select(User).where(User.email == email))
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail={"error": {"code": "BAD_CREDENTIALS", "message": "Email or password is incorrect."}})
    return _issue_session(response, user)


@router.post("/logout")
def logout(response: Response) -> dict:
    settings = get_settings()
    response.delete_cookie(key=settings.access_token_cookie_name, path="/")
    return {"status": "ok"}


@router.get("/me")
def me(user: User = Depends(current_user)) -> dict:
    return {"email": user.email, "full_name": user.full_name, "role": user.role.value}


@router.patch("/users/{user_id}/role")
def set_user_role(user_id: str, payload: RoleUpdateRequest, db: Session = Depends(get_db), _=Depends(require_role(Role.ADMIN))) -> dict:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail={"error": {"code": "USER_NOT_FOUND", "message": "User could not be found."}})
    if payload.role not in Role.__members__:
        raise HTTPException(status_code=400, detail={"error": {"code": "INVALID_ROLE", "message": "Role must be one of " + ", ".join(Role.__members__)}})
    user.role = Role(payload.role)
    db.commit()
    return {"id": user.id, "email": user.email, "role": user.role.value}
