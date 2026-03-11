from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user
from app.models.user import User
from app.services import quality_service

router = APIRouter(prefix="/quality", tags=["quality"])


@router.get("/products/{sku}")
async def product_quality(
    sku: str,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    """
    Returns quality score for a single product.

    Response shape:
    {
      "sku": "...",
      "overall": 66.7,          # 0–100
      "dimensions": {
        "brand": 1.0,
        "category": 1.0,
        "seo": 0.5,
        "attributes": 1.0,
        "media": 0.0,
        "i18n": 0.0
      }
    }
    """
    return await quality_service.get_product_quality(db, sku)


@router.get("/report")
async def quality_report(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    """Paginated quality report for all products, sorted by last-updated."""
    return await quality_service.get_quality_report(db, page=page, size=size)


@router.get("/simulate/{rule_set_id}")
async def simulate_quality(
    rule_set_id: str,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    """Simula los scores de calidad aplicando un conjunto de reglas específico."""
    return await quality_service.simulate_rule_set(db, rule_set_id, page=page, size=size)
