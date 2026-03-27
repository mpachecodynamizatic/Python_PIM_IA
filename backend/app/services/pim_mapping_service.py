"""Servicio para mapeo de campos desde MySQL."""
import logging
import re
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.export.configs import get_config
from app.schemas.pim_mapping import ExternalPimFieldSchema, ResourceFieldSchema, PimFieldMapping
from app.models.pim_field_mapping import PimResourceMapping
from app.models.category import Category
from app.models.brand import Brand
from app.models.supplier import Supplier
from app.models.channel import Channel
from app.services import mysql_service

logger = logging.getLogger(__name__)


# ── Diccionario de sugerencias de mapeo (nombre columna MySQL → campo interno) ─
# Clave: nombre de columna MySQL en minúsculas
# Valor: field_path interno (dot notation) o None (sin sugerencia)
FIELD_NAME_MAP: dict[str, str | None] = {
    # Identificadores de producto
    "sku":                    "sku",
    "referencia":             "sku",
    "codigo":                 "sku",
    "ref":                    "sku",
    "articulo":               "sku",
    "codigo_articulo":        "sku",
    "nombre":                 "name",
    "titulo":                 "name",
    "name":                   "name",
    "title":                  "name",
    # Descripción
    "descripcion":            "attributes.description",
    "descripcion_larga":      "attributes.description",
    "descripcion_corta":      "attributes.short_description",
    "description":            "attributes.description",
    # Marca
    "marca":                  "brand",
    "brand":                  "brand",
    # Categoría
    "categoria":              "category_id",
    "categorias":             "category_id",
    "category":               "category_id",
    # Estado
    "estado":                 "status",
    "estado_referencia":      "status",
    "activo":                 "status",
    "activo_sn":              "status",
    "activosn":               "status",
    "status":                 "status",
    # Slug / código URL
    "slug":                   "slug",
    "codigo_url":             "slug",
    # EAN / GTIN
    "ean":                    "attributes.ean",
    "ean13":                  "attributes.ean",
    "ean14":                  "attributes.ean",
    "gtin":                   "attributes.ean",
    "codigo_barras":          "attributes.ean",
    # SEO
    "palabras_clave":         "seo.keywords",
    "keywords":               "seo.keywords",
    "meta_descripcion":       "seo.description",
    "meta_titulo":            "seo.title",
    # Dimensiones y peso
    "peso":                   "attributes.weight",
    "peso_neto":              "attributes.weight",
    "ancho":                  "attributes.width",
    "alto":                   "attributes.height",
    "fondo":                  "attributes.depth",
    "volumen":                "attributes.volume",
    "largo":                  "attributes.length",
    # Marketplace
    "activoenmarketplace":    "attributes.active_marketplace",
    "referencia_agrupacion":  "attributes.group_reference",
    # Familia / proveedor
    "familia":                "family_id",
    "familia_id":             "family_id",
    "proveedor":              "supplier_id",
    "proveedor_id":           "supplier_id",
    # Campos para recurso "brands"
    "codigo_marca":           "code",
    "marca_codigo":           "code",
    # Campos para recurso "categories"
    "codigo_categoria":       "code",
    "tagaecoc":               "attributes.aecoc_tag",
    "codigoaecoc":            "attributes.aecoc_code",
    # Campos que se omiten (sin mapeo útil)
    "id":                     None,
    "empresa_id":             None,
    "empresaid":              None,
    "imagen":                 None,
    "url_imagen":             None,
    "imagen_url":             None,
    "precio":                 None,
    "pvp":                    None,
    "categoria_padre":        None,
}

MYSQL_TYPE_TO_INTERNAL: dict[str, str] = {
    "int": "int", "bigint": "int", "smallint": "int",
    "tinyint": "int", "mediumint": "int",
    "float": "float", "double": "float", "decimal": "float", "numeric": "float",
    "varchar": "str", "char": "str", "text": "str", "longtext": "str",
    "mediumtext": "str", "tinytext": "str",
    "boolean": "bool", "bool": "bool", "bit": "bool",
    "date": "datetime", "datetime": "datetime", "timestamp": "datetime",
    "json": "json",
}


def _generate_slug(text: str) -> str:
    slug = text.lower()
    slug = re.sub(r'[\s_]+', '-', slug)
    slug = re.sub(r'[^a-z0-9-]', '', slug)
    slug = re.sub(r'-+', '-', slug)
    return slug.strip('-')


def _mysql_type_to_internal(mysql_data_type: str) -> str:
    return MYSQL_TYPE_TO_INTERNAL.get(mysql_data_type.lower(), "str")


# ── Funciones MySQL ────────────────────────────────────────────────────────────

async def introspect_mysql_table_fields(table_name: str) -> list[ExternalPimFieldSchema]:
    """
    Obtiene las columnas de una tabla MySQL como ExternalPimFieldSchema.
    Incluye un valor de muestra (primera fila) para cada columna.
    """
    try:
        columns = await mysql_service.get_table_columns(
            settings.MYSQL_HOST, settings.MYSQL_PORT,
            settings.MYSQL_USER, settings.MYSQL_PASSWORD,
            settings.MYSQL_DATABASE, table_name,
        )
    except Exception as e:
        raise ValueError(f"Error al acceder a la tabla MySQL '{table_name}': {e}")

    try:
        samples = await mysql_service.get_sample_data(
            settings.MYSQL_HOST, settings.MYSQL_PORT,
            settings.MYSQL_USER, settings.MYSQL_PASSWORD,
            settings.MYSQL_DATABASE, table_name, limit=1,
        )
        sample_row = samples[0] if samples else {}
    except Exception:
        sample_row = {}

    fields = []
    for col in columns:
        col_name = col["column_name"]
        raw_sample = sample_row.get(col_name)
        fields.append(ExternalPimFieldSchema(
            field_path=col_name,
            sample_value=str(raw_sample)[:100] if raw_sample is not None else None,
            data_type=_mysql_type_to_internal(col["data_type"]),
            is_nullable=col["is_nullable"] == "YES",
        ))

    return fields


async def propose_mysql_mapping(table_name: str, resource: str) -> list[dict]:
    """
    Propone un mapeo automático entre las columnas de la tabla MySQL y los campos internos.

    Analiza los nombres de columnas de la tabla MySQL y aplica un diccionario de
    sugerencias (FIELD_NAME_MAP) para proponer el mapeo con las transformaciones
    adecuadas (status_map, fk_resolve, etc.).

    Returns:
        Lista de dicts con estructura PimFieldMapping
    """
    try:
        columns = await mysql_service.get_table_columns(
            settings.MYSQL_HOST, settings.MYSQL_PORT,
            settings.MYSQL_USER, settings.MYSQL_PASSWORD,
            settings.MYSQL_DATABASE, table_name,
        )
    except Exception as e:
        raise ValueError(f"Error al acceder a la tabla MySQL '{table_name}': {e}")

    proposed = []
    for col in columns:
        col_name = col["column_name"]
        col_lower = col_name.lower()

        # Buscar en el diccionario de sugerencias
        target = FIELD_NAME_MAP.get(col_lower)
        if target is None:
            continue  # Sin sugerencia → omitir

        # Determinar transformación según el campo
        transform = None
        fk_config = None

        if col_lower in ("estado", "estado_referencia", "activo", "activo_sn", "activosn"):
            transform = "status_map"
        elif col_lower == "marca":
            transform = "fk_resolve"
            fk_config = {
                "table": "brands",
                "lookup_by": "name",
                "return_field": "id",
                "auto_create": True,
            }
        elif col_lower in ("categoria", "categorias"):
            transform = "fk_resolve"
            fk_config = {
                "table": "categories",
                "lookup_by": "name",
                "return_field": "id",
                "auto_create": True,
            }
        elif col_lower in ("proveedor", "proveedor_id"):
            transform = "fk_resolve"
            fk_config = {
                "table": "suppliers",
                "lookup_by": "name",
                "return_field": "id",
                "auto_create": False,
            }

        proposed.append({
            "source_field":  col_name,
            "target_field":  target,
            "transform":     transform,
            "required":      col.get("column_key") == "PRI",
            "default_value": None,
            "fk_config":     fk_config,
        })

    return proposed


async def get_internal_fields_metadata(resource: str) -> list[ResourceFieldSchema]:
    """
    Obtiene metadata de los campos del modelo interno reutilizando ExportConfig.

    Args:
        resource: Tipo de recurso (products, categories, brands, etc.)

    Returns:
        Lista de campos internos con metadata (type, required, fk, choices)

    Raises:
        ValueError: Si el recurso no existe en ExportConfig
    """
    try:
        config = get_config(resource)
    except:
        raise ValueError(f"Recurso '{resource}' no encontrado en export configs")

    fields = []
    for field in config.fields:
        fk_dict = None
        if field.fk:
            fk_dict = {"table": field.fk.table, "column": field.fk.column}

        fields.append(ResourceFieldSchema(
            field_path=field.key,
            label=field.label,
            data_type=field.type,
            is_required=field.required,
            is_readonly=field.readonly,
            fk_constraint=fk_dict,
            choices=field.choices,
        ))

    return fields


async def apply_field_mapping(
    db: AsyncSession,
    resource: str,
    external_data: dict,
) -> dict:
    """
    Aplica la configuración de mapeo para transformar datos externos a formato interno.

    Args:
        db: Sesión de base de datos
        resource: Tipo de recurso (products, categories, etc.)
        external_data: Datos de la API externa

    Returns:
        Dict listo para crear modelo (ej: Product(**output))

    Raises:
        ValueError: Si no hay config activa o faltan campos requeridos
    """
    # Obtener configuración activa
    result = await db.execute(
        select(PimResourceMapping).where(
            PimResourceMapping.resource == resource,
            PimResourceMapping.is_active == True
        )
    )
    mapping_config = result.scalar_one_or_none()
    if not mapping_config:
        raise ValueError(f"No hay configuración de mapeo activa para el recurso '{resource}'")

    # Comenzar con defaults
    output = {}
    for key, value in mapping_config.defaults.items():
        _set_nested_value(output, key, value)

    # Aplicar mapeos de campos
    for mapping in mapping_config.mappings:
        source_field = mapping["source_field"]
        target_field = mapping["target_field"]
        transform = mapping.get("transform")
        required = mapping.get("required", False)
        default_value = mapping.get("default_value")
        fk_config = mapping.get("fk_config")

        # Extraer valor de datos externos (soporta dot notation)
        value = _get_nested_value(external_data, source_field)

        # Manejar valores faltantes
        if (value is None or str(value).strip() == "") and required and default_value is None:
            raise ValueError(f"Campo requerido '{source_field}' está ausente")

        if value is None or str(value).strip() == "":
            value = default_value

        if value is None:
            continue

        # Aplicar transformación
        value = await _apply_transform(db, value, transform, mapping_config.transform_config, fk_config)

        # Almacenar en output (soporta dot notation)
        _set_nested_value(output, target_field, value)

    return output


async def _apply_transform(
    db: AsyncSession,
    value: any,
    transform: str | None,
    transform_config: dict,
    fk_config: dict | None
) -> any:
    """
    Aplica transformación a un valor de campo.

    Args:
        db: Sesión de base de datos
        value: Valor a transformar
        transform: Tipo de transformación (strip, upper, lower, int, float, bool, status_map, brand_code_map, fk_resolve)
        transform_config: Configuración global de transformaciones
        fk_config: Configuración de FK (para fk_resolve)

    Returns:
        Valor transformado
    """
    if value is None:
        return None

    s = str(value).strip()

    # Transformaciones básicas
    if transform == "strip":
        return s
    if transform == "upper":
        return s.upper()
    if transform == "lower":
        return s.lower()
    if transform == "int":
        try:
            return int(s)
        except ValueError:
            return None
    if transform == "float":
        try:
            return float(s)
        except ValueError:
            return None
    if transform == "bool":
        return s.lower() in ("true", "1", "yes", "si", "sí")

    # Transformaciones personalizadas usando transform_config
    if transform == "status_map":
        status_map = transform_config.get("status_map", {})
        return status_map.get(s, s)

    if transform == "brand_code_map":
        brand_map = transform_config.get("brand_code_map", {})
        return brand_map.get(s, s)

    # Resolución de FK: busca entidad por campo, retorna ID
    if transform == "fk_resolve" and fk_config:
        table = fk_config["table"]
        lookup_by = fk_config.get("lookup_by", "name")
        return_field = fk_config.get("return_field", "id")
        auto_create = fk_config.get("auto_create", False)

        model_map = {
            "categories": Category,
            "brands": Brand,
            "suppliers": Supplier,
            "channels": Channel,
        }

        model = model_map.get(table)
        if not model:
            raise ValueError(f"Tabla FK desconocida: {table}")

        # Query por campo de lookup
        query = select(model).where(getattr(model, lookup_by) == s)
        result = await db.execute(query)
        entity = result.scalar_one_or_none()

        if not entity:
            if auto_create:
                # Crear entidad si no existe
                logger.info(f"Auto-creating {table} with {lookup_by}='{s}'")

                # Preparar datos para crear la entidad
                entity_data = {lookup_by: s}

                # Generar slug si la entidad lo requiere (Brand, Category, Supplier, Channel)
                if hasattr(model, 'slug'):
                    base_slug = _generate_slug(s)
                    slug = base_slug

                    # Check if slug already exists and add suffix if needed
                    counter = 1
                    while True:
                        existing_slug = await db.execute(
                            select(model).where(model.slug == slug)
                        )
                        if existing_slug.scalar_one_or_none() is None:
                            break
                        slug = f"{base_slug}-{counter}"
                        counter += 1

                    entity_data['slug'] = slug

                # Crear la entidad con los datos preparados
                entity = model(**entity_data)
                db.add(entity)
                await db.flush()
            else:
                raise ValueError(f"{table}.{lookup_by}='{s}' no encontrado")

        return getattr(entity, return_field)

    # Sin transformación
    return s


def _get_nested_value(data: dict, path: str) -> any:
    """
    Obtiene valor de un dict usando dot notation.
    Ejemplo: 'attributes.color' → data['attributes']['color']
    """
    keys = path.split(".")
    value = data
    for key in keys:
        if isinstance(value, dict):
            value = value.get(key)
        else:
            return None
        if value is None:
            return None
    return value


def _set_nested_value(data: dict, path: str, value: any):
    """
    Establece valor en un dict usando dot notation.
    Ejemplo: 'attributes.color', 'red' → data['attributes']['color'] = 'red'
    """
    keys = path.split(".")
    if len(keys) == 1:
        data[path] = value
    else:
        # Navegar hasta el penúltimo nivel
        current = data
        for key in keys[:-1]:
            if key not in current:
                current[key] = {}
            current = current[key]
        # Establecer valor en el último nivel
        current[keys[-1]] = value


async def import_resource_from_mysql(
    db: AsyncSession,
    resource: str,
) -> dict[str, int]:
    """
    Importa un recurso desde MySQL usando la configuración de mapeo activa.

    Lee la tabla MySQL configurada en transform_config["__mysql_table"] del mapeo activo,
    aplica los mapeos de campo y crea/actualiza registros en la base de datos interna.

    Args:
        db: Sesión de base de datos interna (SQLite)
        resource: Tipo de recurso (products, brands, categories, etc.)

    Returns:
        Dict con contadores: created, updated, skipped, errors

    Raises:
        ValueError: Si no hay mapeo activo, tabla configurada, o error de conexión
    """
    # Si estamos importando productos, asegurar que existe categoría por defecto
    default_category_id = None
    if resource == "products":
        try:
            default_cat_query = await db.execute(
                select(Category).where(Category.name == "Sin Categoría")
            )
            default_category = default_cat_query.scalar_one_or_none()
            if not default_category:
                logger.info("Creando categoría por defecto 'Sin Categoría'")
                default_category = Category(
                    name="Sin Categoría",
                    slug="sin-categoria",
                    description="Productos sin categoría asignada"
                )
                db.add(default_category)
                await db.flush()
                logger.info(f"Categoría 'Sin Categoría' creada con id={default_category.id}")
            default_category_id = default_category.id
            logger.info(f"Usando categoría por defecto: {default_category.name} (id={default_category_id})")

            if default_category_id is None:
                raise ValueError("ERROR CRÍTICO: default_category_id es None después de crear/obtener la categoría")
        except Exception as e:
            logger.error(f"Error al crear/obtener categoría por defecto: {e}")
            raise

    # Verificar que existe mapeo activo
    result = await db.execute(
        select(PimResourceMapping).where(
            PimResourceMapping.resource == resource,
            PimResourceMapping.is_active == True,
        )
    )
    mapping_config = result.scalar_one_or_none()
    if not mapping_config:
        raise ValueError(f"No hay configuración de mapeo activa para el recurso '{resource}'")

    # Leer tabla MySQL desde transform_config
    source_table = mapping_config.transform_config.get("__mysql_table")
    if not source_table:
        raise ValueError(
            f"No hay tabla MySQL configurada para '{resource}'. "
            "Configura '__mysql_table' en el campo Transform Config."
        )

    from app.models.product import Product, ProductI18n
    from app.models.media import MediaAsset
    from app.models.product_logistics import ProductLogistics
    from app.models.product_compliance import ProductCompliance
    from app.models.product_channel import ProductChannel
    from app.models.external_taxonomy import ExternalTaxonomy, ProductExternalTaxonomy
    from app.models.attribute_family import AttributeFamily, AttributeDefinition

    model_map = {
        "products":   Product,
        "brands":     Brand,
        "categories": Category,
        "suppliers":  Supplier,
        "channels":   Channel,
        "product_i18n": ProductI18n,
        "media_assets": MediaAsset,
        "product_logistics": ProductLogistics,
        "product_compliance": ProductCompliance,
        "product_channels": ProductChannel,
        "external_taxonomies": ExternalTaxonomy,
        "product_external_taxonomies": ProductExternalTaxonomy,
        "attribute_families": AttributeFamily,
        "attribute_definitions": AttributeDefinition,
    }
    model = model_map.get(resource)
    if not model:
        raise ValueError(f"Recurso '{resource}' no soportado para importación")

    # Determinar campo PK según el recurso
    pk_fields_map = {
        "products": "sku",
        "product_i18n": "sku",  # También usa locale, pero sku es principal
        "media_assets": "id",
        "product_logistics": "sku",
        "product_compliance": "sku",
        "product_channels": "sku",  # También usa channel_id
        "product_external_taxonomies": "sku",  # También usa taxonomy_id
        "attribute_definitions": "name",  # También usa family_id
        # Por defecto, todos los demás usan 'name'
    }
    pk_field = pk_fields_map.get(resource, "name")

    counts = {"created": 0, "updated": 0, "skipped": 0, "errors": 0}

    # Leer todos los registros de MySQL (con filtro WHERE opcional)
    where_clause = mapping_config.where_clause
    if where_clause:
        logger.info(f"Aplicando filtro WHERE: {where_clause}")

    try:
        items = await mysql_service.fetch_all_rows(
            settings.MYSQL_HOST, settings.MYSQL_PORT,
            settings.MYSQL_USER, settings.MYSQL_PASSWORD,
            settings.MYSQL_DATABASE, source_table,
            where_clause=where_clause,
        )
    except Exception as e:
        raise ValueError(f"Error al leer de MySQL '{source_table}': {e}")

    logger.info(f"Leídas {len(items)} filas de MySQL '{source_table}' para recurso '{resource}' (filtradas con WHERE: {bool(where_clause)})")

    for idx, item in enumerate(items, 1):
        try:
            entity_data = await apply_field_mapping(db, resource, item)
            pk_value = entity_data.get(pk_field)

            if idx % 50 == 0:
                logger.info(f"Procesando {resource} {idx}/{len(items)}: {pk_value}")

            if not pk_value:
                logger.warning(f"Fila {idx} sin valor para '{pk_field}', omitida")
                counts["skipped"] += 1
                continue

            # Auto-generar slug si el modelo lo requiere y no está mapeado
            if hasattr(model, "slug") and "slug" not in entity_data and "name" in entity_data:
                base_slug = _generate_slug(entity_data["name"])
                slug = base_slug
                counter = 1
                while counter < 100:
                    existing_slug = await db.execute(
                        select(model).where(model.slug == slug)
                    )
                    if existing_slug.scalar_one_or_none() is None:
                        break
                    slug = f"{base_slug}-{counter}"
                    counter += 1
                entity_data["slug"] = slug

            # Asignar valores por defecto para productos
            if resource == "products":
                logger.debug(f"Producto {pk_value}: category_id actual={entity_data.get('category_id')}, default_id={default_category_id}")

                # category_id es obligatorio
                if not entity_data.get("category_id") or entity_data.get("category_id") is None:
                    logger.info(f"Asignando categoría por defecto a producto {pk_value} (era: {entity_data.get('category_id')})")
                    entity_data["category_id"] = default_category_id
                    logger.info(f"Categoría asignada: {entity_data['category_id']}")

                # brand es obligatorio - si no existe, crear "Sin Marca"
                if not entity_data.get("brand") or entity_data.get("brand") == "":
                    logger.info(f"Brand vacío para producto {pk_value}, asignando 'Sin Marca'")
                    entity_data["brand"] = "Sin Marca"

                # status es obligatorio
                if not entity_data.get("status"):
                    entity_data["status"] = "draft"

            # Auto-generar campos obligatorios según el recurso
            if resource == "channels":
                # code es obligatorio
                if not entity_data.get("code"):
                    name_val = entity_data.get("name", "")
                    if name_val:
                        code = name_val.upper().replace(" ", "").replace("-", "")[:10]
                        entity_data["code"] = code
                        logger.debug(f"Auto-generando code '{code}' para canal '{name_val}'")
                    else:
                        raise ValueError(f"Canal sin nombre ni código en fila {idx}")

            elif resource == "brands":
                # Valores por defecto para campos NOT NULL
                if not entity_data.get("description"):
                    entity_data["description"] = ""
                if not entity_data.get("website"):
                    entity_data["website"] = ""
                if not entity_data.get("logo_url"):
                    entity_data["logo_url"] = ""

            elif resource == "suppliers":
                # code es obligatorio
                if not entity_data.get("code"):
                    name_val = entity_data.get("name", "")
                    if name_val:
                        code = name_val.upper().replace(" ", "").replace("-", "")[:10]
                        entity_data["code"] = code
                        logger.debug(f"Auto-generando code '{code}' para proveedor '{name_val}'")
                    else:
                        raise ValueError(f"Proveedor sin nombre ni código en fila {idx}")
                # Valores por defecto para campos NOT NULL
                if not entity_data.get("country"):
                    entity_data["country"] = ""
                if not entity_data.get("contact_email"):
                    entity_data["contact_email"] = ""
                if not entity_data.get("contact_phone"):
                    entity_data["contact_phone"] = ""
                if not entity_data.get("notes"):
                    entity_data["notes"] = ""

            # Buscar entidad existente
            existing_q = await db.execute(
                select(model).where(getattr(model, pk_field) == pk_value)
            )
            entity = existing_q.scalar_one_or_none()

            if entity:
                for k, v in entity_data.items():
                    if k != pk_field and hasattr(entity, k):
                        setattr(entity, k, v)
                counts["updated"] += 1
            else:
                entity = model(**entity_data)
                db.add(entity)
                counts["created"] += 1

            # Flush periódico para no saturar memoria
            if idx % 100 == 0:
                await db.flush()

        except ValueError as e:
            logger.warning(f"Fila {idx} omitida por error de mapeo: {e}")
            counts["skipped"] += 1
        except Exception as e:
            logger.error(f"Error procesando fila {idx}: {e}")
            counts["errors"] += 1

    await db.flush()
    await db.commit()
    logger.info(f"Importación de '{resource}' completada: {counts}")
    return counts

