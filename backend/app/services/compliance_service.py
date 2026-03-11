from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.product_compliance import ProductCompliance
from app.schemas.product_compliance import ComplianceUpdate


async def get_or_create_compliance(db: AsyncSession, sku: str) -> ProductCompliance:
    result = await db.execute(select(ProductCompliance).where(ProductCompliance.sku == sku))
    row = result.scalar_one_or_none()
    if row is None:
        row = ProductCompliance(sku=sku)
        db.add(row)
        await db.flush()
        await db.refresh(row)
    return row


async def update_compliance(db: AsyncSession, sku: str, data: ComplianceUpdate) -> ProductCompliance:
    row = await get_or_create_compliance(db, sku)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(row, field, value)
    await db.flush()
    await db.refresh(row)
    return row
