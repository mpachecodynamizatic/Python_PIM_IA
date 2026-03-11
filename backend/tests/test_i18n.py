"""Tests for I18N enrichment endpoints."""
import pytest

pytestmark = pytest.mark.asyncio


async def _setup(client, auth_headers, sku="I18N-TEST-001"):
    cat = await client.post(
        "/api/v1/taxonomy/categories",
        json={"name": "I18N Cat", "slug": f"i18n-cat-{sku}"},
        headers=auth_headers,
    )
    cat_id = cat.json()["id"]
    prod = await client.post(
        "/api/v1/products",
        json={"sku": sku, "brand": "Brand", "category_id": cat_id},
        headers=auth_headers,
    )
    assert prod.status_code == 201
    return sku, cat_id


async def test_list_locales_empty(client, auth_headers):
    """With no translations the locales list is empty."""
    resp = await client.get("/api/v1/i18n/locales", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json() == []


async def test_list_locales_after_translation(client, auth_headers):
    """Locales endpoint reflects translations that exist."""
    sku, _ = await _setup(client, auth_headers)
    await client.post(
        f"/api/v1/products/{sku}/i18n/es",
        json={"locale": "es", "title": "Hola"},
        headers=auth_headers,
    )
    resp = await client.get("/api/v1/i18n/locales", headers=auth_headers)
    assert "es" in resp.json()


async def test_missing_translations(client, auth_headers):
    """A product without 'en' locale appears in missing list."""
    sku, _ = await _setup(client, auth_headers)
    resp = await client.get("/api/v1/i18n/missing?locale=en", headers=auth_headers)
    assert resp.status_code == 200
    skus = [item["sku"] for item in resp.json()["items"]]
    assert sku in skus


async def test_missing_disappears_after_translation(client, auth_headers):
    """After adding translation the product no longer appears as missing."""
    sku, _ = await _setup(client, auth_headers, sku="I18N-TEST-002")
    await client.post(
        f"/api/v1/products/{sku}/i18n/fr",
        json={"locale": "fr", "title": "Bonjour"},
        headers=auth_headers,
    )
    resp = await client.get("/api/v1/i18n/missing?locale=fr", headers=auth_headers)
    skus = [item["sku"] for item in resp.json()["items"]]
    assert sku not in skus


async def test_get_product_translations(client, auth_headers):
    """GET /products/{sku}/i18n returns all translations."""
    sku, _ = await _setup(client, auth_headers, sku="I18N-TEST-003")
    for locale, title in [("es", "Español"), ("en", "English")]:
        await client.post(
            f"/api/v1/products/{sku}/i18n/{locale}",
            json={"locale": locale, "title": title},
            headers=auth_headers,
        )
    resp = await client.get(f"/api/v1/products/{sku}/i18n", headers=auth_headers)
    assert resp.status_code == 200
    locales = [t["locale"] for t in resp.json()]
    assert "es" in locales
    assert "en" in locales


async def test_delete_translation(client, auth_headers):
    """DELETE removes the specific locale translation."""
    sku, _ = await _setup(client, auth_headers, sku="I18N-TEST-004")
    await client.post(
        f"/api/v1/products/{sku}/i18n/de",
        json={"locale": "de", "title": "Deutsch"},
        headers=auth_headers,
    )

    del_resp = await client.delete(f"/api/v1/products/{sku}/i18n/de", headers=auth_headers)
    assert del_resp.status_code == 204

    get_resp = await client.get(f"/api/v1/products/{sku}/i18n", headers=auth_headers)
    locales = [t["locale"] for t in get_resp.json()]
    assert "de" not in locales


async def test_delete_nonexistent_translation(client, auth_headers):
    """Deleting a locale that doesn't exist returns 404."""
    sku, _ = await _setup(client, auth_headers, sku="I18N-TEST-005")
    resp = await client.delete(f"/api/v1/products/{sku}/i18n/xx", headers=auth_headers)
    assert resp.status_code == 404
