from sqlalchemy import Boolean, Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, UUIDMixin, TimestampMixin


class QualityRuleSet(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "quality_rule_sets"

    name: Mapped[str] = mapped_column(String(255), nullable=False, unique=True, index=True)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)

    rules = relationship("QualityRule", back_populates="rule_set", cascade="all, delete-orphan")


class QualityRule(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "quality_rules"

    rule_set_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("quality_rule_sets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    # Dimension a la que aplica: brand, category, seo, attributes, media, i18n, overall, etc.
    dimension: Mapped[str] = mapped_column(String(50), nullable=False)
    # Peso relativo de la dimensión en el cálculo del overall.
    weight: Mapped[float] = mapped_column(Float, nullable=False, default=1.0)
    # Umbral mínimo de score (0.0 – 1.0) para considerar que la dimensión cumple.
    min_score: Mapped[float] = mapped_column(Float, nullable=False, default=0.0)
    # Condición opcional: solo aplica si el producto tiene este estado.
    required_status: Mapped[str | None] = mapped_column(String(20), nullable=True)
    # Ámbito opcional: solo aplica a productos de esta categoría.
    scope_category_id: Mapped[str | None] = mapped_column(
        String(36),
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
    )

    rule_set = relationship("QualityRuleSet", back_populates="rules")

