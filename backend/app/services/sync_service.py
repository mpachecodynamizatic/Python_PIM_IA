import asyncio
import logging
from datetime import datetime, timedelta, timezone

from croniter import croniter
from sqlalchemy import distinct, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.connectors.csv_connector import CsvConnector
from app.connectors.http_connector import HttpConnector
from app.models.product_sync_history import ProductSyncHistory
from app.models.sync_job import SyncJob
from app.schemas.common import PaginatedResponse
from app.schemas.product_sync_history import ProductSyncHistoryRead, ProductSyncStatusRead
from app.schemas.sync_job import SyncJobCreate, SyncJobRead

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Session factory — overridable for tests
# ---------------------------------------------------------------------------
_session_factory = None


def _get_session_factory():
    global _session_factory
    if _session_factory is None:
        from app.core.database import AsyncSessionLocal
        _session_factory = AsyncSessionLocal
    return _session_factory


# ---------------------------------------------------------------------------
# Concurrency limiter — at most N concurrent jobs per channel
# ---------------------------------------------------------------------------
_channel_semaphores: dict[str, asyncio.Semaphore] = {}
MAX_CONCURRENT_PER_CHANNEL = 2


def _get_channel_semaphore(channel: str) -> asyncio.Semaphore:
    if channel not in _channel_semaphores:
        _channel_semaphores[channel] = asyncio.Semaphore(MAX_CONCURRENT_PER_CHANNEL)
    return _channel_semaphores[channel]


# ---------------------------------------------------------------------------
# Retry helpers
# ---------------------------------------------------------------------------
def _compute_next_retry(retry_count: int) -> datetime:
    """Exponential backoff: 30s, 120s, 480s, …"""
    delay = 30 * (2 ** retry_count)
    return datetime.now(timezone.utc) + timedelta(seconds=delay)


def _compute_next_run(cron_expression: str) -> datetime | None:
    try:
        cron = croniter(cron_expression, datetime.now(timezone.utc))
        return cron.get_next(datetime)
    except (ValueError, KeyError):
        return None


def _get_connector_for_type(connection_type: str | None):
    """Selects connector implementation based on connection_type.
    ftp / ssh  → CsvConnector (file-based transport)
    http_post / None → HttpConnector (HTTP-based transport)
    """
    if connection_type in ("ftp", "ssh"):
        return CsvConnector()
    return HttpConnector()


# ---------------------------------------------------------------------------
# CRUD
# ---------------------------------------------------------------------------
async def create_sync_job(db: AsyncSession, data: SyncJobCreate) -> SyncJob:
    from fastapi import HTTPException
    from app.services.channel_service import get_channel

    channel = await get_channel(db, data.channel_id)  # raises 404 if not found
    if not channel.active:
        raise HTTPException(status_code=400, detail="El canal no está activo")

    # Inherit connection from channel; override if explicitly supplied
    connection_type = data.connection_type if data.connection_type is not None else channel.connection_type
    connection_config = data.connection_config if data.connection_config is not None else (channel.connection_config or {})

    scheduled = bool(data.cron_expression)
    next_run = _compute_next_run(data.cron_expression) if data.cron_expression else None

    job = SyncJob(
        channel=channel.code,
        connection_type=connection_type,
        connection_config=connection_config,
        status="queued",
        filters=data.filters.model_dump(exclude_none=True),
        metrics={},
        max_retries=data.max_retries,
        scheduled=scheduled,
        cron_expression=data.cron_expression,
        next_run_at=next_run,
    )
    db.add(job)
    await db.flush()
    return job


async def get_sync_job(db: AsyncSession, job_id: str) -> SyncJobRead:
    result = await db.execute(select(SyncJob).where(SyncJob.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Sync job not found")
    return SyncJobRead.model_validate(job)


async def list_sync_jobs(
    db: AsyncSession,
    page: int = 1,
    size: int = 20,
    channel: str | None = None,
    status: str | None = None,
) -> PaginatedResponse[SyncJobRead]:
    query = select(SyncJob)
    if channel:
        query = query.where(SyncJob.channel == channel)
    if status:
        query = query.where(SyncJob.status == status)

    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar() or 0
    result = await db.execute(
        query.order_by(SyncJob.created_at.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
    items = [SyncJobRead.model_validate(j) for j in result.scalars().all()]

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size if size > 0 else 0,
    )


async def update_schedule(db: AsyncSession, job_id: str, cron_expression: str | None, enabled: bool) -> SyncJob:
    result = await db.execute(select(SyncJob).where(SyncJob.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Sync job not found")

    job.scheduled = enabled and bool(cron_expression)
    job.cron_expression = cron_expression
    job.next_run_at = _compute_next_run(cron_expression) if cron_expression and enabled else None
    await db.flush()
    return job


async def delete_sync_job(db: AsyncSession, job_id: str) -> None:
    """Elimina un trabajo de sincronización."""
    from fastapi import HTTPException

    result = await db.execute(select(SyncJob).where(SyncJob.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Sync job not found")

    await db.delete(job)


# ---------------------------------------------------------------------------
# Run job (with concurrency limit + history recording)
# ---------------------------------------------------------------------------
async def run_sync_job(job_id: str) -> None:
    """Ejecuta el conector real con control de concurrencia por canal."""
    async with _get_session_factory()() as db:
        result = await db.execute(select(SyncJob).where(SyncJob.id == job_id))
        job = result.scalar_one_or_none()
        if not job:
            return

        sem = _get_channel_semaphore(job.channel)

        async with sem:
            job.status = "running"
            job.started_at = datetime.now(timezone.utc)
            await db.commit()

            try:
                connector = _get_connector_for_type(job.connection_type)
                conn_result = await connector.run(db, job.filters)

                job.metrics = conn_result.to_metrics()
                job.status = "done"
                job.error_message = None

                # Record per-product sync history
                for detail in conn_result.product_details:
                    history = ProductSyncHistory(
                        sku=detail.sku,
                        channel=job.channel,
                        job_id=str(job.id),
                        status=detail.status,
                        detail={},
                        error_message=detail.error,
                    )
                    db.add(history)

            except Exception as exc:
                logger.exception("Error en sync job %s", job_id)
                job.status = "failed"
                job.error_message = str(exc)
                job.metrics = {"total_products": 0, "exported": 0, "skipped": 0, "errors": [str(exc)]}

                # Auto-retry with exponential backoff
                if job.retry_count < job.max_retries:
                    job.retry_count += 1
                    job.next_retry_at = _compute_next_retry(job.retry_count)
                    job.status = "retry_pending"

            job.finished_at = datetime.now(timezone.utc)

            # Schedule next run if cron is enabled
            if job.scheduled and job.cron_expression:
                job.next_run_at = _compute_next_run(job.cron_expression)

            await db.commit()


async def retry_sync_job(db: AsyncSession, job_id: str) -> SyncJob:
    """Re-encola un job fallido para reintentarlo."""
    result = await db.execute(select(SyncJob).where(SyncJob.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Sync job not found")
    if job.status not in ("failed", "done", "retry_pending"):
        from fastapi import HTTPException

        raise HTTPException(status_code=400, detail="Solo se pueden reintentar jobs finalizados o fallidos")

    job.status = "queued"
    job.started_at = None
    job.finished_at = None
    job.error_message = None
    job.metrics = {}
    job.next_retry_at = None
    await db.flush()
    return job


# ---------------------------------------------------------------------------
# Product sync history queries
# ---------------------------------------------------------------------------
async def get_product_sync_history(
    db: AsyncSession,
    sku: str,
    channel: str | None = None,
    page: int = 1,
    size: int = 20,
) -> PaginatedResponse[ProductSyncHistoryRead]:
    query = select(ProductSyncHistory).where(ProductSyncHistory.sku == sku)
    if channel:
        query = query.where(ProductSyncHistory.channel == channel)

    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar() or 0
    result = await db.execute(
        query.order_by(ProductSyncHistory.synced_at.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
    items = [ProductSyncHistoryRead.model_validate(h) for h in result.scalars().all()]

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size if size > 0 else 0,
    )


async def get_product_sync_status(db: AsyncSession, sku: str) -> list[ProductSyncStatusRead]:
    """Devuelve el estado más reciente de un producto en cada canal donde se ha publicado."""
    # Get distinct channels for this SKU
    ch_result = await db.execute(
        select(distinct(ProductSyncHistory.channel)).where(ProductSyncHistory.sku == sku)
    )
    channels = [row[0] for row in ch_result.all()]

    statuses: list[ProductSyncStatusRead] = []
    for ch in channels:
        latest = await db.execute(
            select(ProductSyncHistory)
            .where(ProductSyncHistory.sku == sku, ProductSyncHistory.channel == ch)
            .order_by(ProductSyncHistory.synced_at.desc())
            .limit(1)
        )
        record = latest.scalar_one_or_none()
        if record:
            statuses.append(
                ProductSyncStatusRead(
                    sku=record.sku,
                    channel=record.channel,
                    status=record.status,
                    synced_at=record.synced_at,
                    job_id=record.job_id,
                )
            )

    return statuses


async def get_channel_sync_history(
    db: AsyncSession,
    channel: str,
    page: int = 1,
    size: int = 20,
) -> PaginatedResponse[ProductSyncHistoryRead]:
    query = select(ProductSyncHistory).where(ProductSyncHistory.channel == channel)
    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar() or 0
    result = await db.execute(
        query.order_by(ProductSyncHistory.synced_at.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
    items = [ProductSyncHistoryRead.model_validate(h) for h in result.scalars().all()]

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        size=size,
        pages=(total + size - 1) // size if size > 0 else 0,
    )


# ---------------------------------------------------------------------------
# Background scheduler tick — to be called periodically
# ---------------------------------------------------------------------------
async def process_pending_retries() -> None:
    """Procesa jobs en estado retry_pending cuyo next_retry_at ya pasó."""
    async with _get_session_factory()() as db:
        now = datetime.now(timezone.utc)
        result = await db.execute(
            select(SyncJob).where(
                SyncJob.status == "retry_pending",
                SyncJob.next_retry_at <= now,
            )
        )
        jobs = result.scalars().all()
        for job in jobs:
            job.status = "queued"
            job.next_retry_at = None
        await db.commit()

        # Launch each retry
        for job in jobs:
            asyncio.create_task(run_sync_job(str(job.id)))


async def process_scheduled_jobs() -> None:
    """Crea nuevos jobs para las programaciones cron cuyo next_run_at ya pasó."""
    async with _get_session_factory()() as db:
        now = datetime.now(timezone.utc)
        result = await db.execute(
            select(SyncJob).where(
                SyncJob.scheduled == True,  # noqa: E712
                SyncJob.next_run_at <= now,
                SyncJob.status.in_(["done", "failed", "retry_pending"]),
            )
        )
        templates = result.scalars().all()
        for tmpl in templates:
            # Create a fresh job based on this schedule template
            new_job = SyncJob(
                channel=tmpl.channel,
                status="queued",
                filters=tmpl.filters,
                metrics={},
                max_retries=tmpl.max_retries,
                scheduled=False,  # child job is not a schedule template
            )
            db.add(new_job)
            await db.flush()

            # Advance the template's next_run_at
            tmpl.next_run_at = _compute_next_run(tmpl.cron_expression) if tmpl.cron_expression else None
            await db.commit()

            asyncio.create_task(run_sync_job(str(new_job.id)))

