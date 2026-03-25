"""Schemas para configuración de mapeo de campos PIM externo."""
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
    notes: str | None = None


class PimResourceMappingUpdate(BaseModel):
    """Request para actualizar una configuración de mapeo."""
    is_active: bool | None = None
    mappings: list[PimFieldMapping] | None = None
    defaults: dict | None = None
    transform_config: dict | None = None
    notes: str | None = None


class PimResourceMappingRead(BaseModel):
    """Response con configuración completa de mapeo."""
    id: str
    resource: str
    is_active: bool
    mappings: list[PimFieldMapping]
    defaults: dict
    transform_config: dict
    created_by: str
    notes: str | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ExternalPimFieldSchema(BaseModel):
    """Describe un campo de la API externa (resultado de introspección)."""
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
