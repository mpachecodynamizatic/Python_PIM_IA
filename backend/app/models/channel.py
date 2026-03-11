from sqlalchemy import Boolean, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class Channel(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "channels"

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    code: Mapped[str] = mapped_column(String(50), unique=True, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Transport configuration
    # connection_type: "ftp" | "ssh" | "http_post" | None
    connection_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
    connection_config: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict, server_default="{}")

    product_channels = relationship("ProductChannel", back_populates="channel_obj", cascade="all, delete-orphan")
