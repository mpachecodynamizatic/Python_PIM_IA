"""Servicio para mapeo de campos desde base de datos MySQL externa (datosejemplo)."""
import logging
import re
from typing import Optional
from difflib import SequenceMatcher
import mysql.connector
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.export.configs import get_config
from app.schemas.pim_mapping import ExternalPimFieldSchema, ResourceFieldSchema, FieldMappingSuggestion

logger = logging.getLogger(__name__)


def _similarity_score(a: str, b: str) -> float:
    """
    Calcula la similitud entre dos strings (0.0 a 1.0).

    Args:
        a: Primer string
        b: Segundo string

    Returns:
        Score de similitud (0.0 = completamente diferentes, 1.0 = idénticos)
    """
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def _normalize_field_name(field: str) -> str:
    """
    Normaliza nombre de campo para comparación:
    - Convierte a minúsculas
    - Elimina guiones bajos y cambia a snake_case
    - Elimina prefijos comunes (producto_, tb_, etc.)

    Args:
        field: Nombre del campo

    Returns:
        Nombre normalizado
    """
    field = field.lower()
    # Eliminar prefijos comunes
    for prefix in ['producto_', 'tb_', 'tbl_', 'cat_', 'master_']:
        if field.startswith(prefix):
            field = field[len(prefix):]
    return field


def _suggest_field_mapping(
    external_field: str,
    internal_fields: list[str],
    threshold: float = 0.6
) -> Optional[tuple[str, float]]:
    """
    Sugiere el mejor campo interno para mapear un campo externo.

    Args:
        external_field: Nombre del campo externo (MySQL)
        internal_fields: Lista de campos internos disponibles
        threshold: Umbral mínimo de similitud (0.0 a 1.0)

    Returns:
        Tupla (campo_interno, score) o None si no hay match suficiente
    """
    external_norm = _normalize_field_name(external_field)

    # Mapeos directos conocidos
    direct_mappings = {
        # Productos
        'sku': 'sku',
        'codigo': 'sku',
        'reference': 'sku',
        'nombre': 'name',
        'name': 'name',
        'titulo': 'name',
        'marca': 'brand',
        'brand': 'brand',
        'categoria': 'category_id',
        'category': 'category_id',
        'categoria_id': 'category_id',
        'descripcion': 'short_description',
        'description': 'short_description',
        'desc_corta': 'short_description',
        'desc_larga': 'long_description',
        'long_desc': 'long_description',
        'ean': 'ean_gtin',
        'gtin': 'ean_gtin',
        'ean13': 'ean_gtin',
        'estado': 'status',
        'status': 'status',
        'precio': 'price',
        'price': 'price',
        'pvp': 'price',

        # Marcas
        'slug': 'slug',
        'web': 'website',
        'website': 'website',
        'sitio_web': 'website',
        'logo': 'logo_url',
        'logo_url': 'logo_url',
        'activo': 'active',
        'active': 'active',

        # Categorías
        'parent_id': 'parent_id',
        'padre_id': 'parent_id',
        'categoria_padre': 'parent_id',

        # Proveedores
        'codigo_proveedor': 'code',
        'supplier_code': 'code',
        'pais': 'country',
        'country': 'country',
        'email': 'email',
        'telefono': 'phone',
        'phone': 'phone',
        'notas': 'notes',
        'notes': 'notes',
    }

    # Buscar mapeo directo
    if external_norm in direct_mappings:
        suggested = direct_mappings[external_norm]
        if suggested in internal_fields:
            return (suggested, 1.0)

    # Buscar por similitud
    best_match = None
    best_score = 0.0

    for internal_field in internal_fields:
        internal_norm = _normalize_field_name(internal_field)
        score = _similarity_score(external_norm, internal_norm)

        if score > best_score and score >= threshold:
            best_score = score
            best_match = internal_field

    if best_match:
        return (best_match, best_score)

    return None


async def get_mysql_tables() -> list[dict]:
    """
    Obtiene lista de tablas disponibles en la BD MySQL datosejemplo.

    Returns:
        Lista de diccionarios con información de cada tabla:
        {
            "name": "nombre_tabla",
            "row_count": 1234,
            "description": "Descripción inferida del nombre"
        }
    """
    try:
        conn = mysql.connector.connect(
            host=settings.MYSQL_HOST or "localhost",
            user=settings.MYSQL_USER or "root",
            password=settings.MYSQL_PASSWORD or "",
            database=settings.MYSQL_DATABASE or "datosejemplo"
        )
        cursor = conn.cursor()

        # Obtener lista de tablas
        cursor.execute("SHOW TABLES")
        tables = cursor.fetchall()

        result = []
        for (table_name,) in tables:
            # Obtener número de filas
            cursor.execute(f"SELECT COUNT(*) FROM `{table_name}`")
            row_count = cursor.fetchone()[0]

            # Generar descripción basada en el nombre
            description = table_name.replace('_', ' ').title()

            result.append({
                "name": table_name,
                "row_count": row_count,
                "description": description
            })

        cursor.close()
        conn.close()

        return result

    except mysql.connector.Error as e:
        logger.error(f"Error al conectar con MySQL: {e}")
        raise ValueError(f"No se pudo conectar a la base de datos MySQL: {e}")


async def introspect_mysql_table(table_name: str, resource: str) -> list[ExternalPimFieldSchema]:
    """
    Introspecciona una tabla MySQL y retorna sus columnas con metadatos.

    Args:
        table_name: Nombre de la tabla a introspeccionar
        resource: Tipo de recurso interno (products, categories, brands, etc.)

    Returns:
        Lista de campos externos con metadata
    """
    try:
        conn = mysql.connector.connect(
            host=settings.MYSQL_HOST or "localhost",
            user=settings.MYSQL_USER or "root",
            password=settings.MYSQL_PASSWORD or "",
            database=settings.MYSQL_DATABASE or "datosejemplo"
        )
        cursor = conn.cursor()

        # Obtener información de columnas
        cursor.execute(f"DESCRIBE `{table_name}`")
        columns = cursor.fetchall()

        # Obtener sample values (primera fila)
        cursor.execute(f"SELECT * FROM `{table_name}` LIMIT 1")
        sample_row = cursor.fetchone()

        fields = []
        for i, (field, field_type, null, key, default, extra) in enumerate(columns):
            # Mapear tipos MySQL a tipos Python
            data_type = "str"
            if "int" in field_type.lower():
                data_type = "int"
            elif "float" in field_type.lower() or "double" in field_type.lower() or "decimal" in field_type.lower():
                data_type = "float"
            elif "date" in field_type.lower() or "time" in field_type.lower():
                data_type = "datetime"
            elif "text" in field_type.lower() or "blob" in field_type.lower():
                data_type = "text"
            elif "bool" in field_type.lower() or "tinyint(1)" in field_type.lower():
                data_type = "bool"

            # Sample value
            sample_value = None
            if sample_row and i < len(sample_row):
                val = sample_row[i]
                if val is not None:
                    sample_value = str(val)[:100]

            fields.append(ExternalPimFieldSchema(
                field_path=field,
                sample_value=sample_value,
                data_type=data_type,
                is_nullable=(null == "YES"),
                is_primary_key=(key == "PRI"),
            ))

        cursor.close()
        conn.close()

        return fields

    except mysql.connector.Error as e:
        logger.error(f"Error al introspeccionar tabla MySQL: {e}")
        raise ValueError(f"No se pudo introspeccionar la tabla: {e}")


async def suggest_field_mappings(
    table_name: str,
    resource: str
) -> list[FieldMappingSuggestion]:
    """
    Genera sugerencias automáticas de mapeo de campos.

    Args:
        table_name: Nombre de la tabla MySQL
        resource: Tipo de recurso interno (products, categories, brands, etc.)

    Returns:
        Lista de sugerencias de mapeo con scores de confianza
    """
    # Obtener campos externos
    external_fields = await introspect_mysql_table(table_name, resource)

    # Obtener campos internos
    config = get_config(resource)
    if not config:
        raise ValueError(f"Recurso '{resource}' no válido")

    internal_field_names = [f["name"] for f in config.fields]

    suggestions = []

    for ext_field in external_fields:
        suggestion = _suggest_field_mapping(
            ext_field.field_path,
            internal_field_names,
            threshold=0.5
        )

        if suggestion:
            internal_field, confidence = suggestion

            # Encontrar metadata del campo interno
            internal_metadata = next(
                (f for f in config.fields if f["name"] == internal_field),
                None
            )

            suggestions.append(FieldMappingSuggestion(
                external_field=ext_field.field_path,
                internal_field=internal_field,
                confidence=confidence,
                external_sample=ext_field.sample_value,
                internal_description=internal_metadata.get("label", "") if internal_metadata else "",
                reason=_get_mapping_reason(ext_field.field_path, internal_field, confidence)
            ))

    # Ordenar por confianza (mayor a menor)
    suggestions.sort(key=lambda x: x.confidence, reverse=True)

    return suggestions


def _get_mapping_reason(external: str, internal: str, confidence: float) -> str:
    """
    Genera una razón legible para el mapeo sugerido.

    Args:
        external: Campo externo
        internal: Campo interno
        confidence: Score de confianza

    Returns:
        Descripción de por qué se sugirió el mapeo
    """
    if confidence == 1.0:
        return f"Mapeo directo: '{external}' → '{internal}'"
    elif confidence >= 0.8:
        return f"Alta similitud ({confidence:.0%}): '{external}' es muy similar a '{internal}'"
    else:
        return f"Similitud media ({confidence:.0%}): '{external}' podría corresponder a '{internal}'"


async def get_internal_fields_metadata(resource: str) -> list[ResourceFieldSchema]:
    """
    Obtiene metadata de los campos del modelo interno reutilizando ExportConfig.

    Args:
        resource: Tipo de recurso (products, categories, brands, etc.)

    Returns:
        Lista de campos internos con metadata
    """
    config = get_config(resource)
    if not config:
        return []

    fields = []
    for field_def in config.fields:
        fields.append(ResourceFieldSchema(
            name=field_def["name"],
            label=field_def.get("label", field_def["name"]),
            data_type=field_def.get("type", "str"),
            is_required=field_def.get("required", False),
            description=field_def.get("description", ""),
        ))

    return fields
