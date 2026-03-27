"""API endpoints para configuración de mapeo de campos desde MySQL."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
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
    MySQLTableInfo,
    MySQLColumnInfo,
    MySQLConnectionStatus,
    ProposeMappingRequest,
)
from app.services import pim_mapping_service, mysql_service

router = APIRouter(prefix="/pim-mappings", tags=["pim-mapping"])


# ── Recursos internos disponibles ──────────────────────────────────────────────

@router.get("/resources", response_model=list[str])
async def list_available_resources(
    _user: User = Depends(require_roles("admin")),
):
    """Lista todos los recursos internos que pueden ser mapeados desde MySQL."""
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


@router.get("/resources/{resource}/internal-fields", response_model=list[ResourceFieldSchema])
async def get_internal_model_fields(
    resource: str,
    _user: User = Depends(require_roles("admin")),
):
    """Obtiene metadata de los campos del modelo interno para un recurso."""
    try:
        return await pim_mapping_service.get_internal_fields_metadata(resource)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))


# ── Endpoints MySQL ────────────────────────────────────────────────────────────

@router.get("/mysql/status", response_model=MySQLConnectionStatus)
async def test_mysql_connection(
    _user: User = Depends(require_roles("admin")),
):
    """
    Comprueba la conexión a la base de datos MySQL configurada en el servidor.
    Usa las variables MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE del .env.
    """
    result = await mysql_service.test_connection(
        settings.MYSQL_HOST, settings.MYSQL_PORT,
        settings.MYSQL_USER, settings.MYSQL_PASSWORD,
        settings.MYSQL_DATABASE,
    )
    return MySQLConnectionStatus(**result)


@router.get("/mysql/tables", response_model=list[MySQLTableInfo])
async def list_mysql_tables(
    _user: User = Depends(require_roles("admin")),
):
    """Lista todas las tablas de la base de datos MySQL configurada en el servidor."""
    try:
        tables = await mysql_service.list_tables(
            settings.MYSQL_HOST, settings.MYSQL_PORT,
            settings.MYSQL_USER, settings.MYSQL_PASSWORD,
            settings.MYSQL_DATABASE,
        )
        return [MySQLTableInfo(**t) for t in tables]
    except Exception as e:
        raise HTTPException(status_code=503, detail=f"No se pudo conectar a MySQL: {e}")


@router.get("/mysql/tables/{table_name}/columns", response_model=list[ExternalPimFieldSchema])
async def get_mysql_table_columns(
    table_name: str,
    _user: User = Depends(require_roles("admin")),
):
    """
    Obtiene las columnas de una tabla MySQL con tipo y valor de muestra.
    Úsalo para explorar el esquema antes de configurar el mapeo.
    """
    try:
        return await pim_mapping_service.introspect_mysql_table_fields(table_name)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/mysql/propose", response_model=list[dict])
async def propose_mysql_field_mapping(
    body: ProposeMappingRequest,
    _user: User = Depends(require_roles("admin")),
):
    """
    Propone un mapeo automático entre las columnas de la tabla MySQL y el recurso interno.

    Analiza los nombres de columnas y aplica heurísticas (diccionario español→campo interno)
    para sugerir correspondencias con las transformaciones adecuadas.

    El campo '__mysql_table' se añade automáticamente a transform_config al guardar el mapeo.
    """
    try:
        return await pim_mapping_service.propose_mysql_mapping(body.table, body.resource)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


# ── CRUD de configuraciones de mapeo ──────────────────────────────────────────

@router.get("", response_model=list[PimResourceMappingRead])
async def list_all_mappings(
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_roles("admin")),
):
    """Lista todas las configuraciones de mapeo existentes."""
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
    """Obtiene la configuración de mapeo para un recurso específico."""
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
    """Crea una nueva configuración de mapeo para un recurso.
    
    Incluye '__mysql_table' en transform_config para indicar la tabla MySQL de origen.
    """
    existing = await db.execute(
        select(PimResourceMapping).where(PimResourceMapping.resource == body.resource)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(409, f"Ya existe una configuración de mapeo para '{body.resource}'")

    mapping = PimResourceMapping(
        resource=body.resource,
        is_active=body.is_active,
        mappings=[m.model_dump() for m in body.mappings],
        defaults=body.defaults,
        transform_config=body.transform_config,
        where_clause=body.where_clause.strip() if body.where_clause else None,
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
    """Actualiza una configuración de mapeo existente."""
    result = await db.execute(
        select(PimResourceMapping).where(PimResourceMapping.resource == resource)
    )
    mapping = result.scalar_one_or_none()
    if not mapping:
        raise HTTPException(404, f"No se encontró configuración de mapeo para '{resource}'")

    if body.is_active is not None:
        mapping.is_active = body.is_active
    if body.mappings is not None:
        mapping.mappings = [m.model_dump() for m in body.mappings]
    if body.defaults is not None:
        mapping.defaults = body.defaults
    if body.transform_config is not None:
        mapping.transform_config = body.transform_config
    if body.where_clause is not None:
        # Convertir string vacío a None
        mapping.where_clause = body.where_clause.strip() if body.where_clause else None
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
    """Elimina una configuración de mapeo."""
    result = await db.execute(
        select(PimResourceMapping).where(PimResourceMapping.resource == resource)
    )
    mapping = result.scalar_one_or_none()
    if not mapping:
        raise HTTPException(404, f"No se encontró configuración de mapeo para '{resource}'")

    await db.delete(mapping)
    await db.commit()


# ── Importación desde MySQL ────────────────────────────────────────────────────

@router.post("/{resource}/import")
async def import_resource_from_mysql(
    resource: str,
    db: AsyncSession = Depends(get_db),
    _user: User = Depends(require_roles("admin")),
):
    """
    Importa un recurso desde MySQL usando el mapeo configurado.

    Requiere:
    - Una configuración de mapeo activa para el recurso.
    - El campo '__mysql_table' en transform_config con el nombre de la tabla MySQL de origen.

    Returns:
        Estadísticas: created, updated, skipped, errors
    """
    try:
        counts = await pim_mapping_service.import_resource_from_mysql(db, resource)
        return {
            "message": f"Importación de '{resource}' completada",
            "stats": counts,
        }
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, f"Error inesperado durante la importación: {e}")

