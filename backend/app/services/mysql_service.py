"""Servicio de conexión e introspección de base de datos MySQL."""
import asyncio
import logging
from datetime import date, datetime, time

logger = logging.getLogger(__name__)


# ── Sync helpers (ejecutados en hilo separado) ─────────────────────────────────

def _get_connection(host: str, port: int, user: str, password: str, database: str):
    """Crea una conexión MySQL síncrona."""
    try:
        import mysql.connector
    except ImportError:
        raise RuntimeError(
            "mysql-connector-python no está instalado. Ejecuta: pip install mysql-connector-python"
        )
    return mysql.connector.connect(
        host=host,
        port=port,
        user=user,
        password=password,
        database=database,
        connection_timeout=10,
        charset="utf8mb4",
        use_unicode=True,
    )


def _serialize_value(v):
    """Convierte valores no-JSON-serializables a tipos primitivos."""
    if v is None:
        return None
    if isinstance(v, (bool, int, float)):
        return v
    if isinstance(v, (datetime, date, time)):
        return str(v)
    if isinstance(v, bytes):
        try:
            return v.decode("utf-8")
        except Exception:
            return v.hex()
    return str(v)


def _serialize_row(row: dict) -> dict:
    return {k: _serialize_value(v) for k, v in row.items()}


def _test_connection_sync(host, port, user, password, database) -> dict:
    try:
        conn = _get_connection(host, port, user, password, database)
        cursor = conn.cursor()
        cursor.execute("SELECT VERSION()")
        version = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        return {"success": True, "version": version, "database": database, "host": host}
    except Exception as e:
        return {"success": False, "error": str(e)}


def _list_tables_sync(host, port, user, password, database) -> list[dict]:
    conn = _get_connection(host, port, user, password, database)
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT
            TABLE_NAME AS table_name,
            ENGINE AS engine,
            IFNULL(TABLE_ROWS, 0) AS row_count,
            IFNULL(TABLE_COMMENT, '') AS table_comment
        FROM information_schema.TABLES
        WHERE TABLE_SCHEMA = %s AND TABLE_TYPE = 'BASE TABLE'
        ORDER BY TABLE_NAME
        """,
        (database,),
    )
    tables = [dict(r) for r in cursor.fetchall()]
    cursor.close()
    conn.close()
    return tables


def _get_table_columns_sync(host, port, user, password, database, table_name) -> list[dict]:
    conn = _get_connection(host, port, user, password, database)
    cursor = conn.cursor(dictionary=True)
    cursor.execute(
        """
        SELECT
            COLUMN_NAME    AS column_name,
            DATA_TYPE      AS data_type,
            COLUMN_TYPE    AS column_type,
            IS_NULLABLE    AS is_nullable,
            COLUMN_DEFAULT AS column_default,
            COLUMN_KEY     AS column_key,
            IFNULL(COLUMN_COMMENT, '') AS column_comment
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = %s AND TABLE_NAME = %s
        ORDER BY ORDINAL_POSITION
        """,
        (database, table_name),
    )
    columns = [dict(r) for r in cursor.fetchall()]
    cursor.close()
    conn.close()
    return columns


def _get_sample_data_sync(host, port, user, password, database, table_name, limit) -> list[dict]:
    conn = _get_connection(host, port, user, password, database)
    cursor = conn.cursor(dictionary=True)
    cursor.execute(f"SELECT * FROM `{table_name}` LIMIT %s", (limit,))
    rows = [_serialize_row(dict(r)) for r in cursor.fetchall()]
    cursor.close()
    conn.close()
    return rows


def _fetch_all_rows_sync(host, port, user, password, database, table_name, where_clause=None) -> list[dict]:
    conn = _get_connection(host, port, user, password, database)
    cursor = conn.cursor(dictionary=True)

    # Construir query con WHERE opcional
    query = f"SELECT * FROM `{table_name}`"
    if where_clause:
        query += f" WHERE {where_clause}"

    cursor.execute(query)
    rows = [_serialize_row(dict(r)) for r in cursor.fetchall()]
    cursor.close()
    conn.close()
    return rows


# ── Async wrappers ─────────────────────────────────────────────────────────────

async def test_connection(host: str, port: int, user: str, password: str, database: str) -> dict:
    return await asyncio.to_thread(_test_connection_sync, host, port, user, password, database)


async def list_tables(host: str, port: int, user: str, password: str, database: str) -> list[dict]:
    return await asyncio.to_thread(_list_tables_sync, host, port, user, password, database)


async def get_table_columns(
    host: str, port: int, user: str, password: str, database: str, table_name: str
) -> list[dict]:
    return await asyncio.to_thread(
        _get_table_columns_sync, host, port, user, password, database, table_name
    )


async def get_sample_data(
    host: str, port: int, user: str, password: str, database: str, table_name: str, limit: int = 3
) -> list[dict]:
    return await asyncio.to_thread(
        _get_sample_data_sync, host, port, user, password, database, table_name, limit
    )


async def fetch_all_rows(
    host: str, port: int, user: str, password: str, database: str, table_name: str, where_clause: str | None = None
) -> list[dict]:
    return await asyncio.to_thread(
        _fetch_all_rows_sync, host, port, user, password, database, table_name, where_clause
    )
