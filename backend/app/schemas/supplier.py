from datetime import datetime
from pydantic import BaseModel


class SupplierCreate(BaseModel):
    name: str
    code: str | None = None
    country: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    notes: str | None = None
    active: bool = True


class SupplierUpdate(BaseModel):
    name: str | None = None
    code: str | None = None
    country: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    notes: str | None = None
    active: bool | None = None


class SupplierRead(BaseModel):
    id: str
    name: str
    code: str | None = None
    country: str | None = None
    contact_email: str | None = None
    contact_phone: str | None = None
    notes: str | None = None
    active: bool = True
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class ProductSupplierCreate(BaseModel):
    supplier_id: str
    is_primary: bool = False
    supplier_sku: str | None = None
    moq: int | None = None
    lead_time_days: int | None = None
    country_of_origin: str | None = None
    purchase_price: float | None = None
    currency: str | None = None
    notes: str | None = None


class ProductSupplierUpdate(BaseModel):
    is_primary: bool | None = None
    supplier_sku: str | None = None
    moq: int | None = None
    lead_time_days: int | None = None
    country_of_origin: str | None = None
    purchase_price: float | None = None
    currency: str | None = None
    notes: str | None = None


class ProductSupplierRead(BaseModel):
    id: str
    sku: str
    supplier_id: str
    is_primary: bool = False
    supplier_sku: str | None = None
    moq: int | None = None
    lead_time_days: int | None = None
    country_of_origin: str | None = None
    purchase_price: float | None = None
    currency: str | None = None
    notes: str | None = None
    supplier: SupplierRead | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
