from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.db.session import get_db
from app.models.domain import Certificate, Issuer, Role, User
from app.schemas.domain import CertificateCreate, RevokeRequest
from app.services.blockchain import BlockchainService
from app.services.certificates import _certificate_list_item, create_and_issue_certificate, recipient_certificates, revoke_certificate

router = APIRouter(prefix="/api/certificates", tags=["certificates"])


@router.post("")
async def create_certificate(
    recipient_name: str = Form(...),
    recipient_email: str = Form(...),
    course_name: str = Form(...),
    certificate_title: str = Form(...),
    issue_date: str = Form(...),
    expiry_date: str | None = Form(None),
    certificate_number: str = Form(...),
    issuer_id: str = Form(...),
    description: str | None = Form(None),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _=Depends(require_role(Role.ISSUER, Role.ADMIN)),
) -> dict:
    try:
        payload = CertificateCreate(
            recipient_name=recipient_name,
            recipient_email=recipient_email,
            course_name=course_name,
            certificate_title=certificate_title,
            issue_date=issue_date,
            expiry_date=expiry_date,
            certificate_number=certificate_number,
            issuer_id=issuer_id,
            description=description,
        )
        cert = await create_and_issue_certificate(db, payload, file)
        return {"certificate_id": cert.certificate_id, "document_hash": cert.file.document_hash, "verification_url": cert.verification_url, "transaction_hash": cert.blockchain_transaction.transaction_hash}
    except ValueError as exc:
        raise HTTPException(status_code=400, detail={"error": {"code": "INVALID_CERTIFICATE_FILE", "message": str(exc)}}) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail={"error": {"code": "ISSUER_NOT_APPROVED", "message": str(exc)}}) from exc
    except ConnectionError as exc:
        raise HTTPException(status_code=503, detail={"error": {"code": "BLOCKCHAIN_UNAVAILABLE", "message": str(exc)}}) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail={"error": {"code": "BLOCKCHAIN_TRANSACTION_FAILED", "message": str(exc)}}) from exc


@router.get("")
def list_certificates(db: Session = Depends(get_db), user: User = Depends(require_role(Role.ISSUER, Role.ADMIN))) -> list[dict]:
    query = select(Certificate).order_by(Certificate.created_at.desc())
    if user.role == Role.ISSUER:
        issuer = db.scalar(select(Issuer).where(Issuer.email == user.email))
        query = query.where(Certificate.issuer_id == issuer.id) if issuer else query.where(False)
    return [_certificate_list_item(c) for c in db.scalars(query).all()]


@router.get("/recipient")
def list_recipient_certificates(db: Session = Depends(get_db), user: User = Depends(require_role(Role.RECIPIENT, Role.ADMIN))) -> list[dict]:
    return recipient_certificates(db, user.email)


@router.get("/{certificate_id}")
def get_certificate(certificate_id: str, db: Session = Depends(get_db)) -> dict:
    cert = db.scalar(select(Certificate).where(Certificate.certificate_id == certificate_id))
    if not cert:
        raise HTTPException(status_code=404, detail={"error": {"code": "CERTIFICATE_NOT_FOUND", "message": "Certificate could not be found."}})
    return {"certificate_id": cert.certificate_id, "recipient": cert.recipient.name, "document_hash": cert.file.document_hash, "status": cert.status.value, "verification_url": cert.verification_url}


@router.post("/{certificate_id}/issue")
def issue_alias(certificate_id: str) -> dict:
    return {"certificate_id": certificate_id, "message": "Certificates are issued atomically by POST /api/certificates in this prototype."}


@router.post("/{certificate_id}/revoke")
def revoke(certificate_id: str, payload: RevokeRequest, db: Session = Depends(get_db), user: User = Depends(require_role(Role.ISSUER, Role.ADMIN))) -> dict:
    try:
        cert = db.scalar(select(Certificate).where(Certificate.certificate_id == certificate_id))
        if not cert:
            raise LookupError("Certificate not found.")
        blockchain = BlockchainService()
        if user.role == Role.ISSUER:
            if cert.issuer.email != user.email:
                raise PermissionError("Issuers can only revoke certificates they issued.")
            signer = blockchain.get_signer_for_issuer(cert.issuer.wallet_address)
        else:
            signer = blockchain.admin_signer()
        cert = revoke_certificate(db, certificate_id, payload.reason, signer=signer)
        return {"certificate_id": cert.certificate_id, "status": cert.status.value, "revocation_reason": cert.revocation_reason}
    except LookupError as exc:
        raise HTTPException(status_code=404, detail={"error": {"code": "CERTIFICATE_NOT_FOUND", "message": "Certificate could not be found."}}) from exc
    except ConnectionError as exc:
        raise HTTPException(status_code=503, detail={"error": {"code": "BLOCKCHAIN_UNAVAILABLE", "message": str(exc)}}) from exc
    except PermissionError as exc:
        raise HTTPException(status_code=403, detail={"error": {"code": "FORBIDDEN", "message": str(exc)}}) from exc
    except ValueError as exc:
        raise HTTPException(status_code=403, detail={"error": {"code": "ISSUER_SIGNER_UNAVAILABLE", "message": str(exc)}}) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=502, detail={"error": {"code": "BLOCKCHAIN_TRANSACTION_FAILED", "message": str(exc)}}) from exc


@router.get("/{certificate_id}/download")
def download_certificate(certificate_id: str) -> dict:
    return {"certificate_id": certificate_id, "message": "Use the stored PDF path from the backend in trusted deployments; public downloads should be signed URLs."}
