from pathlib import Path

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile
from fastapi.responses import FileResponse, Response
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.db.session import get_db
from app.models.domain import Certificate, CertificateStatus, Issuer, Recipient, Role, User
from app.schemas.domain import CertificateCreate, RevokeRequest
from app.services.badges import render_badge_svg
from app.services.blockchain import BlockchainService
from app.services.certificates import _certificate_list_item, bulk_issue_certificates, create_and_issue_certificate, recipient_certificates, revoke_certificate

router = APIRouter(prefix="/api/certificates", tags=["certificates"])


def _assert_can_issue_for(db: Session, user: User, issuer_id: str) -> None:
    if user.role == Role.ADMIN:
        return
    issuer = db.scalar(select(Issuer).where(Issuer.email == user.email))
    if not issuer or issuer.id != issuer_id:
        raise HTTPException(status_code=403, detail={"error": {"code": "FORBIDDEN", "message": "Issuers can only issue certificates for their own issuer profile."}})


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
    user: User = Depends(require_role(Role.ISSUER, Role.ADMIN)),
) -> dict:
    _assert_can_issue_for(db, user, issuer_id)
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


@router.post("/bulk")
async def bulk_create_certificates(
    issuer_id: str = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    user: User = Depends(require_role(Role.ISSUER, Role.ADMIN)),
) -> dict:
    _assert_can_issue_for(db, user, issuer_id)
    csv_bytes = await file.read()
    try:
        return bulk_issue_certificates(db, issuer_id, csv_bytes)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail={"error": {"code": "INVALID_CSV", "message": str(exc)}}) from exc


@router.get("")
def list_certificates(
    db: Session = Depends(get_db),
    user: User = Depends(require_role(Role.ISSUER, Role.ADMIN)),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    q: str | None = Query(default=None, description="Search certificate ID, number, title, program, or recipient name"),
    status: CertificateStatus | None = Query(default=None),
) -> list[dict]:
    query = select(Certificate).order_by(Certificate.created_at.desc())
    if user.role == Role.ISSUER:
        issuer = db.scalar(select(Issuer).where(Issuer.email == user.email))
        query = query.where(Certificate.issuer_id == issuer.id) if issuer else query.where(False)
    if status is not None:
        query = query.where(Certificate.status == status)
    if q:
        pattern = f"%{q.strip()}%"
        query = query.join(Recipient, Certificate.recipient_id == Recipient.id).where(
            Certificate.certificate_id.ilike(pattern)
            | Certificate.certificate_number.ilike(pattern)
            | Certificate.title.ilike(pattern)
            | Certificate.program_name.ilike(pattern)
            | Recipient.name.ilike(pattern)
        )
    query = query.limit(limit).offset(offset)
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


@router.get("/{certificate_id}/badge.svg")
def certificate_badge(certificate_id: str, db: Session = Depends(get_db)) -> Response:
    # A cheap DB-only status lookup, not a full re-verification — this is embedded as an <img>,
    # so it must not trigger a blockchain call, an AI review, or an audit-log write on every page view.
    cert = db.scalar(select(Certificate).where(Certificate.certificate_id == certificate_id))
    status = cert.status.value if cert else "NOT_FOUND"
    svg = render_badge_svg(status)
    return Response(content=svg, media_type="image/svg+xml", headers={"Cache-Control": "public, max-age=300"})


@router.get("/{certificate_id}/download")
def download_certificate(certificate_id: str, db: Session = Depends(get_db)) -> FileResponse:
    cert = db.scalar(select(Certificate).where(Certificate.certificate_id == certificate_id))
    if not cert:
        raise HTTPException(status_code=404, detail={"error": {"code": "CERTIFICATE_NOT_FOUND", "message": "Certificate could not be found."}})
    path = Path(cert.file.storage_path)
    if not path.exists():
        raise HTTPException(status_code=404, detail={"error": {"code": "FILE_MISSING", "message": "The certificate file is not available on this server."}})
    return FileResponse(path, media_type=cert.file.content_type, filename=cert.file.original_filename)
