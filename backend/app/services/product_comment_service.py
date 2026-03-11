from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product_comment import ProductComment
from app.models.user import User
from app.schemas.product_comment import ProductCommentCreate, ProductCommentRead
from app.services import product_service


async def list_comments(
    db: AsyncSession, sku: str, version_id: str | None = None,
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
    query = query.order_by(ProductComment.created_at.asc())
    result = await db.execute(query)
    rows = result.all()
    return [
        ProductCommentRead(
            id=str(c.id),
            sku=c.sku,
            user_id=c.user_id,
            author_name=full_name or "",
            body=c.body,
            mentions=c.mentions,
            version_id=c.version_id,
            created_at=c.created_at,
        )
        for c, full_name in rows
    ]


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
    comment = ProductComment(
        sku=sku,
        user_id=user_id,
        body=body,
        mentions=data.mentions,
        version_id=version_id,
    )
    db.add(comment)
    await db.flush()
    await db.refresh(comment)

    user_result = await db.execute(select(User.full_name).where(User.id == user_id))
    author_name = user_result.scalar_one_or_none() or ""

    return ProductCommentRead(
        id=str(comment.id),
        sku=comment.sku,
        user_id=comment.user_id,
        author_name=author_name,
        body=comment.body,
        mentions=comment.mentions,
        version_id=comment.version_id,
        created_at=comment.created_at,
    )


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
