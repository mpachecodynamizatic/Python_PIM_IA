from datetime import datetime

from sqlalchemy import Boolean, DateTime, JSON, String, Text, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDMixin


class PimResourceMapping(UUIDMixin, Base):
    """
    Almacena configuración de mapeo de campos para importación desde PIM externo.

    Cada recurso (products, categories, brands, etc.) tiene su propia configuración
    que define cómo mapear los campos de la API externa a los campos del modelo interno.
    """
    __tablename__ = "pim_resource_mappings"
    __table_args__ = (UniqueConstraint("resource", name="uq_pim_resource"),)

    # Identificador del recurso (products, categories, brands, suppliers, etc.)
    resource: Mapped[str] = mapped_column(String(50), nullable=False, index=True)

    # Solo una config activa por recurso
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)

    # Array JSON de mapeos campo a campo
    # Estructura: [{"source_field": "titulo", "target_field": "name", "transform": "strip", ...}]
    mappings: Mapped[list] = mapped_column(JSON, nullable=False, default=list, server_default="[]")

    # Valores por defecto para campos no mapeados
    # Estructura: {"status": "draft", "brand": "SV"}
    defaults: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict, server_default="{}")

    # Configuraciones de transformación globales
    # Estructura: {"status_map": {"ACTIVA": "approved"}, "brand_code_map": {"Aspes": "AS"}}
    transform_config: Mapped[dict] = mapped_column(JSON, nullable=False, default=dict, server_default="{}")

    # Usuario que creó la configuración
    created_by: Mapped[str] = mapped_column(String(255), nullable=False)

    # Notas/documentación del usuario
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, server_default=func.now(), onupdate=func.now(), nullable=False
    )
