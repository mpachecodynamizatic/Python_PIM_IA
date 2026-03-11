from __future__ import annotations

from app.connectors.base import BaseConnector
from app.connectors.csv_connector import CsvConnector
from app.connectors.http_connector import HttpConnector

_REGISTRY: dict[str, type[BaseConnector]] = {
    "csv": CsvConnector,
    "http": HttpConnector,
}


def get_connector(channel: str) -> BaseConnector:
    cls = _REGISTRY.get(channel)
    if cls is None:
        raise ValueError(f"Canal no soportado: {channel}. Canales disponibles: {list(_REGISTRY)}")
    return cls()


def list_channels() -> list[str]:
    return list(_REGISTRY)
