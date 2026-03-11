from typing import Generic, TypeVar

from pydantic import BaseModel

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    size: int
    pages: int


class ErrorDetail(BaseModel):
    detail: str
    code: str | None = None


class MessageResponse(BaseModel):
    message: str
