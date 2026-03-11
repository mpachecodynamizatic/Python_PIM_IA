from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.channel import Channel
from app.models.product_channel import ProductChannel
from app.schemas.product_channel import ChannelCreate, ChannelUpdate, ProductChannelUpsert


# ── Channel catalog ───────────────────────────────────────────────────────────

async def list_channels(db: AsyncSession, active_only: bool = False) -> list[Channel]:
    q = select(Channel).order_by(Channel.name)
    if active_only:
        q = q.where(Channel.active.is_(True))
    result = await db.execute(q)
    return list(result.scalars().all())


async def get_channel(db: AsyncSession, channel_id: str) -> Channel:
    result = await db.execute(select(Channel).where(Channel.id == channel_id))
    row = result.scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Channel not found")
    return row


async def create_channel(db: AsyncSession, data: ChannelCreate) -> Channel:
    row = Channel(**data.model_dump())
    db.add(row)
    await db.flush()
    await db.refresh(row)
    return row


async def update_channel(db: AsyncSession, channel_id: str, data: ChannelUpdate) -> Channel:
    row = await get_channel(db, channel_id)
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(row, field, value)
    await db.flush()
    await db.refresh(row)
    return row


async def delete_channel(db: AsyncSession, channel_id: str) -> None:
    row = await get_channel(db, channel_id)
    await db.delete(row)


# ── ProductChannel ────────────────────────────────────────────────────────────

async def list_product_channels(db: AsyncSession, sku: str) -> list[ProductChannel]:
    result = await db.execute(
        select(ProductChannel)
        .where(ProductChannel.sku == sku)
        .options(selectinload(ProductChannel.channel_obj))
        .order_by(ProductChannel.channel_id)
    )
    return list(result.scalars().all())


async def upsert_product_channel(db: AsyncSession, sku: str, data: ProductChannelUpsert) -> ProductChannel:
    result = await db.execute(
        select(ProductChannel).where(
            ProductChannel.sku == sku, ProductChannel.channel_id == data.channel_id
        )
    )
    row = result.scalar_one_or_none()
    if row is None:
        row = ProductChannel(sku=sku, **data.model_dump())
        db.add(row)
    else:
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(row, field, value)
    await db.flush()
    await db.refresh(row, attribute_names=["channel_obj"])
    return row


async def delete_product_channel(db: AsyncSession, sku: str, product_channel_id: str) -> None:
    result = await db.execute(
        select(ProductChannel).where(
            ProductChannel.sku == sku, ProductChannel.id == product_channel_id
        )
    )
    row = result.scalar_one_or_none()
    if row is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product channel entry not found")
    await db.delete(row)
