from datetime import datetime, timedelta
from pathlib import Path

from app.core.security import hash_password
from app.db.session import Base, SessionLocal, engine
from app.models.domain import BlockchainTransaction, Certificate, CertificateFile, CertificateStatus, Issuer, IssuerStatus, Organization, Recipient, User, Role
from app.services.hashing import sha256_bytes


def fake_pdf(text: str) -> bytes:
    return b"%PDF-1.4\n1 0 obj<</Type/Catalog>>endobj\n% " + text.encode() + b"\n%%EOF"


def run() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        if db.query(User).count():
            print("Seed data already exists.")
            return
        users = [
            User(email="admin@verificert.local", full_name="VerifiCert Admin", role=Role.ADMIN, password_hash=hash_password("Password123!")),
            User(email="issuer@abc-academy.local", full_name="ABC Academy Issuer", role=Role.ISSUER, password_hash=hash_password("Password123!")),
            User(email="john.tan@example.com", full_name="John Tan", role=Role.RECIPIENT, password_hash=hash_password("Password123!")),
        ]
        orgs = [
            Organization(name="ABC Academy", registration_number="MY-ABC-001", website="https://abc-academy.example"),
            Organization(name="Northbridge University", registration_number="NB-2026", website="https://northbridge.example"),
            Organization(name="Cloud Skills Council", registration_number="CSC-88", website="https://cloudskills.example"),
        ]
        db.add_all(users + orgs)
        db.flush()
        issuers = [
            Issuer(organization=orgs[0], contact_person="Alicia Chen", email="issuer@abc-academy.local", wallet_address="0x1111111111111111111111111111111111111111", status=IssuerStatus.APPROVED, description="Technology training provider."),
            Issuer(organization=orgs[1], contact_person="Dr Maya Rao", email="registrar@northbridge.example", wallet_address="0x2222222222222222222222222222222222222222", status=IssuerStatus.APPROVED),
            Issuer(organization=orgs[2], contact_person="Ken Lim", email="certs@cloudskills.example", wallet_address="0x3333333333333333333333333333333333333333", status=IssuerStatus.APPROVED),
            Issuer(organization=orgs[0], contact_person="Pending Officer", email="pending@abc-academy.local", wallet_address="0x4444444444444444444444444444444444444444", status=IssuerStatus.PENDING),
            Issuer(organization=orgs[1], contact_person="Suspended Officer", email="suspended@northbridge.example", wallet_address="0x5555555555555555555555555555555555555555", status=IssuerStatus.SUSPENDED),
        ]
        recipients = [Recipient(name=name, email=f"{name.lower().replace(' ', '.')}@example.com") for name in ["John Tan", "Priya Singh", "Nur Aisyah", "Alex Wong", "Mei Lin", "Sara Lee", "Daniel Ong", "Fatima Rahman", "Lucas Teo", "Emily Chan"]]
        db.add_all(issuers + recipients)
        db.flush()
        storage = Path("./storage/certificates")
        storage.mkdir(parents=True, exist_ok=True)
        statuses = [CertificateStatus.ACTIVE] * 20 + [CertificateStatus.EXPIRED] * 5 + [CertificateStatus.REVOKED] * 5
        for idx, status in enumerate(statuses, start=1):
            cert_id = f"CERT-2026-{idx:06d}"
            recipient = recipients[(idx - 1) % len(recipients)]
            issuer = issuers[(idx - 1) % 3]
            pdf = fake_pdf(f"{cert_id} {recipient.name} Advanced Python Programming")
            path = storage / f"{cert_id}.pdf"
            path.write_bytes(pdf)
            file = CertificateFile(original_filename=f"{cert_id}.pdf", storage_path=str(path), content_type="application/pdf", size_bytes=len(pdf), document_hash=sha256_bytes(pdf))
            tx = BlockchainTransaction(transaction_hash="0x" + sha256_bytes(cert_id.encode())[:64], block_number=1000 + idx, contract_address="0x0000000000000000000000000000000000000000", action="ISSUE_CERTIFICATE")
            cert = Certificate(
                certificate_id=cert_id,
                certificate_number=f"ABC-{idx:05d}",
                title="Professional Certificate",
                program_name="Advanced Python Programming" if idx == 1 else f"Credential Program {idx}",
                issuer=issuer,
                recipient=recipient,
                organization=issuer.organization,
                file=file,
                blockchain_transaction=tx,
                issue_date=datetime(2026, 8, 22) - timedelta(days=idx),
                expiry_date=datetime.utcnow() - timedelta(days=1) if status == CertificateStatus.EXPIRED else datetime.utcnow() + timedelta(days=365),
                status=status,
                verification_url=f"http://localhost:3000/verify/{cert_id}",
                qr_payload=f"http://localhost:3000/verify/{cert_id}",
                revoked_at=datetime.utcnow() if status == CertificateStatus.REVOKED else None,
                revocation_reason="Certificate issued in error" if status == CertificateStatus.REVOKED else None,
            )
            db.add_all([file, tx, cert])
        modified = storage / "CERT-2026-000001-modified.pdf"
        modified.write_bytes(fake_pdf("CERT-2026-000001 Jane Tan Advanced Python Programming"))
        db.commit()
        print("Seeded VERIFICERT demo data.")
    finally:
        db.close()


if __name__ == "__main__":
    run()
