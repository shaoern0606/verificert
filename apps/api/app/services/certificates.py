import csv
import io
import logging
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
from app.services.certificate_template import generate_certificate_pdf
from app.services.email import certificate_issued_email, certificate_revoked_email, send_email
from app.services.hashing import sha256_bytes
from app.services.id_service import generate_certificate_id
from app.services.pdf_stamp import stamp_pdf_with_qr

BULK_CSV_REQUIRED_COLUMNS: Final[set[str]] = {"recipient_name", "recipient_email", "course_name", "certificate_title", "certificate_number", "issue_date"}


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
    content = await file.read()
    return issue_certificate_from_bytes(db, payload, content, file.content_type or "", file.filename)


def issue_certificate_from_bytes(db: Session, payload: CertificateCreate, content: bytes, content_type: str, filename: str | None) -> Certificate:
    settings = get_settings()
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
    verification_url = f"{settings.next_public_app_url}/verify/{cert_id}"
    if content_type == "application/pdf":
        try:
            content = stamp_pdf_with_qr(content, verification_url)
        except Exception as exc:  # malformed PDFs shouldn't block issuance
            logging.getLogger("verificert").warning("qr_stamp_failed cert_id=%s error=%s", cert_id, exc)
    document_hash = sha256_bytes(content)
    cert_dir = Path(settings.storage_path) / "certificates"
    cert_dir.mkdir(parents=True, exist_ok=True)
    extension = {"application/pdf": ".pdf", "image/jpeg": ".jpg", "image/png": ".png", "image/gif": ".gif", "image/webp": ".webp"}[content_type]
    storage_path = cert_dir / f"{cert_id}{extension}"
    storage_path.write_bytes(content)
    cert_file = CertificateFile(
        original_filename=filename or f"{cert_id}.pdf",
        storage_path=str(storage_path),
        content_type=content_type,
        size_bytes=len(content),
        document_hash=document_hash,
    )
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
    send_email(recipient.email, f"Your certificate: {cert.title}", certificate_issued_email(recipient.name, cert.title, issuer.organization.name, verification_url))
    return cert


def bulk_issue_certificates(db: Session, issuer_id: str, csv_bytes: bytes) -> dict:
    issuer = db.get(Issuer, issuer_id)
    if not issuer:
        raise ValueError("Issuer not found.")
    reader = csv.DictReader(io.StringIO(csv_bytes.decode("utf-8-sig")))
    columns = set(reader.fieldnames or [])
    missing = BULK_CSV_REQUIRED_COLUMNS - columns
    if missing:
        raise ValueError(f"CSV is missing required columns: {', '.join(sorted(missing))}")
    issued: list[dict] = []
    failed: list[dict] = []
    for index, row in enumerate(reader, start=2):  # row 1 is the header
        try:
            issue_date = datetime.fromisoformat(row["issue_date"].strip())
            expiry_raw = (row.get("expiry_date") or "").strip()
            expiry_date = datetime.fromisoformat(expiry_raw) if expiry_raw else None
            payload = CertificateCreate(
                recipient_name=row["recipient_name"].strip(),
                recipient_email=row["recipient_email"].strip(),
                course_name=row["course_name"].strip(),
                certificate_title=row["certificate_title"].strip(),
                issue_date=issue_date,
                expiry_date=expiry_date,
                certificate_number=row["certificate_number"].strip(),
                description=(row.get("description") or "").strip() or None,
                issuer_id=issuer_id,
            )
            pdf_bytes = generate_certificate_pdf(
                recipient_name=payload.recipient_name,
                course_name=payload.course_name,
                certificate_title=payload.certificate_title,
                organization_name=issuer.organization.name,
                certificate_number=payload.certificate_number,
                issue_date=issue_date.date().isoformat(),
            )
            cert = issue_certificate_from_bytes(db, payload, pdf_bytes, "application/pdf", f"{payload.certificate_number}.pdf")
            issued.append({"row": index, "certificate_id": cert.certificate_id, "recipient_email": payload.recipient_email})
        except Exception as exc:
            db.rollback()
            failed.append({"row": index, "error": str(exc)})
    return {"issued": issued, "failed": failed}


def _expected_metadata(cert: Certificate) -> dict:
    return {
        "recipient_name": cert.recipient.name,
        "course_name": cert.program_name,
        "certificate_title": cert.title,
        "certificate_number": cert.certificate_number,
        "issuer_organization": cert.organization.name,
    }


def _ai_state_fields(db: Session, cert: Certificate, uploaded_bytes: bytes | None = None, uploaded_content_type: str | None = None) -> dict:
    if uploaded_bytes:
        return {
            "document_bytes": uploaded_bytes,
            "document_content_type": uploaded_content_type or cert.file.content_type,
            "expected_metadata": _expected_metadata(cert),
        }
    latest = db.scalar(
        select(AIAnalysisResult).where(AIAnalysisResult.certificate_id == cert.certificate_id).order_by(AIAnalysisResult.created_at.desc())
    )
    cached = latest.result.get("ai_document_review") if latest else None
    if cached and cached.get("document_hash") == cert.file.document_hash:
        return {
            "ai_available": cached["available"],
            "metadata_match": cached["metadata_match"],
            "extracted_metadata": cached["extracted_fields"],
            "ai_issues": cached["ai_issues"],
            "ai_notes": cached["ai_notes"],
        }
    try:
        document_bytes = Path(cert.file.storage_path).read_bytes()
    except OSError:
        return {}
    return {
        "document_bytes": document_bytes,
        "document_content_type": cert.file.content_type,
        "expected_metadata": _expected_metadata(cert),
    }


def verify_by_document(db: Session, content: bytes, content_type: str | None = None, ip: str | None = None, actor: str = "public") -> VerificationResponse:
    document_hash = sha256_bytes(content)
    cert = db.scalar(select(Certificate).join(CertificateFile, Certificate.file_id == CertificateFile.id).where(CertificateFile.document_hash == document_hash))
    if cert:
        return verify_certificate(db, cert.certificate_id, uploaded_bytes=content, uploaded_content_type=content_type, ip=ip, actor=actor)
    response = VerificationResponse(
        status=VerificationStatus.NOT_FOUND,
        certificate_id="",
        decisive_reason="No certificate matches this document's hash.",
        checks={"certificate_exists": False, "issuer_recognized": False, "blockchain_record_found": False, "hash_matches": False},
        technical_details={"uploaded_hash": document_hash},
    )
    db.add(VerificationAttempt(certificate_id="", uploaded_hash=document_hash, outcome=response.status, ip_address=ip, details=response.model_dump(mode="json")))
    db.commit()
    return response


def verify_certificate(db: Session, certificate_id: str, uploaded_bytes: bytes | None = None, uploaded_content_type: str | None = None, ip: str | None = None, actor: str = "public") -> VerificationResponse:
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
    # The chain has no record for this certificate (e.g. a local dev chain was reset after
    # issuance) but our own database still has the last known administrative status — trust
    # that over silently reporting "not revoked" just because the chain lookup came back empty.
    revoked = chain_revoked or (not blockchain_found and cert.status == CertificateStatus.REVOKED)
    chain_expires_at = int(chain_record.get("expires_at") or 0)
    now = datetime.utcnow()
    expired = (chain_expires_at > 0 and chain_expires_at < int(now.timestamp())) or (chain_expires_at == 0 and cert.expiry_date is not None and cert.expiry_date < now)
    if revoked:
        status = VerificationStatus.REVOKED
        reason = "Certificate has been revoked on-chain." if chain_revoked else "Certificate was revoked; the blockchain record is currently unavailable to confirm it live."
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
            "revoked": revoked,
            "expired": expired,
            **_ai_state_fields(db, cert, uploaded_bytes, uploaded_content_type),
        }
    )
    ai_document_review = {
        "document_hash": cert.file.document_hash if (not uploaded_bytes or hash_matches) else None,
        "available": ai.ai_available,
        "metadata_match": ai.metadata_match,
        "extracted_fields": ai.extracted_metadata,
        "ai_issues": ai.ai_discrepancies,
        "ai_notes": ai.unknowns,
    }
    response = VerificationResponse(
        status=status,
        certificate_id=certificate_id,
        decisive_reason=reason,
        checks={
            "certificate_exists": True,
            "issuer_recognized": issuer_recognized,
            "blockchain_record_found": blockchain_found,
            "hash_matches": hash_matches,
            "not_revoked": not revoked,
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
            AuditLog(actor=actor, role="VERIFIER", action=AuditAction.VERIFY_CERTIFICATE, certificate_id=certificate_id, ip_address=ip),
            AIAnalysisResult(
                certificate_id=certificate_id,
                risk_score=ai.risk_score,
                risk_level=ai.risk_level,
                result={**ai.model_dump(), "ai_document_review": ai_document_review},
            ),
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
    send_email(cert.recipient.email, f"Certificate revoked: {cert.title}", certificate_revoked_email(cert.recipient.name, cert.title, cert.organization.name, reason))
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
