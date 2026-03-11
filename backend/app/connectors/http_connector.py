from __future__ import annotations

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.connectors.base import BaseConnector, ConnectorResult, ProductSyncDetail
from app.models.product import Product


class HttpConnector(BaseConnector):
    """Envía productos como JSON a un endpoint HTTP configurable.

    La URL destino se indica en filters["endpoint_url"].
    Si no se especifica, usa un endpoint de prueba (httpbin).
    """

    channel = "http"

    async def run(self, db: AsyncSession, filters: dict) -> ConnectorResult:
        result = ConnectorResult()
        endpoint = filters.get("endpoint_url", "https://httpbin.org/post")

        query = select(Product)
        if filters.get("status"):
            query = query.where(Product.status == filters["status"])
        if filters.get("category_id"):
            query = query.where(Product.category_id == filters["category_id"])
        if filters.get("brand"):
            query = query.where(Product.brand == filters["brand"])

        rows = (await db.execute(query)).scalars().all()
        result.total_products = len(rows)

        async with httpx.AsyncClient(timeout=30) as client:
            for p in rows:
                payload = {
                    "sku": p.sku,
                    "brand": p.brand,
                    "status": p.status,
                    "category_id": p.category_id,
                    "attributes": p.attributes,
                    "seo": p.seo,
                }
                try:
                    resp = await client.post(endpoint, json=payload)
                    if resp.status_code < 400:
                        result.exported += 1
                        result.product_details.append(ProductSyncDetail(sku=p.sku, status="published"))
                    else:
                        result.skipped += 1
                        err = f"{p.sku}: HTTP {resp.status_code}"
                        result.errors.append(err)
                        result.product_details.append(ProductSyncDetail(sku=p.sku, status="failed", error=err))
                except httpx.HTTPError as exc:
                    result.skipped += 1
                    err = f"{p.sku}: {exc}"
                    result.errors.append(err)
                    result.product_details.append(ProductSyncDetail(sku=p.sku, status="failed", error=str(exc)))

        return result
