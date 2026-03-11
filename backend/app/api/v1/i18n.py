"""
I18N enrichment endpoints.

Complements the per-product i18n upsert (POST /products/{sku}/i18n/{locale})
with management views:
  GET  /i18n/locales          → all locales currently in use
  GET  /i18n/missing          → products that have NO translation for a given locale
  GET  /products/{sku}/i18n   → all translations for a product (already in products.py,
                                  but also exposed here for convenience)
  DELETE /products/{sku}/i18n/{locale} → delete a specific translation
"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy import distinct, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_scopes
from app.models.product import Product, ProductI18n
from app.models.user import User
from app.schemas.product import ProductI18nRead

router = APIRouter(tags=["i18n"])


@router.get("/i18n/locales")
async def list_locales(
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> list[str]:
    """Return the distinct locales that have at least one translation."""
    result = await db.execute(select(distinct(ProductI18n.locale)).order_by(ProductI18n.locale))
    return list(result.scalars().all())


@router.get("/i18n/missing")
async def missing_translations(
    locale: str = Query(..., description="Locale to check, e.g. 'es', 'en'"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> dict:
    """
    Return products that do NOT have a translation for the given locale.
    Useful to drive enrichment workflows.
    """
    from sqlalchemy import func

    # SKUs that already have the locale
    translated_skus = select(ProductI18n.sku).where(ProductI18n.locale == locale)

    base_q = select(Product).where(Product.sku.notin_(translated_skus))

    count = (
        await db.execute(select(func.count()).select_from(base_q.subquery()))
    ).scalar() or 0

    result = await db.execute(
        base_q.order_by(Product.sku).offset((page - 1) * size).limit(size)
    )
    products = result.scalars().all()

    import math

    return {
        "locale": locale,
        "items": [{"sku": p.sku, "brand": p.brand, "status": p.status} for p in products],
        "total": count,
        "page": page,
        "size": size,
        "pages": math.ceil(count / size) if size > 0 else 0,
    }


@router.get("/products/{sku}/i18n", response_model=list[ProductI18nRead])
async def get_product_translations(
    sku: str,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    """All translations for a product, ordered by locale."""
    result = await db.execute(
        select(ProductI18n)
        .where(ProductI18n.sku == sku)
        .order_by(ProductI18n.locale)
    )
    return list(result.scalars().all())


@router.delete("/products/{sku}/i18n/{locale}", status_code=204)
async def delete_translation(
    sku: str,
    locale: str,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_scopes("products:write")),
):
    """Delete the translation for a specific locale."""
    from fastapi import HTTPException

    result = await db.execute(
        select(ProductI18n).where(ProductI18n.sku == sku, ProductI18n.locale == locale)
    )
    translation = result.scalar_one_or_none()
    if translation is None:
        raise HTTPException(status_code=404, detail=f"Translation '{locale}' not found for SKU '{sku}'")
    await db.delete(translation)
    await db.commit()
