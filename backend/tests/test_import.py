"""
Tests for the Excel import engine (validate + apply).
"""
import io
import pytest
from httpx import AsyncClient
from openpyxl import Workbook


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_xlsx(headers: list[str], rows: list[list]) -> bytes:
    """Build a minimal xlsx in memory."""
    wb = Workbook()
    ws = wb.active
    ws.append(headers)
    for row in rows:
        ws.append(row)
    buf = io.BytesIO()
    wb.save(buf)
    return buf.getvalue()


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
async def cat(client: AsyncClient, auth_headers):
    r = await client.post(
        "/api/v1/taxonomy/categories",
        json={"name": "Import Cat", "slug": "import-cat"},
        headers=auth_headers,
    )
    assert r.status_code == 201
    return r.json()


@pytest.fixture
async def existing_product(client: AsyncClient, auth_headers, cat):
    r = await client.post(
        "/api/v1/products",
        json={"sku": "IMP-EXIST-01", "brand": "OldBrand", "category_id": cat["id"]},
        headers=auth_headers,
    )
    assert r.status_code == 201
    return r.json()


# ── Validate endpoint: happy path ─────────────────────────────────────────────

@pytest.mark.asyncio
async def test_validate_creates_preview(client: AsyncClient, auth_headers, cat):
    xlsx = _make_xlsx(
        ["SKU", "Marca", "ID Categoria"],
        [["IMP-NEW-01", "NewBrand", cat["id"]]],
    )
    r = await client.post(
        "/api/v1/export/products/import/validate",
        files={"file": ("products.xlsx", xlsx, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        headers=auth_headers,
    )
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 1
    assert body["valid"] == 1
    assert body["errors"] == []
    assert body["has_blocking_errors"] is False
    assert body["preview"][0]["mode"] == "create"


@pytest.mark.asyncio
async def test_validate_detects_update_mode(
    client: AsyncClient, auth_headers, existing_product, cat
):
    xlsx = _make_xlsx(
        ["SKU", "Marca", "ID Categoria"],
        [["IMP-EXIST-01", "UpdatedBrand", cat["id"]]],
    )
    r = await client.post(
        "/api/v1/export/products/import/validate",
        files={"file": ("products.xlsx", xlsx, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        headers=auth_headers,
    )
    assert r.status_code == 200
    body = r.json()
    assert body["preview"][0]["mode"] == "update"
    # warn_will_overwrite is present (non-blocking)
    warn_codes = [w["code"] for w in body["warnings"]]
    assert "warn_will_overwrite" in warn_codes
    assert body["has_blocking_errors"] is False


# ── Validate: FK error ────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_validate_fk_error(client: AsyncClient, auth_headers):
    xlsx = _make_xlsx(
        ["SKU", "Marca", "ID Categoria"],
        [["IMP-FKERR-01", "Brand", "nonexistent-category-uuid"]],
    )
    r = await client.post(
        "/api/v1/export/products/import/validate",
        files={"file": ("products.xlsx", xlsx, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        headers=auth_headers,
    )
    assert r.status_code == 200
    body = r.json()
    assert body["has_blocking_errors"] is True
    error_codes = [e["code"] for e in body["errors"]]
    assert "error_fk_not_found" in error_codes


# ── Validate: required field missing ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_validate_required_field_missing(client: AsyncClient, auth_headers, cat):
    xlsx = _make_xlsx(
        ["SKU", "Marca", "ID Categoria"],
        [["", "Brand", cat["id"]]],    # SKU is required
    )
    r = await client.post(
        "/api/v1/export/products/import/validate",
        files={"file": ("products.xlsx", xlsx, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        headers=auth_headers,
    )
    assert r.status_code == 200
    body = r.json()
    assert body["has_blocking_errors"] is True
    assert any(e["field_key"] == "sku" for e in body["errors"])


# ── Validate: invalid status transition ──────────────────────────────────────

@pytest.mark.asyncio
async def test_validate_invalid_status_transition(
    client: AsyncClient, auth_headers, existing_product, cat
):
    # Transition draft → retired is not allowed
    xlsx = _make_xlsx(
        ["SKU", "Marca", "ID Categoria", "Estado"],
        [["IMP-EXIST-01", "Brand", cat["id"], "retired"]],
    )
    r = await client.post(
        "/api/v1/export/products/import/validate",
        files={"file": ("products.xlsx", xlsx, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        headers=auth_headers,
    )
    assert r.status_code == 200
    body = r.json()
    assert body["has_blocking_errors"] is True
    assert any(e["code"] == "error_invalid_transition" for e in body["errors"])


# ── Import endpoint: apply ────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_import_creates_product(client: AsyncClient, auth_headers, cat):
    sku = "IMP-CREATE-99"
    xlsx = _make_xlsx(
        ["SKU", "Marca", "ID Categoria"],
        [[sku, "NewBrand", cat["id"]]],
    )
    r = await client.post(
        "/api/v1/export/products/import",
        files={"file": ("products.xlsx", xlsx, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        headers=auth_headers,
    )
    assert r.status_code == 200
    body = r.json()
    assert body["created"] == 1
    assert body["updated"] == 0

    # Verify product exists
    r2 = await client.get(f"/api/v1/products/{sku}", headers=auth_headers)
    assert r2.status_code == 200
    assert r2.json()["brand"] == "NewBrand"


@pytest.mark.asyncio
async def test_import_updates_product(
    client: AsyncClient, auth_headers, existing_product, cat
):
    xlsx = _make_xlsx(
        ["SKU", "Marca", "ID Categoria"],
        [["IMP-EXIST-01", "UpdatedBrandFinal", cat["id"]]],
    )
    r = await client.post(
        "/api/v1/export/products/import",
        files={"file": ("products.xlsx", xlsx, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        headers=auth_headers,
    )
    assert r.status_code == 200
    body = r.json()
    assert body["updated"] == 1

    r2 = await client.get("/api/v1/products/IMP-EXIST-01", headers=auth_headers)
    assert r2.json()["brand"] == "UpdatedBrandFinal"


@pytest.mark.asyncio
async def test_import_returns_422_on_blocking_errors(client: AsyncClient, auth_headers):
    xlsx = _make_xlsx(
        ["SKU", "Marca", "ID Categoria"],
        [["IMP-ERR-01", "Brand", "nonexistent-cat-uuid"]],
    )
    r = await client.post(
        "/api/v1/export/products/import",
        files={"file": ("products.xlsx", xlsx, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        headers=auth_headers,
    )
    assert r.status_code == 422


# ── Import product_i18n: FK check on sku ─────────────────────────────────────

@pytest.mark.asyncio
async def test_import_i18n_nonexistent_sku(client: AsyncClient, auth_headers):
    xlsx = _make_xlsx(
        ["SKU", "Idioma", "Titulo"],
        [["NONEXISTENT-SKU-XYZ", "es", "Titulo ES"]],
    )
    r = await client.post(
        "/api/v1/export/product_i18n/import/validate",
        files={"file": ("i18n.xlsx", xlsx, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        headers=auth_headers,
    )
    assert r.status_code == 200
    body = r.json()
    assert body["has_blocking_errors"] is True
    assert any(e["code"] == "error_fk_not_found" for e in body["errors"])


# ── Export then re-import round-trip ─────────────────────────────────────────

@pytest.mark.asyncio
async def test_export_import_roundtrip(client: AsyncClient, auth_headers, cat):
    sku = "ROUNDTRIP-01"
    await client.post(
        "/api/v1/products",
        json={"sku": sku, "brand": "RoundTripBrand", "category_id": cat["id"]},
        headers=auth_headers,
    )

    # Export
    r_export = await client.post(
        "/api/v1/export/products",
        json={"fields": ["sku", "brand", "status", "category_id"], "filters": {"status": "draft"}},
        headers=auth_headers,
    )
    assert r_export.status_code == 200

    # Re-import the same file → all rows should be UPDATE mode (already exist)
    r_validate = await client.post(
        "/api/v1/export/products/import/validate",
        files={"file": ("products.xlsx", r_export.content, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")},
        headers=auth_headers,
    )
    assert r_validate.status_code == 200
    body = r_validate.json()
    assert body["has_blocking_errors"] is False
    # All preview rows should be update
    for prev in body["preview"]:
        assert prev["mode"] == "update"


# ── Auth guard ────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_import_validate_requires_auth(client: AsyncClient):
    xlsx = _make_xlsx(["SKU"], [["TEST"]])
    r = await client.post(
        "/api/v1/export/products/import/validate",
        files={"file": ("f.xlsx", xlsx)},
    )
    assert r.status_code in (401, 403)
