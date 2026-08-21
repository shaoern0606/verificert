import enum
import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Index, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class Role(str, enum.Enum):
    ADMIN = "ADMIN"
    ISSUER = "ISSUER"
    RECIPIENT = "RECIPIENT"
    VERIFIER = "VERIFIER"


class IssuerStatus(str, enum.Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    SUSPENDED = "SUSPENDED"
    REJECTED = "REJECTED"


class CertificateStatus(str, enum.Enum):
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    REVOKED = "REVOKED"
    PENDING = "PENDING"
    FAILED = "FAILED"


class VerificationStatus(str, enum.Enum):
    VERIFIED = "VERIFIED"
    INVALID = "INVALID"
    REVOKED = "REVOKED"
    EXPIRED = "EXPIRED"
    NOT_FOUND = "NOT_FOUND"
    PENDING = "PENDING"
    SUSPICIOUS = "SUSPICIOUS"


class AuditAction(str, enum.Enum):
    LOGIN = "LOGIN"
    ISSUE_CERTIFICATE = "ISSUE_CERTIFICATE"
    VERIFY_CERTIFICATE = "VERIFY_CERTIFICATE"
    REVOKE_CERTIFICATE = "REVOKE_CERTIFICATE"
    REGISTER_ISSUER = "REGISTER_ISSUER"
    SUSPEND_ISSUER = "SUSPEND_ISSUER"
    DOWNLOAD_CERTIFICATE = "DOWNLOAD_CERTIFICATE"
    AI_ANALYSIS = "AI_ANALYSIS"


class User(Base):
    __tablename__ = "users"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str] = mapped_column(String(255))
    role: Mapped[Role] = mapped_column(Enum(Role))
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Organization(Base):
    __tablename__ = "organizations"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255), unique=True)
    registration_number: Mapped[str | None] = mapped_column(String(100))
    website: Mapped[str | None] = mapped_column(String(255))


class Issuer(Base):
    __tablename__ = "issuers"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"))
    contact_person: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(255))
    wallet_address: Mapped[str] = mapped_column(String(80), unique=True)
    description: Mapped[str | None] = mapped_column(Text)
    status: Mapped[IssuerStatus] = mapped_column(Enum(IssuerStatus), default=IssuerStatus.PENDING)
    organization: Mapped[Organization] = relationship()


class Recipient(Base):
    __tablename__ = "recipients"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    name: Mapped[str] = mapped_column(String(255))
    email: Mapped[str] = mapped_column(String(255), index=True)


class CertificateFile(Base):
    __tablename__ = "certificate_files"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    original_filename: Mapped[str] = mapped_column(String(255))
    storage_path: Mapped[str] = mapped_column(String(500))
    content_type: Mapped[str] = mapped_column(String(100))
    size_bytes: Mapped[int] = mapped_column(Integer)
    document_hash: Mapped[str] = mapped_column(String(64), index=True)


class BlockchainTransaction(Base):
    __tablename__ = "blockchain_transactions"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    network: Mapped[str] = mapped_column(String(50), default="hardhat-local")
    contract_address: Mapped[str | None] = mapped_column(String(80))
    transaction_hash: Mapped[str] = mapped_column(String(90))
    block_number: Mapped[int | None] = mapped_column(Integer)
    action: Mapped[str] = mapped_column(String(80))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class Certificate(Base):
    __tablename__ = "certificates"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    certificate_id: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    certificate_number: Mapped[str] = mapped_column(String(80))
    title: Mapped[str] = mapped_column(String(255))
    program_name: Mapped[str] = mapped_column(String(255))
    description: Mapped[str | None] = mapped_column(Text)
    issuer_id: Mapped[str] = mapped_column(ForeignKey("issuers.id"), index=True)
    recipient_id: Mapped[str] = mapped_column(ForeignKey("recipients.id"), index=True)
    organization_id: Mapped[str] = mapped_column(ForeignKey("organizations.id"))
    file_id: Mapped[str] = mapped_column(ForeignKey("certificate_files.id"))
    blockchain_transaction_id: Mapped[str | None] = mapped_column(ForeignKey("blockchain_transactions.id"))
    issue_date: Mapped[datetime] = mapped_column(DateTime)
    expiry_date: Mapped[datetime | None] = mapped_column(DateTime)
    status: Mapped[CertificateStatus] = mapped_column(Enum(CertificateStatus), default=CertificateStatus.PENDING, index=True)
    verification_url: Mapped[str] = mapped_column(String(500))
    qr_payload: Mapped[str] = mapped_column(String(500))
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime)
    revocation_reason: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    issuer: Mapped[Issuer] = relationship()
    recipient: Mapped[Recipient] = relationship()
    organization: Mapped[Organization] = relationship()
    file: Mapped[CertificateFile] = relationship()
    blockchain_transaction: Mapped[BlockchainTransaction | None] = relationship()

    __table_args__ = (Index("ix_cert_hash_status", "certificate_id", "status"),)


class VerificationAttempt(Base):
    __tablename__ = "verification_attempts"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    certificate_id: Mapped[str] = mapped_column(String(40), index=True)
    uploaded_hash: Mapped[str | None] = mapped_column(String(64))
    outcome: Mapped[VerificationStatus] = mapped_column(Enum(VerificationStatus))
    ip_address: Mapped[str | None] = mapped_column(String(80))
    details: Mapped[dict] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    actor: Mapped[str] = mapped_column(String(255), default="public")
    role: Mapped[str] = mapped_column(String(30), default="VERIFIER")
    action: Mapped[AuditAction] = mapped_column(Enum(AuditAction))
    certificate_id: Mapped[str | None] = mapped_column(String(40), index=True)
    ip_address: Mapped[str | None] = mapped_column(String(80))
    metadata_json: Mapped[dict] = mapped_column(JSON, default=dict)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)


class AIAnalysisResult(Base):
    __tablename__ = "ai_analysis_results"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    certificate_id: Mapped[str] = mapped_column(String(40), index=True)
    risk_score: Mapped[int] = mapped_column(Integer)
    risk_level: Mapped[str] = mapped_column(String(20))
    result: Mapped[dict] = mapped_column(JSON)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class IssuerWallet(Base):
    __tablename__ = "issuer_wallets"
    id: Mapped[str] = mapped_column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    issuer_id: Mapped[str] = mapped_column(ForeignKey("issuers.id"))
    wallet_address: Mapped[str] = mapped_column(String(80))
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    __table_args__ = (UniqueConstraint("issuer_id", "wallet_address", name="uq_issuer_wallet"),)
