from datetime import datetime
from enum import Enum

from pydantic import BaseModel, EmailStr, Field


class VerificationStatus(str, Enum):
    VERIFIED = "VERIFIED"
    INVALID = "INVALID"
    REVOKED = "REVOKED"
    EXPIRED = "EXPIRED"
    NOT_FOUND = "NOT_FOUND"
    PENDING = "PENDING"
    SUSPICIOUS = "SUSPICIOUS"


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    role: str


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: str
    role: str = "RECIPIENT"


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class IssuerCreate(BaseModel):
    organization_name: str
    registration_number: str | None = None
    contact_person: str
    email: EmailStr
    website: str | None = None
    wallet_address: str
    description: str | None = None


class CertificateCreate(BaseModel):
    recipient_name: str
    recipient_email: EmailStr
    course_name: str
    certificate_title: str
    issue_date: datetime
    expiry_date: datetime | None = None
    certificate_number: str
    description: str | None = None
    issuer_id: str


class CertificateSummary(BaseModel):
    certificate_id: str
    recipient: str
    program: str
    issuer: str
    issued: datetime
    expires: datetime | None
    status: str
    document_hash: str
    verification_url: str
    transaction_hash: str | None = None


class VerificationRiskAssessment(BaseModel):
    risk_score: int = Field(ge=0, le=100)
    risk_level: str
    hash_match: bool
    issuer_match: bool
    certificate_id_match: bool
    blockchain_record_found: bool
    revoked: bool
    expired: bool
    issues: list[str]
    recommendations: list[str]
    facts: list[str] = []
    inferences: list[str] = []
    unknowns: list[str] = []


class VerificationResponse(BaseModel):
    status: VerificationStatus
    certificate_id: str
    decisive_reason: str
    checks: dict[str, bool]
    certificate: CertificateSummary | None = None
    ai: VerificationRiskAssessment | None = None
    technical_details: dict = {}


class RevokeRequest(BaseModel):
    reason: str = Field(min_length=6)


class DashboardResponse(BaseModel):
    cards: dict[str, int]
    charts: dict[str, list[dict]]
