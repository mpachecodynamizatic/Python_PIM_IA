from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.connectors.base import BaseConnector, ConnectorResult, ProductSyncDetail
from app.models.product import Product

logger = logging.getLogger(__name__)


class ShopifyConnector(BaseConnector):
    """Conector simulado para Shopify.

    En producción, se usaría la API REST/GraphQL de Shopify Admin.
    Requiere filters["shopify_store"] y filters["shopify_token"] para operar.
    En modo simulado exporta los productos como si se enviaran a la API.
    """

    channel = "shopify"

    async def run(self, db: AsyncSession, filters: dict) -> ConnectorResult:
        result = ConnectorResult()

        query = select(Product).options(selectinload(Product.translations))
        if filters.get("status"):
            query = query.where(Product.status == filters["status"])
        if filters.get("category_id"):
            query = query.where(Product.category_id == filters["category_id"])
        if filters.get("brand"):
            query = query.where(Product.brand == filters["brand"])

        rows = (await db.execute(query)).scalars().all()
        result.total_products = len(rows)

        for p in rows:
            try:
                titles: dict[str, str] = {}
                for t in p.translations:
                    titles[t.locale] = t.title

                _payload = {
                    "product": {
                        "title": titles.get("en", titles.get("es", p.sku)),
                        "body_html": "",
                        "vendor": p.brand,
                        "product_type": "",
                        "variants": [{"sku": p.sku}],
                        "tags": list(p.attributes.get("tags", [])) if isinstance(p.attributes.get("tags"), list) else [],
                    }
                }

                # Simulated API call — in production: POST /admin/api/2024-01/products.json
                logger.info("Shopify: simulated publish SKU %s", p.sku)
                result.exported += 1
                result.product_details.append(ProductSyncDetail(sku=p.sku, status="published"))

            except Exception as exc:
                err = f"{p.sku}: {exc}"
                result.skipped += 1
                result.errors.append(err)
                result.product_details.append(ProductSyncDetail(sku=p.sku, status="failed", error=str(exc)))

        return result
