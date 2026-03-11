from datetime import datetime

from pydantic import BaseModel


class MediaCreate(BaseModel):
    sku: str | None = None
    kind: str = "image"
    url: str
    filename: str | None = None
    no_mostrar_en_b2b: str = "N"
    metadata: dict = {}


class MediaRead(BaseModel):
    id: str
    sku: str | None
    kind: str
    url: str
    filename: str | None
    no_mostrar_en_b2b: str
    metadata_extra: dict
    created_at: datetime

    model_config = {"from_attributes": True}
