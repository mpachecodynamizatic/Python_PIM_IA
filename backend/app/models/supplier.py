from sqlalchemy import Boolean, ForeignKey, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class Supplier(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "suppliers"

    name: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    code: Mapped[str | None] = mapped_column(String(50), unique=True, nullable=True)
    country: Mapped[str | None] = mapped_column(String(3), nullable=True)  # ISO 3166-1
    contact_email: Mapped[str | None] = mapped_column(String(255), nullable=True)
    contact_phone: Mapped[str | None] = mapped_column(String(50), nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    product_links = relationship("ProductSupplier", back_populates="supplier", cascade="all, delete-orphan")


class ProductSupplier(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "product_suppliers"
    __table_args__ = (UniqueConstraint("sku", "supplier_id", name="uq_product_supplier"),)

    sku: Mapped[str] = mapped_column(
        String(100),
        ForeignKey("products.sku", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    supplier_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("suppliers.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    is_primary: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    supplier_sku: Mapped[str | None] = mapped_column(String(100), nullable=True)
    moq: Mapped[int | None] = mapped_column(Integer, nullable=True)        # Minimum order quantity
    lead_time_days: Mapped[int | None] = mapped_column(Integer, nullable=True)
    country_of_origin: Mapped[str | None] = mapped_column(String(3), nullable=True)
    purchase_price: Mapped[float | None] = mapped_column(nullable=True)
    currency: Mapped[str | None] = mapped_column(String(3), nullable=True)  # ISO 4217
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    supplier = relationship("Supplier", back_populates="product_links")
    product = relationship("Product", foreign_keys=[sku])
