"""Schemas para configuración de mapeo de campos desde MySQL."""
from datetime import datetime
from pydantic import BaseModel, Field, ConfigDict


class PimFieldMapping(BaseModel):
    """Define mapeo de un campo individual."""
    source_field: str
    target_field: str
    transform: str | None = None
    required: bool = False
    default_value: str | None = None
    fk_config: dict | None = None


class PimResourceMappingCreate(BaseModel):
    """Request para crear una configuración de mapeo."""
    resource: str
    is_active: bool = True
    mappings: list[PimFieldMapping]
    defaults: dict = Field(default_factory=dict)
    transform_config: dict = Field(default_factory=dict)
    where_clause: str | None = None
    notes: str | None = None


class PimResourceMappingUpdate(BaseModel):
    """Request para actualizar una configuración de mapeo."""
    is_active: bool | None = None
    mappings: list[PimFieldMapping] | None = None
    defaults: dict | None = None
    transform_config: dict | None = None
    where_clause: str | None = None
    notes: str | None = None


class PimResourceMappingRead(BaseModel):
    """Response con configuración completa de mapeo."""
    id: str
    resource: str
    is_active: bool
    mappings: list[PimFieldMapping]
    defaults: dict
    transform_config: dict
    where_clause: str | None
    created_by: str
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ExternalPimFieldSchema(BaseModel):
    """Describe una columna MySQL (resultado de introspección de tabla)."""
    field_path: str
    sample_value: str | None
    data_type: str
    is_nullable: bool


class ResourceFieldSchema(BaseModel):
    """Describe un campo del modelo interno (metadata)."""
    field_path: str
    label: str
    data_type: str
    is_required: bool
    is_readonly: bool = False
    fk_constraint: dict | None = None
    choices: list[str] | None = None


# ── Schemas MySQL ──────────────────────────────────────────────────────────────

class MySQLTableInfo(BaseModel):
    """Información de una tabla MySQL."""
    table_name: str
    engine: str | None = None
    row_count: int = 0
    table_comment: str = ""


class MySQLColumnInfo(BaseModel):
    """Información de una columna MySQL."""
    column_name: str
    data_type: str
    column_type: str
    is_nullable: bool
    column_default: str | None = None
    column_key: str = ""
    column_comment: str = ""


class MySQLConnectionStatus(BaseModel):
    """Estado de la conexión MySQL."""
    success: bool
    version: str | None = None
    database: str | None = None
    host: str | None = None
    error: str | None = None


class ProposeMappingRequest(BaseModel):
    """Request para proponer mapeo automático."""
    table: str
    resource: str
