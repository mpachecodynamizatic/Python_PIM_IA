from sqlalchemy import String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class Brand(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "brands"

    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    slug: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    website: Mapped[str | None] = mapped_column(String(500), nullable=True)
    logo_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    active: Mapped[bool] = mapped_column(nullable=False, default=True)
