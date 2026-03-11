from datetime import datetime
from pydantic import BaseModel, model_validator


# ── Channel catalog ───────────────────────────────────────────────────────────

class ChannelCreate(BaseModel):
    name: str
    code: str
    description: str | None = None
    active: bool = True
    connection_type: str | None = None  # "ftp" | "ssh" | "http_post"
    connection_config: dict = {}


class ChannelUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    active: bool | None = None
    connection_type: str | None = None
    connection_config: dict | None = None


class ChannelRead(BaseModel):
    id: str
    name: str
    code: str
    description: str | None = None
    active: bool
    connection_type: str | None = None
    connection_config: dict = {}
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ── ProductChannel (producto ↔ canal) ─────────────────────────────────────────

class ProductChannelUpsert(BaseModel):
    channel_id: str
    name: str | None = None
    description: str | None = None
    active: bool = True
    country_restrictions: list = []
    marketplace_fields: dict = {}


class ProductChannelRead(BaseModel):
    id: str
    sku: str
    channel_id: str
    channel: ChannelRead | None = None
    name: str | None = None
    description: str | None = None
    active: bool = True
    country_restrictions: list = []
    marketplace_fields: dict = {}
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    @model_validator(mode="before")
    @classmethod
    def _map_channel_obj(cls, data):
        """Map SQLAlchemy relationship channel_obj → channel field."""
        if hasattr(data, "channel_obj"):
            return {
                "id": data.id,
                "sku": data.sku,
                "channel_id": data.channel_id,
                "channel": data.channel_obj,
                "name": data.name,
                "description": data.description,
                "active": data.active,
                "country_restrictions": data.country_restrictions,
                "marketplace_fields": data.marketplace_fields,
                "created_at": data.created_at,
                "updated_at": data.updated_at,
            }
        return data
