from __future__ import annotations

import abc
from dataclasses import dataclass, field

from sqlalchemy.ext.asyncio import AsyncSession


@dataclass
class ConnectorResult:
    total_products: int = 0
    exported: int = 0
    skipped: int = 0
    errors: list[str] = field(default_factory=list)

    def to_metrics(self) -> dict:
        return {
            "total_products": self.total_products,
            "exported": self.exported,
            "skipped": self.skipped,
            "errors": self.errors,
        }


class BaseConnector(abc.ABC):
    """Interfaz base para conectores de publicación multicanal."""

    channel: str

    @abc.abstractmethod
    async def run(self, db: AsyncSession, filters: dict) -> ConnectorResult:
        """Ejecuta la sincronización y devuelve métricas."""
        ...
