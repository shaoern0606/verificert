from datetime import datetime
from pathlib import Path

from app.core.security import hash_password
from app.core.config import get_settings
from app.db.session import Base, SessionLocal, engine
from app.models.domain import BlockchainTransaction, Certificate, CertificateFile, CertificateStatus, Issuer, IssuerStatus, Organization, Recipient, Role, User
from app.services.blockchain import BlockchainService
from app.services.hashing import sha256_bytes


DEMO_CERTIFICATE_ID = "CERT-2026-105F0A"
ISSUER_ACCOUNTS = {
    "issuer@abc-academy.local": "ABC Academy Issuer",
    "registrar@northbridge.example": "Northbridge Registrar",
    "certificates@cloudskills-academy.local": "CloudSkills Academy Coordinator",
    "admin@brightpath-institute.local": "BrightPath Institute Administrator",
    "verification@techbridge-academy.local": "TechBridge Academy Verifier",
    "pending@abc-academy.local": "Pending Officer",
    "suspended@northbridge.example": "Suspended Officer",
}
ISSUER_SEED_STATUSES = {
    "issuer@abc-academy.local": IssuerStatus.APPROVED,
    "registrar@northbridge.example": IssuerStatus.APPROVED,
    "certificates@cloudskills-academy.local": IssuerStatus.APPROVED,
    "admin@brightpath-institute.local": IssuerStatus.APPROVED,
    "verification@techbridge-academy.local": IssuerStatus.APPROVED,
    "pending@abc-academy.local": IssuerStatus.PENDING,
    "suspended@northbridge.example": IssuerStatus.SUSPENDED,
}
ISSUER_SEED_DETAILS = {
    "issuer@abc-academy.local": ("ABC Academy", "Alicia Chen", "0x70997970C51812dc3A010C7d01b50e0d17dc79C8"),
    "registrar@northbridge.example": ("Northbridge University", "Dr Maya Rao", "0x3C44CdDdB6a900fa2b585dd299e03d12FA4293BC"),
    "certificates@cloudskills-academy.local": ("CloudSkills Academy", "Ken Lim", "0x90F79bf6EB2c4f870365E785982E1f101E93b906"),
    "admin@brightpath-institute.local": ("BrightPath Institute", "BrightPath Admin", "0x15d34AAf54267DB7D7c367839AAf71A00a2C6A65"),
    "verification@techbridge-academy.local": ("TechBridge Academy", "TechBridge Verifier", "0x9965507D1a55bcC2695C58ba16FB37d819B0A4dc"),
    "pending@abc-academy.local": ("ABC Academy", "Pending Officer", "0x4444444444444444444444444444444444444444"),
    "suspended@northbridge.example": ("Northbridge University", "Suspended Officer", "0x5555555555555555555555555555555555555555"),
}


def ensure_issuer_accounts(db) -> None:
    if db.query(User).filter_by(email="certificates@cloudskills-academy.local").first() is None:
        db.query(User).filter_by(email="certs@cloudskills.example").update(
            {"email": "certificates@cloudskills-academy.local", "full_name": ISSUER_ACCOUNTS["certificates@cloudskills-academy.local"]},
            synchronize_session=False,
        )
        db.flush()
    for email, full_name in ISSUER_ACCOUNTS.items():
        if not db.query(User).filter_by(email=email).first():
            db.add(User(email=email, full_name=full_name, role=Role.ISSUER, password_hash=hash_password("Password123!")))
            db.flush()
        issuer = db.query(Issuer).filter_by(email=email).first()
        if not issuer and email == "certificates@cloudskills-academy.local":
            db.query(Issuer).filter_by(email="certs@cloudskills.example").update({"email": email}, synchronize_session=False)
            db.flush()
            issuer = db.query(Issuer).filter_by(email=email).first()
        if issuer:
            issuer.status = ISSUER_SEED_STATUSES[email]
            issuer.wallet_address = ISSUER_SEED_DETAILS[email][2]
    db.commit()


def ensure_issuer_profiles(db) -> None:
    for email, (organization_name, contact_person, wallet_address) in ISSUER_SEED_DETAILS.items():
        organization = db.query(Organization).filter_by(name=organization_name).first()
        if not organization:
            organization = Organization(name=organization_name)
            db.add(organization)
            db.flush()
        issuer = db.query(Issuer).filter_by(email=email).first()
        if not issuer:
            issuer = Issuer(email=email, organization=organization, contact_person=contact_person, wallet_address=wallet_address, status=ISSUER_SEED_STATUSES[email])
            db.add(issuer)
        else:
            issuer.organization = organization
            issuer.wallet_address = wallet_address
            issuer.status = ISSUER_SEED_STATUSES[email]
    db.commit()


def ensure_demo_certificate(db) -> None:
    settings = get_settings()
    if not settings.verificert_contract_address or not settings.blockchain_private_key:
        print("Demo certificate skipped: blockchain configuration is incomplete.")
        return
    fixture = Path(__file__).resolve().parents[2] / "fixtures" / "demo-certificate.pdf"
    content = fixture.read_bytes()
    document_hash = sha256_bytes(content)
    issuer = db.query(Issuer).filter_by(email="issuer@abc-academy.local").first()
    recipient = db.query(Recipient).filter_by(email="john.tan@example.com").first()
    if not issuer or not recipient:
        return
    certificate = db.query(Certificate).filter_by(certificate_id=DEMO_CERTIFICATE_ID).first()
    blockchain = BlockchainService()
    chain = blockchain.verify_certificate(DEMO_CERTIFICATE_ID)
    if certificate and chain.get("record_found"):
        return
    if not certificate:
        storage_path = Path(settings.storage_path) / "certificates" / f"{DEMO_CERTIFICATE_ID}.pdf"
        storage_path.parent.mkdir(parents=True, exist_ok=True)
        storage_path.write_bytes(content)
        cert_file = CertificateFile(original_filename="demo-certificate.pdf", storage_path=str(storage_path), content_type="application/pdf", size_bytes=len(content), document_hash=document_hash)
        certificate = Certificate(
            certificate_id=DEMO_CERTIFICATE_ID,
            certificate_number="DEMO-2026-001",
            title="Local Demo Certificate",
            program_name="Blockchain Verification Demo",
            description="Local development fixture.",
            issuer=issuer,
            recipient=recipient,
            organization=issuer.organization,
            file=cert_file,
            issue_date=datetime(2026, 1, 1),
            status=CertificateStatus.ACTIVE,
            verification_url=f"{settings.next_public_app_url}/verify/{DEMO_CERTIFICATE_ID}",
            qr_payload=f"{settings.next_public_app_url}/verify/{DEMO_CERTIFICATE_ID}",
        )
        db.add(cert_file)
    receipt = blockchain.issue_certificate(DEMO_CERTIFICATE_ID, document_hash, None, certificate.verification_url)
    tx = BlockchainTransaction(network=receipt.network, contract_address=receipt.contract_address, transaction_hash=receipt.transaction_hash, block_number=receipt.block_number, action="ISSUE_CERTIFICATE")
    certificate.blockchain_transaction = tx
    certificate.file.document_hash = document_hash
    db.add(tx)
    db.add(certificate)
    db.commit()
    print(f"Ensured demo certificate {DEMO_CERTIFICATE_ID} is backed by PostgreSQL and blockchain.")


def run() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(User).count():
            ensure_issuer_accounts(db)
            ensure_issuer_profiles(db)
            ensure_demo_certificate(db)
            print("Seed data already exists.")
            return
        users = [
            User(email="admin@verificert.local", full_name="VerifiCert Admin", role=Role.ADMIN, password_hash=hash_password("Password123!")),
            User(email="john.tan@example.com", full_name="John Tan", role=Role.RECIPIENT, password_hash=hash_password("Password123!")),
        ]
        users.extend(User(email=email, full_name=full_name, role=Role.ISSUER, password_hash=hash_password("Password123!")) for email, full_name in ISSUER_ACCOUNTS.items())
        orgs = [
            Organization(name="ABC Academy", registration_number="MY-ABC-001", website="https://abc-academy.example"),
            Organization(name="Northbridge University", registration_number="NB-2026", website="https://northbridge.example"),
            Organization(name="Cloud Skills Council", registration_number="CSC-88", website="https://cloudskills.example"),
            Organization(name="BrightPath Institute", registration_number="BPI-2026", website="https://brightpath.example"),
            Organization(name="TechBridge Academy", registration_number="TBA-2026", website="https://techbridge.example"),
        ]
        db.add_all(users + orgs)
        db.flush()
        recipients = [Recipient(name=name, email=f"{name.lower().replace(' ', '.')}@example.com") for name in ["John Tan", "Priya Singh", "Nur Aisyah", "Alex Wong", "Mei Lin", "Sara Lee", "Daniel Ong", "Fatima Rahman", "Lucas Teo", "Emily Chan"]]
        db.add_all(recipients)
        db.flush()
        db.commit()
        ensure_issuer_profiles(db)
        ensure_demo_certificate(db)
        print("Seeded users, organizations, issuers, and recipients. Certificates must be issued through the API so every record is backed by a real blockchain transaction.")
    finally:
        db.close()


if __name__ == "__main__":
    run()
