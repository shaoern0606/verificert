from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.db.session import get_db
from app.models.domain import AuditAction, AuditLog, Issuer, IssuerStatus, Organization, Role
from app.schemas.domain import IssuerCreate
from app.services.blockchain import BlockchainService

router = APIRouter(prefix="/api/issuers", tags=["issuers"])


@router.post("")
def create_issuer(payload: IssuerCreate, db: Session = Depends(get_db)) -> dict:
    org = db.scalar(select(Organization).where(Organization.name == payload.organization_name)) or Organization(
        name=payload.organization_name, registration_number=payload.registration_number, website=payload.website
    )
    issuer = Issuer(
        organization=org,
        contact_person=payload.contact_person,
        email=str(payload.email),
        wallet_address=payload.wallet_address,
        description=payload.description,
        status=IssuerStatus.PENDING,
    )
    db.add_all([org, issuer, AuditLog(actor=payload.email, role="ISSUER", action=AuditAction.REGISTER_ISSUER)])
    db.commit()
    return {"id": issuer.id, "status": issuer.status.value}


@router.get("")
def list_issuers(db: Session = Depends(get_db)) -> list[dict]:
    issuers = db.scalars(select(Issuer)).all()
    return [
        {
            "id": i.id,
            "organization": i.organization.name,
            "email": i.email,
            "wallet_address": i.wallet_address,
            "status": i.status.value,
        }
        for i in issuers
    ]


@router.get("/me")
def get_my_issuer(db: Session = Depends(get_db), user=Depends(require_role(Role.ISSUER, Role.ADMIN))) -> dict:
    issuer = db.scalar(select(Issuer).where(Issuer.email == user.email))
    if not issuer:
        raise HTTPException(status_code=404, detail={"error": {"code": "ISSUER_NOT_FOUND", "message": "No issuer profile is linked to this account."}})
    return {"id": issuer.id, "organization": issuer.organization.name, "status": issuer.status.value}


@router.get("/{issuer_id}")
def get_issuer(issuer_id: str, db: Session = Depends(get_db)) -> dict:
    issuer = db.get(Issuer, issuer_id)
    if not issuer:
        raise HTTPException(status_code=404, detail={"error": {"code": "ISSUER_NOT_FOUND", "message": "Issuer could not be found."}})
    return {"id": issuer.id, "organization": issuer.organization.name, "status": issuer.status.value, "website": issuer.organization.website}


@router.post("/{issuer_id}/approve")
def approve_issuer(issuer_id: str, db: Session = Depends(get_db), _=Depends(require_role(Role.ADMIN))) -> dict:
    issuer = db.get(Issuer, issuer_id)
    if not issuer:
        raise HTTPException(status_code=404, detail={"error": {"code": "ISSUER_NOT_FOUND", "message": "Issuer could not be found."}})
    issuer.status = IssuerStatus.APPROVED
    try:
        receipt = BlockchainService().register_issuer(issuer.wallet_address)
    except ConnectionError as exc:
        raise HTTPException(status_code=503, detail={"error": {"code": "BLOCKCHAIN_UNAVAILABLE", "message": str(exc)}}) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail={"error": {"code": "BLOCKCHAIN_TRANSACTION_FAILED", "message": str(exc)}}) from exc
    db.add(AuditLog(actor="admin", role="ADMIN", action=AuditAction.REGISTER_ISSUER, metadata_json={"tx": receipt.transaction_hash}))
    db.commit()
    return {"id": issuer.id, "status": issuer.status.value, "transaction_hash": receipt.transaction_hash}


@router.post("/{issuer_id}/suspend")
def suspend_issuer(issuer_id: str, db: Session = Depends(get_db), _=Depends(require_role(Role.ADMIN))) -> dict:
    issuer = db.get(Issuer, issuer_id)
    if not issuer:
        raise HTTPException(status_code=404, detail={"error": {"code": "ISSUER_NOT_FOUND", "message": "Issuer could not be found."}})
    issuer.status = IssuerStatus.SUSPENDED
    try:
        receipt = BlockchainService().suspend_issuer(issuer.wallet_address)
    except ConnectionError as exc:
        raise HTTPException(status_code=503, detail={"error": {"code": "BLOCKCHAIN_UNAVAILABLE", "message": str(exc)}}) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail={"error": {"code": "BLOCKCHAIN_TRANSACTION_FAILED", "message": str(exc)}}) from exc
    db.add(AuditLog(actor="admin", role="ADMIN", action=AuditAction.SUSPEND_ISSUER, metadata_json={"tx": receipt.transaction_hash}))
    db.commit()
    return {"id": issuer.id, "status": issuer.status.value, "transaction_hash": receipt.transaction_hash}
