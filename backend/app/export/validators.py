"""
Value coercion and validation for Excel import.
"""
from __future__ import annotations

import json
import re
from datetime import date, datetime
from typing import Any

from app.export.configs import ExportField


def coerce_value(raw: Any, field: ExportField) -> tuple[Any, str | None]:
    """Coerce a raw Excel cell value to the field's declared type.

    Returns (coerced_value, None)      on success
            (None,          error_msg) on failure
    """
    # Normalise empty / None
    if raw is None or (isinstance(raw, str) and raw.strip() == ""):
        if field.required:
            return None, "Campo obligatorio (valor vacío o nulo)"
        return None, None

    if isinstance(raw, str):
        raw = raw.strip()

    match field.type:
        case "str":
            value = str(raw)
            if field.max_length and len(value) > field.max_length:
                return None, f"Longitud maxima {field.max_length} caracteres (actual: {len(value)})"
            return value, None

        case "int":
            try:
                return int(float(str(raw))), None
            except (ValueError, TypeError):
                return None, f"Debe ser un numero entero (valor actual: '{raw}')"

        case "float":
            try:
                return float(str(raw)), None
            except (ValueError, TypeError):
                return None, f"Debe ser un numero decimal (valor actual: '{raw}')"

        case "bool":
            raw_lower = str(raw).lower().strip()
            if raw_lower in ("1", "true", "si", "sí", "yes"):
                return True, None
            if raw_lower in ("0", "false", "no"):
                return False, None
            return None, f"Debe ser verdadero/falso (valor actual: '{raw}', use: 1/0, true/false, si/no)"

        case "date":
            if isinstance(raw, (date, datetime)):
                return raw.date() if isinstance(raw, datetime) else raw, None
            s = str(raw)
            if re.match(r"\d{4}-\d{2}-\d{2}", s):
                try:
                    return date.fromisoformat(s[:10]), None
                except ValueError:
                    pass
            if re.match(r"\d{2}/\d{2}/\d{4}", s):
                try:
                    return datetime.strptime(s, "%d/%m/%Y").date(), None
                except ValueError:
                    pass
            return None, f"Formato de fecha no valido (valor: '{raw}', use: YYYY-MM-DD o DD/MM/YYYY)"

        case "datetime":
            if isinstance(raw, datetime):
                return raw, None
            if isinstance(raw, date):
                return datetime(raw.year, raw.month, raw.day), None
            s = str(raw)
            for fmt in ("%Y-%m-%dT%H:%M:%S", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d"):
                try:
                    return datetime.strptime(s, fmt), None
                except ValueError:
                    pass
            # ISO with timezone / milliseconds
            try:
                return datetime.fromisoformat(s), None
            except ValueError:
                pass
            return None, f"Formato de datetime no valido (valor: '{raw}', use: ISO 8601 o YYYY-MM-DD HH:MM)"

        case "enum":
            val = str(raw)
            if field.choices and val not in field.choices:
                return None, f"Valor '{val}' no es valido. Valores permitidos: {', '.join(field.choices)}"
            return val, None

        case "json":
            if isinstance(raw, (dict, list)):
                return raw, None
            if isinstance(raw, str):
                try:
                    return json.loads(raw), None
                except json.JSONDecodeError as e:
                    return None, f"JSON invalido (valor: '{raw[:50]}...', error: {str(e)})"
            return None, f"Valor '{raw}' no es JSON valido (debe ser un objeto o array JSON)"

        case _:
            return str(raw), None


def serialize_value(value: Any, field_type: str) -> Any:
    """Serialize an ORM value to an Excel-compatible cell value."""
    if value is None:
        return ""
    if field_type == "json":
        return json.dumps(value, ensure_ascii=False, default=str)
    if field_type == "datetime" and isinstance(value, datetime):
        return value.strftime("%Y-%m-%d %H:%M")
    if field_type == "date" and isinstance(value, date):
        return value.isoformat()
    if field_type == "bool":
        return "true" if value else "false"
    return value
