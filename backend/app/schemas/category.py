from datetime import datetime

from pydantic import BaseModel


class CategoryCreate(BaseModel):
    name: str
    slug: str
    description: str | None = None
    parent_id: str | None = None
    attribute_schema: dict = {}
    sort_order: int = 0


class CategoryUpdate(BaseModel):
    name: str | None = None
    slug: str | None = None
    description: str | None = None
    parent_id: str | None = None
    attribute_schema: dict | None = None
    sort_order: int | None = None


class CategoryRead(BaseModel):
    id: str
    name: str
    slug: str
    description: str | None
    parent_id: str | None
    attribute_schema: dict
    sort_order: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CategoryTree(CategoryRead):
    children: list["CategoryTree"] = []
