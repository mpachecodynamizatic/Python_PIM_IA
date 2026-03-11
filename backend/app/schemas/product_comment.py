from datetime import datetime

from pydantic import BaseModel, Field


class ProductCommentCreate(BaseModel):
    body: str = Field(..., min_length=1)
    mentions: dict | None = None  # e.g. {"user_ids": ["uuid1", "uuid2"]}
    parent_id: str | None = None
    tags: list[str] | None = None  # e.g. ["pendiente revision", "aprobado"]


class ProductCommentUpdate(BaseModel):
    body: str | None = Field(default=None, min_length=1)
    tags: list[str] | None = None


class ProductCommentRead(BaseModel):
    id: str
    sku: str
    user_id: str
    author_name: str
    body: str
    mentions: dict | None = None
    version_id: str | None = None
    parent_id: str | None = None
    reply_count: int = 0
    tags: list[str] | None = None
    created_at: datetime
    updated_at: datetime | None = None
