from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles, require_scopes
from app.schemas.product_channel import ChannelCreate, ChannelRead, ChannelUpdate, ProductChannelRead, ProductChannelUpsert
from app.services import channel_service

router = APIRouter(tags=["channels"])


# ── Channel catalog ───────────────────────────────────────────────────────────

@router.get("/channels", response_model=list[ChannelRead])
async def list_channels(
    active_only: bool = False,
    db: AsyncSession = Depends(get_db),
    _user=Depends(get_current_user),
):
    return await channel_service.list_channels(db, active_only=active_only)


@router.post("/channels", response_model=ChannelRead, status_code=201)
async def create_channel(
    body: ChannelCreate,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_roles("admin")),
):
    return await channel_service.create_channel(db, body)


@router.patch("/channels/{channel_id}", response_model=ChannelRead)
async def update_channel(
    channel_id: str,
    body: ChannelUpdate,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_roles("admin")),
):
    return await channel_service.update_channel(db, channel_id, body)


@router.delete("/channels/{channel_id}", status_code=204)
async def delete_channel(
    channel_id: str,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_roles("admin")),
):
    await channel_service.delete_channel(db, channel_id)


# ── ProductChannel (producto ↔ canal) ─────────────────────────────────────────

@router.get("/products/{sku}/channels", response_model=list[ProductChannelRead])
async def list_product_channels(
    sku: str,
    db: AsyncSession = Depends(get_db),
    _user=Depends(get_current_user),
):
    return await channel_service.list_product_channels(db, sku)


@router.put("/products/{sku}/channels", response_model=ProductChannelRead, status_code=200)
async def upsert_product_channel(
    sku: str,
    body: ProductChannelUpsert,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_scopes("products:write")),
):
    return await channel_service.upsert_product_channel(db, sku, body)


@router.delete("/products/{sku}/channels/{product_channel_id}", status_code=204)
async def delete_product_channel(
    sku: str,
    product_channel_id: str,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_scopes("products:write")),
):
    await channel_service.delete_product_channel(db, sku, product_channel_id)
