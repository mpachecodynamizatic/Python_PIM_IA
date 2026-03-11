import asyncio
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from sqlalchemy import select

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import AsyncSessionLocal, engine
from app.core.security import hash_password
from app.models.base import Base
from app.models.user import User
from app.schemas.common import ErrorDetail

# Import all models so they register with Base.metadata
from app.models import (  # noqa: F401
    audit,
    category,
    import_job,
    mapping_template,
    media,
    product,
    product_sync_history,
    sync_job,
    attribute_family,
    quality_rule,
    saved_view,
    product_comment,
    brand,
    product_logistics,
    product_compliance,
    channel,
    product_channel,
    supplier,
    external_taxonomy,
)

UPLOAD_DIR = Path(__file__).parent.parent / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: create tables when enabled (development by default; use Alembic in production).
    if settings.RUN_DB_INIT:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

    # Seed admin user if not exists
    async with AsyncSessionLocal() as session:
        result = await session.execute(select(User).where(User.email == settings.ADMIN_EMAIL))
        user = result.scalar_one_or_none()
        if user is None:
            admin = User(
                email=settings.ADMIN_EMAIL,
                hashed_password=hash_password(settings.ADMIN_PASSWORD),
                full_name="Admin",
                role="admin",
                scopes=[
                    "products:read",
                    "products:write",
                    "media:write",
                    "taxonomy:write",
                    "syndication:run",
                    "quality:read",
                ],
            )
            session.add(admin)
        else:
            user.hashed_password = hash_password(settings.ADMIN_PASSWORD)
        await session.commit()

    # Background scheduler for retries & cron jobs (runs every 30 seconds)
    from app.services.sync_service import process_pending_retries, process_scheduled_jobs

    async def _scheduler_loop():
        while True:
            try:
                await process_pending_retries()
                await process_scheduled_jobs()
            except Exception:
                pass  # scheduler should never crash
            await asyncio.sleep(30)

    scheduler_task = asyncio.create_task(_scheduler_loop())

    yield

    # Shutdown
    scheduler_task.cancel()
    await engine.dispose()


app = FastAPI(
    title=settings.PROJECT_NAME,
    version="0.1.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix=settings.API_V1_PREFIX)

# Serve uploaded files as static assets
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")


@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException):
    detail = exc.detail if isinstance(exc.detail, str) else "Unexpected error"
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorDetail(detail=detail).model_dump(),
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, __: RequestValidationError):
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=ErrorDetail(detail="Validation error", code="validation_error").model_dump(),
    )


@app.get("/")
async def root():
    return RedirectResponse(url="/docs")


@app.get("/health")
async def health():
    return {"status": "ok"}
