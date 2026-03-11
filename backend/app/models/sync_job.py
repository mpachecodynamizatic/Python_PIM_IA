from datetime import datetime

from sqlalchemy import Boolean, DateTime, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class SyncJob(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "sync_jobs"

    channel: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="queued",
    )
    filters: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict, server_default="{}")
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    metrics: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict, server_default="{}")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # --- Retry fields ---
    retry_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    max_retries: Mapped[int] = mapped_column(Integer, nullable=False, default=3, server_default="3")
    next_retry_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    # --- Scheduling fields ---
    scheduled: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False, server_default="0")
    cron_expression: Mapped[str | None] = mapped_column(String(100), nullable=True)
    next_run_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
