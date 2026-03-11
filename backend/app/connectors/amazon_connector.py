from __future__ import annotations

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.connectors.base import BaseConnector, ConnectorResult, ProductSyncDetail
from app.models.product import Product

logger = logging.getLogger(__name__)


class AmazonConnector(BaseConnector):
    """Conector simulado para Amazon SP-API.

    En producción, se usaría la Selling Partner API (SP-API) de Amazon.
    Requiere filters["amazon_marketplace_id"] y credenciales SP-API.
    En modo simulado, genera el feed XML y contabiliza los productos.
    """

    channel = "amazon"

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

                _feed_item = {
                    "MessageType": "Product",
                    "Message": {
                        "SKU": p.sku,
                        "Title": titles.get("en", titles.get("es", p.sku)),
                        "Brand": p.brand,
                        "Description": "",
                        "BulletPoint": [],
                    },
                }

                # Simulated — in production: POST feed via SP-API
                logger.info("Amazon: simulated feed for SKU %s", p.sku)
                result.exported += 1
                result.product_details.append(ProductSyncDetail(sku=p.sku, status="published"))

            except Exception as exc:
                err = f"{p.sku}: {exc}"
                result.skipped += 1
                result.errors.append(err)
                result.product_details.append(ProductSyncDetail(sku=p.sku, status="failed", error=str(exc)))

        return result
