from sqlalchemy import Boolean, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class ProductCompliance(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "product_compliance"

    sku: Mapped[str] = mapped_column(
        String(100),
        ForeignKey("products.sku", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    # Certificaciones (lista de strings: CE, RoHS, REACH, FCC, UL, ...)
    certifications: Mapped[list] = mapped_column(JSON, nullable=False, default=list, server_default="[]")

    # Fichas técnicas / seguridad
    technical_sheet_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    safety_sheet_url: Mapped[str | None] = mapped_column(String(1000), nullable=True)

    # Avisos legales / restricciones
    legal_warnings: Mapped[str | None] = mapped_column(Text, nullable=True)
    min_age: Mapped[int | None] = mapped_column(Integer, nullable=True)

    # Trazabilidad
    has_lot_traceability: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    has_expiry_date: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    # Datos adicionales de conformidad
    country_of_origin: Mapped[str | None] = mapped_column(String(3), nullable=True)  # ISO 3166-1 alpha-2/3
    hs_code: Mapped[str | None] = mapped_column(String(20), nullable=True)  # Código arancelario

    product = relationship("Product", foreign_keys=[sku])
