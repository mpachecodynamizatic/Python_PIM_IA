from datetime import datetime

from pydantic import BaseModel

MEDIA_TYPES = (
    "image_main",
    "image_secondary",
    "video",
    "pdf_manual",
    "pdf_safety",
    "render",
    "icon",
    "other",
)


class MediaCreate(BaseModel):
    sku: str | None = None
    kind: str = "image"
    media_type: str = "other"
    sort_order: int = 0
    url: str
    filename: str | None = None
    no_mostrar_en_b2b: str = "N"
    metadata: dict = {}


class MediaUpdate(BaseModel):
    kind: str | None = None
    media_type: str | None = None
    sort_order: int | None = None
    no_mostrar_en_b2b: str | None = None
    metadata: dict | None = None


class MediaRead(BaseModel):
    id: str
    sku: str | None
    kind: str
    media_type: str
    sort_order: int
    url: str
    filename: str | None
    no_mostrar_en_b2b: str
    metadata_extra: dict
    created_at: datetime

    model_config = {"from_attributes": True}
