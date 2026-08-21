from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.db.session import get_db
from app.models.domain import AuditLog, Role

router = APIRouter(prefix="/api/audit-logs", tags=["audit"])


@router.get("")
def list_audit_logs(db: Session = Depends(get_db), _=Depends(require_role(Role.ADMIN))) -> list[dict]:
    logs = db.scalars(select(AuditLog).order_by(AuditLog.timestamp.desc()).limit(200)).all()
    return [
        {"timestamp": log.timestamp.isoformat(), "actor": log.actor, "role": log.role, "action": log.action.value, "certificate_id": log.certificate_id, "metadata": log.metadata_json}
        for log in logs
    ]
