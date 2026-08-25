from fastapi import APIRouter, Depends, File, Query, Request, UploadFile
from sqlalchemy.orm import Session

from app.api.deps import optional_api_key
from app.core.rate_limit import limiter
from app.db.session import get_db
from app.models.domain import ApiKey
from app.schemas.domain import VerificationResponse
from app.services.certificates import verify_by_document, verify_certificate

router = APIRouter(prefix="/api/verify", tags=["verification"])


def _actor(api_key: ApiKey | None) -> str:
    return f"api:{api_key.label}" if api_key else "public"


@router.get("/{certificate_id}", response_model=VerificationResponse)
@limiter.limit("30/minute")
def verify_by_id(certificate_id: str, request: Request, db: Session = Depends(get_db), api_key: ApiKey | None = Depends(optional_api_key)) -> VerificationResponse:
    return verify_certificate(db, certificate_id, ip=request.client.host if request.client else None, actor=_actor(api_key))


@router.post("", response_model=VerificationResponse)
@limiter.limit("30/minute")
async def verify_post(certificate_id: str, request: Request, db: Session = Depends(get_db), api_key: ApiKey | None = Depends(optional_api_key)) -> VerificationResponse:
    return verify_certificate(db, certificate_id, ip=request.client.host if request.client else None, actor=_actor(api_key))


@router.post("/upload", response_model=VerificationResponse)
@limiter.limit("15/minute")
async def verify_upload(
    request: Request,
    file: UploadFile = File(...),
    certificate_id: str | None = Query(default=None),
    db: Session = Depends(get_db),
    api_key: ApiKey | None = Depends(optional_api_key),
) -> VerificationResponse:
    content = await file.read()
    ip = request.client.host if request.client else None
    actor = _actor(api_key)
    if certificate_id:
        return verify_certificate(db, certificate_id, uploaded_bytes=content, uploaded_content_type=file.content_type, ip=ip, actor=actor)
    return verify_by_document(db, content, content_type=file.content_type, ip=ip, actor=actor)
