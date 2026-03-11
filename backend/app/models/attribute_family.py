from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDMixin, TimestampMixin


class AttributeFamily(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "attribute_families"

    code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Asociación opcional a una categoría para uso por defecto
    category_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    attributes = relationship("AttributeDefinition", back_populates="family", cascade="all, delete-orphan")


class AttributeDefinition(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "attribute_definitions"

    family_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("attribute_families.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    code: Mapped[str] = mapped_column(String(100), nullable=False)
    label: Mapped[str] = mapped_column(String(255), nullable=False)
    type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="string",  # string, number, boolean, enum
    )
    required: Mapped[bool] = mapped_column(default=False, nullable=False)
    options_json: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )  # JSON serializado con opciones para enums u otra metainformación

    family = relationship("AttributeFamily", back_populates="attributes")
