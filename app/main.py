import logging
import os
import time
import uuid

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import text

from app.api.auth import router as auth_router
from app.api.chat import router as chat_router
from app.api.meta import router as meta_router
from app.api.oauth import router as oauth_router
from app.api.profiles import router as profiles_router
from app.api.recommendations import router as recommendations_router
from app.api.team_projects import router as team_projects_router
from app.api.users import router as users_router
from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.core.rate_limit import InMemoryRateLimiter

settings = get_settings()

logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s %(levelname)s [%(name)s] %(message)s",
)
logger = logging.getLogger("devmatch")

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Developer matching and recommendation platform",
)

cors_origins = settings.CORS_ORIGINS
allow_credentials = True
if cors_origins == ["*"]:
    # Browsers reject wildcard origins combined with credentials.
    allow_credentials = False

app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=allow_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.add_middleware(GZipMiddleware, minimum_size=1024)
app.add_middleware(InMemoryRateLimiter)


@app.middleware("http")
async def request_context_middleware(request: Request, call_next):
    request_id = request.headers.get("x-request-id", uuid.uuid4().hex[:12])
    start = time.perf_counter()
    response = await call_next(request)
    elapsed_ms = (time.perf_counter() - start) * 1000
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    logger.info(
        "%s %s -> %s (%.1fms) rid=%s",
        request.method,
        request.url.path,
        response.status_code,
        elapsed_ms,
        request_id,
    )
    return response

register_exception_handlers(app)

app.include_router(auth_router, prefix="/api/v1")
app.include_router(chat_router, prefix="/api/v1")
app.include_router(meta_router, prefix="/api/v1")
app.include_router(oauth_router, prefix="/api/v1")
app.include_router(users_router, prefix="/api/v1")
app.include_router(profiles_router, prefix="/api/v1")
app.include_router(recommendations_router, prefix="/api/v1")
app.include_router(team_projects_router, prefix="/api/v1")


@app.get("/health")
def health():
    return {"status": "healthy", "version": settings.APP_VERSION}


@app.get("/readyz")
def readyz():
    try:
        from app.db.session import engine

        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
    except Exception:
        return JSONResponse(
            status_code=503, content={"status": "not_ready"}
        )
    return {"status": "ready"}


FRONTEND_DIR = settings.FRONTEND_DIR

if os.path.isdir(FRONTEND_DIR):
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIR, "assets")), name="assets")

    @app.get("/favicon.svg", include_in_schema=False)
    def serve_favicon():
        favicon = os.path.join(FRONTEND_DIR, "favicon.svg")
        if not os.path.isfile(favicon):
            return JSONResponse(status_code=404, content={"detail": "Not found"})
        return FileResponse(favicon, media_type="image/svg+xml")

    @app.get("/", include_in_schema=False)
    def serve_spa():
        index_file = os.path.join(FRONTEND_DIR, "index.html")
        if not os.path.isfile(index_file):
            return JSONResponse(
                status_code=503, content={"detail": "Frontend not built"}
            )
        return FileResponse(index_file)

    @app.get("/{full_path:path}", include_in_schema=False)
    def serve_spa_catch_all(full_path: str):
        # Never swallow API or health-check 404s with index.html.
        if full_path.startswith("api/") or full_path in (
            "health",
            "readyz",
            "docs",
            "openapi.json",
            "redoc",
        ):
            return JSONResponse(status_code=404, content={"detail": "Not found"})
        index_file = os.path.join(FRONTEND_DIR, "index.html")
        if not os.path.isfile(index_file):
            return JSONResponse(
                status_code=503, content={"detail": "Frontend not built"}
            )
        return FileResponse(index_file)
