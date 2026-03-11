from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_roles
from app.schemas.brand import BrandCreate, BrandRead, BrandUpdate
from app.services import brand_service

router = APIRouter(prefix="/brands", tags=["brands"])


@router.get("", response_model=list[BrandRead])
async def list_brands(
    active_only: bool = Query(False),
    db: AsyncSession = Depends(get_db),
    _user=Depends(get_current_user),
):
    return await brand_service.list_brands(db, active_only=active_only)


@router.post("", response_model=BrandRead, status_code=201)
async def create_brand(
    body: BrandCreate,
    db: AsyncSession = Depends(get_db),
    _admin=Depends(require_roles("admin")),
):
    return await brand_service.create_brand(db, body)


@router.get("/{brand_id}", response_model=BrandRead)
async def get_brand(
    brand_id: str,
    db: AsyncSession = Depends(get_db),
    _user=Depends(get_current_user),
):
    return await brand_service.get_brand(db, brand_id)


@router.patch("/{brand_id}", response_model=BrandRead)
async def update_brand(
    brand_id: str,
    body: BrandUpdate,
    db: AsyncSession = Depends(get_db),
    _admin=Depends(require_roles("admin")),
):
    return await brand_service.update_brand(db, brand_id, body)


@router.delete("/{brand_id}", status_code=204)
async def delete_brand(
    brand_id: str,
    db: AsyncSession = Depends(get_db),
    _admin=Depends(require_roles("admin")),
):
    await brand_service.delete_brand(db, brand_id)
