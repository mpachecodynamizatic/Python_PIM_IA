from datetime import datetime
from pydantic import BaseModel


class ComplianceUpdate(BaseModel):
    certifications: list | None = None
    technical_sheet_url: str | None = None
    safety_sheet_url: str | None = None
    legal_warnings: str | None = None
    min_age: int | None = None
    has_lot_traceability: bool | None = None
    has_expiry_date: bool | None = None
    country_of_origin: str | None = None
    hs_code: str | None = None


class ComplianceRead(BaseModel):
    id: str
    sku: str
    certifications: list = []
    technical_sheet_url: str | None = None
    safety_sheet_url: str | None = None
    legal_warnings: str | None = None
    min_age: int | None = None
    has_lot_traceability: bool = False
    has_expiry_date: bool = False
    country_of_origin: str | None = None
    hs_code: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
