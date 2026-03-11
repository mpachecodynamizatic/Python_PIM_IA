from datetime import datetime

from pydantic import BaseModel


class ProductCreate(BaseModel):
    sku: str
    brand: str
    category_id: str
    family_id: str | None = None
    status: str = "draft"
    seo: dict = {}
    attributes: dict = {}


class ProductUpdate(BaseModel):
    brand: str | None = None
    category_id: str | None = None
    family_id: str | None = None
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
