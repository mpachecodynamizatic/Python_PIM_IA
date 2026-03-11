import json
import math
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, Query, UploadFile
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_scopes
from app.models.import_job import ImportJob
from app.models.mapping_template import MappingTemplate
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.ingest import (
    ColumnMapping,
    ColumnMappingSet,
    ImportJobRead,
    ImportJobSummary,
    MappingTemplateCreate,
    MappingTemplateRead,
    UploadResponse,
)
from app.services import import_service

router = APIRouter(prefix="/ingest", tags=["ingest"])

MAX_FILE_BYTES = 50 * 1024 * 1024  # 50 MB


# ── Upload ─────────────────────────────────────────────────────────────────────

@router.post("/uploads", response_model=UploadResponse, status_code=202)
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    mapping_json: str = Form(..., description="ColumnMappingSet as JSON string"),
    dry_run: bool = Form(False),
    mode: str = Form("upsert", description="upsert | create_only"),
    template_id: str | None = Form(None),
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_scopes("products:write")),
):
    filename = file.filename or "upload"
    ext = filename.rsplit(".", 1)[-1].lower()
    if ext not in ("xlsx", "csv"):
        raise HTTPException(status_code=422, detail="Only .xlsx and .csv files are supported")

    file_bytes = await file.read()
    if len(file_bytes) > MAX_FILE_BYTES:
        raise HTTPException(status_code=413, detail="File exceeds 50 MB limit")

    try:
        mapping = ColumnMappingSet.model_validate(json.loads(mapping_json))
    except Exception as exc:
        raise HTTPException(status_code=422, detail=f"Invalid mapping JSON: {exc}")

    # Merge saved template (inline mappings override template)
    if template_id:
        result = await db.execute(select(MappingTemplate).where(MappingTemplate.id == template_id))
        tmpl = result.scalar_one_or_none()
        if tmpl:
            base = {cm["source_column"]: ColumnMapping.model_validate(cm) for cm in tmpl.mappings}
            inline = {cm.source_column: cm for cm in mapping.mappings}
            mapping.mappings = list({**base, **inline}.values())
            if not mapping.defaults:
                mapping.defaults = tmpl.defaults

    job = await import_service.create_import_job(
        db=db,
        actor=str(user.id),
        filename=filename,
        file_format=ext,
        mapping=mapping,
        dry_run=dry_run,
    )
    await db.commit()

    background_tasks.add_task(
        import_service.run_import_job,
        job_id=str(job.id),
        file_bytes=file_bytes,
        file_format=ext,
        mapping=mapping,
        mode=mode,
        actor=str(user.id),
    )

    return UploadResponse(
        job_id=str(job.id),
        status="pending",
        message=f"Job created. Poll GET /api/v1/ingest/jobs/{job.id} for progress.",
    )


# ── Job status ─────────────────────────────────────────────────────────────────

@router.get("/jobs", response_model=PaginatedResponse[ImportJobSummary])
async def list_jobs(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    total = (await db.execute(select(func.count(ImportJob.id)))).scalar() or 0
    result = await db.execute(
        select(ImportJob).order_by(ImportJob.created_at.desc()).offset((page - 1) * size).limit(size)
    )
    return PaginatedResponse(
        items=[ImportJobSummary.model_validate(j) for j in result.scalars().all()],
        total=total,
        page=page,
        size=size,
        pages=math.ceil(total / size) if size > 0 else 0,
    )


@router.get("/jobs/{job_id}", response_model=ImportJobRead)
async def get_job(
    job_id: str,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    return await import_service.get_import_job(db, job_id)


# ── Mapping templates ──────────────────────────────────────────────────────────

@router.post("/mapping-templates", response_model=MappingTemplateRead, status_code=201)
async def create_template(
    body: MappingTemplateCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_scopes("products:write")),
):
    existing = await db.execute(select(MappingTemplate).where(MappingTemplate.name == body.name))
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail=f"Template '{body.name}' already exists")

    tmpl = MappingTemplate(
        name=body.name,
        description=body.description,
        created_by=str(user.id),
        mappings=[cm.model_dump() for cm in body.mappings],
        defaults=body.defaults,
    )
    db.add(tmpl)
    await db.flush()
    return tmpl


@router.get("/mapping-templates", response_model=list[MappingTemplateRead])
async def list_templates(
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    result = await db.execute(select(MappingTemplate).order_by(MappingTemplate.name))
    return result.scalars().all()


@router.get("/mapping-templates/{template_id}", response_model=MappingTemplateRead)
async def get_template(
    template_id: str,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    result = await db.execute(select(MappingTemplate).where(MappingTemplate.id == template_id))
    tmpl = result.scalar_one_or_none()
    if not tmpl:
        raise HTTPException(status_code=404, detail="Template not found")
    return tmpl


@router.delete("/mapping-templates/{template_id}", status_code=204)
async def delete_template(
    template_id: str,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_scopes("products:write")),
):
    result = await db.execute(select(MappingTemplate).where(MappingTemplate.id == template_id))
    tmpl = result.scalar_one_or_none()
    if not tmpl:
        raise HTTPException(status_code=404, detail="Template not found")
    await db.delete(tmpl)
