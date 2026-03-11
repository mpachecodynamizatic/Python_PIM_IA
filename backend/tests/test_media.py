"""Tests for DAM / media endpoints."""
import io
import pytest

pytestmark = pytest.mark.asyncio


async def _create_product(client, auth_headers, category_id):
    resp = await client.post(
        "/api/v1/products",
        json={"sku": "MEDIA-TEST-001", "brand": "TestBrand", "category_id": category_id},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    return resp.json()


async def _create_category(client, auth_headers):
    resp = await client.post(
        "/api/v1/taxonomy/categories",
        json={"name": "Media Cat", "slug": "media-cat"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    return resp.json()["id"]


async def test_upload_image(client, auth_headers):
    """Upload a PNG image and verify the returned asset."""
    cat_id = await _create_category(client, auth_headers)
    await _create_product(client, auth_headers, cat_id)

    img_bytes = b"\x89PNG\r\n\x1a\n" + b"\x00" * 20  # minimal fake PNG header
    resp = await client.post(
        "/api/v1/media",
        files={"file": ("test.png", io.BytesIO(img_bytes), "image/png")},
        data={"sku": "MEDIA-TEST-001", "kind": "image"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["sku"] == "MEDIA-TEST-001"
    assert data["kind"] == "image"
    assert data["url"].startswith("/uploads/")
    assert data["filename"] == "test.png"


async def test_upload_invalid_type(client, auth_headers):
    """Uploading an unsupported MIME type returns 400."""
    resp = await client.post(
        "/api/v1/media",
        files={"file": ("test.exe", io.BytesIO(b"MZ"), "application/octet-stream")},
        data={"kind": "other"},
        headers=auth_headers,
    )
    assert resp.status_code == 400


async def test_list_media_by_sku(client, auth_headers):
    """Listing by SKU returns only assets for that product."""
    cat_id = await _create_category(client, auth_headers)
    await _create_product(client, auth_headers, cat_id)

    for i in range(2):
        await client.post(
            "/api/v1/media",
            files={"file": (f"img{i}.png", io.BytesIO(b"\x89PNG\r\n\x1a\n"), "image/png")},
            data={"sku": "MEDIA-TEST-001", "kind": "image"},
            headers=auth_headers,
        )

    resp = await client.get("/api/v1/media?sku=MEDIA-TEST-001", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) >= 2


async def test_delete_media(client, auth_headers):
    """Uploaded asset can be deleted."""
    cat_id = await _create_category(client, auth_headers)
    await _create_product(client, auth_headers, cat_id)

    up = await client.post(
        "/api/v1/media",
        files={"file": ("del.png", io.BytesIO(b"\x89PNG\r\n\x1a\n"), "image/png")},
        data={"sku": "MEDIA-TEST-001", "kind": "image"},
        headers=auth_headers,
    )
    media_id = up.json()["id"]

    del_resp = await client.delete(f"/api/v1/media/{media_id}", headers=auth_headers)
    assert del_resp.status_code == 204

    get_resp = await client.get(f"/api/v1/media/{media_id}", headers=auth_headers)
    assert get_resp.status_code == 404


async def test_link_unlinked_asset(client, auth_headers):
    """An asset uploaded without SKU can be linked later."""
    cat_id = await _create_category(client, auth_headers)
    await _create_product(client, auth_headers, cat_id)

    up = await client.post(
        "/api/v1/media",
        files={"file": ("nolink.png", io.BytesIO(b"\x89PNG\r\n\x1a\n"), "image/png")},
        data={"kind": "image"},
        headers=auth_headers,
    )
    assert up.json()["sku"] is None
    media_id = up.json()["id"]

    link_resp = await client.patch(
        f"/api/v1/media/{media_id}/link?sku=MEDIA-TEST-001",
        headers=auth_headers,
    )
    assert link_resp.status_code == 200
    assert link_resp.json()["sku"] == "MEDIA-TEST-001"
