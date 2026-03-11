from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import get_current_user, require_scopes, require_roles
from app.models.user import User
from app.schemas.common import PaginatedResponse
from app.schemas.product import (
    ProductCreate,
    ProductI18nRead,
    ProductI18nUpsert,
    ProductListItem,
    ProductRead,
    ProductUpdate,
    TransitionRequest,
    ProductVersionRead,
    WorkflowActionRequest,
    RetentionPolicy,
    RetentionResult,
)
from app.schemas.product_comment import ProductCommentCreate, ProductCommentRead
from app.services import product_service
from app.services import product_comment_service

router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=PaginatedResponse[ProductListItem])
async def list_products(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    status: str | None = None,
    brand: str | None = None,
    category_id: str | None = None,
    q: str | None = None,
    created_from: str | None = Query(None, description="Fecha minima de creacion (ISO 8601)"),
    created_to: str | None = Query(None, description="Fecha maxima de creacion (ISO 8601)"),
    updated_from: str | None = Query(None, description="Fecha minima de actualizacion (ISO 8601)"),
    updated_to: str | None = Query(None, description="Fecha maxima de actualizacion (ISO 8601)"),
    has_media: bool | None = Query(None, description="Solo productos con/sin media"),
    has_i18n: bool | None = Query(None, description="Solo productos con/sin traducciones"),
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    return await product_service.list_products(
        db,
        page=page,
        size=size,
        status_filter=status,
        brand=brand,
        category_id=category_id,
        q=q,
        created_from=created_from,
        created_to=created_to,
        updated_from=updated_from,
        updated_to=updated_to,
        has_media=has_media,
        has_i18n=has_i18n,
    )


@router.post("", response_model=ProductRead, status_code=201)
async def create_product(
    body: ProductCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_scopes("products:write")),
):
    return await product_service.create_product(db, body, actor=str(user.id))


@router.get("/{sku}", response_model=ProductRead)
async def get_product(
    sku: str,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    return await product_service.get_product(db, sku)


@router.patch("/{sku}", response_model=ProductRead)
async def update_product(
    sku: str,
    body: ProductUpdate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_scopes("products:write")),
):
    return await product_service.update_product(db, sku, body, actor=str(user.id))


@router.post("/{sku}/transitions", response_model=ProductRead)
async def transition_product(
    sku: str,
    body: TransitionRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_scopes("products:write")),
):
    return await product_service.transition_product(db, sku, body, actor=str(user.id))


@router.post("/{sku}/workflow/submit", response_model=ProductRead)
async def submit_for_review(
    sku: str,
    body: WorkflowActionRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_scopes("products:write")),
):
    """Pasa el producto de draft a in_review (envío a revisión)."""
    transition = TransitionRequest(new_status="in_review", reason=body.reason)
    return await product_service.transition_product(db, sku, transition, actor=str(user.id))


@router.post("/{sku}/workflow/approve", response_model=ProductRead)
async def approve_product(
    sku: str,
    body: WorkflowActionRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles("admin")),
):
    """Aprueba un producto en revisión (in_review → approved)."""
    transition = TransitionRequest(new_status="approved", reason=body.reason)
    return await product_service.transition_product(db, sku, transition, actor=str(user.id))


@router.post("/{sku}/workflow/reject", response_model=ProductRead)
async def reject_product(
    sku: str,
    body: WorkflowActionRequest,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles("admin")),
):
    """Rechaza un producto en revisión (in_review → draft)."""
    transition = TransitionRequest(new_status="draft", reason=body.reason)
    return await product_service.transition_product(db, sku, transition, actor=str(user.id))


@router.post("/{sku}/i18n/{locale}", response_model=ProductI18nRead)
async def upsert_i18n(
    sku: str,
    locale: str,
    body: ProductI18nUpsert,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_scopes("products:write")),
):
    body.locale = locale
    return await product_service.upsert_i18n(db, sku, body, actor=str(user.id))


@router.get("/{sku}/audit")
async def get_audit(
    sku: str,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    logs = await product_service.get_audit_log(db, sku)
    return [
        {
            "id": str(log.id),
            "resource": log.resource,
            "resource_id": log.resource_id,
            "actor": log.actor,
            "action": log.action,
            "before": log.before,
            "after": log.after,
            "created_at": log.created_at.isoformat() if log.created_at else None,
        }
        for log in logs
    ]


@router.get("/{sku}/versions", response_model=list[ProductVersionRead])
async def get_versions(
    sku: str,
    action: str | None = Query(None, description="Filtrar por tipo de acción (create,update,transition,restore). Separar múltiples con coma."),
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    """Devuelve el historial de versiones del producto basado en AuditLog."""
    return await product_service.get_product_versions(db, sku, action_filter=action)


@router.get("/{sku}/comments", response_model=list[ProductCommentRead])
async def list_product_comments(
    sku: str,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    """Lista comentarios del producto."""
    return await product_comment_service.list_comments(db, sku)


@router.post("/{sku}/comments", response_model=ProductCommentRead, status_code=201)
async def create_product_comment(
    sku: str,
    body: ProductCommentCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Añade un comentario al producto."""
    comment = await product_comment_service.create_comment(db, sku, str(user.id), body)
    await db.commit()
    return comment


@router.delete("/{sku}/comments/{comment_id}", status_code=204)
async def delete_product_comment(
    sku: str,
    comment_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Elimina un comentario (solo autor o admin)."""
    await product_comment_service.delete_comment(
        db, sku, comment_id, str(user.id), is_admin=(user.role == "admin")
    )
    await db.commit()


@router.post("/{sku}/versions/{version_id}/restore", response_model=ProductRead)
async def restore_version(
    sku: str,
    version_id: str,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_scopes("products:write")),
):
    """Restaura un producto a una versión anterior (parcialmente, sin tocar el status)."""
    product = await product_service.restore_product_version(db, sku, version_id, actor=str(user.id))
    await db.commit()
    return product


@router.post("/{sku}/versions/retention", response_model=RetentionResult)
async def apply_retention(
    sku: str,
    body: RetentionPolicy,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_roles("admin")),
):
    """Aplica una política de retención al historial de versiones (solo admin)."""
    result = await product_service.apply_retention_policy(db, sku, body)
    await db.commit()
    return result


@router.get("/{sku}/versions/{version_id}/comments", response_model=list[ProductCommentRead])
async def list_version_comments(
    sku: str,
    version_id: str,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(get_current_user),
):
    """Lista comentarios asociados a una versión específica."""
    return await product_comment_service.list_comments(db, sku, version_id=version_id)


@router.post("/{sku}/versions/{version_id}/comments", response_model=ProductCommentRead, status_code=201)
async def create_version_comment(
    sku: str,
    version_id: str,
    body: ProductCommentCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(get_current_user),
):
    """Añade un comentario asociado a una versión específica."""
    comment = await product_comment_service.create_comment(db, sku, str(user.id), body, version_id=version_id)
    await db.commit()
    return comment
