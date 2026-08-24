from fastapi import Depends, Header, HTTPException, status
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_db
from app.models.domain import Role, User


def current_user(authorization: str | None = Header(default=None), db: Session = Depends(get_db)) -> User:
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={"error": {"code": "AUTH_REQUIRED", "message": "Authentication is required."}})
    token = authorization.removeprefix("Bearer ").strip()
    try:
        payload = jwt.decode(token, get_settings().jwt_secret, algorithms=[get_settings().jwt_algorithm])
    except JWTError as exc:
        raise HTTPException(status_code=401, detail={"error": {"code": "INVALID_TOKEN", "message": "Token is invalid or expired."}}) from exc
    user = db.scalar(select(User).where(User.email == payload["sub"]))
    if not user or not user.is_active:
        raise HTTPException(status_code=401, detail={"error": {"code": "USER_DISABLED", "message": "User is not active."}})
    return user


def require_role(*roles: Role):
    def _guard(user: User = Depends(current_user)) -> User:
        if user.role not in roles:
            raise HTTPException(status_code=403, detail={"error": {"code": "FORBIDDEN", "message": "You do not have permission for this action."}})
        return user

    return _guard
