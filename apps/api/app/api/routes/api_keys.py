from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.db.session import get_db
from app.models.domain import ApiKey, Role, User
from app.schemas.domain import ApiKeyCreateRequest
from app.services.api_keys import generate_api_key

router = APIRouter(prefix="/api/admin/api-keys", tags=["api-keys"])


@router.post("")
def create_api_key(payload: ApiKeyCreateRequest, db: Session = Depends(get_db), user: User = Depends(require_role(Role.ADMIN))) -> dict:
    raw_key, key_hash, prefix = generate_api_key()
    record = ApiKey(label=payload.label, key_hash=key_hash, key_prefix=prefix, created_by=user.email)
    db.add(record)
    db.commit()
    return {"id": record.id, "label": record.label, "key": raw_key, "prefix": record.key_prefix}


@router.get("")
def list_api_keys(db: Session = Depends(get_db), _=Depends(require_role(Role.ADMIN))) -> list[dict]:
    keys = db.scalars(select(ApiKey).order_by(ApiKey.created_at.desc())).all()
    return [
        {
            "id": k.id,
            "label": k.label,
            "prefix": k.key_prefix,
            "created_by": k.created_by,
            "created_at": k.created_at.isoformat(),
            "last_used_at": k.last_used_at.isoformat() if k.last_used_at else None,
            "revoked": k.revoked_at is not None,
        }
        for k in keys
    ]


@router.delete("/{key_id}")
def revoke_api_key(key_id: str, db: Session = Depends(get_db), _=Depends(require_role(Role.ADMIN))) -> dict:
    key = db.get(ApiKey, key_id)
    if not key:
        raise HTTPException(status_code=404, detail={"error": {"code": "API_KEY_NOT_FOUND", "message": "API key could not be found."}})
    key.revoked_at = datetime.utcnow()
    db.commit()
    return {"id": key.id, "revoked": True}
