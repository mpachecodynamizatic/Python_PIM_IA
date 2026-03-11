import pytest
from httpx import AsyncClient


@pytest.fixture
async def sample_category(client: AsyncClient, auth_headers):
    response = await client.post(
        "/api/v1/taxonomy/categories",
        json={"name": "Electronics", "slug": "electronics"},
        headers=auth_headers,
    )
    return response.json()


@pytest.mark.asyncio
async def test_create_product(client: AsyncClient, auth_headers, sample_category):
    response = await client.post(
        "/api/v1/products",
        json={
            "sku": "TEST-001",
            "brand": "TestBrand",
            "category_id": sample_category["id"],
        },
        headers=auth_headers,
    )
    assert response.status_code == 201
    data = response.json()
    assert data["sku"] == "TEST-001"
    assert data["brand"] == "TestBrand"
    assert data["status"] == "draft"


@pytest.mark.asyncio
async def test_create_duplicate_product(client: AsyncClient, auth_headers, sample_category):
    await client.post(
        "/api/v1/products",
        json={"sku": "DUP-001", "brand": "B", "category_id": sample_category["id"]},
        headers=auth_headers,
    )
    response = await client.post(
        "/api/v1/products",
        json={"sku": "DUP-001", "brand": "B", "category_id": sample_category["id"]},
        headers=auth_headers,
    )
    assert response.status_code == 409


@pytest.mark.asyncio
async def test_list_products(client: AsyncClient, auth_headers, sample_category):
    await client.post(
        "/api/v1/products",
        json={"sku": "LIST-001", "brand": "A", "category_id": sample_category["id"]},
        headers=auth_headers,
    )
    response = await client.get("/api/v1/products", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert data["total"] >= 1


@pytest.mark.asyncio
async def test_get_product(client: AsyncClient, auth_headers, sample_category):
    await client.post(
        "/api/v1/products",
        json={"sku": "GET-001", "brand": "B", "category_id": sample_category["id"]},
        headers=auth_headers,
    )
    response = await client.get("/api/v1/products/GET-001", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["sku"] == "GET-001"


@pytest.mark.asyncio
async def test_update_product(client: AsyncClient, auth_headers, sample_category):
    await client.post(
        "/api/v1/products",
        json={"sku": "UPD-001", "brand": "Old", "category_id": sample_category["id"]},
        headers=auth_headers,
    )
    response = await client.patch(
        "/api/v1/products/UPD-001",
        json={"brand": "New"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["brand"] == "New"


@pytest.mark.asyncio
async def test_transition_product(client: AsyncClient, auth_headers, sample_category):
    await client.post(
        "/api/v1/products",
        json={"sku": "TRANS-001", "brand": "B", "category_id": sample_category["id"]},
        headers=auth_headers,
    )
    response = await client.post(
        "/api/v1/products/TRANS-001/transitions",
        json={"new_status": "ready"},
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json()["status"] == "ready"


@pytest.mark.asyncio
async def test_invalid_transition(client: AsyncClient, auth_headers, sample_category):
    await client.post(
        "/api/v1/products",
        json={"sku": "INV-001", "brand": "B", "category_id": sample_category["id"]},
        headers=auth_headers,
    )
    response = await client.post(
        "/api/v1/products/INV-001/transitions",
        json={"new_status": "retired"},
        headers=auth_headers,
    )
    assert response.status_code == 422


@pytest.mark.asyncio
async def test_product_not_found(client: AsyncClient, auth_headers):
    response = await client.get("/api/v1/products/NONEXIST", headers=auth_headers)
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_audit_log(client: AsyncClient, auth_headers, sample_category):
    await client.post(
        "/api/v1/products",
        json={"sku": "AUDIT-001", "brand": "B", "category_id": sample_category["id"]},
        headers=auth_headers,
    )
    response = await client.get("/api/v1/products/AUDIT-001/audit", headers=auth_headers)
    assert response.status_code == 200
    logs = response.json()
    assert len(logs) >= 1
    assert logs[0]["action"] == "create"
