import math
from datetime import datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy import func, select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

import json

from app.models.audit import AuditLog
from app.models.attribute_family import AttributeFamily, AttributeDefinition
from app.models.product import Product, ProductI18n
from app.schemas.common import PaginatedResponse
from app.schemas.product import (
    ProductCreate,
    ProductI18nUpsert,
    ProductListItem,
    ProductRead,
    ProductUpdate,
    TransitionRequest,
    ProductVersionRead,
    RetentionPolicy,
    RetentionResult,
)

VALID_TRANSITIONS = {
    # Workflow de aprobación
    "draft": ["in_review", "ready"],  # se permite salto directo a ready para compatibilidad
    "in_review": ["approved", "draft"],
    "approved": ["ready", "in_review", "draft"],
    # Estados existentes
    "ready": ["draft", "retired"],
    "retired": ["draft"],
}


async def _validate_attributes(
    db: AsyncSession,
    attributes: dict,
    family_id: str | None,
    category_id: str | None,
) -> None:
    """Valida los atributos del producto contra las definiciones de la familia.

    Estrategia: si family_id está presente, usa esa familia. Si no, busca una
    familia asociada a la categoría. Si no hay familia, no valida (JSON libre).
    """
    if not family_id and category_id:
        result = await db.execute(
            select(AttributeFamily).where(AttributeFamily.category_id == category_id).limit(1)
        )
        family = result.scalar_one_or_none()
        if family:
            family_id = family.id

    if not family_id:
        return  # Sin familia, no hay validación

    result = await db.execute(
        select(AttributeDefinition).where(AttributeDefinition.family_id == family_id)
    )
    definitions = list(result.scalars().all())
    if not definitions:
        return

    errors: list[str] = []
    for defn in definitions:
        value = attributes.get(defn.code)

        # Requeridos
        if defn.required and (value is None or value == ""):
            errors.append(f"Atributo '{defn.code}' ({defn.label}) es obligatorio")
            continue

        if value is None:
            continue  # Opcional y no presente

        # Validación de tipos
        if defn.type == "string" and not isinstance(value, str):
            errors.append(f"Atributo '{defn.code}' debe ser texto")
        elif defn.type == "number" and not isinstance(value, (int, float)):
            errors.append(f"Atributo '{defn.code}' debe ser numerico")
        elif defn.type == "boolean" and not isinstance(value, bool):
            errors.append(f"Atributo '{defn.code}' debe ser booleano")
        elif defn.type == "enum":
            options: list[str] = []
            if defn.options_json:
                try:
                    options = json.loads(defn.options_json)
                except (json.JSONDecodeError, TypeError):
                    pass
            if options and value not in options:
                errors.append(
                    f"Atributo '{defn.code}' debe ser uno de: {', '.join(str(o) for o in options)}"
                )

    if errors:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=errors,
        )


async def list_products(
    db: AsyncSession,
    page: int = 1,
    size: int = 20,
    status_filter: str | None = None,
    brand: str | None = None,
    category_id: str | None = None,
    q: str | None = None,
    created_from: str | None = None,
    created_to: str | None = None,
    updated_from: str | None = None,
    updated_to: str | None = None,
    has_media: bool | None = None,
    has_i18n: bool | None = None,
) -> PaginatedResponse[ProductListItem]:
    from app.models.product import ProductI18n
    from app.models.media import MediaAsset

    query = select(Product)

    if status_filter:
        query = query.where(Product.status == status_filter)
    if brand:
        query = query.where(Product.brand.ilike(f"%{brand}%"))
    if category_id:
        query = query.where(Product.category_id == category_id)
    if q:
        query = query.where(
            Product.sku.ilike(f"%{q}%") | Product.brand.ilike(f"%{q}%")
        )

    # Date range filters
    if created_from:
        query = query.where(Product.created_at >= datetime.fromisoformat(created_from))
    if created_to:
        query = query.where(Product.created_at <= datetime.fromisoformat(created_to))
    if updated_from:
        query = query.where(Product.updated_at >= datetime.fromisoformat(updated_from))
    if updated_to:
        query = query.where(Product.updated_at <= datetime.fromisoformat(updated_to))

    # Existence filters (has media / has translations)
    if has_media is True:
        query = query.where(Product.sku.in_(select(MediaAsset.sku).distinct()))
    elif has_media is False:
        query = query.where(~Product.sku.in_(select(MediaAsset.sku).distinct()))
    if has_i18n is True:
        query = query.where(Product.sku.in_(select(ProductI18n.sku).distinct()))
    elif has_i18n is False:
        query = query.where(~Product.sku.in_(select(ProductI18n.sku).distinct()))

    count_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_query)).scalar() or 0

    query = query.order_by(Product.updated_at.desc()).offset((page - 1) * size).limit(size)
    result = await db.execute(query)
    items = [ProductListItem.model_validate(p) for p in result.scalars().all()]

    return PaginatedResponse(
        items=items,
        total=total,
        page=page,
        size=size,
        pages=math.ceil(total / size) if size > 0 else 0,
    )


async def get_product(db: AsyncSession, sku: str) -> Product:
    result = await db.execute(
        select(Product)
        .options(selectinload(Product.translations))
        .where(Product.sku == sku)
    )
    product = result.scalar_one_or_none()
    if product is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Product not found")
    return product


async def create_product(db: AsyncSession, data: ProductCreate, actor: str) -> Product:
    existing = await db.execute(select(Product).where(Product.sku == data.sku))
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Product with SKU '{data.sku}' already exists",
        )
    await _validate_attributes(db, data.attributes, data.family_id, data.category_id)
    product = Product(**data.model_dump())
    product.translations = []  # Initialize to avoid lazy-load outside greenlet
    db.add(product)

    audit = AuditLog(
        resource="product",
        resource_id=data.sku,
        actor=actor,
        action="create",
        before=None,
        after=data.model_dump(mode="json"),
    )
    db.add(audit)
    await db.flush()
    return product


async def update_product(db: AsyncSession, sku: str, data: ProductUpdate, actor: str) -> Product:
    product = await get_product(db, sku)
    before = ProductRead.model_validate(product).model_dump(mode="json")

    update_data = data.model_dump(exclude_unset=True)
    # Validar atributos si se actualizan
    attrs = update_data.get("attributes", product.attributes)
    fam_id = update_data.get("family_id", product.family_id)
    cat_id = update_data.get("category_id", product.category_id)
    if "attributes" in update_data or "family_id" in update_data:
        await _validate_attributes(db, attrs, fam_id, cat_id)

    for field, value in update_data.items():
        setattr(product, field, value)

    after = ProductRead.model_validate(product).model_dump(mode="json")
    audit = AuditLog(
        resource="product",
        resource_id=sku,
        actor=actor,
        action="update",
        before=before,
        after=after,
    )
    db.add(audit)
    await db.flush()
    await db.refresh(product)
    return product


async def transition_product(
    db: AsyncSession, sku: str, data: TransitionRequest, actor: str
) -> Product:
    product = await get_product(db, sku)
    allowed = VALID_TRANSITIONS.get(product.status, [])
    if data.new_status not in allowed:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail=f"Cannot transition from '{product.status}' to '{data.new_status}'. Allowed: {allowed}",
        )
    old_status = product.status
    product.status = data.new_status

    audit = AuditLog(
        resource="product",
        resource_id=sku,
        actor=actor,
        action="transition",
        before={"status": old_status},
        after={"status": data.new_status, "reason": data.reason},
    )
    db.add(audit)
    await db.flush()
    await db.refresh(product)
    return product


async def upsert_i18n(
    db: AsyncSession, sku: str, data: ProductI18nUpsert, actor: str
) -> ProductI18n:
    await get_product(db, sku)
    result = await db.execute(
        select(ProductI18n).where(ProductI18n.sku == sku, ProductI18n.locale == data.locale)
    )
    existing = result.scalar_one_or_none()

    if existing:
        existing.title = data.title
        existing.description_rich = data.description_rich
        i18n = existing
    else:
        i18n = ProductI18n(sku=sku, **data.model_dump())
        db.add(i18n)

    audit = AuditLog(
        resource="product_i18n",
        resource_id=f"{sku}:{data.locale}",
        actor=actor,
        action="upsert",
        after=data.model_dump(mode="json"),
    )
    db.add(audit)
    await db.flush()
    return i18n


async def get_audit_log(db: AsyncSession, sku: str) -> list[AuditLog]:
    result = await db.execute(
        select(AuditLog)
        .where(AuditLog.resource_id == sku)
        .order_by(AuditLog.created_at.desc())
    )
    return list(result.scalars().all())


async def get_product_versions(
    db: AsyncSession,
    sku: str,
    action_filter: str | None = None,
) -> list[ProductVersionRead]:
    """Construye una vista de versiones de producto basada en AuditLog.

    Args:
        action_filter: filtrar por tipo de acción (create, update, transition, restore).
                       Se aceptan múltiples valores separados por coma.
    """
    query = select(AuditLog).where(
        AuditLog.resource == "product",
        AuditLog.resource_id == sku,
    )

    if action_filter:
        actions = [a.strip() for a in action_filter.split(",") if a.strip()]
        if actions:
            query = query.where(AuditLog.action.in_(actions))

    result = await db.execute(query.order_by(AuditLog.created_at.asc()))
    logs = list(result.scalars().all())

    versions: list[ProductVersionRead] = []
    for log in logs:
        if log.action in ("create", "update", "transition"):
            snapshot = log.after or {}
        else:
            snapshot = log.after or log.before or {}

        versions.append(
            ProductVersionRead(
                id=str(log.id),
                sku=sku,
                actor=log.actor,
                action=log.action,
                created_at=log.created_at,
                snapshot=snapshot,
            )
        )

    return versions


async def restore_product_version(
    db: AsyncSession,
    sku: str,
    version_id: str,
    actor: str,
) -> Product:
    """Restaura parcialmente un producto a una versión anterior.

    Solo se restauran campos de contenido (brand, category_id, seo, attributes),
    manteniendo el estado gestionado por las reglas de transición.
    """
    # Localizar la entrada de auditoría que representa la versión
    result = await db.execute(
        select(AuditLog).where(
            AuditLog.id == version_id,
            AuditLog.resource == "product",
            AuditLog.resource_id == sku,
        )
    )
    log = result.scalar_one_or_none()
    if log is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Version not found")

    snapshot = log.after or log.before
    if not snapshot:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Selected version does not contain product data to restore",
        )

    product = await get_product(db, sku)
    before = ProductRead.model_validate(product).model_dump(mode="json")

    # Campos que se permiten restaurar desde la versión
    restorable_fields = {"brand", "category_id", "family_id", "seo", "attributes"}
    for field in restorable_fields:
        if field in snapshot:
            setattr(product, field, snapshot[field])

    after = ProductRead.model_validate(product).model_dump(mode="json")

    audit = AuditLog(
        resource="product",
        resource_id=sku,
        actor=actor,
        action="restore",
        before=before,
        after=after,
    )
    db.add(audit)
    await db.flush()
    await db.refresh(product)
    return product


async def apply_retention_policy(
    db: AsyncSession,
    sku: str,
    policy: RetentionPolicy,
) -> RetentionResult:
    """Aplica una política de retención eliminando versiones antiguas o excedentes.

    Nunca elimina la versión más reciente (siempre se conserva).
    """
    result = await db.execute(
        select(AuditLog)
        .where(AuditLog.resource == "product", AuditLog.resource_id == sku)
        .order_by(AuditLog.created_at.asc())
    )
    logs = list(result.scalars().all())

    if len(logs) <= 1:
        return RetentionResult(deleted=0, remaining=len(logs))

    # Siempre preservar el último registro
    candidates = logs[:-1]
    ids_to_delete: set[str] = set()

    # Eliminar por antigüedad
    if policy.max_age_days is not None:
        cutoff = datetime.utcnow() - timedelta(days=policy.max_age_days)
        for log in candidates:
            if log.created_at < cutoff:
                ids_to_delete.add(log.id)

    # Eliminar por cantidad máxima (mantener las N más recientes)
    if policy.max_versions is not None and len(logs) > policy.max_versions:
        excess = len(logs) - policy.max_versions
        for log in candidates[:excess]:
            ids_to_delete.add(log.id)

    if ids_to_delete:
        await db.execute(
            delete(AuditLog).where(AuditLog.id.in_(ids_to_delete))
        )
        await db.flush()

    remaining = len(logs) - len(ids_to_delete)
    return RetentionResult(deleted=len(ids_to_delete), remaining=remaining)
