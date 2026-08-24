from datetime import datetime, timedelta

from jose import jwt
from passlib.context import CryptContext

from app.core.config import get_settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def create_access_token(subject: str, role: str) -> str:
    settings = get_settings()
    expires = datetime.utcnow() + timedelta(minutes=settings.jwt_minutes)
    return jwt.encode({"sub": subject, "role": role, "exp": expires}, settings.jwt_secret, algorithm=settings.jwt_algorithm)
