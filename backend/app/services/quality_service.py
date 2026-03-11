"""
Data Quality service.

Computes quality scores on-the-fly from existing product data.
No separate model needed — avoids sync issues.

Dimensions (each 0.0 – 1.0):
  brand       → brand field is non-empty
  category    → category_id is set
  seo         → seo.title AND seo.description both present
  attributes  → at least one attribute key-value pair
  media       → at least one linked MediaAsset
  i18n        → at least one ProductI18n translation

Cuando hay un QualityRuleSet activo, se aplican pesos y umbrales
configurados por el negocio para recalcular el overall.
"""

import math
from typing import Sequence

from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from sqlalchemy import func

from app.models.product import Product
from app.models.quality_rule import QualityRule, QualityRuleSet

# ── Dimensiones base ────────────────────────────────────────────────────────

DIMENSION_KEYS = ("brand", "category", "seo", "attributes", "media", "i18n")


def _compute_dimensions(product: Product) -> dict[str, float]:
    scores: dict[str, float] = {}
    scores["brand"] = 1.0 if product.brand else 0.0
    scores["category"] = 1.0 if product.category_id else 0.0

    seo = product.seo or {}
    seo_filled = sum(1 for k in ("title", "description") if seo.get(k))
    scores["seo"] = seo_filled / 2

    scores["attributes"] = 1.0 if product.attributes else 0.0
    scores["media"] = 1.0 if product.media else 0.0
    scores["i18n"] = 1.0 if product.translations else 0.0
    return scores


def _apply_rules(
    dimensions: dict[str, float],
    rules: Sequence[QualityRule],
    product_status: str,
    product_category_id: str | None = None,
) -> dict:
    """Aplica las reglas del conjunto activo sobre las dimensiones base.

    - weight: peso relativo de la dimensión en el overall.
    - min_score: umbral mínimo; si el score base < min_score la dimensión
      se marca como "no cumple" (0.0 a efectos de overall ponderado).
    - required_status: la regla solo aplica si el producto tiene ese estado.
    - scope_category_id: la regla solo aplica si el producto pertenece a esa categoría.

    Si no hay reglas, se usa el cálculo por defecto (media aritmética).
    """
    if not rules:
        overall = sum(dimensions.values()) / len(dimensions) if dimensions else 0
        return {
            "dimensions": dimensions,
            "overall": round(overall * 100, 1),
            "rule_set": None,
        }

    weighted_sum = 0.0
    total_weight = 0.0
    violations: list[str] = []

    # Filtrar reglas aplicables por categoría y mapear por dimensión
    rule_map: dict[str, QualityRule] = {}
    for r in rules:
        if r.dimension not in DIMENSION_KEYS:
            continue
        # Si la regla tiene scope_category_id y no coincide, se ignora
        if r.scope_category_id and r.scope_category_id != product_category_id:
            continue
        # Si ya hay una regla para esta dimensión, la más específica (con scope) gana
        existing = rule_map.get(r.dimension)
        if existing is None or (r.scope_category_id and not existing.scope_category_id):
            rule_map[r.dimension] = r

    for dim in DIMENSION_KEYS:
        base_score = dimensions.get(dim, 0.0)
        rule = rule_map.get(dim)

        if rule is None:
            weighted_sum += base_score * 1.0
            total_weight += 1.0
            continue

        # Si la regla tiene required_status y el producto no coincide, se ignora
        if rule.required_status and product_status != rule.required_status:
            weighted_sum += base_score * 1.0
            total_weight += 1.0
            continue

        # Aplicar umbral mínimo
        effective_score = base_score
        if base_score < rule.min_score:
            effective_score = 0.0
            violations.append(dim)

        weighted_sum += effective_score * rule.weight
        total_weight += rule.weight

    overall = (weighted_sum / total_weight * 100) if total_weight > 0 else 0
    result: dict = {
        "dimensions": dimensions,
        "overall": round(overall, 1),
    }
    if violations:
        result["violations"] = violations
    return result


# ── Helpers ──────────────────────────────────────────────────────────────────

async def _get_active_rules(db: AsyncSession) -> tuple[QualityRuleSet | None, Sequence[QualityRule]]:
    """Devuelve el conjunto activo y sus reglas, o (None, []) si no hay."""
    rs_result = await db.execute(
        select(QualityRuleSet)
        .options(selectinload(QualityRuleSet.rules))
        .where(QualityRuleSet.active.is_(True))
    )
    rule_set = rs_result.scalar_one_or_none()
    if rule_set is None:
        return None, []
    return rule_set, rule_set.rules


def _build_quality(product: Product, rule_set: QualityRuleSet | None, rules: Sequence[QualityRule]) -> dict:
    dimensions = _compute_dimensions(product)
    result = _apply_rules(dimensions, rules, product.status, product.category_id)
    if rule_set:
        result["rule_set"] = {"id": rule_set.id, "name": rule_set.name}
    return result


# ── API pública ──────────────────────────────────────────────────────────────

async def get_product_quality(db: AsyncSession, sku: str) -> dict:
    result = await db.execute(
        select(Product)
        .options(selectinload(Product.translations), selectinload(Product.media))
        .where(Product.sku == sku)
    )
    product = result.scalar_one_or_none()
    if product is None:
        raise HTTPException(status_code=404, detail="Product not found")

    rule_set, rules = await _get_active_rules(db)
    return {"sku": sku, **_build_quality(product, rule_set, rules)}


async def get_quality_report(
    db: AsyncSession,
    page: int = 1,
    size: int = 20,
) -> dict:
    count = (await db.execute(select(func.count()).select_from(Product))).scalar() or 0

    result = await db.execute(
        select(Product)
        .options(selectinload(Product.translations), selectinload(Product.media))
        .order_by(Product.updated_at.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
    products = result.scalars().all()

    rule_set, rules = await _get_active_rules(db)
    items = [
        {"sku": p.sku, "status": p.status, **_build_quality(p, rule_set, rules)}
        for p in products
    ]

    return {
        "items": items,
        "total": count,
        "page": page,
        "size": size,
        "pages": math.ceil(count / size) if size > 0 else 0,
        "active_rule_set": {"id": rule_set.id, "name": rule_set.name} if rule_set else None,
    }


async def simulate_rule_set(
    db: AsyncSession,
    rule_set_id: str,
    page: int = 1,
    size: int = 20,
) -> dict:
    """Simula cómo quedarían los scores si se activara un conjunto de reglas distinto."""
    rs_result = await db.execute(
        select(QualityRuleSet)
        .options(selectinload(QualityRuleSet.rules))
        .where(QualityRuleSet.id == rule_set_id)
    )
    rule_set = rs_result.scalar_one_or_none()
    if rule_set is None:
        raise HTTPException(status_code=404, detail="Rule set not found")

    count = (await db.execute(select(func.count()).select_from(Product))).scalar() or 0
    result = await db.execute(
        select(Product)
        .options(selectinload(Product.translations), selectinload(Product.media))
        .order_by(Product.updated_at.desc())
        .offset((page - 1) * size)
        .limit(size)
    )
    products = result.scalars().all()

    # Calcular con las reglas activas actuales (para comparar)
    active_set, active_rules = await _get_active_rules(db)

    items = []
    for p in products:
        current = _build_quality(p, active_set, active_rules)
        simulated = _build_quality(p, rule_set, rule_set.rules)
        items.append({
            "sku": p.sku,
            "status": p.status,
            "current_overall": current["overall"],
            "simulated_overall": simulated["overall"],
            "diff": round(simulated["overall"] - current["overall"], 1),
            "simulated_violations": simulated.get("violations", []),
            "dimensions": simulated["dimensions"],
        })

    return {
        "rule_set": {"id": rule_set.id, "name": rule_set.name},
        "compared_to": {"id": active_set.id, "name": active_set.name} if active_set else None,
        "items": items,
        "total": count,
        "page": page,
        "size": size,
        "pages": math.ceil(count / size) if size > 0 else 0,
    }
