from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import HTTPException

from app.models.saved_view import SavedView
from app.schemas.saved_view import SavedViewCreate, SavedViewRead, SavedViewUpdate


RESOURCE_PRODUCTS = "products"


async def list_product_views(db: AsyncSession, user_id: str) -> list[SavedViewRead]:
    result = await db.execute(
        select(SavedView)
        .where(SavedView.user_id == user_id, SavedView.resource == RESOURCE_PRODUCTS)
        .order_by(SavedView.name)
    )
    views = result.scalars().all()
    return [SavedViewRead.model_validate(v) for v in views]


async def create_product_view(
    db: AsyncSession,
    user_id: str,
    data: SavedViewCreate,
) -> SavedViewRead:
    if data.is_default:
        # Desmarcar otras vistas por defecto del usuario para este recurso
        existing = await db.execute(
            select(SavedView).where(
                SavedView.user_id == user_id,
                SavedView.resource == RESOURCE_PRODUCTS,
                SavedView.is_default.is_(True),
            )
        )
        for v in existing.scalars().all():
            v.is_default = False

    view = SavedView(
        user_id=user_id,
        resource=RESOURCE_PRODUCTS,
        **data.model_dump(),
    )
    db.add(view)
    await db.flush()
    await db.refresh(view)
    return SavedViewRead.model_validate(view)


async def get_product_view(
    db: AsyncSession,
    user_id: str,
    view_id: str,
) -> SavedViewRead:
    result = await db.execute(
        select(SavedView).where(
            SavedView.id == view_id,
            SavedView.user_id == user_id,
            SavedView.resource == RESOURCE_PRODUCTS,
        )
    )
    view = result.scalar_one_or_none()
    if not view:
        raise HTTPException(status_code=404, detail="Saved view not found")
    return SavedViewRead.model_validate(view)


async def update_product_view(
    db: AsyncSession,
    user_id: str,
    view_id: str,
    data: SavedViewUpdate,
) -> SavedViewRead:
    result = await db.execute(
        select(SavedView).where(
            SavedView.id == view_id,
            SavedView.user_id == user_id,
            SavedView.resource == RESOURCE_PRODUCTS,
        )
    )
    view = result.scalar_one_or_none()
    if not view:
        raise HTTPException(status_code=404, detail="Saved view not found")

    update_data = data.model_dump(exclude_unset=True)

    # Si se marca como default, desmarcar las demás
    if update_data.get("is_default"):
        existing = await db.execute(
            select(SavedView).where(
                SavedView.user_id == user_id,
                SavedView.resource == RESOURCE_PRODUCTS,
                SavedView.is_default.is_(True),
                SavedView.id != view_id,
            )
        )
        for v in existing.scalars().all():
            v.is_default = False

    for field, value in update_data.items():
        setattr(view, field, value)

    await db.flush()
    await db.refresh(view)
    return SavedViewRead.model_validate(view)


async def delete_product_view(
    db: AsyncSession,
    user_id: str,
    view_id: str,
) -> None:
    result = await db.execute(
        select(SavedView).where(
            SavedView.id == view_id,
            SavedView.user_id == user_id,
            SavedView.resource == RESOURCE_PRODUCTS,
        )
    )
    view = result.scalar_one_or_none()
    if not view:
        raise HTTPException(status_code=404, detail="Saved view not found")
    await db.delete(view)

