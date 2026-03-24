"""
Export / Import Excel router.

Endpoints:
  GET  /export/resources                        – list supported resources
  GET  /export/{resource}/fields                – field metadata for UI
  POST /export/{resource}                       – download xlsx
  GET  /export/{resource}/template              – download empty template
  POST /export/{resource}/import/validate       – dry-run validation
  POST /export/{resource}/import                – validate + apply
"""
from __future__ import annotations

from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, File, Path, Query, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User

router = APIRouter(prefix="/export", tags=["export"])


# ── Schemas ───────────────────────────────────────────────────────────────────

class ExportRequest(BaseModel):
    fields: list[str] | None = None   # if None → default fields
    filters: dict | None = None


class ImportIssueOut(BaseModel):
    row: int
    field_key: str
    code: str
    message: str


class ImportPreviewRowOut(BaseModel):
    row: int
    mode: str
    data: dict


class ImportValidationOut(BaseModel):
    total: int
    valid: int
    errors: list[ImportIssueOut]
    warnings: list[ImportIssueOut]
    preview: list[ImportPreviewRowOut]
    has_blocking_errors: bool


class ImportResultOut(BaseModel):
    created: int
    updated: int
    skipped: int


# ── Helpers ───────────────────────────────────────────────────────────────────

def _xlsx_response(buffer, filename: str) -> StreamingResponse:
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


def _validation_to_out(v) -> ImportValidationOut:
    return ImportValidationOut(
        total=v.total,
        valid=v.valid,
        errors=[ImportIssueOut(**vars(e)) for e in v.errors],
        warnings=[ImportIssueOut(**vars(w)) for w in v.warnings],
        preview=[ImportPreviewRowOut(**vars(p)) for p in v.preview],
        has_blocking_errors=v.has_blocking_errors,
    )


# ── Endpoints ─────────────────────────────────────────────────────────────────

@router.get("/resources")
async def list_resources(
    _: User = Depends(get_current_user),
):
    """List all resources that support export/import."""
    from app.export.export_service import list_resources
    return list_resources()


@router.get("/{resource}/fields")
async def get_fields(
    resource: str = Path(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Return field metadata for the field selector dialog, including user preferences."""
    from app.export.export_service import list_fields
    from sqlalchemy import select
    from app.models.export_preference import ExportPreference

    fields = list_fields(resource)

    # Get user preferences for this resource
    stmt = select(ExportPreference).where(
        ExportPreference.user_id == str(current_user.id),
        ExportPreference.resource == resource
    )
    result = await db.execute(stmt)
    pref = result.scalar_one_or_none()

    return {
        "fields": fields,
        "user_selection": pref.selected_fields if pref else None
    }


@router.post("/{resource}")
async def export_resource(
    resource: str = Path(...),
    body: ExportRequest = ExportRequest(),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Export rows to Excel and download."""
    from app.export.export_service import export_to_excel
    from sqlalchemy import select
    from app.models.export_preference import ExportPreference

    # Save user preferences if fields were selected
    if body.fields is not None:
        stmt = select(ExportPreference).where(
            ExportPreference.user_id == str(current_user.id),
            ExportPreference.resource == resource
        )
        result = await db.execute(stmt)
        pref = result.scalar_one_or_none()

        if pref:
            pref.selected_fields = body.fields
        else:
            pref = ExportPreference(
                user_id=str(current_user.id),
                resource=resource,
                selected_fields=body.fields
            )
            db.add(pref)

        await db.commit()

    buffer = await export_to_excel(
        resource=resource,
        selected_keys=body.fields,
        filters=body.filters or {},
        db=db,
    )
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return _xlsx_response(buffer, f"{resource}_{ts}.xlsx")


@router.get("/{resource}/template")
async def download_template(
    resource: str = Path(...),
    fields: Annotated[list[str] | None, Query()] = None,
    _: User = Depends(get_current_user),
):
    """Download an empty xlsx template with headers and one example row."""
    from app.export.export_service import generate_template

    buffer = await generate_template(resource=resource, selected_keys=fields)
    return _xlsx_response(buffer, f"{resource}_template.xlsx")


@router.post("/{resource}/import/validate", response_model=ImportValidationOut)
async def validate_import_endpoint(
    resource: str = Path(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    _: User = Depends(get_current_user),
):
    """Dry-run: parse and validate the xlsx without saving anything."""
    from app.export.import_service import validate_import

    file_bytes = await file.read()
    validation = await validate_import(resource=resource, file_bytes=file_bytes, db=db)
    return _validation_to_out(validation)


@router.post("/{resource}/import", response_model=ImportResultOut)
async def apply_import_endpoint(
    resource: str = Path(...),
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Validate and apply the xlsx import.  Returns 422 if blocking errors exist."""
    from fastapi import HTTPException
    from app.export.import_service import validate_import, apply_import

    file_bytes = await file.read()
    validation = await validate_import(resource=resource, file_bytes=file_bytes, db=db)

    if validation.has_blocking_errors:
        raise HTTPException(
            status_code=422,
            detail={
                "message": "El fichero contiene errores que impiden la importacion",
                "errors": [vars(e) for e in validation.errors if e.code.startswith("error_")],
            },
        )

    result = await apply_import(
        resource=resource,
        validation=validation,
        actor=current_user.email,
        db=db,
    )
    return ImportResultOut(
        created=result.created,
        updated=result.updated,
        skipped=result.skipped,
    )
