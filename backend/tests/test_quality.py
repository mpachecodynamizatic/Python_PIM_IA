"""Tests for Data Quality endpoint."""
import pytest

pytestmark = pytest.mark.asyncio


async def _setup(client, auth_headers):
    """Create a category and a bare-minimum product, return sku and cat_id."""
    cat = await client.post(
        "/api/v1/taxonomy/categories",
        json={"name": "Quality Cat", "slug": "quality-cat"},
        headers=auth_headers,
    )
    assert cat.status_code == 201
    cat_id = cat.json()["id"]

    prod = await client.post(
        "/api/v1/products",
        json={"sku": "QUAL-001", "brand": "Brand", "category_id": cat_id},
        headers=auth_headers,
    )
    assert prod.status_code == 201
    return "QUAL-001", cat_id


async def test_quality_new_product(client, auth_headers):
    """A freshly created product should have low quality (no SEO, media, i18n)."""
    sku, _ = await _setup(client, auth_headers)
    resp = await client.get(f"/api/v1/quality/products/{sku}", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert data["sku"] == sku
    assert 0 <= data["overall"] <= 100
    dims = data["dimensions"]
    assert dims["brand"] == 1.0
    assert dims["category"] == 1.0
    assert dims["media"] == 0.0
    assert dims["i18n"] == 0.0


async def test_quality_improves_after_i18n(client, auth_headers):
    """Adding a translation should raise i18n dimension to 1.0."""
    sku, _ = await _setup(client, auth_headers)
    before = await client.get(f"/api/v1/quality/products/{sku}", headers=auth_headers)

    await client.post(
        f"/api/v1/products/{sku}/i18n/es",
        json={"locale": "es", "title": "Titulo en espanol"},
        headers=auth_headers,
    )

    after = await client.get(f"/api/v1/quality/products/{sku}", headers=auth_headers)
    assert after.json()["dimensions"]["i18n"] == 1.0
    assert after.json()["overall"] > before.json()["overall"]


async def test_quality_report(client, auth_headers):
    """Quality report endpoint returns paginated results."""
    await _setup(client, auth_headers)
    resp = await client.get("/api/v1/quality/report?page=1&size=20", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "items" in data
    assert "total" in data
    assert len(data["items"]) >= 1
    # Every item has the expected fields
    for item in data["items"]:
        assert "sku" in item
        assert "overall" in item
        assert "dimensions" in item


async def test_quality_not_found(client, auth_headers):
    """Requesting quality for a non-existent SKU returns 404."""
    resp = await client.get("/api/v1/quality/products/NO-SUCH-SKU", headers=auth_headers)
    assert resp.status_code == 404
