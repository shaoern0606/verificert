from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.db.session import get_db
from app.models.domain import AuditAction, AuditLog, Certificate, Issuer, Role, User

router = APIRouter(prefix="/api/audit-logs", tags=["audit"])


@router.get("")
def list_audit_logs(db: Session = Depends(get_db), user: User = Depends(require_role(Role.ADMIN, Role.ISSUER))) -> list[dict]:
    query = select(AuditLog).order_by(AuditLog.timestamp.desc()).limit(200)
    if user.role == Role.ISSUER:
        issuer = db.scalar(select(Issuer).where(Issuer.email == user.email))
        certificate_ids = select(Certificate.certificate_id).where(Certificate.issuer_id == issuer.id) if issuer else select(Certificate.certificate_id).where(False)
        query = select(AuditLog).where(
            (AuditLog.action == AuditAction.VERIFY_CERTIFICATE) | AuditLog.certificate_id.in_(certificate_ids)
        ).order_by(AuditLog.timestamp.desc()).limit(200)
    logs = db.scalars(query).all()
    return [
        {"timestamp": log.timestamp.isoformat(), "actor": log.actor, "role": log.role, "action": log.action.value, "certificate_id": log.certificate_id, "metadata": log.metadata_json}
        for log in logs
    ]
