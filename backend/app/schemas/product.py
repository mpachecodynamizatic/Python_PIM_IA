from datetime import datetime

from pydantic import BaseModel


class ProductCreate(BaseModel):
    sku: str
    brand: str
    category_id: str
    family_id: str | None = None
    status: str = "draft"
    # Identity
    ean_gtin: str | None = None
    dun14: str | None = None
    supplier_ref: str | None = None
    # Naming / descriptions
    name: str | None = None
    short_description: str | None = None
    long_description: str | None = None
    key_benefits: list = []
    sales_pitch: str | None = None
    marketing_claims: list = []
    marketplace_text: dict = {}
    seo: dict = {}
    attributes: dict = {}


class ProductUpdate(BaseModel):
    brand: str | None = None
    category_id: str | None = None
    family_id: str | None = None
    # Identity
    ean_gtin: str | None = None
    dun14: str | None = None
    supplier_ref: str | None = None
    # Naming / descriptions
    name: str | None = None
    short_description: str | None = None
    long_description: str | None = None
    key_benefits: list | None = None
    sales_pitch: str | None = None
    marketing_claims: list | None = None
    marketplace_text: dict | None = None
    seo: dict | None = None
    attributes: dict | None = None


class ProductI18nUpsert(BaseModel):
    locale: str
    title: str
    description_rich: dict | None = None


class ProductI18nRead(BaseModel):
    locale: str
    title: str
    description_rich: dict | None = None

    model_config = {"from_attributes": True}


class ProductRead(BaseModel):
    sku: str
    brand: str
    status: str
    category_id: str
    family_id: str | None = None
    # Identity
    ean_gtin: str | None = None
    dun14: str | None = None
    supplier_ref: str | None = None
    # Naming / descriptions
    name: str | None = None
    short_description: str | None = None
    long_description: str | None = None
    key_benefits: list = []
    sales_pitch: str | None = None
    marketing_claims: list = []
    marketplace_text: dict = {}
    seo: dict
    attributes: dict
    created_at: datetime
    updated_at: datetime
    translations: list[ProductI18nRead] = []

    model_config = {"from_attributes": True}


class ProductListItem(BaseModel):
    sku: str
    brand: str
    status: str
    category_id: str
    name: str | None = None
    ean_gtin: str | None = None
    updated_at: datetime

    model_config = {"from_attributes": True}


class TransitionRequest(BaseModel):
    new_status: str
    reason: str | None = None


class ProductVersionRead(BaseModel):
    """Entrada de historial/versionado basada en AuditLog."""

    id: str
    sku: str
    actor: str
    action: str
    created_at: datetime
    snapshot: dict | None = None


class RetentionPolicy(BaseModel):
    """Política de retención de versiones."""

    max_versions: int | None = None
    max_age_days: int | None = None


class RetentionResult(BaseModel):
    """Resultado de aplicar una política de retención."""

    deleted: int
    remaining: int


class WorkflowActionRequest(BaseModel):
    """Petición simple para acciones de workflow (motivo opcional)."""

    reason: str | None = None
