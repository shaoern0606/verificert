from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import current_user, require_role
from app.db.session import get_db
from app.models.domain import AuditAction, AuditLog, Issuer, IssuerStatus, Organization, Role, User
from app.schemas.domain import IssuerCreate
from app.services.blockchain import BlockchainService

router = APIRouter(prefix="/api/issuers", tags=["issuers"])


@router.post("")
def create_issuer(payload: IssuerCreate, db: Session = Depends(get_db), user: User = Depends(current_user)) -> dict:
    if db.scalar(select(Issuer).where(Issuer.email == user.email)):
        raise HTTPException(status_code=409, detail={"error": {"code": "ISSUER_EXISTS", "message": "An issuer profile is already linked to this account."}})
    org = db.scalar(select(Organization).where(Organization.name == payload.organization_name)) or Organization(
        name=payload.organization_name, registration_number=payload.registration_number, website=payload.website
    )
    issuer = Issuer(
        organization=org,
        contact_person=payload.contact_person,
        email=user.email,
        wallet_address=payload.wallet_address,
        description=payload.description,
        status=IssuerStatus.PENDING,
    )
    db.add_all([org, issuer, AuditLog(actor=user.email, role="ISSUER", action=AuditAction.REGISTER_ISSUER)])
    db.commit()
    return {"id": issuer.id, "status": issuer.status.value}


@router.get("")
def list_issuers(
    db: Session = Depends(get_db),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    q: str | None = Query(default=None, description="Search organization name, contact person, or email"),
    status: IssuerStatus | None = Query(default=None),
    _=Depends(require_role(Role.ADMIN)),
) -> list[dict]:
    query = select(Issuer).join(Organization, Issuer.organization_id == Organization.id).order_by(Issuer.id)
    if status is not None:
        query = query.where(Issuer.status == status)
    if q:
        pattern = f"%{q.strip()}%"
        query = query.where(Organization.name.ilike(pattern) | Issuer.contact_person.ilike(pattern) | Issuer.email.ilike(pattern))
    issuers = db.scalars(query.limit(limit).offset(offset)).all()
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
    return {
        "id": issuer.id,
        "organization": issuer.organization.name,
        "status": issuer.status.value,
        "contact_person": issuer.contact_person,
        "email": issuer.email,
        "wallet_address": issuer.wallet_address,
        "description": issuer.description,
        "website": issuer.organization.website,
        "registration_number": issuer.organization.registration_number,
    }


@router.get("/directory")
def issuer_directory(db: Session = Depends(get_db), q: str | None = Query(default=None)) -> list[dict]:
    query = select(Issuer).join(Organization, Issuer.organization_id == Organization.id).where(Issuer.status == IssuerStatus.APPROVED).order_by(Organization.name)
    if q:
        pattern = f"%{q.strip()}%"
        query = query.where(Organization.name.ilike(pattern))
    issuers = db.scalars(query).all()
    return [
        {
            "id": i.id,
            "organization": i.organization.name,
            "website": i.organization.website,
            "description": i.description,
            "wallet_address": i.wallet_address,
        }
        for i in issuers
    ]


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
    linked_user = db.scalar(select(User).where(User.email == issuer.email))
    if linked_user and linked_user.role == Role.RECIPIENT:
        linked_user.role = Role.ISSUER
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
