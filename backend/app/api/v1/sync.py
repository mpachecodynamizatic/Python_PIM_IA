from fastapi import APIRouter, BackgroundTasks, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.product_channel import ChannelRead
from app.schemas.product_sync_history import ProductSyncHistoryRead, ProductSyncStatusRead
from app.schemas.sync_job import SyncJobCreate, SyncJobRead, SyncScheduleUpdate
from app.services import sync_service, channel_service

router = APIRouter(prefix="/sync", tags=["sync"])


@router.get("/channels", response_model=list[ChannelRead])
async def get_available_channels(
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    """Devuelve el catálogo de canales activos disponibles para sincronización."""
    return await channel_service.list_channels(db, active_only=True)


@router.post("/jobs", response_model=SyncJobRead, status_code=201)
async def create_sync_job(
    background_tasks: BackgroundTasks,
    body: SyncJobCreate,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_roles("admin")),
):
    job = await sync_service.create_sync_job(db, body)
    await db.commit()

    background_tasks.add_task(sync_service.run_sync_job, str(job.id))

    return await sync_service.get_sync_job(db, str(job.id))


@router.get("/jobs", response_model=PaginatedResponse[SyncJobRead])
async def list_sync_jobs(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    channel: str | None = None,
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    return await sync_service.list_sync_jobs(db, page=page, size=size, channel=channel, status=status)


@router.get("/jobs/{job_id}", response_model=SyncJobRead)
async def get_sync_job(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    return await sync_service.get_sync_job(db, job_id)


@router.post("/jobs/{job_id}/retry", response_model=SyncJobRead)
async def retry_sync_job(
    job_id: str,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_roles("admin")),
):
    job = await sync_service.retry_sync_job(db, job_id)
    await db.commit()

    background_tasks.add_task(sync_service.run_sync_job, str(job.id))

    return await sync_service.get_sync_job(db, str(job.id))


@router.put("/jobs/{job_id}/schedule", response_model=SyncJobRead)
async def update_job_schedule(
    job_id: str,
    body: SyncScheduleUpdate,
    db: AsyncSession = Depends(get_db),
    _admin: User = Depends(require_roles("admin")),
):
    await sync_service.update_schedule(db, job_id, body.cron_expression, body.enabled)
    await db.commit()
    return await sync_service.get_sync_job(db, job_id)


# ---------------------------------------------------------------------------
# Product sync history endpoints
# ---------------------------------------------------------------------------
@router.get("/history/product/{sku}", response_model=PaginatedResponse[ProductSyncHistoryRead])
async def get_product_sync_history(
    sku: str,
    channel: str | None = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    return await sync_service.get_product_sync_history(db, sku, channel=channel, page=page, size=size)


@router.get("/history/product/{sku}/status", response_model=list[ProductSyncStatusRead])
async def get_product_sync_status(
    sku: str,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    return await sync_service.get_product_sync_status(db, sku)


@router.get("/history/channel/{channel}", response_model=PaginatedResponse[ProductSyncHistoryRead])
async def get_channel_sync_history(
    channel: str,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    return await sync_service.get_channel_sync_history(db, channel, page=page, size=size)

