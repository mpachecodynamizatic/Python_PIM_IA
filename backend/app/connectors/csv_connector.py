from __future__ import annotations

import csv
import io
from datetime import datetime, timezone
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.connectors.base import BaseConnector, ConnectorResult
from app.models.product import Product

EXPORT_DIR = Path("exports")


class CsvConnector(BaseConnector):
    """Exporta productos a un fichero CSV en disco (directorio exports/)."""

    channel = "csv"

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

        if not rows:
            return result

        EXPORT_DIR.mkdir(exist_ok=True)
        ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        filepath = EXPORT_DIR / f"products_{ts}.csv"

        buf = io.StringIO()
        writer = csv.writer(buf)
        writer.writerow(["sku", "brand", "status", "category_id", "attributes", "seo", "title_es", "title_en"])

        for p in rows:
            titles: dict[str, str] = {}
            for t in p.translations:
                titles[t.locale] = t.title
            writer.writerow([
                p.sku,
                p.brand,
                p.status,
                p.category_id,
                str(p.attributes),
                str(p.seo),
                titles.get("es", ""),
                titles.get("en", ""),
            ])
            result.exported += 1

        filepath.write_text(buf.getvalue(), encoding="utf-8")
        return result
