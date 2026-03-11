from datetime import datetime

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product_comment import ProductComment
from app.models.user import User
from app.schemas.product_comment import ProductCommentCreate, ProductCommentRead, ProductCommentUpdate
from app.services import product_service


async def _reply_counts(db: AsyncSession, comment_ids: list[str]) -> dict[str, int]:
    """Return {comment_id: reply_count} for the given IDs."""
    if not comment_ids:
        return {}
    result = await db.execute(
        select(ProductComment.parent_id, func.count())
        .where(ProductComment.parent_id.in_(comment_ids))
        .group_by(ProductComment.parent_id)
    )
    return {pid: cnt for pid, cnt in result.all()}


def _to_read(c: ProductComment, full_name: str, reply_count: int = 0) -> ProductCommentRead:
    return ProductCommentRead(
        id=str(c.id),
        sku=c.sku,
        user_id=c.user_id,
        author_name=full_name or "",
        body=c.body,
        mentions=c.mentions,
        version_id=c.version_id,
        parent_id=c.parent_id,
        reply_count=reply_count,
        tags=c.tags,
        created_at=c.created_at,
        updated_at=c.updated_at,
    )


async def list_comments(
    db: AsyncSession, sku: str, version_id: str | None = None,
    parent_id: str | None = "__unset__",
    author_id: str | None = None,
    tag: str | None = None,
    since: datetime | None = None,
    until: datetime | None = None,
) -> list[ProductCommentRead]:
    await product_service.get_product(db, sku)
    query = (
        select(ProductComment, User.full_name)
        .join(User, ProductComment.user_id == User.id)
        .where(ProductComment.sku == sku)
    )
    if version_id is not None:
        query = query.where(ProductComment.version_id == version_id)
    else:
        query = query.where(ProductComment.version_id.is_(None))

    # Filter by parent: top-level only (None), replies of a specific comment, or all
    if parent_id == "__unset__":
        query = query.where(ProductComment.parent_id.is_(None))
    elif parent_id is not None:
        query = query.where(ProductComment.parent_id == parent_id)
    # else parent_id is None → return all comments (no filter)

    if author_id is not None:
        query = query.where(ProductComment.user_id == author_id)
    if since is not None:
        query = query.where(ProductComment.created_at >= since)
    if until is not None:
        query = query.where(ProductComment.created_at <= until)

    query = query.order_by(ProductComment.created_at.asc())
    result = await db.execute(query)
    rows = result.all()

    # Post-filter by tag (JSON array field, SQLite-compatible in-Python filter)
    if tag is not None:
        rows = [(c, name) for c, name in rows if c.tags and tag in c.tags]

    comment_ids = [str(c.id) for c, _ in rows]
    counts = await _reply_counts(db, comment_ids)

    return [
        _to_read(c, full_name, counts.get(str(c.id), 0))
        for c, full_name in rows
    ]


async def get_replies(
    db: AsyncSession, sku: str, comment_id: str,
) -> list[ProductCommentRead]:
    """Get replies of a specific comment."""
    return await list_comments(db, sku, version_id=None, parent_id=comment_id)


async def create_comment(
    db: AsyncSession,
    sku: str,
    user_id: str,
    data: ProductCommentCreate,
    version_id: str | None = None,
) -> ProductCommentRead:
    await product_service.get_product(db, sku)
    body = data.body.strip()
    if not body:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="body cannot be empty")

    # Validate parent_id if provided
    if data.parent_id:
        parent_result = await db.execute(
            select(ProductComment).where(
                ProductComment.id == data.parent_id,
                ProductComment.sku == sku,
            )
        )
        if not parent_result.scalar_one_or_none():
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parent comment not found")

    comment = ProductComment(
        sku=sku,
        user_id=user_id,
        body=body,
        mentions=data.mentions,
        version_id=version_id,
        parent_id=data.parent_id,
        tags=data.tags,
    )
    db.add(comment)
    await db.flush()
    await db.refresh(comment)

    user_result = await db.execute(select(User.full_name).where(User.id == user_id))
    author_name = user_result.scalar_one_or_none() or ""

    return _to_read(comment, author_name)


async def delete_comment(
    db: AsyncSession,
    sku: str,
    comment_id: str,
    user_id: str,
    is_admin: bool,
) -> None:
    result = await db.execute(
        select(ProductComment).where(
            ProductComment.id == comment_id,
            ProductComment.sku == sku,
        )
    )
    comment = result.scalar_one_or_none()
    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")
    if not is_admin and comment.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not allowed to delete this comment")
    await db.delete(comment)


async def update_comment(
    db: AsyncSession,
    sku: str,
    comment_id: str,
    user_id: str,
    data: ProductCommentUpdate,
) -> ProductCommentRead:
    result = await db.execute(
        select(ProductComment).where(
            ProductComment.id == comment_id,
            ProductComment.sku == sku,
        )
    )
    comment = result.scalar_one_or_none()
    if not comment:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")
    if comment.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Only the author can edit this comment")

    if data.body is not None:
        body = data.body.strip()
        if not body:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="body cannot be empty")
        comment.body = body
    if data.tags is not None:
        comment.tags = data.tags

    await db.flush()
    await db.refresh(comment)

    user_result = await db.execute(select(User.full_name).where(User.id == user_id))
    author_name = user_result.scalar_one_or_none() or ""

    return _to_read(comment, author_name)
