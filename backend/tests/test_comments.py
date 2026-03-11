"""Tests for product comments: CRUD, threads (parent_id), and permissions."""
import uuid

import pytest

from app.core.security import create_access_token, hash_password
from app.models.user import User

pytestmark = pytest.mark.asyncio

PRODUCTS_URL = "/api/v1/products"


async def _create_product(client, auth_headers, sku="CM-001"):
    cat = await client.post(
        "/api/v1/taxonomy/categories",
        json={"name": "Comment Cat", "slug": f"cm-cat-{sku}"},
        headers=auth_headers,
    )
    cat_id = cat.json()["id"]
    await client.post(
        f"{PRODUCTS_URL}",
        json={"sku": sku, "brand": "TestBrand", "category_id": cat_id},
        headers=auth_headers,
    )
    return sku


async def _create_editor(db_session):
    """Create a non-admin editor user."""
    user = User(
        id=str(uuid.uuid4()),
        email="editor@pim.local",
        hashed_password=hash_password("editorpass"),
        full_name="Editor User",
        role="editor",
        scopes=["products:read", "products:write"],
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    token = create_access_token(sub=str(user.id), role=user.role, scopes=user.scopes)
    return user, {"Authorization": f"Bearer {token}"}


# ── Basic CRUD ──────────────────────────────────────────────────────

async def test_create_comment(client, auth_headers):
    sku = await _create_product(client, auth_headers)
    resp = await client.post(
        f"{PRODUCTS_URL}/{sku}/comments",
        json={"body": "First comment"},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["body"] == "First comment"
    assert data["author_name"] == "Test Admin"
    assert data["parent_id"] is None
    assert data["reply_count"] == 0


async def test_list_comments(client, auth_headers):
    sku = await _create_product(client, auth_headers)
    await client.post(f"{PRODUCTS_URL}/{sku}/comments", json={"body": "A"}, headers=auth_headers)
    await client.post(f"{PRODUCTS_URL}/{sku}/comments", json={"body": "B"}, headers=auth_headers)
    resp = await client.get(f"{PRODUCTS_URL}/{sku}/comments", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 2


async def test_delete_own_comment(client, auth_headers):
    sku = await _create_product(client, auth_headers)
    create_resp = await client.post(
        f"{PRODUCTS_URL}/{sku}/comments", json={"body": "To delete"}, headers=auth_headers,
    )
    comment_id = create_resp.json()["id"]
    resp = await client.delete(f"{PRODUCTS_URL}/{sku}/comments/{comment_id}", headers=auth_headers)
    assert resp.status_code in (200, 204)
    # Verify deleted
    list_resp = await client.get(f"{PRODUCTS_URL}/{sku}/comments", headers=auth_headers)
    assert len(list_resp.json()) == 0


async def test_delete_nonexistent_comment_returns_404(client, auth_headers):
    sku = await _create_product(client, auth_headers)
    resp = await client.delete(
        f"{PRODUCTS_URL}/{sku}/comments/{uuid.uuid4()}", headers=auth_headers,
    )
    assert resp.status_code == 404


# ── Threads / parent_id ────────────────────────────────────────────

async def test_create_reply(client, auth_headers):
    sku = await _create_product(client, auth_headers)
    parent = await client.post(
        f"{PRODUCTS_URL}/{sku}/comments", json={"body": "Parent"}, headers=auth_headers,
    )
    parent_id = parent.json()["id"]
    reply = await client.post(
        f"{PRODUCTS_URL}/{sku}/comments",
        json={"body": "Reply", "parent_id": parent_id},
        headers=auth_headers,
    )
    assert reply.status_code == 201
    assert reply.json()["parent_id"] == parent_id


async def test_list_replies(client, auth_headers):
    sku = await _create_product(client, auth_headers)
    parent = await client.post(
        f"{PRODUCTS_URL}/{sku}/comments", json={"body": "Parent"}, headers=auth_headers,
    )
    parent_id = parent.json()["id"]
    await client.post(
        f"{PRODUCTS_URL}/{sku}/comments",
        json={"body": "Reply 1", "parent_id": parent_id},
        headers=auth_headers,
    )
    await client.post(
        f"{PRODUCTS_URL}/{sku}/comments",
        json={"body": "Reply 2", "parent_id": parent_id},
        headers=auth_headers,
    )
    resp = await client.get(
        f"{PRODUCTS_URL}/{sku}/comments/{parent_id}/replies", headers=auth_headers,
    )
    assert resp.status_code == 200
    assert len(resp.json()) == 2


async def test_reply_count_in_parent(client, auth_headers):
    sku = await _create_product(client, auth_headers)
    parent = await client.post(
        f"{PRODUCTS_URL}/{sku}/comments", json={"body": "Parent"}, headers=auth_headers,
    )
    parent_id = parent.json()["id"]
    await client.post(
        f"{PRODUCTS_URL}/{sku}/comments",
        json={"body": "Reply", "parent_id": parent_id},
        headers=auth_headers,
    )
    # List top-level comments; parent should show reply_count=1
    resp = await client.get(f"{PRODUCTS_URL}/{sku}/comments", headers=auth_headers)
    comments = resp.json()
    assert len(comments) == 1  # Only top-level
    assert comments[0]["reply_count"] == 1


async def test_reply_to_nonexistent_parent_returns_404(client, auth_headers):
    sku = await _create_product(client, auth_headers)
    resp = await client.post(
        f"{PRODUCTS_URL}/{sku}/comments",
        json={"body": "Orphan reply", "parent_id": str(uuid.uuid4())},
        headers=auth_headers,
    )
    assert resp.status_code == 404


async def test_top_level_excludes_replies(client, auth_headers):
    sku = await _create_product(client, auth_headers)
    parent = await client.post(
        f"{PRODUCTS_URL}/{sku}/comments", json={"body": "Parent"}, headers=auth_headers,
    )
    parent_id = parent.json()["id"]
    await client.post(
        f"{PRODUCTS_URL}/{sku}/comments", json={"body": "Top 2"}, headers=auth_headers,
    )
    await client.post(
        f"{PRODUCTS_URL}/{sku}/comments",
        json={"body": "Reply", "parent_id": parent_id},
        headers=auth_headers,
    )
    # Top-level should only return 2 comments (not the reply)
    resp = await client.get(f"{PRODUCTS_URL}/{sku}/comments", headers=auth_headers)
    assert len(resp.json()) == 2


# ── Permissions ─────────────────────────────────────────────────────

async def test_editor_cannot_delete_others_comment(client, auth_headers, db_session):
    sku = await _create_product(client, auth_headers)
    # Admin creates a comment
    create_resp = await client.post(
        f"{PRODUCTS_URL}/{sku}/comments", json={"body": "Admin comment"}, headers=auth_headers,
    )
    comment_id = create_resp.json()["id"]
    # Editor tries to delete it
    _, editor_headers = await _create_editor(db_session)
    resp = await client.delete(
        f"{PRODUCTS_URL}/{sku}/comments/{comment_id}", headers=editor_headers,
    )
    assert resp.status_code == 403


async def test_admin_can_delete_any_comment(client, auth_headers, db_session):
    sku = await _create_product(client, auth_headers)
    _, editor_headers = await _create_editor(db_session)
    # Editor creates a comment
    create_resp = await client.post(
        f"{PRODUCTS_URL}/{sku}/comments", json={"body": "Editor comment"}, headers=editor_headers,
    )
    comment_id = create_resp.json()["id"]
    # Admin deletes it
    resp = await client.delete(
        f"{PRODUCTS_URL}/{sku}/comments/{comment_id}", headers=auth_headers,
    )
    assert resp.status_code in (200, 204)


async def test_empty_body_rejected(client, auth_headers):
    sku = await _create_product(client, auth_headers)
    resp = await client.post(
        f"{PRODUCTS_URL}/{sku}/comments", json={"body": "   "}, headers=auth_headers,
    )
    assert resp.status_code == 422


async def test_comment_on_nonexistent_product_returns_404(client, auth_headers):
    resp = await client.post(
        f"{PRODUCTS_URL}/NONEXISTENT/comments", json={"body": "test"}, headers=auth_headers,
    )
    assert resp.status_code == 404


# ── Fase 4: Edición de comentarios ─────────────────────────────────

async def test_edit_own_comment_body(client, auth_headers):
    sku = await _create_product(client, auth_headers)
    create_resp = await client.post(
        f"{PRODUCTS_URL}/{sku}/comments", json={"body": "Original"}, headers=auth_headers,
    )
    comment_id = create_resp.json()["id"]

    patch_resp = await client.patch(
        f"{PRODUCTS_URL}/{sku}/comments/{comment_id}",
        json={"body": "Updated body"},
        headers=auth_headers,
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["body"] == "Updated body"


async def test_editor_cannot_edit_others_comment(client, auth_headers, db_session):
    sku = await _create_product(client, auth_headers)
    create_resp = await client.post(
        f"{PRODUCTS_URL}/{sku}/comments", json={"body": "Admin comment"}, headers=auth_headers,
    )
    comment_id = create_resp.json()["id"]

    _, editor_headers = await _create_editor(db_session)
    resp = await client.patch(
        f"{PRODUCTS_URL}/{sku}/comments/{comment_id}",
        json={"body": "Hijacked"},
        headers=editor_headers,
    )
    assert resp.status_code == 403


async def test_edit_comment_empty_body_rejected(client, auth_headers):
    sku = await _create_product(client, auth_headers)
    create_resp = await client.post(
        f"{PRODUCTS_URL}/{sku}/comments", json={"body": "Original"}, headers=auth_headers,
    )
    comment_id = create_resp.json()["id"]

    resp = await client.patch(
        f"{PRODUCTS_URL}/{sku}/comments/{comment_id}",
        json={"body": "   "},
        headers=auth_headers,
    )
    assert resp.status_code == 422


async def test_edit_nonexistent_comment(client, auth_headers):
    sku = await _create_product(client, auth_headers)
    resp = await client.patch(
        f"{PRODUCTS_URL}/{sku}/comments/{uuid.uuid4()}",
        json={"body": "ghost"},
        headers=auth_headers,
    )
    assert resp.status_code == 404


# ── Fase 4: Etiquetas/tags ──────────────────────────────────────────

async def test_create_comment_with_tags(client, auth_headers):
    sku = await _create_product(client, auth_headers)
    resp = await client.post(
        f"{PRODUCTS_URL}/{sku}/comments",
        json={"body": "Tagged comment", "tags": ["pendiente revision", "aprobado"]},
        headers=auth_headers,
    )
    assert resp.status_code == 201
    data = resp.json()
    assert set(data["tags"]) == {"pendiente revision", "aprobado"}


async def test_update_comment_tags(client, auth_headers):
    sku = await _create_product(client, auth_headers)
    create_resp = await client.post(
        f"{PRODUCTS_URL}/{sku}/comments",
        json={"body": "Comment", "tags": ["old-tag"]},
        headers=auth_headers,
    )
    comment_id = create_resp.json()["id"]

    patch_resp = await client.patch(
        f"{PRODUCTS_URL}/{sku}/comments/{comment_id}",
        json={"tags": ["new-tag", "another"]},
        headers=auth_headers,
    )
    assert patch_resp.status_code == 200
    assert set(patch_resp.json()["tags"]) == {"new-tag", "another"}


async def test_clear_comment_tags(client, auth_headers):
    sku = await _create_product(client, auth_headers)
    create_resp = await client.post(
        f"{PRODUCTS_URL}/{sku}/comments",
        json={"body": "Comment", "tags": ["some-tag"]},
        headers=auth_headers,
    )
    comment_id = create_resp.json()["id"]

    patch_resp = await client.patch(
        f"{PRODUCTS_URL}/{sku}/comments/{comment_id}",
        json={"tags": []},
        headers=auth_headers,
    )
    assert patch_resp.status_code == 200
    assert patch_resp.json()["tags"] == []


# ── Fase 4: Filtros por autor y fecha ──────────────────────────────

async def test_filter_comments_by_author(client, auth_headers, db_session):
    sku = await _create_product(client, auth_headers, sku="FILT-001")
    _, editor_headers = await _create_editor(db_session)

    await client.post(f"{PRODUCTS_URL}/{sku}/comments", json={"body": "Admin comment"}, headers=auth_headers)
    editor_create = await client.post(f"{PRODUCTS_URL}/{sku}/comments", json={"body": "Editor comment"}, headers=editor_headers)
    editor_user_id = editor_create.json()["user_id"]

    resp = await client.get(
        f"{PRODUCTS_URL}/{sku}/comments?author_id={editor_user_id}", headers=auth_headers,
    )
    assert resp.status_code == 200
    comments = resp.json()
    assert len(comments) == 1
    assert comments[0]["body"] == "Editor comment"


async def test_filter_comments_by_tag(client, auth_headers):
    sku = await _create_product(client, auth_headers, sku="FILT-002")
    await client.post(
        f"{PRODUCTS_URL}/{sku}/comments",
        json={"body": "Tagged", "tags": ["urgente"]},
        headers=auth_headers,
    )
    await client.post(
        f"{PRODUCTS_URL}/{sku}/comments",
        json={"body": "Not tagged"},
        headers=auth_headers,
    )

    resp = await client.get(f"{PRODUCTS_URL}/{sku}/comments?tag=urgente", headers=auth_headers)
    assert resp.status_code == 200
    comments = resp.json()
    assert len(comments) == 1
    assert comments[0]["body"] == "Tagged"


async def test_filter_comments_by_since(client, auth_headers):
    sku = await _create_product(client, auth_headers, sku="FILT-003")
    await client.post(f"{PRODUCTS_URL}/{sku}/comments", json={"body": "Old"}, headers=auth_headers)

    from datetime import datetime, timezone
    future = datetime.now(timezone.utc).isoformat()

    # All existing comments are before `future`
    resp = await client.get(
        f"{PRODUCTS_URL}/{sku}/comments?since={future}", headers=auth_headers,
    )
    assert resp.status_code == 200
    assert len(resp.json()) == 0


async def test_filter_returns_all_without_filters(client, auth_headers):
    sku = await _create_product(client, auth_headers, sku="FILT-004")
    for i in range(3):
        await client.post(f"{PRODUCTS_URL}/{sku}/comments", json={"body": f"comment {i}"}, headers=auth_headers)

    resp = await client.get(f"{PRODUCTS_URL}/{sku}/comments", headers=auth_headers)
    assert resp.status_code == 200
    assert len(resp.json()) == 3
