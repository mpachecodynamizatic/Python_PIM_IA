"""
Import service: Excel/CSV ingestion pipeline.

Flow:
  1. API endpoint creates an ImportJob row and returns job_id immediately.
  2. A FastAPI BackgroundTask calls run_import_job() with the raw file bytes.
  3. run_import_job() opens its OWN session (the request session is already closed).
  4. File bytes are parsed in asyncio.to_thread() to avoid blocking the event loop.
  5. Each row is processed inside a per-row savepoint so a bad row doesn't abort the job.
  6. dry_run=True rolls back all product writes at the end but keeps the job record.
"""

import asyncio
import csv
import io
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.import_job import ImportJob
from app.models.product import Product
from app.schemas.ingest import ColumnMapping, ColumnMappingSet, ImportRowError
from app.schemas.product import ProductCreate, ProductUpdate
from app.services import product_service


# ── File parsing (sync, runs in thread) ───────────────────────────────────────

def _parse_xlsx_sync(file_bytes: bytes) -> list[dict]:
    import openpyxl
    wb = openpyxl.load_workbook(filename=io.BytesIO(file_bytes), read_only=True, data_only=True)
    ws = wb.active
    rows_iter = ws.iter_rows(values_only=True)
    raw_headers = next(rows_iter, [])
    headers = [
        str(h).strip() if h is not None else f"col_{i}"
        for i, h in enumerate(raw_headers)
    ]
    result = [
        {headers[i]: (row[i] if i < len(row) else None) for i in range(len(headers))}
        for row in rows_iter
    ]
    wb.close()
    return result


def _parse_csv_sync(file_bytes: bytes) -> list[dict]:
    try:
        text = file_bytes.decode("utf-8-sig")
    except UnicodeDecodeError:
        text = file_bytes.decode("latin-1")
    dialect = csv.Sniffer().sniff(text[:4096], delimiters=",;\t")
    reader = csv.DictReader(io.StringIO(text), dialect=dialect)
    return list(reader)


# ── Column mapping + transforms ────────────────────────────────────────────────

def _apply_transform(value, transform: str | None):
    if value is None:
        return None
    s = str(value).strip()
    if transform == "strip":
        return s
    if transform == "upper":
        return s.upper()
    if transform == "lower":
        return s.lower()
    if transform == "int":
        return int(s)
    if transform == "float":
        return float(s)
    return s


def _map_row(
    raw_row: dict,
    mapping: ColumnMappingSet,
    row_number: int,
) -> tuple[dict, list[ImportRowError]]:
    """Returns (product_fields_dict, errors)."""
    fields: dict = {"attributes": {}, "seo": {}}
    errors: list[ImportRowError] = []

    # Apply defaults first so explicit mappings can override them
    for k, v in mapping.defaults.items():
        if "." in k:
            prefix, sub_key = k.split(".", 1)
            fields.setdefault(prefix, {})[sub_key] = v
        else:
            fields[k] = v

    for cm in mapping.mappings:
        raw_value = raw_row.get(cm.source_column)
        empty = raw_value is None or str(raw_value).strip() == ""

        if empty:
            if cm.required:
                errors.append(ImportRowError(
                    row=row_number,
                    field=cm.product_field,
                    value=None,
                    message=f"Required column '{cm.source_column}' is empty",
                ))
            continue

        try:
            value = _apply_transform(raw_value, cm.transform)
        except (ValueError, TypeError) as exc:
            errors.append(ImportRowError(
                row=row_number,
                field=cm.product_field,
                value=str(raw_value),
                message=f"Transform '{cm.transform}' failed: {exc}",
            ))
            continue

        if "." in cm.product_field:
            prefix, sub_key = cm.product_field.split(".", 1)
            fields.setdefault(prefix, {})[sub_key] = value
        else:
            fields[cm.product_field] = value

    return fields, errors


# ── Job helpers ────────────────────────────────────────────────────────────────

async def create_import_job(
    db: AsyncSession,
    actor: str,
    filename: str,
    file_format: str,
    mapping: ColumnMappingSet,
    dry_run: bool,
) -> ImportJob:
    job = ImportJob(
        actor=actor,
        file_format=file_format,
        original_filename=filename,
        dry_run=dry_run,
        column_mapping=mapping.model_dump(mode="json"),
    )
    db.add(job)
    await db.flush()
    return job


async def get_import_job(db: AsyncSession, job_id: str) -> ImportJob:
    result = await db.execute(select(ImportJob).where(ImportJob.id == job_id))
    job = result.scalar_one_or_none()
    if job is None:
        raise HTTPException(status_code=404, detail="Import job not found")
    return job


# ── Core background worker ─────────────────────────────────────────────────────

# Module-level session factory — can be overridden in tests via:
#   import app.services.import_service as svc; svc._session_factory = TestSessionLocal
_session_factory = None


def _get_session_factory():
    global _session_factory
    if _session_factory is None:
        from app.core.database import AsyncSessionLocal
        _session_factory = AsyncSessionLocal
    return _session_factory


async def run_import_job(
    job_id: str,
    file_bytes: bytes,
    file_format: str,
    mapping: ColumnMappingSet,
    mode: str,
    actor: str,
) -> None:
    """Background task: opens its own DB session independently of the request."""
    async with _get_session_factory()() as db:
        job = await get_import_job(db, job_id)
        job.status = "running"
        job.started_at = datetime.now(timezone.utc)
        await db.commit()

        # Parse file in thread to avoid blocking event loop
        try:
            if file_format == "xlsx":
                rows = await asyncio.to_thread(_parse_xlsx_sync, file_bytes)
            else:
                rows = await asyncio.to_thread(_parse_csv_sync, file_bytes)
        except Exception as exc:
            job.status = "failed"
            job.finished_at = datetime.now(timezone.utc)
            job.errors = [{"row": 0, "field": "file", "message": str(exc), "value": None}]
            await db.commit()
            return

        job.total_rows = len(rows)
        await db.commit()

        all_errors: list[dict] = []
        success = 0
        failed = 0

        # Outer savepoint for dry_run rollback
        async with db.begin_nested() as outer_sp:
            for idx, raw_row in enumerate(rows, start=2):  # row 1 = header
                fields, row_errors = _map_row(raw_row, mapping, row_number=idx)

                if row_errors:
                    all_errors.extend(e.model_dump() for e in row_errors)
                    failed += 1
                else:
                    missing = [f for f in ("sku", "brand", "category_id") if not fields.get(f)]
                    if missing:
                        all_errors.append({
                            "row": idx,
                            "field": ", ".join(missing),
                            "message": f"Missing required fields: {missing}",
                            "value": None,
                        })
                        failed += 1
                    else:
                        sku = str(fields["sku"]).strip()
                        async with db.begin_nested() as sp:
                            try:
                                exists = (await db.execute(
                                    select(Product).where(Product.sku == sku)
                                )).scalar_one_or_none() is not None

                                if exists and mode == "upsert":
                                    # Only pass non-empty values to avoid overwriting with None
                                    update_kwargs: dict = {}
                                    if fields.get("brand"):
                                        update_kwargs["brand"] = fields["brand"]
                                    if fields.get("category_id"):
                                        update_kwargs["category_id"] = fields["category_id"]
                                    if fields.get("seo"):
                                        update_kwargs["seo"] = fields["seo"]
                                    if fields.get("attributes"):
                                        update_kwargs["attributes"] = fields["attributes"]
                                    await product_service.update_product(
                                        db, sku,
                                        ProductUpdate(**update_kwargs),
                                        actor=actor,
                                    )
                                elif not exists:
                                    await product_service.create_product(
                                        db,
                                        ProductCreate(
                                            sku=sku,
                                            brand=fields["brand"],
                                            category_id=fields["category_id"],
                                            status=fields.get("status", "draft"),
                                            seo=fields.get("seo", {}),
                                            attributes=fields.get("attributes", {}),
                                        ),
                                        actor=actor,
                                    )
                                # mode == "create_only" + exists → silent skip
                                success += 1
                            except HTTPException as exc:
                                await sp.rollback()
                                all_errors.append({"row": idx, "field": "sku", "message": exc.detail, "value": sku})
                                failed += 1
                            except Exception as exc:
                                await sp.rollback()
                                all_errors.append({"row": idx, "field": "unknown", "message": str(exc), "value": None})
                                failed += 1

                job.processed_rows = idx - 1
                job.success_rows = success
                job.failed_rows = failed

                # Flush progress every 500 rows
                if idx % 500 == 0:
                    job.errors = all_errors
                    await db.commit()

            if job.dry_run:
                await outer_sp.rollback()

        job.status = "done"
        job.finished_at = datetime.now(timezone.utc)
        job.errors = all_errors
        job.processed_rows = len(rows)
        job.success_rows = success
        job.failed_rows = failed
        await db.commit()
