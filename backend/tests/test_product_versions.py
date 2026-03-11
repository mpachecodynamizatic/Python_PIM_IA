import pytest
from httpx import AsyncClient


@pytest.fixture
async def sample_category(client: AsyncClient, auth_headers):
    response = await client.post(
        "/api/v1/taxonomy/categories",
        json={"name": "Versioning Test", "slug": "versioning-test"},
        headers=auth_headers,
    )
    return response.json()


@pytest.fixture
async def sample_product(client: AsyncClient, auth_headers, sample_category):
    """Crea un producto y lo actualiza varias veces para generar historial."""
    cat_id = sample_category["id"]
    await client.post(
        "/api/v1/products",
        json={"sku": "VER-001", "brand": "Original", "category_id": cat_id},
        headers=auth_headers,
    )
    await client.patch(
        "/api/v1/products/VER-001",
        json={"brand": "Updated"},
        headers=auth_headers,
    )
    await client.post(
        "/api/v1/products/VER-001/transitions",
        json={"new_status": "ready"},
        headers=auth_headers,
    )
    return "VER-001"


# --- Filtrado de versiones ---


@pytest.mark.asyncio
async def test_get_versions_no_filter(client: AsyncClient, auth_headers, sample_product):
    response = await client.get(
        f"/api/v1/products/{sample_product}/versions",
        headers=auth_headers,
    )
    assert response.status_code == 200
    versions = response.json()
    assert len(versions) == 3  # create + update + transition
    actions = [v["action"] for v in versions]
    assert "create" in actions
    assert "update" in actions
    assert "transition" in actions


@pytest.mark.asyncio
async def test_get_versions_filter_single(client: AsyncClient, auth_headers, sample_product):
    response = await client.get(
        f"/api/v1/products/{sample_product}/versions?action=update",
        headers=auth_headers,
    )
    assert response.status_code == 200
    versions = response.json()
    assert len(versions) == 1
    assert versions[0]["action"] == "update"


@pytest.mark.asyncio
async def test_get_versions_filter_multiple(client: AsyncClient, auth_headers, sample_product):
    response = await client.get(
        f"/api/v1/products/{sample_product}/versions?action=create,transition",
        headers=auth_headers,
    )
    assert response.status_code == 200
    versions = response.json()
    assert len(versions) == 2
    actions = {v["action"] for v in versions}
    assert actions == {"create", "transition"}


@pytest.mark.asyncio
async def test_get_versions_filter_empty_result(client: AsyncClient, auth_headers, sample_product):
    response = await client.get(
        f"/api/v1/products/{sample_product}/versions?action=restore",
        headers=auth_headers,
    )
    assert response.status_code == 200
    assert response.json() == []


# --- Snapshot en versiones ---


@pytest.mark.asyncio
async def test_version_snapshot_present(client: AsyncClient, auth_headers, sample_product):
    response = await client.get(
        f"/api/v1/products/{sample_product}/versions",
        headers=auth_headers,
    )
    versions = response.json()
    create_version = next(v for v in versions if v["action"] == "create")
    assert create_version["snapshot"] is not None
    assert create_version["snapshot"]["sku"] == "VER-001"

    update_version = next(v for v in versions if v["action"] == "update")
    assert update_version["snapshot"] is not None
    assert update_version["snapshot"]["brand"] == "Updated"


# --- Retención ---


@pytest.mark.asyncio
async def test_retention_max_versions(client: AsyncClient, auth_headers, sample_product):
    response = await client.post(
        f"/api/v1/products/{sample_product}/versions/retention",
        json={"max_versions": 2},
        headers=auth_headers,
    )
    assert response.status_code == 200
    result = response.json()
    assert result["deleted"] == 1
    assert result["remaining"] == 2

    # Verificar que quedan 2 versiones
    ver_response = await client.get(
        f"/api/v1/products/{sample_product}/versions",
        headers=auth_headers,
    )
    assert len(ver_response.json()) == 2


@pytest.mark.asyncio
async def test_retention_preserves_latest(client: AsyncClient, auth_headers, sample_product):
    """Verifica que la retención nunca elimina la última versión."""
    response = await client.post(
        f"/api/v1/products/{sample_product}/versions/retention",
        json={"max_versions": 1},
        headers=auth_headers,
    )
    result = response.json()
    assert result["remaining"] == 1

    ver_response = await client.get(
        f"/api/v1/products/{sample_product}/versions",
        headers=auth_headers,
    )
    versions = ver_response.json()
    assert len(versions) == 1
    # La última versión (transition) se conserva
    assert versions[0]["action"] == "transition"


@pytest.mark.asyncio
async def test_retention_no_policy(client: AsyncClient, auth_headers, sample_product):
    """Sin criterios de retención, no se elimina nada."""
    response = await client.post(
        f"/api/v1/products/{sample_product}/versions/retention",
        json={},
        headers=auth_headers,
    )
    result = response.json()
    assert result["deleted"] == 0
    assert result["remaining"] == 3


# --- Comentarios en versiones ---


@pytest.mark.asyncio
async def test_version_comments_crud(client: AsyncClient, auth_headers, sample_product):
    # Obtener una versión
    ver_response = await client.get(
        f"/api/v1/products/{sample_product}/versions",
        headers=auth_headers,
    )
    version_id = ver_response.json()[0]["id"]

    # Crear comentario
    comment_response = await client.post(
        f"/api/v1/products/{sample_product}/versions/{version_id}/comments",
        json={"body": "Buen cambio inicial"},
        headers=auth_headers,
    )
    assert comment_response.status_code == 201
    comment = comment_response.json()
    assert comment["body"] == "Buen cambio inicial"
    assert comment["version_id"] == version_id

    # Listar comentarios
    list_response = await client.get(
        f"/api/v1/products/{sample_product}/versions/{version_id}/comments",
        headers=auth_headers,
    )
    assert list_response.status_code == 200
    comments = list_response.json()
    assert len(comments) == 1
    assert comments[0]["body"] == "Buen cambio inicial"


@pytest.mark.asyncio
async def test_version_comments_isolated(client: AsyncClient, auth_headers, sample_product):
    """Comentarios de una versión no aparecen en otra."""
    ver_response = await client.get(
        f"/api/v1/products/{sample_product}/versions",
        headers=auth_headers,
    )
    versions = ver_response.json()
    v1_id = versions[0]["id"]
    v2_id = versions[1]["id"]

    await client.post(
        f"/api/v1/products/{sample_product}/versions/{v1_id}/comments",
        json={"body": "Comentario en v1"},
        headers=auth_headers,
    )

    # v2 no debe tener comentarios
    list_response = await client.get(
        f"/api/v1/products/{sample_product}/versions/{v2_id}/comments",
        headers=auth_headers,
    )
    assert len(list_response.json()) == 0


@pytest.mark.asyncio
async def test_product_level_comments_unaffected(client: AsyncClient, auth_headers, sample_product):
    """Los comentarios a nivel producto no se mezclan con los de versión."""
    # Crear comentario a nivel producto
    await client.post(
        f"/api/v1/products/{sample_product}/comments",
        json={"body": "Comentario general"},
        headers=auth_headers,
    )

    # Obtener versiones y crear comentario de versión
    ver_response = await client.get(
        f"/api/v1/products/{sample_product}/versions",
        headers=auth_headers,
    )
    version_id = ver_response.json()[0]["id"]
    await client.post(
        f"/api/v1/products/{sample_product}/versions/{version_id}/comments",
        json={"body": "Comentario de version"},
        headers=auth_headers,
    )

    # Comentarios del producto (sin version_id)
    product_comments = await client.get(
        f"/api/v1/products/{sample_product}/comments",
        headers=auth_headers,
    )
    assert len(product_comments.json()) == 1
    assert product_comments.json()[0]["body"] == "Comentario general"

    # Comentarios de la versión
    version_comments = await client.get(
        f"/api/v1/products/{sample_product}/versions/{version_id}/comments",
        headers=auth_headers,
    )
    assert len(version_comments.json()) == 1
    assert version_comments.json()[0]["body"] == "Comentario de version"
