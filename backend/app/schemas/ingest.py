from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class ColumnMapping(BaseModel):
    source_column: str
    product_field: str
    required: bool = False
    transform: str | None = None  # strip | upper | lower | int | float


class ColumnMappingSet(BaseModel):
    mappings: list[ColumnMapping]
    defaults: dict = Field(default_factory=dict)


class MappingTemplateCreate(BaseModel):
    name: str
    description: str | None = None
    mappings: list[ColumnMapping]
    defaults: dict = Field(default_factory=dict)


class MappingTemplateRead(BaseModel):
    id: str
    name: str
    description: str | None = None
    mappings: list[ColumnMapping]
    defaults: dict
    created_by: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ImportRowError(BaseModel):
    row: int
    field: str
    value: str | None = None
    message: str


class ImportJobRead(BaseModel):
    id: str
    actor: str
    file_format: str
    original_filename: str
    status: str
    dry_run: bool
    total_rows: int
    processed_rows: int
    success_rows: int
    failed_rows: int
    column_mapping: dict
    errors: list[ImportRowError]
    started_at: datetime | None
    finished_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class ImportJobSummary(BaseModel):
    id: str
    original_filename: str
    status: str
    dry_run: bool
    total_rows: int
    success_rows: int
    failed_rows: int
    created_at: datetime

    model_config = {"from_attributes": True}


class UploadResponse(BaseModel):
    job_id: str
    status: str = "pending"
    message: str
