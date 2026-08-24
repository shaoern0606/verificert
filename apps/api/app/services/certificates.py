from datetime import datetime
from pathlib import Path
from typing import Final

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
    Recipient,
    VerificationAttempt,
    VerificationStatus,
)
from app.schemas.domain import CertificateCreate, CertificateSummary, VerificationResponse
from app.services.blockchain import BlockchainService
from app.services.hashing import sha256_bytes
from app.services.id_service import generate_certificate_id


SUPPORTED_DOCUMENT_TYPES: Final[dict[str, tuple[bytes, ...]]] = {
    "application/pdf": (b"%PDF",),
    "image/jpeg": (b"\xff\xd8\xff",),
    "image/png": (b"\x89PNG\r\n\x1a\n",),
    "image/gif": (b"GIF87a", b"GIF89a"),
    "image/webp": (b"RIFF",),
}


def _has_valid_signature(content_type: str, content: bytes) -> bool:
    if content_type == "image/webp":
        return content.startswith(b"RIFF") and content[8:12] == b"WEBP"
    return any(content.startswith(signature) for signature in SUPPORTED_DOCUMENT_TYPES[content_type])


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


def _strip_0x(value: str | None) -> str | None:
    if value is None:
        return None
    return value[2:].lower() if value.lower().startswith("0x") else value.lower()


def _tx_explorer_url(tx_hash: str | None) -> str | None:
    settings = get_settings()
    if not tx_hash or not settings.blockchain_explorer_tx_url:
        return None
    return settings.blockchain_explorer_tx_url.rstrip("/") + "/" + tx_hash


async def create_and_issue_certificate(db: Session, payload: CertificateCreate, file: UploadFile) -> Certificate:
    settings = get_settings()
    content = await file.read()
    content_type = file.content_type or ""
    if content_type not in SUPPORTED_DOCUMENT_TYPES or not _has_valid_signature(content_type, content):
        raise ValueError("Only PDF, JPEG, PNG, GIF, or WebP certificates are accepted.")
    if len(content) > settings.max_upload_mb * 1024 * 1024:
        raise ValueError("Certificate file is larger than the configured limit.")
    issuer = db.get(Issuer, payload.issuer_id)
    if not issuer or issuer.status != IssuerStatus.APPROVED:
        raise PermissionError("Issuer must be approved before issuing certificates.")
    blockchain = BlockchainService()
    try:
        signer = blockchain.get_signer_for_issuer(issuer.wallet_address)
    except ValueError as exc:
        raise PermissionError(str(exc)) from exc
    if not blockchain.is_approved_issuer(issuer.wallet_address):
        raise PermissionError("Issuer wallet is not approved by the smart contract.")
    recipient = db.scalar(select(Recipient).where(Recipient.email == payload.recipient_email)) or Recipient(
        name=payload.recipient_name, email=str(payload.recipient_email)
    )
    db.add(recipient)
    cert_id = generate_certificate_id(db)
    document_hash = sha256_bytes(content)
    cert_dir = Path(settings.storage_path) / "certificates"
    cert_dir.mkdir(parents=True, exist_ok=True)
    extension = {"application/pdf": ".pdf", "image/jpeg": ".jpg", "image/png": ".png", "image/gif": ".gif", "image/webp": ".webp"}[content_type]
    storage_path = cert_dir / f"{cert_id}{extension}"
    storage_path.write_bytes(content)
    cert_file = CertificateFile(
        original_filename=file.filename or f"{cert_id}.pdf",
        storage_path=str(storage_path),
        content_type=content_type,
        size_bytes=len(content),
        document_hash=document_hash,
    )
    verification_url = f"{settings.next_public_app_url}/verify/{cert_id}"
    receipt = blockchain.issue_certificate(cert_id, document_hash, payload.expiry_date, verification_url, signer=signer)
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
        chain_record: dict = {}
        chain_error: str | None = None
        try:
            chain_record = BlockchainService().verify_certificate(certificate_id)
        except Exception as exc:
            chain_error = str(exc)
        blockchain_found = bool(chain_record.get("record_found"))
        response = VerificationResponse(
            status=VerificationStatus.SUSPICIOUS if blockchain_found else VerificationStatus.NOT_FOUND,
            certificate_id=certificate_id,
            decisive_reason="Blockchain record exists, but application metadata is missing." if blockchain_found else "Certificate could not be found.",
            checks={"certificate_exists": False, "issuer_recognized": False, "blockchain_record_found": blockchain_found, "hash_matches": False},
            technical_details={"chain_record": chain_record, "chain_error": chain_error},
        )
        db.add(VerificationAttempt(certificate_id=certificate_id, uploaded_hash=uploaded_hash, outcome=response.status, ip_address=ip, details=response.model_dump(mode="json")))
        db.commit()
        return response
    chain_record: dict = {}
    chain_error: str | None = None
    try:
        chain_record = BlockchainService().verify_certificate(certificate_id)
    except Exception as exc:
        chain_error = str(exc)
    chain_hash = _strip_0x(chain_record.get("document_hash"))
    expected_hash = chain_hash or cert.file.document_hash.lower()
    document_hash_to_check = uploaded_hash.lower() if uploaded_hash else cert.file.document_hash.lower()
    hash_matches = bool(chain_hash) and document_hash_to_check == expected_hash
    issuer_on_chain = str(chain_record.get("issuer") or "").lower()
    issuer_recognized = (
        cert.issuer.status == IssuerStatus.APPROVED
        and bool(issuer_on_chain)
        and issuer_on_chain == cert.issuer.wallet_address.lower()
    )
    blockchain_found = bool(chain_record.get("record_found"))
    chain_revoked = bool(chain_record.get("revoked"))
    chain_expires_at = int(chain_record.get("expires_at") or 0)
    now = datetime.utcnow()
    expired = (chain_expires_at > 0 and chain_expires_at < int(now.timestamp())) or (chain_expires_at == 0 and cert.expiry_date is not None and cert.expiry_date < now)
    if chain_revoked:
        status = VerificationStatus.REVOKED
        reason = "Certificate has been revoked on-chain."
    elif not blockchain_found:
        status = VerificationStatus.PENDING
        reason = "Blockchain record is missing or unavailable; this certificate cannot be commercially verified yet."
    elif not hash_matches:
        status = VerificationStatus.INVALID
        reason = "Document hash does not match the authoritative blockchain record."
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
            "revoked": chain_revoked,
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
            "not_revoked": not chain_revoked,
            "not_expired": not expired,
        },
        certificate=_summary(cert),
        ai=ai,
        technical_details={
            "uploaded_hash": uploaded_hash,
            "database_hash": cert.file.document_hash,
            "blockchain_hash": chain_hash,
            "chain_issuer": chain_record.get("issuer"),
            "database_issuer_wallet": cert.issuer.wallet_address,
            "network": chain_record.get("network") or (cert.blockchain_transaction.network if cert.blockchain_transaction else None),
            "contract_address": chain_record.get("contract_address") or (cert.blockchain_transaction.contract_address if cert.blockchain_transaction else None),
            "block_number": cert.blockchain_transaction.block_number if cert.blockchain_transaction else None,
            "transaction_hash": cert.blockchain_transaction.transaction_hash if cert.blockchain_transaction else None,
            "explorer_url": _tx_explorer_url(cert.blockchain_transaction.transaction_hash if cert.blockchain_transaction else None),
            "chain_error": chain_error,
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


def revoke_certificate(db: Session, certificate_id: str, reason: str, signer=None) -> Certificate:
    cert = db.scalar(select(Certificate).where(Certificate.certificate_id == certificate_id))
    if not cert:
        raise LookupError("Certificate not found.")
    receipt = BlockchainService().revoke_certificate(certificate_id, signer=signer)
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


def issuer_dashboard(db: Session, email: str) -> dict:
    issuer = db.scalar(select(Issuer).where(Issuer.email == email))
    if not issuer:
        return {"cards": {"total_certificates": 0, "active": 0, "expired": 0, "revoked": 0}, "certificates": []}
    certificates = db.scalars(select(Certificate).where(Certificate.issuer_id == issuer.id).order_by(Certificate.created_at.desc())).all()
    counts = {status.value.lower(): sum(cert.status == status for cert in certificates) for status in CertificateStatus}
    return {
        "cards": {
            "total_certificates": len(certificates),
            "active": counts.get("active", 0),
            "expired": counts.get("expired", 0),
            "revoked": counts.get("revoked", 0),
        },
        "certificates": [_certificate_list_item(cert) for cert in certificates],
    }


def recipient_certificates(db: Session, email: str) -> list[dict]:
    recipient = db.scalar(select(Recipient).where(Recipient.email == email))
    if not recipient:
        return []
    certificates = db.scalars(select(Certificate).where(Certificate.recipient_id == recipient.id).order_by(Certificate.issue_date.desc())).all()
    return [_certificate_list_item(cert) for cert in certificates]


def _certificate_list_item(cert: Certificate) -> dict:
    return {
        "certificate_id": cert.certificate_id,
        "certificate_number": cert.certificate_number,
        "title": cert.title,
        "program": cert.program_name,
        "recipient": cert.recipient.name,
        "issuer": cert.organization.name,
        "issued": cert.issue_date,
        "expires": cert.expiry_date,
        "status": cert.status.value,
        "verification_url": cert.verification_url,
        "transaction_hash": cert.blockchain_transaction.transaction_hash if cert.blockchain_transaction else None,
    }
