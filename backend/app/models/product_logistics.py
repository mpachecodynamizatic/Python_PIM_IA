from sqlalchemy import Boolean, Float, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class ProductLogistics(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "product_logistics"

    sku: Mapped[str] = mapped_column(
        String(100),
        ForeignKey("products.sku", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    # Unidades de medida
    base_unit: Mapped[str | None] = mapped_column(String(50), nullable=True)  # pieza, kg, litro...
    box_units: Mapped[int | None] = mapped_column(Integer, nullable=True)       # unidades por caja
    pallet_boxes: Mapped[int | None] = mapped_column(Integer, nullable=True)    # cajas por palet
    pallet_units: Mapped[int | None] = mapped_column(Integer, nullable=True)    # unidades por palet

    # Dimensiones (mm) por unidad de venta
    height_mm: Mapped[float | None] = mapped_column(Float, nullable=True)
    width_mm: Mapped[float | None] = mapped_column(Float, nullable=True)
    depth_mm: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Peso (gramos)
    weight_gross_g: Mapped[float | None] = mapped_column(Float, nullable=True)
    weight_net_g: Mapped[float | None] = mapped_column(Float, nullable=True)

    # Embalaje / logística
    stackable: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    packaging_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    transport_conditions: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Mercancía peligrosa ADR
    adr: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    adr_class: Mapped[str | None] = mapped_column(String(20), nullable=True)
    adr_un_number: Mapped[str | None] = mapped_column(String(10), nullable=True)
    adr_details: Mapped[str | None] = mapped_column(Text, nullable=True)

    product = relationship("Product", foreign_keys=[sku])
