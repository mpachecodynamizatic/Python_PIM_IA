import asyncio
import csv
import io
import json

import openpyxl
import pytest
from httpx import AsyncClient


def make_xlsx_bytes(rows: list[dict]) -> bytes:
    """Create a minimal in-memory .xlsx file from a list of row dicts."""
    wb = openpyxl.Workbook()
    ws = wb.active
    if not rows:
        buf = io.BytesIO()
        wb.save(buf)
        return buf.getvalue()
    headers = list(rows[0].keys())
    ws.append(headers)
    for row in rows:
        ws.append([row.get(h) for h in headers])
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


def make_csv_bytes(rows: list[dict]) -> bytes:
    buf = io.StringIO()
    if not rows:
        return b""
    writer = csv.DictWriter(buf, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)
    return buf.getvalue().encode("utf-8")


MAPPING = {
    "mappings": [
        {"source_column": "SKU", "product_field": "sku", "required": True, "transform": "strip"},
        {"source_column": "Brand", "product_field": "brand", "required": True},
        {"source_column": "CategoryID", "product_field": "category_id", "required": True},
        {"source_column": "Color", "product_field": "attributes.color"},
    ],
    "defaults": {"status": "draft"},
}


@pytest.fixture
async def category_id(client: AsyncClient, auth_headers):
    resp = await client.post(
        "/api/v1/taxonomy/categories",
        json={"name": "Import Cat", "slug": "import-cat"},
        headers=auth_headers,
    )
    return resp.json()["id"]


async def _wait_for_job(client, auth_headers, job_id, timeout=10):
    """Poll until the job is done or failed."""
    for _ in range(timeout * 10):
        resp = await client.get(f"/api/v1/ingest/jobs/{job_id}", headers=auth_headers)
        status = resp.json()["status"]
        if status in ("done", "failed"):
            return resp.json()
        await asyncio.sleep(0.1)
    return None


@pytest.mark.asyncio
async def test_upload_csv(client: AsyncClient, auth_headers, category_id):
    rows = [
        {"SKU": "IMP-001", "Brand": "AcmeCorp", "CategoryID": category_id, "Color": "red"},
        {"SKU": "IMP-002", "Brand": "AcmeCorp", "CategoryID": category_id, "Color": "blue"},
    ]
    csv_bytes = make_csv_bytes(rows)

    resp = await client.post(
        "/api/v1/ingest/uploads",
        files={"file": ("products.csv", csv_bytes, "text/csv")},
        data={"mapping_json": json.dumps(MAPPING), "dry_run": "false", "mode": "upsert"},
        headers=auth_headers,
    )
    assert resp.status_code == 202
    job_id = resp.json()["job_id"]

    job = await _wait_for_job(client, auth_headers, job_id)
    assert job is not None
    assert job["status"] == "done"
    assert job["success_rows"] == 2
    assert job["failed_rows"] == 0

    # Verify products were actually created
    p1 = await client.get("/api/v1/products/IMP-001", headers=auth_headers)
    assert p1.status_code == 200
    assert p1.json()["attributes"]["color"] == "red"


@pytest.mark.asyncio
async def test_upload_xlsx(client: AsyncClient, auth_headers, category_id):
    rows = [{"SKU": "XLSX-001", "Brand": "XlsBrand", "CategoryID": category_id, "Color": "green"}]
    xlsx_bytes = make_xlsx_bytes(rows)

    resp = await client.post(
        "/api/v1/ingest/uploads",
        files={"file": ("products.xlsx", xlsx_bytes, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        data={"mapping_json": json.dumps(MAPPING), "dry_run": "false"},
        headers=auth_headers,
    )
    assert resp.status_code == 202
    job = await _wait_for_job(client, auth_headers, resp.json()["job_id"])
    assert job["status"] == "done"
    assert job["success_rows"] == 1


@pytest.mark.asyncio
async def test_dry_run_does_not_persist(client: AsyncClient, auth_headers, category_id):
    rows = [{"SKU": "DRY-001", "Brand": "DryBrand", "CategoryID": category_id, "Color": ""}]
    csv_bytes = make_csv_bytes(rows)

    resp = await client.post(
        "/api/v1/ingest/uploads",
        files={"file": ("dry.csv", csv_bytes, "text/csv")},
        data={"mapping_json": json.dumps(MAPPING), "dry_run": "true"},
        headers=auth_headers,
    )
    assert resp.status_code == 202
    job = await _wait_for_job(client, auth_headers, resp.json()["job_id"])
    assert job["status"] == "done"
    assert job["dry_run"] is True

    # Product must NOT exist after a dry-run
    check = await client.get("/api/v1/products/DRY-001", headers=auth_headers)
    assert check.status_code == 404


@pytest.mark.asyncio
async def test_row_error_missing_required(client: AsyncClient, auth_headers, category_id):
    rows = [
        {"SKU": "ERR-001", "Brand": "", "CategoryID": category_id},  # Brand required but empty
    ]
    csv_bytes = make_csv_bytes(rows)
    mapping_with_required_brand = {
        "mappings": [
            {"source_column": "SKU", "product_field": "sku", "required": True},
            {"source_column": "Brand", "product_field": "brand", "required": True},
            {"source_column": "CategoryID", "product_field": "category_id", "required": True},
        ],
        "defaults": {},
    }
    resp = await client.post(
        "/api/v1/ingest/uploads",
        files={"file": ("err.csv", csv_bytes, "text/csv")},
        data={"mapping_json": json.dumps(mapping_with_required_brand)},
        headers=auth_headers,
    )
    job = await _wait_for_job(client, auth_headers, resp.json()["job_id"])
    assert job["failed_rows"] == 1
    assert len(job["errors"]) >= 1
    assert job["errors"][0]["row"] == 2


@pytest.mark.asyncio
async def test_upsert_updates_existing(client: AsyncClient, auth_headers, category_id):
    # Create product first
    await client.post(
        "/api/v1/products",
        json={"sku": "UPS-001", "brand": "OldBrand", "category_id": category_id},
        headers=auth_headers,
    )
    rows = [{"SKU": "UPS-001", "Brand": "NewBrand", "CategoryID": category_id, "Color": ""}]
    csv_bytes = make_csv_bytes(rows)

    resp = await client.post(
        "/api/v1/ingest/uploads",
        files={"file": ("upsert.csv", csv_bytes, "text/csv")},
        data={"mapping_json": json.dumps(MAPPING), "mode": "upsert"},
        headers=auth_headers,
    )
    job = await _wait_for_job(client, auth_headers, resp.json()["job_id"])
    assert job["status"] == "done"
    assert job["success_rows"] == 1

    updated = await client.get("/api/v1/products/UPS-001", headers=auth_headers)
    assert updated.json()["brand"] == "NewBrand"


@pytest.mark.asyncio
async def test_create_only_skips_existing(client: AsyncClient, auth_headers, category_id):
    await client.post(
        "/api/v1/products",
        json={"sku": "SKIP-001", "brand": "Existing", "category_id": category_id},
        headers=auth_headers,
    )
    rows = [{"SKU": "SKIP-001", "Brand": "ShouldBeIgnored", "CategoryID": category_id, "Color": ""}]
    csv_bytes = make_csv_bytes(rows)

    resp = await client.post(
        "/api/v1/ingest/uploads",
        files={"file": ("skip.csv", csv_bytes, "text/csv")},
        data={"mapping_json": json.dumps(MAPPING), "mode": "create_only"},
        headers=auth_headers,
    )
    job = await _wait_for_job(client, auth_headers, resp.json()["job_id"])
    assert job["status"] == "done"

    p = await client.get("/api/v1/products/SKIP-001", headers=auth_headers)
    assert p.json()["brand"] == "Existing"


@pytest.mark.asyncio
async def test_invalid_file_format(client: AsyncClient, auth_headers):
    resp = await client.post(
        "/api/v1/ingest/uploads",
        files={"file": ("data.pdf", b"fake", "application/pdf")},
        data={"mapping_json": json.dumps(MAPPING)},
        headers=auth_headers,
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_list_jobs(client: AsyncClient, auth_headers, category_id):
    rows = [{"SKU": "LIST-J-001", "Brand": "B", "CategoryID": category_id, "Color": ""}]
    await client.post(
        "/api/v1/ingest/uploads",
        files={"file": ("list.csv", make_csv_bytes(rows), "text/csv")},
        data={"mapping_json": json.dumps(MAPPING)},
        headers=auth_headers,
    )
    resp = await client.get("/api/v1/ingest/jobs", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1


@pytest.mark.asyncio
async def test_mapping_template_crud(client: AsyncClient, auth_headers):
    tmpl_body = {
        "name": "Supplier A Template",
        "mappings": [
            {"source_column": "REF", "product_field": "sku", "required": True},
            {"source_column": "MARCA", "product_field": "brand"},
        ],
        "defaults": {"status": "draft"},
    }
    create = await client.post("/api/v1/ingest/mapping-templates", json=tmpl_body, headers=auth_headers)
    assert create.status_code == 201
    tmpl_id = create.json()["id"]

    get = await client.get(f"/api/v1/ingest/mapping-templates/{tmpl_id}", headers=auth_headers)
    assert get.status_code == 200
    assert get.json()["name"] == "Supplier A Template"

    lst = await client.get("/api/v1/ingest/mapping-templates", headers=auth_headers)
    assert any(t["id"] == tmpl_id for t in lst.json())

    delete = await client.delete(f"/api/v1/ingest/mapping-templates/{tmpl_id}", headers=auth_headers)
    assert delete.status_code == 204
