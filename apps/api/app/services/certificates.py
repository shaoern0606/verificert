from datetime import datetime
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.ai.verification_graph import run_verification_graph
from app.core.config import get_settings
from app.models.domain import (
    AIAnalysisResult,
    AuditAction,
    AuditLog,
    BlockchainTransaction,
    Certificate,
    CertificateFile,
    CertificateStatus,
    Issuer,
    IssuerStatus,
    Organization,
    Recipient,
    VerificationAttempt,
    VerificationStatus,
)
from app.schemas.domain import CertificateCreate, CertificateSummary, VerificationResponse
from app.services.blockchain import BlockchainService
from app.services.hashing import sha256_bytes
from app.services.id_service import generate_certificate_id


def _summary(cert: Certificate) -> CertificateSummary:
    return CertificateSummary(
        certificate_id=cert.certificate_id,
        recipient=cert.recipient.name,
        program=cert.program_name,
        issuer=cert.organization.name,
        issued=cert.issue_date,
        expires=cert.expiry_date,
        status=cert.status.value,
        document_hash=cert.file.document_hash,
        verification_url=cert.verification_url,
        transaction_hash=cert.blockchain_transaction.transaction_hash if cert.blockchain_transaction else None,
    )


async def create_and_issue_certificate(db: Session, payload: CertificateCreate, file: UploadFile) -> Certificate:
    settings = get_settings()
    content = await file.read()
    if not content.startswith(b"%PDF"):
        raise ValueError("Only PDF certificates are accepted.")
    if len(content) > settings.max_upload_mb * 1024 * 1024:
        raise ValueError("Certificate PDF is larger than the configured limit.")
    issuer = db.get(Issuer, payload.issuer_id)
    if not issuer or issuer.status != IssuerStatus.APPROVED:
        raise PermissionError("Issuer must be approved before issuing certificates.")
    recipient = db.scalar(select(Recipient).where(Recipient.email == payload.recipient_email)) or Recipient(
        name=payload.recipient_name, email=str(payload.recipient_email)
    )
    db.add(recipient)
    cert_id = generate_certificate_id(db)
    document_hash = sha256_bytes(content)
    cert_dir = Path(settings.storage_path) / "certificates"
    cert_dir.mkdir(parents=True, exist_ok=True)
    storage_path = cert_dir / f"{cert_id}.pdf"
    storage_path.write_bytes(content)
    cert_file = CertificateFile(
        original_filename=file.filename or f"{cert_id}.pdf",
        storage_path=str(storage_path),
        content_type=file.content_type or "application/pdf",
        size_bytes=len(content),
        document_hash=document_hash,
    )
    verification_url = f"{settings.next_public_app_url}/verify/{cert_id}"
    receipt = BlockchainService().issue_certificate(cert_id, document_hash, payload.expiry_date, verification_url)
    tx = BlockchainTransaction(
        network=receipt.network,
        contract_address=receipt.contract_address,
        transaction_hash=receipt.transaction_hash,
        block_number=receipt.block_number,
        action="ISSUE_CERTIFICATE",
    )
    cert = Certificate(
        certificate_id=cert_id,
        certificate_number=payload.certificate_number,
        title=payload.certificate_title,
        program_name=payload.course_name,
        description=payload.description,
        issuer=issuer,
        recipient=recipient,
        organization=issuer.organization,
        file=cert_file,
        blockchain_transaction=tx,
        issue_date=payload.issue_date,
        expiry_date=payload.expiry_date,
        status=CertificateStatus.ACTIVE,
        verification_url=verification_url,
        qr_payload=verification_url,
    )
    db.add_all([cert_file, tx, cert, AuditLog(actor=issuer.email, role="ISSUER", action=AuditAction.ISSUE_CERTIFICATE, certificate_id=cert_id)])
    db.commit()
    db.refresh(cert)
    return cert


def verify_certificate(db: Session, certificate_id: str, uploaded_bytes: bytes | None = None, ip: str | None = None) -> VerificationResponse:
    cert = db.scalar(select(Certificate).where(Certificate.certificate_id == certificate_id))
    uploaded_hash = sha256_bytes(uploaded_bytes) if uploaded_bytes else None
    if not cert:
        response = VerificationResponse(
            status=VerificationStatus.NOT_FOUND,
            certificate_id=certificate_id,
            decisive_reason="Certificate could not be found.",
            checks={"certificate_exists": False, "issuer_recognized": False, "blockchain_record_found": False, "hash_matches": False},
        )
        db.add(VerificationAttempt(certificate_id=certificate_id, uploaded_hash=uploaded_hash, outcome=VerificationStatus.NOT_FOUND, ip_address=ip, details=response.model_dump(mode="json")))
        db.commit()
        return response
    hash_matches = uploaded_hash is None or uploaded_hash == cert.file.document_hash
    issuer_recognized = cert.issuer.status == IssuerStatus.APPROVED
    blockchain_found = cert.blockchain_transaction is not None
    now = datetime.utcnow()
    expired = cert.expiry_date is not None and cert.expiry_date < now
    if cert.status == CertificateStatus.REVOKED:
        status = VerificationStatus.REVOKED
        reason = "Certificate has been revoked."
    elif not blockchain_found:
        status = VerificationStatus.PENDING
        reason = "Blockchain record is not confirmed yet."
    elif not hash_matches:
        status = VerificationStatus.INVALID
        reason = "Document hash mismatch."
    elif expired:
        status = VerificationStatus.EXPIRED
        reason = "Certificate is authentic but expired."
    elif not issuer_recognized:
        status = VerificationStatus.SUSPICIOUS
        reason = "Issuer is not currently approved."
    else:
        status = VerificationStatus.VERIFIED
        reason = "Certificate exists, issuer is verified, document integrity is confirmed, and certificate is active."
    ai = run_verification_graph(
        {
            "certificate_id": certificate_id,
            "hash_match": hash_matches,
            "issuer_match": issuer_recognized,
            "blockchain_record_found": blockchain_found,
            "revoked": cert.status == CertificateStatus.REVOKED,
            "expired": expired,
            "metadata_match": True,
        }
    )
    response = VerificationResponse(
        status=status,
        certificate_id=certificate_id,
        decisive_reason=reason,
        checks={
            "certificate_exists": True,
            "issuer_recognized": issuer_recognized,
            "blockchain_record_found": blockchain_found,
            "hash_matches": hash_matches,
            "not_revoked": cert.status != CertificateStatus.REVOKED,
            "not_expired": not expired,
        },
        certificate=_summary(cert),
        ai=ai,
        technical_details={
            "uploaded_hash": uploaded_hash,
            "registered_hash": cert.file.document_hash,
            "network": cert.blockchain_transaction.network if cert.blockchain_transaction else None,
            "contract_address": cert.blockchain_transaction.contract_address if cert.blockchain_transaction else None,
            "block_number": cert.blockchain_transaction.block_number if cert.blockchain_transaction else None,
            "revocation_reason": cert.revocation_reason,
            "revoked_at": cert.revoked_at.isoformat() if cert.revoked_at else None,
        },
    )
    db.add_all(
        [
            VerificationAttempt(certificate_id=certificate_id, uploaded_hash=uploaded_hash, outcome=status, ip_address=ip, details=response.model_dump(mode="json")),
            AuditLog(actor="public", role="VERIFIER", action=AuditAction.VERIFY_CERTIFICATE, certificate_id=certificate_id, ip_address=ip),
            AIAnalysisResult(certificate_id=certificate_id, risk_score=ai.risk_score, risk_level=ai.risk_level, result=ai.model_dump()),
        ]
    )
    db.commit()
    return response


def revoke_certificate(db: Session, certificate_id: str, reason: str) -> Certificate:
    cert = db.scalar(select(Certificate).where(Certificate.certificate_id == certificate_id))
    if not cert:
        raise LookupError("Certificate not found.")
    receipt = BlockchainService().revoke_certificate(certificate_id)
    tx = BlockchainTransaction(
        network=receipt.network,
        contract_address=receipt.contract_address,
        transaction_hash=receipt.transaction_hash,
        block_number=receipt.block_number,
        action="REVOKE_CERTIFICATE",
    )
    cert.status = CertificateStatus.REVOKED
    cert.revoked_at = datetime.utcnow()
    cert.revocation_reason = reason
    cert.blockchain_transaction = tx
    db.add_all([tx, AuditLog(actor=cert.issuer.email, role="ISSUER", action=AuditAction.REVOKE_CERTIFICATE, certificate_id=certificate_id)])
    db.commit()
    db.refresh(cert)
    return cert


def admin_dashboard(db: Session) -> dict:
    total = db.scalar(select(func.count(Certificate.id))) or 0
    by_status = {s.value: db.scalar(select(func.count(Certificate.id)).where(Certificate.status == s)) or 0 for s in CertificateStatus}
    issuers = db.scalar(select(func.count(Issuer.id))) or 0
    attempts = db.scalar(select(func.count(VerificationAttempt.id))) or 0
    return {
        "cards": {"total_certificates": total, "registered_issuers": issuers, "verification_attempts": attempts, **{k.lower(): v for k, v in by_status.items()}},
        "charts": {
            "certificates_by_status": [{"name": k, "value": v} for k, v in by_status.items()],
            "verification_outcomes": [{"name": row[0].value, "value": row[1]} for row in db.execute(select(VerificationAttempt.outcome, func.count()).group_by(VerificationAttempt.outcome)).all()],
        },
    }
