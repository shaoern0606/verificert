from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.services.certificates import verify_certificate

router = APIRouter(prefix="/api/ai", tags=["ai"])


@router.post("/analyze-certificate")
def analyze_certificate(certificate_id: str, db: Session = Depends(get_db)) -> dict:
    return verify_certificate(db, certificate_id).ai.model_dump()
