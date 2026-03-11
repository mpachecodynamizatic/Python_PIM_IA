from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_scopes
from app.schemas.product_logistics import LogisticsRead, LogisticsUpdate
from app.services import logistics_service

router = APIRouter(prefix="/products/{sku}/logistics", tags=["logistics"])


@router.get("", response_model=LogisticsRead)
async def get_logistics(
    sku: str,
    db: AsyncSession = Depends(get_db),
    _user=Depends(get_current_user),
):
    return await logistics_service.get_or_create_logistics(db, sku)


@router.put("", response_model=LogisticsRead)
async def upsert_logistics(
    sku: str,
    body: LogisticsUpdate,
    db: AsyncSession = Depends(get_db),
    _user=Depends(require_scopes("products:write")),
):
    return await logistics_service.update_logistics(db, sku, body)
