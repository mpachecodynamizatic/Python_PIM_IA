import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_category(client: AsyncClient, auth_headers):
    response = await client.post(
        "/api/v1/taxonomy/categories",
        json={"name": "Furniture", "slug": "furniture"},
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["name"] == "Furniture"
    assert data["slug"] == "furniture"


@pytest.mark.asyncio
async def test_create_child_category(client: AsyncClient, auth_headers):
    parent = await client.post(
        "/api/v1/taxonomy/categories",
        json={"name": "Parent", "slug": "parent"},
        headers=auth_headers,
    )
    parent_id = parent.json()["id"]

    response = await client.post(
        "/api/v1/taxonomy/categories",
        json={"name": "Child", "slug": "child", "parent_id": parent_id},
        headers=auth_headers,
    )
    assert response.status_code == 201
    assert response.json()["parent_id"] == parent_id


@pytest.mark.asyncio
async def test_duplicate_slug(client: AsyncClient, auth_headers):
    await client.post(
        "/api/v1/taxonomy/categories",
        json={"name": "Unique", "slug": "unique-slug"},
        headers=auth_headers,
    )
    response = await client.post(
        "/api/v1/taxonomy/categories",
        json={"name": "Another", "slug": "unique-slug"},
        headers=auth_headers,
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_list_categories(client: AsyncClient, auth_headers):
    await client.post(
        "/api/v1/taxonomy/categories",
        json={"name": "Listed", "slug": "listed"},
        headers=auth_headers,
    )
    response = await client.get("/api/v1/taxonomy/categories", headers=auth_headers)
    assert response.status_code == 200
    assert len(response.json()) >= 1


@pytest.mark.asyncio
async def test_get_category(client: AsyncClient, auth_headers):
    create_resp = await client.post(
        "/api/v1/taxonomy/categories",
        json={"name": "Specific", "slug": "specific"},
        headers=auth_headers,
    )
    cat_id = create_resp.json()["id"]

    response = await client.get(f"/api/v1/taxonomy/categories/{cat_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["name"] == "Specific"


@pytest.mark.asyncio
async def test_update_category(client: AsyncClient, auth_headers):
    create_resp = await client.post(
        "/api/v1/taxonomy/categories",
        json={"name": "Old Name", "slug": "old-name"},
        headers=auth_headers,
    )
    cat_id = create_resp.json()["id"]

    response = await client.patch(
        f"/api/v1/taxonomy/categories/{cat_id}",
        json={"name": "New Name"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["name"] == "New Name"


@pytest.mark.asyncio
async def test_delete_category(client: AsyncClient, auth_headers):
    create_resp = await client.post(
        "/api/v1/taxonomy/categories",
        json={"name": "ToDelete", "slug": "to-delete"},
        headers=auth_headers,
    )
    cat_id = create_resp.json()["id"]

    response = await client.delete(f"/api/v1/taxonomy/categories/{cat_id}", headers=auth_headers)
    assert response.status_code == 200

    get_resp = await client.get(f"/api/v1/taxonomy/categories/{cat_id}", headers=auth_headers)
    assert get_resp.status_code == 404


@pytest.mark.asyncio
async def test_get_category_schema(client: AsyncClient, auth_headers):
    create_resp = await client.post(
        "/api/v1/taxonomy/categories",
        json={
            "name": "WithSchema",
            "slug": "with-schema",
            "attribute_schema": {
                "color": {"type": "string", "required": True},
                "weight": {"type": "number", "unit": "kg"},
            },
        },
        headers=auth_headers,
    )
    cat_id = create_resp.json()["id"]

    response = await client.get(
        f"/api/v1/taxonomy/categories/{cat_id}/schema", headers=auth_headers
    )
    assert response.status_code == 200
    schema = response.json()
    assert "color" in schema["attribute_schema"]
    assert schema["attribute_schema"]["color"]["required"] is True


@pytest.mark.asyncio
async def test_category_tree(client: AsyncClient, auth_headers):
    parent = await client.post(
        "/api/v1/taxonomy/categories",
        json={"name": "TreeParent", "slug": "tree-parent"},
        headers=auth_headers,
    )
    parent_id = parent.json()["id"]

    await client.post(
        "/api/v1/taxonomy/categories",
        json={"name": "TreeChild", "slug": "tree-child", "parent_id": parent_id},
        headers=auth_headers,
    )

    response = await client.get("/api/v1/taxonomy/categories/tree", headers=auth_headers)
    assert response.status_code == 200
