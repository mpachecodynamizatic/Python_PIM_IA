from sqlalchemy import ForeignKey, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class ProductComment(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "product_comments"

    sku: Mapped[str] = mapped_column(
        String(100),
        ForeignKey("products.sku", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    version_id: Mapped[str | None] = mapped_column(
        String(36), nullable=True, index=True,
    )
    parent_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("product_comments.id", ondelete="CASCADE"),
        nullable=True,
        index=True,
    )
    body: Mapped[str] = mapped_column(Text, nullable=False)
    mentions: Mapped[dict | None] = mapped_column(JSON, nullable=True)  # e.g. {"user_ids": ["..."]}
    tags: Mapped[list | None] = mapped_column(JSON, nullable=True)  # e.g. ["pendiente revision", "aprobado"]
