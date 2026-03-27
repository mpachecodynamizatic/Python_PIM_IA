#!/usr/bin/env python3
"""
Importa el backup MySQL a una nueva base de datos llamada 'datosejemplo'.
"""
import re
import sys

try:
    import mysql.connector
except ImportError:
    print("ERROR: mysql-connector-python no está instalado")
    print("Instalando mysql-connector-python...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "mysql-connector-python"])
    import mysql.connector

def create_database_and_import(
    host: str = "localhost",
    user: str = "root",
    password: str = None,
    database: str = "datosejemplo",
    sql_file: str = "backup_bd_pim_marce.sql"
):
    """Crea la base de datos e importa el backup."""

    print(f"Conectando a MySQL en {host}...")

    # Intentar primero sin contraseña (común en desarrollo)
    passwords_to_try = []
    if password is not None:
        passwords_to_try.append(password)
    else:
        # Intentar primero sin contraseña, luego vacía, luego 'root'
        passwords_to_try = ["", "root", "password"]

    conn = None
    last_error = None

    for pwd in passwords_to_try:
        try:
            # Conectar a MySQL (sin especificar base de datos)
            conn = mysql.connector.connect(
                host=host,
                user=user,
                password=pwd
            )
            cursor = conn.cursor()
            print(f"Conexión establecida correctamente" + (f" (password: {'***' if pwd else '[sin contraseña]'})" if len(passwords_to_try) > 1 else ""))
            break  # Conexión exitosa
        except mysql.connector.Error as e:
            last_error = e
            continue

    if conn is None:
        print(f"\nERROR: No se pudo conectar con ninguna de las contraseñas probadas")
        print(f"Último error: {last_error.msg if last_error else 'desconocido'}")
        print(f"\nPor favor, especifica la contraseña correcta editando el script")
        print(f"o ejecuta:")
        print(f"  python import_mysql_backup.py")
        print(f"Y edita la variable PASSWORD en el script con tu contraseña")
        sys.exit(1)

    try:

        # Verificar si la base de datos ya existe
        cursor.execute(f"SHOW DATABASES LIKE '{database}'")
        exists = cursor.fetchone()

        if exists:
            print(f"\nADVERTENCIA: La base de datos '{database}' ya existe")
            print(f"Eliminando y recreando...")
            cursor.execute(f"DROP DATABASE {database}")
            print(f"Base de datos eliminada")

        # Crear base de datos
        print(f"\nCreando base de datos '{database}'...")
        cursor.execute(f"CREATE DATABASE {database} CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
        print(f"Base de datos '{database}' creada correctamente")

        # Usar la nueva base de datos
        cursor.execute(f"USE {database}")

        # Desactivar checks temporalmente para facilitar importación
        cursor.execute("SET FOREIGN_KEY_CHECKS=0")
        cursor.execute("SET sql_mode = ''")

        # Leer archivo SQL
        print(f"\nLeyendo archivo SQL: {sql_file}")
        with open(sql_file, 'r', encoding='utf-8', errors='ignore') as f:
            sql_content = f.read()

        # Reemplazar collation de MySQL 8.x por uno compatible con MariaDB
        sql_content = sql_content.replace('utf8mb4_0900_ai_ci', 'utf8mb4_unicode_ci')
        sql_content = sql_content.replace('utf8_general_ci', 'utf8_unicode_ci')
        print(f"  Collations convertidos a versión compatible con MariaDB")

        # Separar statements por punto y coma
        # Esto es simplificado - un parser real sería más robusto
        statements = []
        current_statement = []

        for line in sql_content.split('\n'):
            # Ignorar comentarios
            if line.strip().startswith('--'):
                continue

            current_statement.append(line)

            # Si la línea termina con ; (y no está dentro de comillas)
            if line.strip().endswith(';'):
                stmt = '\n'.join(current_statement).strip()
                if stmt and not stmt.startswith('/*'):
                    # Filtrar comandos que pueden causar problemas
                    stmt_upper = stmt.upper()
                    skip_keywords = ['/*!40', 'CREATE DATABASE', 'USE `', 'LOCK TABLES', 'UNLOCK TABLES']
                    if not any(x in stmt_upper for x in skip_keywords):
                        statements.append(stmt)
                current_statement = []

        print(f"Archivo leído: {len(statements)} statements encontrados")

        # Ejecutar statements
        print(f"\nImportando datos...")
        success_count = 0
        error_count = 0
        tables_created = []
        packet_too_big_errors = 0
        connection_lost_errors = 0

        for i, statement in enumerate(statements):
            try:
                # Mostrar progreso y commit cada 25 statements
                if (i + 1) % 25 == 0:
                    print(f"  Procesados {i + 1}/{len(statements)} statements...")
                    # Commit incremental cada 25 statements para evitar pérdida de conexión
                    try:
                        conn.commit()
                    except mysql.connector.Error as commit_err:
                        print(f"  Warning: Error en commit incremental: {commit_err.msg}")

                # Detectar creación de tablas
                if statement.upper().strip().startswith('CREATE TABLE'):
                    match = re.search(r'CREATE TABLE\s+`?(\w+)`?', statement, re.IGNORECASE)
                    if match:
                        table_name = match.group(1)
                        tables_created.append(table_name)
                        print(f"  Creando tabla: {table_name}")

                cursor.execute(statement)
                success_count += 1

            except mysql.connector.Error as e:
                error_count += 1

                # Contar tipos específicos de errores
                if 'max_allowed_packet' in str(e.msg).lower():
                    packet_too_big_errors += 1
                elif 'lost connection' in str(e.msg).lower():
                    connection_lost_errors += 1
                    # Intentar reconectar
                    try:
                        conn.ping(reconnect=True)
                        cursor = conn.cursor()
                        cursor.execute(f"USE {database}")
                        cursor.execute("SET FOREIGN_KEY_CHECKS=0")
                        cursor.execute("SET sql_mode = ''")
                    except:
                        pass

                # Solo mostrar los primeros 10 errores
                if error_count <= 10:
                    stmt_preview = statement[:100].replace('\n', ' ')
                    print(f"  Error en statement {i + 1}: {e.msg}")
                    print(f"    Statement: {stmt_preview}...")

        # Commit final
        conn.commit()

        # Reactivar checks
        cursor.execute("SET FOREIGN_KEY_CHECKS=1")

        print(f"\n{'='*60}")
        print(f"IMPORTACION COMPLETADA")
        print(f"{'='*60}")
        print(f"Statements exitosos: {success_count}")
        print(f"Statements con error: {error_count}")
        if packet_too_big_errors > 0:
            print(f"  - Errores por paquete muy grande: {packet_too_big_errors}")
        if connection_lost_errors > 0:
            print(f"  - Errores por perdida de conexion: {connection_lost_errors}")
        print(f"Tablas creadas: {len(tables_created)}")

        # Mostrar estadísticas de las tablas
        print(f"\nTablas en la base de datos '{database}':")
        print(f"{'-'*60}")

        for table in tables_created:
            try:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                print(f"  {table:30s} {count:>10} registros")
            except mysql.connector.Error:
                print(f"  {table:30s} {'ERROR':>10}")

        cursor.close()
        conn.close()

        print(f"\n{'='*60}")
        print(f"Base de datos '{database}' lista para usar")
        print(f"{'='*60}")
        print(f"\nPara conectarte desde MySQL CLI:")
        print(f"  mysql -u {user} -p {database}")
        print(f"\nPara conectarte desde phpMyAdmin:")
        print(f"  http://localhost/phpmyadmin")

    except mysql.connector.Error as e:
        print(f"\nERROR al conectar a MySQL:")
        print(f"  Código: {e.errno}")
        print(f"  Mensaje: {e.msg}")
        print(f"\nVerifica que:")
        print(f"  1. MySQL esté ejecutándose en {host}")
        print(f"  2. El usuario '{user}' existe y tiene permisos")
        print(f"  3. La contraseña sea correcta")
        sys.exit(1)

    except FileNotFoundError:
        print(f"\nERROR: No se encontró el archivo '{sql_file}'")
        print(f"Verifica que el archivo exista en el directorio actual")
        sys.exit(1)

    except Exception as e:
        print(f"\nERROR inesperado: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    # Configuración por defecto
    HOST = "localhost"
    USER = "root"
    PASSWORD = ""  # Se solicitará interactivamente
    DATABASE = "datosejemplo"
    SQL_FILE = "backup_bd_pim_marce.sql"

    print("="*60)
    print("IMPORTACION DE BACKUP MYSQL")
    print("="*60)
    print(f"Host: {HOST}")
    print(f"Usuario: {USER}")
    print(f"Base de datos destino: {DATABASE}")
    print(f"Archivo SQL: {SQL_FILE}")
    print("="*60)

    # Si quieres cambiar la configuración, puedes pasarla aquí:
    # create_database_and_import(
    #     host="localhost",
    #     user="root",
    #     password="tu_password",
    #     database="datosejemplo",
    #     sql_file="backup_bd_pim_marce.sql"
    # )

    create_database_and_import(
        host=HOST,
        user=USER,
        password=PASSWORD,
        database=DATABASE,
        sql_file=SQL_FILE
    )
