from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.connectors.base import BaseConnector, ConnectorResult, ProductSyncDetail
from app.models.product import Product

logger = logging.getLogger(__name__)


class WooCommerceConnector(BaseConnector):
    """Conector simulado para WooCommerce REST API.

    En producción, se usaría la REST API v3 de WooCommerce.
    Requiere filters["woo_url"], filters["woo_key"], filters["woo_secret"].
    En modo simulado, genera el payload y contabiliza los productos.
    """

    channel = "woocommerce"

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
                    "name": titles.get("es", titles.get("en", p.sku)),
                    "type": "simple",
                    "sku": p.sku,
                    "status": "publish" if p.status == "ready" else "draft",
                    "categories": [],
                    "attributes": [
                        {"name": k, "options": [str(v)]}
                        for k, v in (p.attributes or {}).items()
                    ],
                }

                # Simulated — in production: POST /wp-json/wc/v3/products
                logger.info("WooCommerce: simulated publish SKU %s", p.sku)
                result.exported += 1
                result.product_details.append(ProductSyncDetail(sku=p.sku, status="published"))

            except Exception as exc:
                err = f"{p.sku}: {exc}"
                result.skipped += 1
                result.errors.append(err)
                result.product_details.append(ProductSyncDetail(sku=p.sku, status="failed", error=str(exc)))

        return result
