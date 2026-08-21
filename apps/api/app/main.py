import logging
import time
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import ai, audit, auth, certificates, dashboard, issuers, verify
from app.core.config import get_settings
from app.db.session import Base, engine
from app.models import domain  # noqa: F401

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
logger = logging.getLogger("verificert")

settings = get_settings()
Base.metadata.create_all(bind=engine)

app = FastAPI(title="VERIFICERT API", version="0.1.0")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "https://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.middleware("http")
async def request_logging(request: Request, call_next):
    request_id = str(uuid4())
    start = time.perf_counter()
    try:
        response = await call_next(request)
    except Exception:
        logger.exception("request_id=%s endpoint=%s error=true", request_id, request.url.path)
        return JSONResponse(status_code=500, content={"error": {"code": "INTERNAL_ERROR", "message": "Unexpected server error."}})
    duration = int((time.perf_counter() - start) * 1000)
    logger.info("request_id=%s endpoint=%s status=%s duration_ms=%s", request_id, request.url.path, response.status_code, duration)
    response.headers["X-Request-ID"] = request_id
    return response


@app.get("/health")
def health() -> dict:
    return {"status": "ok", "demo_mode": settings.demo_mode}


app.include_router(auth.router)
app.include_router(issuers.router)
app.include_router(certificates.router)
app.include_router(verify.router)
app.include_router(ai.router)
app.include_router(dashboard.router)
app.include_router(audit.router)
