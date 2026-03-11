from sqlalchemy import JSON, String, Text, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class MediaAsset(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "media_assets"

    sku: Mapped[str | None] = mapped_column(
        String(100),
        ForeignKey("products.sku"),
        nullable=True,
        index=True,
    )
    kind: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="image",
    )
    url: Mapped[str] = mapped_column(Text, nullable=False)
    filename: Mapped[str | None] = mapped_column(String(500), nullable=True)
    no_mostrar_en_b2b: Mapped[str] = mapped_column(
        String(1),
        nullable=False,
        default="N",
        server_default="N",
    )
    metadata_extra: Mapped[dict] = mapped_column(
        "metadata",
        JSON,
        nullable=False,
        default=dict,
        server_default="{}",
    )

    product = relationship("Product", back_populates="media")
