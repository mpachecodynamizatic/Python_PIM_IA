from sqlalchemy import JSON, ForeignKey, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, UUIDMixin, TimestampMixin


class ExportPreference(UUIDMixin, TimestampMixin, Base):
    __tablename__ = "export_preferences"
    __table_args__ = (UniqueConstraint("user_id", "resource", name="uq_export_pref_user_resource"),)

    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    resource: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    selected_fields: Mapped[list] = mapped_column(
        JSON,
        nullable=False,
        default=list,
        server_default="[]",
    )
