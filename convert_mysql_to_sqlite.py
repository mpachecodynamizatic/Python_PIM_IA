#!/usr/bin/env python3
"""
Convierte el dump MySQL a una base de datos SQLite.
"""
import re
import sqlite3
from pathlib import Path

def convert_mysql_to_sqlite(mysql_file: str, sqlite_file: str):
    """Convierte un dump MySQL a SQLite."""

    print(f"Leyendo archivo MySQL: {mysql_file}")
    with open(mysql_file, 'r', encoding='utf-8', errors='ignore') as f:
        content = f.read()

    print("Limpiando sintaxis MySQL...")

    # Eliminar comentarios específicos de MySQL
    content = re.sub(r'/\*!.*?\*/;', '', content, flags=re.DOTALL)
    content = re.sub(r'/\*!.*?\*/', '', content, flags=re.DOTALL)

    # Eliminar comandos MySQL específicos
    content = re.sub(r'SET .*?;', '', content)
    content = re.sub(r'CREATE DATABASE.*?;', '', content, flags=re.IGNORECASE)
    content = re.sub(r'USE .*?;', '', content, flags=re.IGNORECASE)
    content = re.sub(r'LOCK TABLES .*?;', '', content, flags=re.IGNORECASE)
    content = re.sub(r'UNLOCK TABLES.*?;', '', content, flags=re.IGNORECASE)

    # Convertir tipos de datos MySQL a SQLite
    content = re.sub(r'\bint\(\d+\)', 'INTEGER', content, flags=re.IGNORECASE)
    content = re.sub(r'\btinyint\(\d+\)', 'INTEGER', content, flags=re.IGNORECASE)
    content = re.sub(r'\bsmallint\(\d+\)', 'INTEGER', content, flags=re.IGNORECASE)
    content = re.sub(r'\bmediumint\(\d+\)', 'INTEGER', content, flags=re.IGNORECASE)
    content = re.sub(r'\bbigint\(\d+\)', 'INTEGER', content, flags=re.IGNORECASE)
    content = re.sub(r'\bdatetime\b', 'TEXT', content, flags=re.IGNORECASE)
    content = re.sub(r'\btimestamp\b', 'TEXT', content, flags=re.IGNORECASE)
    content = re.sub(r'\btext\b', 'TEXT', content, flags=re.IGNORECASE)
    content = re.sub(r'\blongtext\b', 'TEXT', content, flags=re.IGNORECASE)
    content = re.sub(r'\bmediumtext\b', 'TEXT', content, flags=re.IGNORECASE)
    content = re.sub(r'\bdouble\b', 'REAL', content, flags=re.IGNORECASE)
    content = re.sub(r'\bfloat\b', 'REAL', content, flags=re.IGNORECASE)
    content = re.sub(r'\bdecimal\([^\)]+\)', 'REAL', content, flags=re.IGNORECASE)

    # Eliminar opciones específicas de MySQL en CREATE TABLE
    content = re.sub(r'CHARACTER SET [^\s]+', '', content)
    content = re.sub(r'COLLATE [^\s]+', '', content)
    content = re.sub(r'ENGINE=\w+', '', content)
    content = re.sub(r'AUTO_INCREMENT=\d+', '', content)
    content = re.sub(r'DEFAULT CHARSET=\w+', '', content)
    content = re.sub(r'COMMENT=\'[^\']*\'', '', content)

    # Eliminar AUTO_INCREMENT (SQLite usa INTEGER PRIMARY KEY automático)
    content = re.sub(r'\s+AUTO_INCREMENT\b', '', content, flags=re.IGNORECASE)

    # Eliminar UNIQUE KEY, KEY, CONSTRAINT que SQLite maneja diferente
    # Mantener solo PRIMARY KEY y FOREIGN KEY básicas
    content = re.sub(r',\s*UNIQUE KEY [^,\)]+', '', content)
    content = re.sub(r',\s*KEY [^,\)]+', '', content)
    content = re.sub(r',\s*CONSTRAINT [^,\)]+', '', content)

    # Eliminar opciones DEFAULT CURRENT_TIMESTAMP ON UPDATE
    content = re.sub(r'DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP',
                     'DEFAULT CURRENT_TIMESTAMP', content)

    # Eliminar líneas en blanco múltiples
    content = re.sub(r'\n\s*\n\s*\n', '\n\n', content)

    # Dividir en statements individuales
    statements = []
    current = []
    in_insert = False

    for line in content.split('\n'):
        line = line.strip()

        if not line or line.startswith('--'):
            continue

        if line.upper().startswith('INSERT INTO'):
            in_insert = True

        current.append(line)

        if line.endswith(';'):
            stmt = ' '.join(current)
            if stmt and not stmt.startswith('--'):
                statements.append(stmt)
            current = []
            in_insert = False

    print(f"Creando base de datos SQLite: {sqlite_file}")

    # Crear base de datos SQLite
    if Path(sqlite_file).exists():
        Path(sqlite_file).unlink()

    conn = sqlite3.connect(sqlite_file)
    cursor = conn.cursor()

    # Desactivar foreign keys temporalmente para la importación
    cursor.execute("PRAGMA foreign_keys = OFF")

    success_count = 0
    error_count = 0

    print("Ejecutando statements SQL...")
    for i, stmt in enumerate(statements):
        try:
            cursor.execute(stmt)
            success_count += 1
            if (i + 1) % 100 == 0:
                print(f"  Procesados {i + 1}/{len(statements)} statements...")
        except sqlite3.Error as e:
            error_count += 1
            if error_count <= 10:  # Solo mostrar los primeros 10 errores
                print(f"  Error en statement {i + 1}: {str(e)[:100]}")

    conn.commit()

    # Reactivar foreign keys
    cursor.execute("PRAGMA foreign_keys = ON")

    # Obtener estadísticas
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cursor.fetchall()

    print(f"\nConversion completada!")
    print(f"   - Statements exitosos: {success_count}")
    print(f"   - Statements con error: {error_count}")
    print(f"   - Tablas creadas: {len(tables)}")
    print(f"\nTablas en la base de datos:")

    for table in tables:
        table_name = table[0]
        cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
        count = cursor.fetchone()[0]
        print(f"   - {table_name}: {count} registros")

    conn.close()
    print(f"\nBase de datos creada: {sqlite_file}")


if __name__ == "__main__":
    mysql_file = "backup_bd_pim_marce.sql"
    sqlite_file = "datosejemplo.db"

    convert_mysql_to_sqlite(mysql_file, sqlite_file)
