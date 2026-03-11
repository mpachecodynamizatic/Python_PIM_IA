import logging
from datetime import datetime, timezone

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.connectors import get_connector, list_channels
from app.models.sync_job import SyncJob
from app.schemas.common import PaginatedResponse
from app.schemas.sync_job import SyncJobCreate, SyncJobRead

logger = logging.getLogger(__name__)


async def create_sync_job(db: AsyncSession, data: SyncJobCreate) -> SyncJob:
    if data.channel not in list_channels():
        from fastapi import HTTPException

        raise HTTPException(
            status_code=400,
            detail=f"Canal no soportado: {data.channel}. Disponibles: {list_channels()}",
        )

    job = SyncJob(
        channel=data.channel,
        status="queued",
        filters=data.filters.model_dump(exclude_none=True),
        metrics={},
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


async def run_sync_job(job_id: str) -> None:
    """Ejecuta el conector real asociado al canal del job."""
    from app.core.database import AsyncSessionLocal

    async with AsyncSessionLocal() as db:
        result = await db.execute(select(SyncJob).where(SyncJob.id == job_id))
        job = result.scalar_one_or_none()
        if not job:
            return

        job.status = "running"
        job.started_at = datetime.now(timezone.utc)
        await db.commit()

        try:
            connector = get_connector(job.channel)
            conn_result = await connector.run(db, job.filters)

            job.metrics = conn_result.to_metrics()
            job.status = "done"
            job.error_message = None
        except Exception as exc:
            logger.exception("Error en sync job %s", job_id)
            job.status = "failed"
            job.error_message = str(exc)
            job.metrics = {"total_products": 0, "exported": 0, "skipped": 0, "errors": [str(exc)]}

        job.finished_at = datetime.now(timezone.utc)
        await db.commit()


async def retry_sync_job(db: AsyncSession, job_id: str) -> SyncJob:
    """Re-encola un job fallido para reintentarlo."""
    result = await db.execute(select(SyncJob).where(SyncJob.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        from fastapi import HTTPException

        raise HTTPException(status_code=404, detail="Sync job not found")
    if job.status not in ("failed", "done"):
        from fastapi import HTTPException

        raise HTTPException(status_code=400, detail="Solo se pueden reintentar jobs finalizados o fallidos")

    job.status = "queued"
    job.started_at = None
    job.finished_at = None
    job.error_message = None
    job.metrics = {}
    await db.flush()
    return job

