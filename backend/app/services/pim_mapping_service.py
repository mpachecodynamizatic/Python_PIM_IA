"""Servicio para mapeo de campos del PIM externo."""
import logging
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
    endpoint_map = {
        "products": "/B2bProductos",
        "categories": "/Categorias",  # Hipotético
        "brands": "/Marcas",  # Hipotético
    }

    endpoint = endpoint_map.get(resource)
    if not endpoint:
        # Usar endpoint de productos por defecto
        endpoint = "/B2bProductos"

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
        return fields

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
                entity = model(**{lookup_by: s})
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
