"""
Export/Import configuration definitions.

Each resource that supports Excel export/import registers an ExportConfig
with the list of ExportField objects describing each column.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class FKConstraint:
    """References a (table_name, column_attr) for FK validation during import."""
    table: str    # SQLAlchemy __tablename__  e.g. "products"
    column: str   # attribute name on that model  e.g. "sku"


@dataclass
class ExportField:
    key: str                           # ORM attribute name / dict key
    label: str                         # Excel column header
    type: str                          # str | int | float | bool | date | datetime | json | enum
    required: bool = False
    default_include: bool = True       # included in export by default
    readonly: bool = False             # exported but ignored on import
    fk: FKConstraint | None = None
    choices: list[str] | None = None   # for enum type
    max_length: int | None = None


@dataclass
class ExportConfig:
    resource: str
    label: str                         # human-readable name for the UI
    model: Any                         # SQLAlchemy model class
    fields: list[ExportField]
    upsert_key: list[str] = field(default_factory=list)
    auto_pk: bool = True               # True = UUID pk auto-generated; False = pk from data (e.g. sku)


# ---------------------------------------------------------------------------
# FK model map: resolves (table_name, column) → (model_class, attr_name)
# Used in import_service for FK existence checks
# ---------------------------------------------------------------------------

def get_fk_model_map() -> dict[tuple[str, str], Any]:
    from app.models.product import Product, ProductI18n
    from app.models.category import Category
    from app.models.attribute_family import AttributeFamily
    from app.models.quality_rule import QualityRuleSet

    return {
        ("products", "sku"): Product,
        ("categories", "id"): Category,
        ("attribute_families", "id"): AttributeFamily,
        ("quality_rule_sets", "id"): QualityRuleSet,
    }


# ---------------------------------------------------------------------------
# Config registry
# ---------------------------------------------------------------------------

def _build_configs() -> dict[str, ExportConfig]:
    from app.models.product import Product, ProductI18n
    from app.models.category import Category
    from app.models.media import MediaAsset
    from app.models.user import User
    from app.models.quality_rule import QualityRule
    from app.models.attribute_family import AttributeFamily

    _STATUSES = ["draft", "in_review", "approved", "ready", "retired"]

    return {
        "products": ExportConfig(
            resource="products",
            label="Productos",
            model=Product,
            auto_pk=False,
            upsert_key=["sku"],
            fields=[
                ExportField("sku", "SKU", "str", required=True),
                ExportField("brand", "Marca", "str", required=True),
                ExportField("status", "Estado", "enum", required=False, choices=_STATUSES),
                ExportField("category_id", "ID Categoria", "str", required=True,
                            fk=FKConstraint("categories", "id")),
                ExportField("family_id", "ID Familia", "str", required=False, default_include=False,
                            fk=FKConstraint("attribute_families", "id")),
                ExportField("seo", "SEO (JSON)", "json", required=False, default_include=False),
                ExportField("attributes", "Atributos (JSON)", "json", required=False, default_include=False),
                ExportField("created_at", "Creado", "datetime", readonly=True),
                ExportField("updated_at", "Actualizado", "datetime", readonly=True, default_include=False),
            ],
        ),

        "categories": ExportConfig(
            resource="categories",
            label="Categorias",
            model=Category,
            auto_pk=True,
            upsert_key=["slug"],
            fields=[
                ExportField("id", "ID", "str", readonly=True, default_include=False),
                ExportField("name", "Nombre", "str", required=True),
                ExportField("slug", "Slug", "str", required=True),
                ExportField("description", "Descripcion", "str", required=False),
                ExportField("parent_id", "ID Padre", "str", required=False, default_include=False,
                            fk=FKConstraint("categories", "id")),
                ExportField("sort_order", "Orden", "int", required=False, default_include=False),
                ExportField("created_at", "Creado", "datetime", readonly=True, default_include=False),
                ExportField("updated_at", "Actualizado", "datetime", readonly=True, default_include=False),
            ],
        ),

        "product_i18n": ExportConfig(
            resource="product_i18n",
            label="Traducciones",
            model=ProductI18n,
            auto_pk=True,
            upsert_key=["sku", "locale"],
            fields=[
                ExportField("sku", "SKU", "str", required=True, fk=FKConstraint("products", "sku")),
                ExportField("locale", "Idioma", "str", required=True),
                ExportField("title", "Titulo", "str", required=True),
                ExportField("description_rich", "Descripcion (JSON)", "json", required=False,
                            default_include=False),
            ],
        ),

        "media_assets": ExportConfig(
            resource="media_assets",
            label="Multimedia",
            model=MediaAsset,
            auto_pk=True,
            upsert_key=["id"],
            fields=[
                ExportField("id", "ID", "str", readonly=True),
                ExportField("sku", "SKU Producto", "str", required=False,
                            fk=FKConstraint("products", "sku")),
                ExportField("kind", "Tipo", "enum", required=False,
                            choices=["image", "video", "document", "other"]),
                ExportField("url", "URL", "str", required=True),
                ExportField("filename", "Nombre Fichero", "str", required=False),
                ExportField("no_mostrar_en_b2b", "No mostrar B2B", "str", required=False,
                            default_include=False),
                ExportField("created_at", "Creado", "datetime", readonly=True),
                ExportField("updated_at", "Actualizado", "datetime", readonly=True, default_include=False),
            ],
        ),

        "users": ExportConfig(
            resource="users",
            label="Usuarios",
            model=User,
            auto_pk=True,
            upsert_key=["email"],
            fields=[
                ExportField("id", "ID", "str", readonly=True, default_include=False),
                ExportField("email", "Email", "str", required=True),
                ExportField("full_name", "Nombre Completo", "str", required=True),
                ExportField("role", "Rol", "enum", required=False,
                            choices=["admin", "editor", "viewer"]),
                ExportField("is_active", "Activo", "bool", required=False),
                ExportField("scopes", "Permisos (JSON)", "json", required=False, default_include=False),
                ExportField("created_at", "Creado", "datetime", readonly=True, default_include=False),
                ExportField("updated_at", "Actualizado", "datetime", readonly=True, default_include=False),
            ],
        ),

        "quality_rules": ExportConfig(
            resource="quality_rules",
            label="Reglas de Calidad",
            model=QualityRule,
            auto_pk=True,
            upsert_key=["id"],
            fields=[
                ExportField("id", "ID", "str", readonly=True),
                ExportField("rule_set_id", "ID Ruleset", "str", required=True,
                            fk=FKConstraint("quality_rule_sets", "id")),
                ExportField("dimension", "Dimension", "str", required=True),
                ExportField("weight", "Peso", "float", required=False),
                ExportField("min_score", "Score Minimo", "float", required=False),
                ExportField("required_status", "Estado requerido", "enum", required=False,
                            default_include=False,
                            choices=["draft", "in_review", "approved", "ready", "retired"]),
                ExportField("scope_category_id", "ID Categoria Ambito", "str", required=False,
                            default_include=False, fk=FKConstraint("categories", "id")),
                ExportField("created_at", "Creado", "datetime", readonly=True, default_include=False),
                ExportField("updated_at", "Actualizado", "datetime", readonly=True, default_include=False),
            ],
        ),

        "attribute_families": ExportConfig(
            resource="attribute_families",
            label="Familias de Atributos",
            model=AttributeFamily,
            auto_pk=True,
            upsert_key=["code"],
            fields=[
                ExportField("id", "ID", "str", readonly=True, default_include=False),
                ExportField("code", "Codigo", "str", required=True),
                ExportField("name", "Nombre", "str", required=True),
                ExportField("description", "Descripcion", "str", required=False),
                ExportField("category_id", "ID Categoria", "str", required=False, default_include=False,
                            fk=FKConstraint("categories", "id")),
                ExportField("created_at", "Creado", "datetime", readonly=True, default_include=False),
                ExportField("updated_at", "Actualizado", "datetime", readonly=True, default_include=False),
            ],
        ),
    }


_CONFIGS: dict[str, ExportConfig] | None = None


def get_configs() -> dict[str, ExportConfig]:
    global _CONFIGS
    if _CONFIGS is None:
        _CONFIGS = _build_configs()
    return _CONFIGS


def get_config(resource: str) -> ExportConfig:
    configs = get_configs()
    if resource not in configs:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail=f"Recurso '{resource}' no soportado")
    return configs[resource]
