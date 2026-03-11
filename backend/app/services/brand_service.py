from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.brand import Brand
from app.schemas.brand import BrandCreate, BrandUpdate


async def list_brands(db: AsyncSession, active_only: bool = False) -> list[Brand]:
    q = select(Brand).order_by(Brand.name)
    if active_only:
        q = q.where(Brand.active.is_(True))
    result = await db.execute(q)
    return list(result.scalars().all())


async def get_brand(db: AsyncSession, brand_id: str) -> Brand:
    result = await db.execute(select(Brand).where(Brand.id == brand_id))
    brand = result.scalar_one_or_none()
    if brand is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Brand not found")
    return brand


async def create_brand(db: AsyncSession, data: BrandCreate) -> Brand:
    existing = await db.execute(select(Brand).where(Brand.slug == data.slug))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Brand with slug '{data.slug}' already exists",
        )
    brand = Brand(**data.model_dump())
    db.add(brand)
    await db.flush()
    await db.refresh(brand)
    return brand


async def update_brand(db: AsyncSession, brand_id: str, data: BrandUpdate) -> Brand:
    brand = await get_brand(db, brand_id)
    update_data = data.model_dump(exclude_unset=True)
    if "slug" in update_data:
        existing = await db.execute(
            select(Brand).where(Brand.slug == update_data["slug"], Brand.id != brand_id)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail=f"Brand with slug '{update_data['slug']}' already exists",
            )
    for field, value in update_data.items():
        setattr(brand, field, value)
    await db.flush()
    await db.refresh(brand)
    return brand


async def delete_brand(db: AsyncSession, brand_id: str) -> None:
    brand = await get_brand(db, brand_id)
    await db.delete(brand)
    await db.flush()
