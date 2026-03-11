from datetime import datetime
from pydantic import BaseModel


class LogisticsUpdate(BaseModel):
    base_unit: str | None = None
    box_units: int | None = None
    pallet_boxes: int | None = None
    pallet_units: int | None = None
    height_mm: float | None = None
    width_mm: float | None = None
    depth_mm: float | None = None
    weight_gross_g: float | None = None
    weight_net_g: float | None = None
    stackable: bool | None = None
    packaging_type: str | None = None
    transport_conditions: str | None = None
    adr: bool | None = None
    adr_class: str | None = None
    adr_un_number: str | None = None
    adr_details: str | None = None


class LogisticsRead(BaseModel):
    id: str
    sku: str
    base_unit: str | None = None
    box_units: int | None = None
    pallet_boxes: int | None = None
    pallet_units: int | None = None
    height_mm: float | None = None
    width_mm: float | None = None
    depth_mm: float | None = None
    weight_gross_g: float | None = None
    weight_net_g: float | None = None
    stackable: bool = False
    packaging_type: str | None = None
    transport_conditions: str | None = None
    adr: bool = False
    adr_class: str | None = None
    adr_un_number: str | None = None
    adr_details: str | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
