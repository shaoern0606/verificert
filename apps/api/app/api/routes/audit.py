from fastapi import APIRouter, Depends, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.db.session import get_db
from app.models.domain import AuditAction, AuditLog, Certificate, Issuer, Role, User

router = APIRouter(prefix="/api/audit-logs", tags=["audit"])


@router.get("")
def list_audit_logs(
    db: Session = Depends(get_db),
    user: User = Depends(require_role(Role.ADMIN, Role.ISSUER)),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    q: str | None = Query(default=None, description="Search certificate ID or actor"),
    action: AuditAction | None = Query(default=None),
) -> list[dict]:
    query = select(AuditLog)
    if user.role == Role.ISSUER:
        issuer = db.scalar(select(Issuer).where(Issuer.email == user.email))
        certificate_ids = select(Certificate.certificate_id).where(Certificate.issuer_id == issuer.id) if issuer else select(Certificate.certificate_id).where(False)
        query = query.where((AuditLog.action == AuditAction.VERIFY_CERTIFICATE) | AuditLog.certificate_id.in_(certificate_ids))
    if action is not None:
        query = query.where(AuditLog.action == action)
    if q:
        pattern = f"%{q.strip()}%"
        query = query.where(AuditLog.certificate_id.ilike(pattern) | AuditLog.actor.ilike(pattern))
    query = query.order_by(AuditLog.timestamp.desc()).limit(limit).offset(offset)
    logs = db.scalars(query).all()
    return [
        {"timestamp": log.timestamp.isoformat(), "actor": log.actor, "role": log.role, "action": log.action.value, "certificate_id": log.certificate_id, "metadata": log.metadata_json}
        for log in logs
    ]
