"""Servicio para mapeo de campos del PIM externo."""
import logging
import re
import requests
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.export.configs import get_config
from app.schemas.pim_mapping import ExternalPimFieldSchema, ResourceFieldSchema
from app.models.pim_field_mapping import PimResourceMapping
from app.models.category import Category
from app.models.brand import Brand
from app.models.supplier import Supplier
from app.models.channel import Channel

logger = logging.getLogger(__name__)


def _generate_slug(text: str) -> str:
    """
    Generate a URL-friendly slug from text.

    Args:
        text: Text to convert to slug

    Returns:
        Slugified text (lowercase, alphanumeric + hyphens)
    """
    # Convert to lowercase
    slug = text.lower()
    # Replace spaces and underscores with hyphens
    slug = re.sub(r'[\s_]+', '-', slug)
    # Remove non-alphanumeric characters except hyphens
    slug = re.sub(r'[^a-z0-9-]', '', slug)
    # Remove multiple consecutive hyphens
    slug = re.sub(r'-+', '-', slug)
    # Strip hyphens from start and end
    slug = slug.strip('-')
    return slug


def _filter_fields_by_resource(fields: list[ExternalPimFieldSchema], resource: str) -> list[ExternalPimFieldSchema]:
    """
    Filtra campos según el recurso para mostrar solo los relevantes.

    Args:
        fields: Lista completa de campos introspectados
        resource: Tipo de recurso (products, brands, categories, etc.)

    Returns:
        Lista filtrada de campos relevantes para el recurso
    """
    # Mapeo de recursos a patrones de campos relevantes
    resource_patterns = {
        "brands": ["marca", "brand"],
        "categories": ["categoria", "category"],
        "suppliers": ["proveedor", "supplier", "fabricante"],
        "channels": ["canal", "channel", "tienda", "store"],
    }

    # Para productos, mostrar todos los campos
    if resource == "products":
        return fields

    # Para otros recursos, filtrar por patrones relevantes
    patterns = resource_patterns.get(resource, [])
    if not patterns:
        return fields

    # Filtrar campos que coincidan con los patrones
    relevant_fields = []
    other_fields = []

    for field in fields:
        field_lower = field.field_path.lower()
        is_relevant = any(pattern in field_lower for pattern in patterns)

        if is_relevant:
            relevant_fields.append(field)
        else:
            other_fields.append(field)

    # Retornar primero los campos relevantes, luego los demás
    # Esto permite ver los campos importantes al principio
    return relevant_fields + other_fields


async def introspect_external_fields(resource: str, db: AsyncSession) -> list[ExternalPimFieldSchema]:
    """
    Conecta a la API externa del PIM y analiza la estructura de respuesta
    para descubrir los campos disponibles.

    Args:
        resource: Tipo de recurso (products, categories, brands, etc.)
        db: Sesión de base de datos

    Returns:
        Lista de campos externos con sample values y tipos

    Raises:
        ValueError: Si la conexión al PIM falla o el recurso no es válido
    """
    # Mapeo de recursos a endpoints de la API externa
    # Para recursos que no tienen endpoint propio (brands, categories),
    # usamos /B2bProductos ya que contiene esa información
    endpoint_map = {
        "products": "/B2bProductos",
        "categories": "/B2bProductos",  # Usa productos (tienen campo 'categorias')
        "brands": "/B2bProductos",  # Usa productos (tienen campo 'marca')
        "suppliers": "/B2bProductos",
        "channels": "/B2bProductos",
    }

    endpoint = endpoint_map.get(resource, "/B2bProductos")

    ssl_verify = settings.PIM_SSL_VERIFY.lower() != 'false'

    try:
        # Autenticación
        login_url = f"{settings.PIM_BASE_URL}/auth/login"
        auth_payload = {"mail": settings.PIM_MAIL, "password": settings.PIM_PASSWORD}

        login_resp = requests.post(login_url, json=auth_payload, verify=ssl_verify, timeout=30)
        login_resp.raise_for_status()
        token_data = login_resp.json()

        # Obtener token
        token = token_data.get('token') or token_data

        # Obtener datos (limitado a 1 item para introspección)
        get_url = f"{settings.PIM_BASE_URL}{endpoint}"
        headers = {"accept": "application/json", "Authorization": f"Bearer {token}"}

        resp = requests.get(get_url, headers=headers, verify=ssl_verify, timeout=60)
        resp.raise_for_status()

        items = resp.json()
        if not items:
            return []

        # Introspeccionar primer item
        sample = items[0] if isinstance(items, list) else items
        fields = []

        def introspect_dict(obj, prefix=""):
            """Recorre recursivamente el objeto JSON y extrae campos."""
            if not isinstance(obj, dict):
                return

            for key, value in obj.items():
                field_path = f"{prefix}.{key}" if prefix else key
                is_nullable = value is None

                if isinstance(value, dict):
                    # Recursivo para objetos anidados
                    introspect_dict(value, field_path)
                else:
                    # Determinar tipo
                    if value is None:
                        data_type = "null"
                    elif isinstance(value, bool):
                        data_type = "bool"
                    elif isinstance(value, int):
                        data_type = "int"
                    elif isinstance(value, float):
                        data_type = "float"
                    elif isinstance(value, str):
                        data_type = "str"
                    elif isinstance(value, list):
                        data_type = "list"
                    else:
                        data_type = type(value).__name__

                    fields.append(ExternalPimFieldSchema(
                        field_path=field_path,
                        sample_value=str(value)[:100] if value is not None else None,
                        data_type=data_type,
                        is_nullable=is_nullable,
                    ))

        introspect_dict(sample)

        # Filtrar campos según el recurso para mostrar solo los relevantes
        filtered_fields = _filter_fields_by_resource(fields, resource)
        return filtered_fields

    except requests.HTTPError as e:
        logger.error(f"HTTP error al conectar con PIM externo: {e}")
        raise ValueError(f"No se pudo conectar al PIM externo: {e}")
    except Exception as e:
        logger.exception("Error inesperado al introspeccionar PIM externo")
        raise ValueError(f"Error al introspeccionar PIM externo: {e}")


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


async def import_resource_from_external_pim(
    db: AsyncSession,
    resource: str,
) -> dict[str, int]:
    """
    Importa un recurso específico desde el PIM externo usando su mapeo configurado.

    Args:
        db: Sesión de base de datos
        resource: Tipo de recurso (products, brands, categories, etc.)

    Returns:
        Dict con contadores de importación (created, updated, skipped, errors)

    Raises:
        ValueError: Si no hay mapeo activo o hay error de conexión
    """
    # Verificar que existe mapeo activo
    result = await db.execute(
        select(PimResourceMapping).where(
            PimResourceMapping.resource == resource,
            PimResourceMapping.is_active == True
        )
    )
    mapping_config = result.scalar_one_or_none()
    if not mapping_config:
        raise ValueError(f"No hay configuración de mapeo activa para el recurso '{resource}'")

    # Mapeo de recursos a modelos
    from app.models.product import Product

    model_map = {
        "products": Product,
        "brands": Brand,
        "categories": Category,
        "suppliers": Supplier,
        "channels": Channel,
    }

    model = model_map.get(resource)
    if not model:
        raise ValueError(f"Recurso '{resource}' no soportado para importación")

    # Obtener datos del PIM externo
    endpoint = "/B2bProductos"  # Único endpoint disponible
    ssl_verify = settings.PIM_SSL_VERIFY.lower() != 'false'

    counts = {
        'created': 0,
        'updated': 0,
        'skipped': 0,
        'errors': 0,
    }

    try:
        # Autenticación
        login_url = f"{settings.PIM_BASE_URL}/auth/login"
        auth_payload = {"mail": settings.PIM_MAIL, "password": settings.PIM_PASSWORD}

        login_resp = requests.post(login_url, json=auth_payload, verify=ssl_verify, timeout=30)
        login_resp.raise_for_status()
        token_data = login_resp.json()
        token = token_data.get('token') or token_data

        # Obtener datos
        get_url = f"{settings.PIM_BASE_URL}{endpoint}"
        headers = {"accept": "application/json", "Authorization": f"Bearer {token}"}

        resp = requests.get(get_url, headers=headers, verify=ssl_verify, timeout=60)
        resp.raise_for_status()

        items = resp.json()
        logger.info(f"Retrieved {len(items)} items from external PIM for resource '{resource}'")

        # Para recursos que no son productos, primero extraer valores únicos
        # para evitar procesar duplicados (ej: 1000 productos con 4 marcas)
        if resource != "products":
            unique_values = {}  # key: valor del campo principal, value: item de ejemplo
            pk_field = "name"  # Para brands, categories, etc. usamos 'name' como PK

            for item in items:
                try:
                    # Aplicar mapeo para obtener el campo principal
                    entity_data = await apply_field_mapping(db, resource, item)
                    pk_value = entity_data.get(pk_field)

                    if pk_value and pk_value not in unique_values:
                        unique_values[pk_value] = entity_data
                except Exception as e:
                    logger.debug(f"Skipping item due to mapping error during deduplication: {e}")
                    continue

            logger.info(f"Found {len(unique_values)} unique {resource} from {len(items)} products")
            # Reemplazar items con los valores únicos ya mapeados
            items_to_process = list(unique_values.values())
        else:
            items_to_process = items

        # Procesar cada item
        for idx, item in enumerate(items_to_process, 1):
            try:
                # Si ya está mapeado (recursos no-productos), usar directamente
                # Si no, aplicar mapeo (productos)
                if resource != "products" and isinstance(item, dict) and 'name' in item:
                    entity_data = item  # Ya mapeado en la fase de deduplicación
                else:
                    entity_data = await apply_field_mapping(db, resource, item)

                # Determinar clave primaria (por defecto 'id', pero puede ser 'sku', 'name', etc.)
                # Para products usamos 'sku', para otros recursos usamos 'name'
                if resource == "products":
                    pk_field = "sku"
                    pk_value = entity_data.get("sku")
                else:
                    pk_field = "name"
                    pk_value = entity_data.get("name")

                # Log de progreso cada 10 items
                if idx % 10 == 0:
                    logger.info(f"Processing {resource} {idx}/{len(items_to_process)}: {pk_value}")

                if not pk_value:
                    logger.warning(f"Skipping item without {pk_field}: {item.get('id', 'unknown')}")
                    counts['skipped'] += 1
                    continue

                # Auto-generar campos requeridos que no están mapeados
                # Si el modelo tiene 'slug' y no está en entity_data, generarlo desde 'name'
                if hasattr(model, 'slug') and 'slug' not in entity_data and 'name' in entity_data:
                    base_slug = _generate_slug(entity_data['name'])
                    slug = base_slug

                    # Verificar si el slug ya existe y añadir sufijo si es necesario
                    # Límite de 100 intentos para evitar loops infinitos
                    counter = 1
                    max_attempts = 100
                    while counter < max_attempts:
                        existing_slug = await db.execute(
                            select(model).where(model.slug == slug)
                        )
                        if existing_slug.scalar_one_or_none() is None:
                            break
                        slug = f"{base_slug}-{counter}"
                        counter += 1

                    if counter >= max_attempts:
                        logger.error(f"Could not generate unique slug for '{entity_data['name']}' after {max_attempts} attempts")
                        counts['errors'] += 1
                        continue

                    entity_data['slug'] = slug

                # Buscar si ya existe
                query = select(model).where(getattr(model, pk_field) == pk_value)
                existing = await db.execute(query)
                entity = existing.scalar_one_or_none()

                if entity:
                    # Actualizar existente
                    for key, value in entity_data.items():
                        if key != pk_field:  # No cambiar la PK
                            setattr(entity, key, value)
                    counts['updated'] += 1
                else:
                    # Crear nuevo
                    entity = model(**entity_data)
                    db.add(entity)
                    counts['created'] += 1

            except ValueError as e:
                # Error de mapeo (campo requerido faltante, FK no encontrado, etc.)
                logger.warning(f"Skipping item due to mapping error: {e}")
                counts['skipped'] += 1
                continue
            except Exception as e:
                logger.error(f"Error processing item: {e}")
                counts['errors'] += 1
                continue

        # Commit todos los cambios
        await db.commit()

        logger.info(f"Import of '{resource}' completed: {counts}")
        return counts

    except requests.HTTPError as e:
        logger.error(f"HTTP error connecting to external PIM: {e}")
        raise ValueError(f"No se pudo conectar al PIM externo: {e}")
    except Exception as e:
        logger.exception("Unexpected error importing from external PIM")
        raise ValueError(f"Error al importar desde PIM externo: {e}")
