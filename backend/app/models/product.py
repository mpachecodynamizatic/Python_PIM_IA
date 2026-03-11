import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, JSON, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Product(Base):
    __tablename__ = "products"

    sku: Mapped[str] = mapped_column(String(100), primary_key=True)
    brand: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="draft",
        index=True,
    )
    category_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("categories.id"),
        nullable=False,
        index=True,
    )
    family_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("attribute_families.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    seo: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict, server_default="{}")
    attributes: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict, server_default="{}")
    created_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )

    category = relationship("Category", back_populates="products")
    translations = relationship("ProductI18n", back_populates="product", cascade="all, delete-orphan")
    media = relationship("MediaAsset", back_populates="product", cascade="all, delete-orphan")


class ProductI18n(Base):
    __tablename__ = "product_i18n"
    __table_args__ = (UniqueConstraint("sku", "locale", name="uq_product_locale"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    sku: Mapped[str] = mapped_column(
        String(100),
        ForeignKey("products.sku", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    locale: Mapped[str] = mapped_column(String(10), nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    description_rich: Mapped[dict | None] = mapped_column(JSON, nullable=True)

    product = relationship("Product", back_populates="translations")
