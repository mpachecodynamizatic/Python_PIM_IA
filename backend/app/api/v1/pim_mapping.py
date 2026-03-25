"""API endpoints para configuración de mapeo de campos PIM."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.dependencies import require_roles
from app.models.user import User
from app.models.pim_field_mapping import PimResourceMapping
from app.schemas.pim_mapping import (
    PimResourceMappingCreate,
    PimResourceMappingRead,
    PimResourceMappingUpdate,
    ExternalPimFieldSchema,
    ResourceFieldSchema,
)
from app.services import pim_mapping_service

router = APIRouter(prefix="/pim-mappings", tags=["pim-mapping"])


@router.get("/resources", response_model=list[str])
async def list_available_resources(
    _user: User = Depends(require_roles("admin")),
):
    """
    Lista todos los recursos que pueden ser mapeados.

    Retorna lista de identificadores de recursos como "products", "categories", "brands", etc.
    Solo admin puede acceder a esta funcionalidad.
    """
    return [
        "products",
        "categories",
        "brands",
        "suppliers",
        "channels",
        "product_i18n",
        "media_assets",
        "product_logistics",
        "product_compliance",
        "product_channels",
        "product_suppliers",
        "external_taxonomies",
        "product_external_taxonomies",
        "attribute_families",
        "attribute_definitions",
    ]


@router.get("/resources/{resource}/external-fields", response_model=list[ExternalPimFieldSchema])
async def introspect_external_pim_fields(
    resource: str,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_roles("admin")),
):
    """
    Introspecciona la API del PIM externo para descubrir campos disponibles.

    Se conecta al PIM externo, obtiene un item de ejemplo y analiza su estructura
    para identificar todos los campos disponibles con sus tipos y valores de muestra.

    Args:
        resource: Tipo de recurso a introspeccionar (products, categories, etc.)

    Returns:
        Lista de campos externos con metadata
    """
    try:
        return await pim_mapping_service.introspect_external_fields(resource, db)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.get("/resources/{resource}/internal-fields", response_model=list[ResourceFieldSchema])
async def get_internal_model_fields(
    resource: str,
    _user: User = Depends(require_roles("admin")),
):
    """
    Obtiene metadata de los campos del modelo interno.

    Retorna información sobre los campos del modelo interno incluyendo tipo,
    si es requerido, restricciones FK, opciones de enum, etc.

    Args:
        resource: Tipo de recurso (products, categories, etc.)

    Returns:
        Lista de campos internos con metadata
    """
    try:
        return await pim_mapping_service.get_internal_fields_metadata(resource)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


@router.get("", response_model=list[PimResourceMappingRead])
async def list_all_mappings(
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_roles("admin")),
):
    """
    Lista todas las configuraciones de mapeo existentes.

    Returns:
        Lista de todas las configuraciones de mapeo ordenadas por recurso
    """
    result = await db.execute(
        select(PimResourceMapping).order_by(PimResourceMapping.resource)
    )
    return result.scalars().all()


@router.get("/{resource}", response_model=PimResourceMappingRead | None)
async def get_mapping_by_resource(
    resource: str,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_roles("admin")),
):
    """
    Obtiene la configuración de mapeo para un recurso específico.

    Args:
        resource: Tipo de recurso (products, categories, etc.)

    Returns:
        Configuración de mapeo o None si no existe
    """
    result = await db.execute(
        select(PimResourceMapping).where(PimResourceMapping.resource == resource)
    )
    return result.scalar_one_or_none()


@router.post("", response_model=PimResourceMappingRead, status_code=201)
async def create_mapping(
    body: PimResourceMappingCreate,
    db: AsyncSession = Depends(get_db),
    user: User = Depends(require_roles("admin")),
):
    """
    Crea una nueva configuración de mapeo para un recurso.

    Args:
        body: Datos de la configuración de mapeo

    Returns:
        Configuración de mapeo creada

    Raises:
        409: Si ya existe una configuración para este recurso
    """
    # Verificar si ya existe
    existing = await db.execute(
        select(PimResourceMapping).where(PimResourceMapping.resource == body.resource)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(409, f"Ya existe una configuración de mapeo para el recurso '{body.resource}'")

    # Crear nueva configuración
    mapping = PimResourceMapping(
        resource=body.resource,
        is_active=body.is_active,
        mappings=[m.model_dump() for m in body.mappings],
        defaults=body.defaults,
        transform_config=body.transform_config,
        created_by=str(user.id),
        notes=body.notes,
    )
    db.add(mapping)
    await db.flush()
    await db.commit()
    await db.refresh(mapping)
    return mapping


@router.patch("/{resource}", response_model=PimResourceMappingRead)
async def update_mapping(
    resource: str,
    body: PimResourceMappingUpdate,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_roles("admin")),
):
    """
    Actualiza una configuración de mapeo existente.

    Args:
        resource: Tipo de recurso
        body: Datos actualizados (solo los campos proporcionados serán actualizados)

    Returns:
        Configuración de mapeo actualizada

    Raises:
        404: Si no existe configuración para este recurso
    """
    result = await db.execute(
        select(PimResourceMapping).where(PimResourceMapping.resource == resource)
    )
    mapping = result.scalar_one_or_none()
    if not mapping:
        raise HTTPException(404, f"No se encontró configuración de mapeo para el recurso '{resource}'")

    # Actualizar campos proporcionados
    if body.is_active is not None:
        mapping.is_active = body.is_active
    if body.mappings is not None:
        mapping.mappings = [m.model_dump() for m in body.mappings]
    if body.defaults is not None:
        mapping.defaults = body.defaults
    if body.transform_config is not None:
        mapping.transform_config = body.transform_config
    if body.notes is not None:
        mapping.notes = body.notes

    await db.commit()
    await db.refresh(mapping)
    return mapping


@router.delete("/{resource}", status_code=204)
async def delete_mapping(
    resource: str,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_roles("admin")),
):
    """
    Elimina una configuración de mapeo.

    Args:
        resource: Tipo de recurso

    Raises:
        404: Si no existe configuración para este recurso
    """
    result = await db.execute(
        select(PimResourceMapping).where(PimResourceMapping.resource == resource)
    )
    mapping = result.scalar_one_or_none()
    if not mapping:
        raise HTTPException(404, f"No se encontró configuración de mapeo para el recurso '{resource}'")

    await db.delete(mapping)
    await db.commit()


@router.post("/{resource}/import")
async def import_resource(
    resource: str,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_roles("admin")),
):
    """
    Importa un recurso específico desde el PIM externo usando su mapeo configurado.

    Args:
        resource: Tipo de recurso (products, brands, categories, etc.)

    Returns:
        Estadísticas de importación (created, updated, skipped, errors)

    Raises:
        400: Si no hay mapeo activo o hay error de conexión
        404: Si el recurso no es soportado
    """
    try:
        counts = await pim_mapping_service.import_resource_from_external_pim(db, resource)
        return {
            "message": f"Importación de '{resource}' completada",
            "stats": counts
        }
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, f"Error inesperado durante la importación: {str(e)}")
