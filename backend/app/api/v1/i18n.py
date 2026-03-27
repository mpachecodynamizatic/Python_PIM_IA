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


@router.get("/i18n/stats")
async def get_i18n_stats(
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
) -> dict:
    """
    Obtener estadísticas de traducción por idioma.

    Calcula para cada locale:
    - Total de productos en el catálogo (activos)
    - Productos con traducción completa (title y description no vacíos)
    - Productos pendientes de traducción
    - Porcentaje de completitud

    Returns:
        {
            "by_locale": {
                "es": {"total": 150, "translated": 130, "pending": 20, "percentage": 86.7},
                "fr": {"total": 150, "translated": 105, "pending": 45, "percentage": 70.0},
                ...
            },
            "total_products": 150,
            "locales": ["es", "fr", "de"]
        }
    """
    from sqlalchemy import func

    # 1. Obtener total de productos activos (no retirados)
    total_result = await db.execute(
        select(func.count(Product.sku)).where(Product.status != 'retired')
    )
    total_products = total_result.scalar_one()

    # 2. Obtener locales únicos
    locales_result = await db.execute(
        select(distinct(ProductI18n.locale)).order_by(ProductI18n.locale)
    )
    locales = [row for row in locales_result.scalars().all()]

    # 3. Para cada locale, contar traducciones completas
    by_locale = {}
    for locale in locales:
        # Contar traducciones completas (solo verificamos que exista el title)
        # description_rich es opcional
        translated_result = await db.execute(
            select(func.count(ProductI18n.sku)).where(
                ProductI18n.locale == locale,
                ProductI18n.title.isnot(None),
                ProductI18n.title != ''
            )
        )
        translated = translated_result.scalar_one()
        pending = total_products - translated
        percentage = round((translated / total_products * 100), 1) if total_products > 0 else 0

        by_locale[locale] = {
            "total": total_products,
            "translated": translated,
            "pending": pending,
            "percentage": percentage
        }

    return {
        "by_locale": by_locale,
        "total_products": total_products,
        "locales": locales
    }
