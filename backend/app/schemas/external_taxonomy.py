from datetime import datetime
from pydantic import BaseModel


class ExternalTaxonomyCreate(BaseModel):
    name: str
    provider: str
    description: str | None = None


class ExternalTaxonomyRead(BaseModel):
    id: str
    name: str
    provider: str
    description: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProductTaxonomyUpsert(BaseModel):
    taxonomy_id: str
    node_code: str | None = None
    node_name: str | None = None
    node_path: str | None = None


class ProductTaxonomyRead(BaseModel):
    id: str
    sku: str
    taxonomy_id: str
    node_code: str | None = None
    node_name: str | None = None
    node_path: str | None = None
    taxonomy: ExternalTaxonomyRead | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
