from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import require_role
from app.db.session import get_db
from app.models.domain import Role
from app.services.certificates import admin_dashboard

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("/admin")
def get_admin_dashboard(db: Session = Depends(get_db), _=Depends(require_role(Role.ADMIN))) -> dict:
    return admin_dashboard(db)


@router.get("/issuer")
def get_issuer_dashboard(db: Session = Depends(get_db), _=Depends(require_role(Role.ISSUER, Role.ADMIN))) -> dict:
    return admin_dashboard(db)
