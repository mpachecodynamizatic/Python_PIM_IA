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


# ── Fase 4: Vistas compartidas (is_public) ───────────────────────────────────

async def test_create_public_view(client, auth_headers):
    resp = await client.post(
        VIEWS_URL,
        json={"name": "Public View", "filters": {"status": "ready"}, "is_public": True},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["is_public"] is True
    assert data["user_id"] is not None


async def test_create_private_view_default(client, auth_headers):
    resp = await client.post(
        VIEWS_URL,
        json={"name": "Private View", "filters": {}},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    assert resp.json()["is_public"] is False


async def test_list_views_includes_own_and_public(client, auth_headers, db_session):
    """Users should see their own views plus public views from others."""
    import uuid
    from app.models.saved_view import SavedView
    from app.core.security import hash_password
    from app.models.user import User

    # Create a second user
    other_user = User(
        id=str(uuid.uuid4()),
        email="other@pim.local",
        hashed_password=hash_password("pass"),
        full_name="Other",
        role="viewer",
        scopes=[],
    )
    db_session.add(other_user)

    # Create a public view owned by the other user
    other_public_view = SavedView(
        user_id=str(other_user.id),
        resource="products",
        name="Other User Public View",
        filters={"brand": "OtherBrand"},
        is_default=False,
        is_public=True,
    )
    # Create a private view owned by the other user
    other_private_view = SavedView(
        user_id=str(other_user.id),
        resource="products",
        name="Other User Private View",
        filters={"status": "draft"},
        is_default=False,
        is_public=False,
    )
    db_session.add_all([other_public_view, other_private_view])
    await db_session.commit()

    # Create own view
    await client.post(
        VIEWS_URL,
        json={"name": "My Own View", "filters": {}},
        headers=auth_headers,
    )

    resp = await client.get(VIEWS_URL, headers=auth_headers)
    assert resp.status_code == 200
    names = [v["name"] for v in resp.json()]

    # Should see own view and the other user's public view
    assert "My Own View" in names
    assert "Other User Public View" in names
    # Should NOT see the other user's private view
    assert "Other User Private View" not in names


async def test_cannot_update_other_users_view(client, auth_headers, db_session):
    """Cannot update a view owned by another user (even if public)."""
    import uuid
    from app.models.saved_view import SavedView
    from app.core.security import hash_password
    from app.models.user import User

    other_user = User(
        id=str(uuid.uuid4()),
        email="other2@pim.local",
        hashed_password=hash_password("pass"),
        full_name="Other2",
        role="viewer",
        scopes=[],
    )
    db_session.add(other_user)
    other_view = SavedView(
        user_id=str(other_user.id),
        resource="products",
        name="Other View",
        filters={},
        is_default=False,
        is_public=True,
    )
    db_session.add(other_view)
    await db_session.commit()

    resp = await client.patch(
        f"{VIEWS_URL}/{other_view.id}",
        json={"name": "Hijacked"},
        headers=auth_headers,
    )
    assert resp.status_code == 404


async def test_cannot_delete_other_users_view(client, auth_headers, db_session):
    """Cannot delete a view owned by another user."""
    import uuid
    from app.models.saved_view import SavedView
    from app.core.security import hash_password
    from app.models.user import User

    other_user = User(
        id=str(uuid.uuid4()),
        email="other3@pim.local",
        hashed_password=hash_password("pass"),
        full_name="Other3",
        role="viewer",
        scopes=[],
    )
    db_session.add(other_user)
    other_view = SavedView(
        user_id=str(other_user.id),
        resource="products",
        name="Other Delete View",
        filters={},
        is_default=False,
        is_public=True,
    )
    db_session.add(other_view)
    await db_session.commit()

    resp = await client.delete(
        f"{VIEWS_URL}/{other_view.id}",
        headers=auth_headers,
    )
    assert resp.status_code == 404


# ── Fase 4: Vistas para otros recursos ───────────────────────────────────────

async def test_generic_resource_views(client, auth_headers):
    """Views work for any resource string, not just products."""
    # Create a view for the 'media' resource
    resp = await client.post(
        "/api/v1/views/media",
        json={"name": "Media View", "filters": {"type": "image"}, "is_public": False},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["resource"] == "media"
    assert data["name"] == "Media View"

    # List media views
    resp = await client.get("/api/v1/views/media", headers=auth_headers)
    assert resp.status_code == 200
    names = [v["name"] for v in resp.json()]
    assert "Media View" in names

    # Products views list should not contain media view
    resp_products = await client.get(VIEWS_URL, headers=auth_headers)
    assert all(v["resource"] == "products" for v in resp_products.json())


async def test_generic_resource_crud(client, auth_headers):
    """Full CRUD cycle for a generic resource view."""
    # Create
    create_resp = await client.post(
        "/api/v1/views/quality",
        json={"name": "Quality View", "filters": {"min_score": 80}},
        headers=auth_headers,
    )
    assert create_resp.status_code == 201
    view_id = create_resp.json()["id"]

    # Get
    get_resp = await client.get(f"/api/v1/views/quality/{view_id}", headers=auth_headers)
    assert get_resp.status_code == 200

    # Update
    patch_resp = await client.patch(
        f"/api/v1/views/quality/{view_id}",
        json={"name": "Updated Quality View"},
        headers=auth_headers,
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["name"] == "Updated Quality View"

    # Delete
    del_resp = await client.delete(f"/api/v1/views/quality/{view_id}", headers=auth_headers)
    assert del_resp.status_code == 204


# ── Fase 4: Exportar / importar vistas ───────────────────────────────────────

async def test_export_view(client, auth_headers):
    """Export returns a portable definition without user_id or id."""
    create_resp = await client.post(
        VIEWS_URL,
        json={"name": "Export Me", "filters": {"status": "ready", "brand": "ACME"}, "is_public": True},
        headers=auth_headers,
    )
    view_id = create_resp.json()["id"]

    resp = await client.get(f"{VIEWS_URL}/{view_id}/export", headers=auth_headers)
    assert resp.status_code == 200
    data = resp.json()

    # Exported data should NOT contain user_id or id
    assert "user_id" not in data
    assert "id" not in data
    assert data["resource"] == "products"
    assert data["name"] == "Export Me"
    assert data["filters"]["status"] == "ready"
    assert data["filters"]["brand"] == "ACME"


async def test_import_view(client, auth_headers):
    """Import creates a new view in the user's account."""
    exported = {
        "resource": "products",
        "name": "Imported View",
        "description": "from export",
        "filters": {"status": "draft"},
        "is_default": False,
        "is_public": False,
    }

    resp = await client.post(
        "/api/v1/views/products/import",
        json=exported,
        headers=auth_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["name"] == "Imported View"
    assert data["filters"]["status"] == "draft"
    assert data["resource"] == "products"
    # Should be assigned to this user
    assert data["user_id"] is not None


async def test_export_then_import_roundtrip(client, auth_headers):
    """Export a view and re-import it — content is preserved."""
    create_resp = await client.post(
        VIEWS_URL,
        json={
            "name": "Roundtrip View",
            "description": "roundtrip desc",
            "filters": {"brand": "Nike", "status": "ready"},
            "is_public": True,
        },
        headers=auth_headers,
    )
    view_id = create_resp.json()["id"]

    # Export
    export_resp = await client.get(f"{VIEWS_URL}/{view_id}/export", headers=auth_headers)
    assert export_resp.status_code == 200
    exported = export_resp.json()

    # Import (creates a duplicate with a new id)
    import_resp = await client.post(
        "/api/v1/views/products/import",
        json=exported,
        headers=auth_headers,
    )
    assert import_resp.status_code == 201
    imported = import_resp.json()

    assert imported["name"] == "Roundtrip View"
    assert imported["filters"] == {"brand": "Nike", "status": "ready"}
    assert imported["description"] == "roundtrip desc"
    assert imported["id"] != view_id  # New view, different id


async def test_export_not_found(client, auth_headers):
    resp = await client.get(f"{VIEWS_URL}/nonexistent/export", headers=auth_headers)
    assert resp.status_code == 404


async def test_import_public_view_from_another_user(client, auth_headers, db_session):
    """A user can import (copy) a public view from another user."""
    import uuid
    from app.models.saved_view import SavedView
    from app.core.security import hash_password
    from app.models.user import User

    other_user = User(
        id=str(uuid.uuid4()),
        email="other4@pim.local",
        hashed_password=hash_password("pass"),
        full_name="Other4",
        role="viewer",
        scopes=[],
    )
    db_session.add(other_user)
    other_view = SavedView(
        user_id=str(other_user.id),
        resource="products",
        name="Public Exportable View",
        filters={"status": "ready"},
        is_default=False,
        is_public=True,
    )
    db_session.add(other_view)
    await db_session.commit()

    # Our user exports the other user's public view
    export_resp = await client.get(
        f"{VIEWS_URL}/{other_view.id}/export",
        headers=auth_headers,
    )
    assert export_resp.status_code == 200

    # Then imports it as their own
    import_resp = await client.post(
        "/api/v1/views/products/import",
        json=export_resp.json(),
        headers=auth_headers,
    )
    assert import_resp.status_code == 201
    assert import_resp.json()["name"] == "Public Exportable View"
