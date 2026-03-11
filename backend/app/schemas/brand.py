from datetime import datetime

from pydantic import BaseModel


class BrandCreate(BaseModel):
    name: str
    slug: str
    description: str | None = None
    website: str | None = None
    logo_url: str | None = None
    active: bool = True


class BrandUpdate(BaseModel):
    name: str | None = None
    slug: str | None = None
    description: str | None = None
    website: str | None = None
    logo_url: str | None = None
    active: bool | None = None


class BrandRead(BaseModel):
    id: str
    name: str
    slug: str
    description: str | None
    website: str | None
    logo_url: str | None
    active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
