from datetime import datetime

from pydantic import BaseModel, Field


class ProductCommentCreate(BaseModel):
    body: str = Field(..., min_length=1)
    mentions: dict | None = None  # e.g. {"user_ids": ["uuid1", "uuid2"]}


class ProductCommentRead(BaseModel):
    id: str
    sku: str
    user_id: str
    author_name: str
    body: str
    mentions: dict | None = None
    version_id: str | None = None
    created_at: datetime
