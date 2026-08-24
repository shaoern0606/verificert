from datetime import datetime
from secrets import token_hex

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.domain import Certificate


def generate_certificate_id(db: Session) -> str:
    year = datetime.utcnow().year
    for _ in range(10):
        entropy = token_hex(3).upper()
        candidate = f"CERT-{year}-{entropy}"
        if not db.scalar(select(Certificate).where(Certificate.certificate_id == candidate)):
            return candidate
    raise RuntimeError("Unable to generate unique certificate ID")
