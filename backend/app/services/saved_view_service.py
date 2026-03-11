from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from fastapi import HTTPException

from app.models.saved_view import SavedView
from app.schemas.saved_view import SavedViewCreate, SavedViewExport, SavedViewRead, SavedViewUpdate


RESOURCE_PRODUCTS = "products"


# ---------------------------------------------------------------------------
# Generic helpers (any resource)
# ---------------------------------------------------------------------------

async def list_views(
    db: AsyncSession,
    user_id: str,
    resource: str,
) -> list[SavedViewRead]:
    """Return the user's own views + all public views for a resource."""
    result = await db.execute(
        select(SavedView)
        .where(
            SavedView.resource == resource,
            or_(SavedView.user_id == user_id, SavedView.is_public.is_(True)),
        )
        .order_by(SavedView.name)
    )
    views = result.scalars().all()
    return [SavedViewRead.model_validate(v) for v in views]


async def create_view(
    db: AsyncSession,
    user_id: str,
    resource: str,
    data: SavedViewCreate,
) -> SavedViewRead:
    if data.is_default:
        existing = await db.execute(
            select(SavedView).where(
                SavedView.user_id == user_id,
                SavedView.resource == resource,
                SavedView.is_default.is_(True),
            )
        )
        for v in existing.scalars().all():
            v.is_default = False

    view = SavedView(user_id=user_id, resource=resource, **data.model_dump())
    db.add(view)
    await db.flush()
    await db.refresh(view)
    return SavedViewRead.model_validate(view)


async def get_view(
    db: AsyncSession,
    user_id: str,
    resource: str,
    view_id: str,
) -> SavedViewRead:
    """Fetch own view or any public view."""
    result = await db.execute(
        select(SavedView).where(
            SavedView.id == view_id,
            SavedView.resource == resource,
            or_(SavedView.user_id == user_id, SavedView.is_public.is_(True)),
        )
    )
    view = result.scalar_one_or_none()
    if not view:
        raise HTTPException(status_code=404, detail="Saved view not found")
    return SavedViewRead.model_validate(view)


async def update_view(
    db: AsyncSession,
    user_id: str,
    resource: str,
    view_id: str,
    data: SavedViewUpdate,
) -> SavedViewRead:
    """Only the owner can update a view."""
    result = await db.execute(
        select(SavedView).where(
            SavedView.id == view_id,
            SavedView.user_id == user_id,
            SavedView.resource == resource,
        )
    )
    view = result.scalar_one_or_none()
    if not view:
        raise HTTPException(status_code=404, detail="Saved view not found")

    update_data = data.model_dump(exclude_unset=True)

    if update_data.get("is_default"):
        existing = await db.execute(
            select(SavedView).where(
                SavedView.user_id == user_id,
                SavedView.resource == resource,
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


async def delete_view(
    db: AsyncSession,
    user_id: str,
    resource: str,
    view_id: str,
) -> None:
    """Only the owner can delete a view."""
    result = await db.execute(
        select(SavedView).where(
            SavedView.id == view_id,
            SavedView.user_id == user_id,
            SavedView.resource == resource,
        )
    )
    view = result.scalar_one_or_none()
    if not view:
        raise HTTPException(status_code=404, detail="Saved view not found")
    await db.delete(view)


async def export_view(
    db: AsyncSession,
    user_id: str,
    resource: str,
    view_id: str,
) -> SavedViewExport:
    """Return a portable (user-agnostic) definition of a view."""
    result = await db.execute(
        select(SavedView).where(
            SavedView.id == view_id,
            SavedView.resource == resource,
            or_(SavedView.user_id == user_id, SavedView.is_public.is_(True)),
        )
    )
    view = result.scalar_one_or_none()
    if not view:
        raise HTTPException(status_code=404, detail="Saved view not found")
    return SavedViewExport(
        resource=view.resource,
        name=view.name,
        description=view.description,
        filters=view.filters,
        is_default=False,  # Imported views are never default automatically
        is_public=view.is_public,
    )


async def import_view(
    db: AsyncSession,
    user_id: str,
    resource: str,
    data: SavedViewExport,
) -> SavedViewRead:
    """Create a view from an exported definition, ignoring the exported resource field."""
    create_data = SavedViewCreate(
        name=data.name,
        description=data.description,
        filters=data.filters,
        is_default=data.is_default,
        is_public=data.is_public,
    )
    return await create_view(db, user_id=user_id, resource=resource, data=create_data)


# ---------------------------------------------------------------------------
# Legacy product-specific aliases (backward compatibility)
# ---------------------------------------------------------------------------

async def list_product_views(db: AsyncSession, user_id: str) -> list[SavedViewRead]:
    return await list_views(db, user_id=user_id, resource=RESOURCE_PRODUCTS)


async def create_product_view(db: AsyncSession, user_id: str, data: SavedViewCreate) -> SavedViewRead:
    return await create_view(db, user_id=user_id, resource=RESOURCE_PRODUCTS, data=data)


async def get_product_view(db: AsyncSession, user_id: str, view_id: str) -> SavedViewRead:
    return await get_view(db, user_id=user_id, resource=RESOURCE_PRODUCTS, view_id=view_id)


async def update_product_view(db: AsyncSession, user_id: str, view_id: str, data: SavedViewUpdate) -> SavedViewRead:
    return await update_view(db, user_id=user_id, resource=RESOURCE_PRODUCTS, view_id=view_id, data=data)


async def delete_product_view(db: AsyncSession, user_id: str, view_id: str) -> None:
    return await delete_view(db, user_id=user_id, resource=RESOURCE_PRODUCTS, view_id=view_id)

