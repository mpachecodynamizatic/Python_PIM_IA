from sqlalchemy import ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin, UUIDMixin


class ExternalTaxonomy(UUIDMixin, TimestampMixin, Base):
    """Catálogo de taxonomías externas (GS1, Amazon, Google Shopping, etc.)."""
    __tablename__ = "external_taxonomies"

    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    provider: Mapped[str] = mapped_column(String(100), nullable=False)  # GS1, Amazon, Google, ...
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    product_mappings = relationship(
        "ProductExternalTaxonomy", back_populates="taxonomy", cascade="all, delete-orphan"
    )


class ProductExternalTaxonomy(UUIDMixin, TimestampMixin, Base):
    """Mapeo SKU ↔ nodo de una taxonomía externa."""
    __tablename__ = "product_external_taxonomies"
    __table_args__ = (UniqueConstraint("sku", "taxonomy_id", name="uq_product_ext_taxonomy"),)

    sku: Mapped[str] = mapped_column(
        String(100),
        ForeignKey("products.sku", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    taxonomy_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("external_taxonomies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    node_code: Mapped[str | None] = mapped_column(String(255), nullable=True)
    node_name: Mapped[str | None] = mapped_column(String(500), nullable=True)
    node_path: Mapped[str | None] = mapped_column(Text, nullable=True)  # breadcrumb

    taxonomy = relationship("ExternalTaxonomy", back_populates="product_mappings")
    product = relationship("Product", foreign_keys=[sku])
