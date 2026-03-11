"""Tests for Saved Views CRUD and advanced product filters."""
import pytest

pytestmark = pytest.mark.asyncio

VIEWS_URL = "/api/v1/views/products"


async def _create_product(client, auth_headers, sku="SV-001"):
    cat = await client.post(
        "/api/v1/taxonomy/categories",
        json={"name": "SV Cat", "slug": f"sv-cat-{sku}"},
        headers=auth_headers,
    )
    cat_id = cat.json()["id"]
    await client.post(
        "/api/v1/products",
        json={"sku": sku, "brand": "TestBrand", "category_id": cat_id},
        headers=auth_headers,
    )
    return sku, cat_id


# ── CRUD Saved Views ────────────────────────────────────────────────

async def test_create_view(client, auth_headers):
    resp = await client.post(
        VIEWS_URL,
        json={"name": "My View", "filters": {"status": "draft"}, "is_default": False},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "My View"
    assert data["filters"] == {"status": "draft"}
    assert data["resource"] == "products"
    assert data["is_default"] is False


async def test_list_views(client, auth_headers):
    await client.post(
        VIEWS_URL,
        json={"name": "View A", "filters": {"status": "draft"}},
        headers=auth_headers,
    )
    await client.post(
        VIEWS_URL,
        json={"name": "View B", "filters": {"brand": "Nike"}},
        headers=auth_headers,
    )
    resp = await client.get(VIEWS_URL, headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) >= 2


async def test_get_view(client, auth_headers):
    create = await client.post(
        VIEWS_URL,
        json={"name": "Detail View", "filters": {"q": "test"}},
        headers=auth_headers,
    )
    view_id = create.json()["id"]
    resp = await client.get(f"{VIEWS_URL}/{view_id}", headers=auth_headers)
    assert resp.status_code == 200
    assert resp.json()["name"] == "Detail View"


async def test_update_view(client, auth_headers):
    create = await client.post(
        VIEWS_URL,
        json={"name": "Original", "filters": {"status": "draft"}},
        headers=auth_headers,
    )
    view_id = create.json()["id"]

    resp = await client.patch(
        f"{VIEWS_URL}/{view_id}",
        json={"name": "Updated", "filters": {"status": "ready"}, "is_default": True},
        headers=auth_headers,
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["name"] == "Updated"
    assert data["filters"] == {"status": "ready"}
    assert data["is_default"] is True


async def test_delete_view(client, auth_headers):
    create = await client.post(
        VIEWS_URL,
        json={"name": "To Delete", "filters": {}},
        headers=auth_headers,
    )
    view_id = create.json()["id"]
    resp = await client.delete(f"{VIEWS_URL}/{view_id}", headers=auth_headers)
    assert resp.status_code in (200, 204)

    get_resp = await client.get(f"{VIEWS_URL}/{view_id}", headers=auth_headers)
    assert get_resp.status_code == 404


async def test_default_view_unsets_previous(client, auth_headers):
    """Setting a new view as default unsets the previous default."""
    a = await client.post(
        VIEWS_URL,
        json={"name": "Default A", "filters": {}, "is_default": True},
        headers=auth_headers,
    )
    a_id = a.json()["id"]
    assert a.json()["is_default"] is True

    b = await client.post(
        VIEWS_URL,
        json={"name": "Default B", "filters": {}, "is_default": True},
        headers=auth_headers,
    )
    b_id = b.json()["id"]

    views = (await client.get(VIEWS_URL, headers=auth_headers)).json()
    defaults = [v for v in views if v["is_default"]]
    assert len(defaults) == 1
    assert defaults[0]["id"] == b_id


async def test_view_not_found(client, auth_headers):
    resp = await client.get(f"{VIEWS_URL}/nonexistent", headers=auth_headers)
    assert resp.status_code == 404


# ── Advanced Product Filters ────────────────────────────────────────

async def test_filter_by_brand(client, auth_headers):
    await _create_product(client, auth_headers, sku="BRAND-A")
    resp = await client.get(
        "/api/v1/products?brand=TestBrand",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert any(p["sku"] == "BRAND-A" for p in items)


async def test_filter_by_category(client, auth_headers):
    sku, cat_id = await _create_product(client, auth_headers, sku="CAT-FILTER")
    resp = await client.get(
        f"/api/v1/products?category_id={cat_id}",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    items = resp.json()["items"]
    assert all(p["category_id"] == cat_id for p in items)


async def test_filter_by_date_range(client, auth_headers):
    await _create_product(client, auth_headers, sku="DATE-001")
    # Use a wide date range that includes today
    resp = await client.get(
        "/api/v1/products?created_from=2020-01-01&created_to=2030-12-31",
        headers=auth_headers,
    )
    assert resp.status_code == 200
    assert resp.json()["total"] >= 1


async def test_filter_has_i18n(client, auth_headers):
    sku, _ = await _create_product(client, auth_headers, sku="I18N-FILTER")

    # Without i18n
    resp = await client.get("/api/v1/products?has_i18n=false", headers=auth_headers)
    assert resp.status_code == 200
    skus_without = [p["sku"] for p in resp.json()["items"]]
    assert sku in skus_without

    # Add translation
    await client.post(
        f"/api/v1/products/{sku}/i18n/es",
        json={"locale": "es", "title": "Titulo"},
        headers=auth_headers,
    )

    # With i18n
    resp = await client.get("/api/v1/products?has_i18n=true", headers=auth_headers)
    skus_with = [p["sku"] for p in resp.json()["items"]]
    assert sku in skus_with
