from datetime import datetime

from pydantic import BaseModel


class ProductSyncHistoryRead(BaseModel):
    id: str
    sku: str
    channel: str
    job_id: str | None = None
    status: str
    detail: dict = {}
    error_message: str | None = None
    synced_at: datetime | None = None

    class Config:
        from_attributes = True


class ProductSyncStatusRead(BaseModel):
    """Estado actual de un SKU en cada canal (último registro)."""

    sku: str
    channel: str
    status: str
    synced_at: datetime | None = None
    job_id: str | None = None
