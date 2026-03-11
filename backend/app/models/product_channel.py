from sqlalchemy import Boolean, ForeignKey, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class ProductChannel(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "product_channels"
    __table_args__ = (UniqueConstraint("sku", "channel_id", name="uq_product_channel"),)

    sku: Mapped[str] = mapped_column(
        String(100),
        ForeignKey("products.sku", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    channel_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("channels.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Nombre y descripción específica para el canal (sobreescribe el nombre del catálogo)
    name: Mapped[str | None] = mapped_column(String(500), nullable=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Activación
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Restricciones por país (lista de códigos ISO)
    country_restrictions: Mapped[list] = mapped_column(JSON, nullable=False, default=list, server_default="[]")

    # Campos específicos del canal (precio, condiciones, etc.)
    marketplace_fields: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict, server_default="{}")

    product = relationship("Product", foreign_keys=[sku])
    channel_obj = relationship("Channel", back_populates="product_channels")
