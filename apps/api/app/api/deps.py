from datetime import datetime

from fastapi import Depends, Header, HTTPException, Request, status
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.models.domain import ApiKey, Role, User
from app.services.api_keys import hash_api_key


def current_user(request: Request, authorization: str | None = Header(default=None), db: Session = Depends(get_db)) -> User:
    settings = get_settings()
    token = request.cookies.get(settings.access_token_cookie_name)
    if not token and authorization and authorization.startswith("Bearer "):
        token = authorization.removeprefix("Bearer ").strip()
    if not token:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={"error": {"code": "AUTH_REQUIRED", "message": "Authentication is required."}})
    try:
        payload = jwt.decode(token, settings.jwt_secret, algorithms=[settings.jwt_algorithm])
    except JWTError as exc:
        raise HTTPException(status_code=401, detail={"error": {"code": "INVALID_TOKEN", "message": "Token is invalid or expired."}}) from exc
    user = db.scalar(select(User).where(User.email == payload["sub"]))
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail={"error": {"code": "USER_DISABLED", "message": "User is not active."}})
    return user


def optional_api_key(x_api_key: str | None = Header(default=None, alias="X-API-Key"), db: Session = Depends(get_db)) -> ApiKey | None:
    if not x_api_key:
        return None
    key = db.scalar(select(ApiKey).where(ApiKey.key_hash == hash_api_key(x_api_key)))
    if not key or key.revoked_at is not None:
        raise HTTPException(status_code=401, detail={"error": {"code": "INVALID_API_KEY", "message": "API key is invalid or has been revoked."}})
    key.last_used_at = datetime.utcnow()
    db.commit()
    return key


def require_role(*roles: Role):
    def _guard(user: User = Depends(current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status_code=403, detail={"error": {"code": "FORBIDDEN", "message": "You do not have permission for this action."}})
        return user

    return _guard
