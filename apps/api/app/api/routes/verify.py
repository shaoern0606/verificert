from fastapi import APIRouter, Depends, File, Request, UploadFile
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.schemas.domain import VerificationResponse
from app.services.certificates import verify_certificate

router = APIRouter(prefix="/api/verify", tags=["verification"])


@router.get("/{certificate_id}", response_model=VerificationResponse)
def verify_by_id(certificate_id: str, request: Request, db: Session = Depends(get_db)) -> VerificationResponse:
    return verify_certificate(db, certificate_id, ip=request.client.host if request.client else None)


@router.post("", response_model=VerificationResponse)
async def verify_post(certificate_id: str, request: Request, db: Session = Depends(get_db)) -> VerificationResponse:
    return verify_certificate(db, certificate_id, ip=request.client.host if request.client else None)


@router.post("/upload", response_model=VerificationResponse)
async def verify_upload(certificate_id: str, request: Request, file: UploadFile = File(...), db: Session = Depends(get_db)) -> VerificationResponse:
    return verify_certificate(db, certificate_id, uploaded_bytes=await file.read(), ip=request.client.host if request.client else None)
