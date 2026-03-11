from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, JSON, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDMixin


class ProductSyncHistory(UUIDMixin, Base):
    """Registra el estado de publicación de cada SKU en cada canal."""

    __tablename__ = "product_sync_history"

    sku: Mapped[str] = mapped_column(
        String(100),
        ForeignKey("products.sku", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    channel: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    job_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("sync_jobs.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="published",
    )
    detail: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict, server_default="{}")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    synced_at: Mapped[datetime] = mapped_column(
        DateTime,
        server_default=func.now(),
        nullable=False,
    )
