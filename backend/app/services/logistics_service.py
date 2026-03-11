from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product_logistics import ProductLogistics
from app.schemas.product_logistics import LogisticsUpdate


async def get_or_create_logistics(db: AsyncSession, sku: str) -> ProductLogistics:
    result = await db.execute(select(ProductLogistics).where(ProductLogistics.sku == sku))
    row = result.scalar_one_or_none()
    if row is None:
        row = ProductLogistics(sku=sku)
        db.add(row)
        await db.flush()
        await db.refresh(row)
    return row


async def update_logistics(db: AsyncSession, sku: str, data: LogisticsUpdate) -> ProductLogistics:
    row = await get_or_create_logistics(db, sku)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(row, field, value)
    await db.flush()
    await db.refresh(row)
    return row
