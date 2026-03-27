# Instrucciones para crear BD MySQL desde backup

## Opción A: Instalar MySQL y crear la BD

### 1. Descargar e instalar MySQL
- Descargar desde: https://dev.mysql.com/downloads/installer/
- Instalar MySQL Community Server
- Durante la instalación, configurar:
  - Root password: (elegir una contraseña)
  - Puerto: 3306 (por defecto)

### 2. Crear la base de datos e importar

Abrir cmd o PowerShell y ejecutar:

```bash
# Conectar a MySQL
mysql -u root -p

# Crear la base de datos
CREATE DATABASE datosejemplo CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
exit;

# Importar el backup
mysql -u root -p datosejemplo < backup_bd_pim_marce.sql
```

### 3. Verificar la importación

```bash
mysql -u root -p datosejemplo

# Ver tablas creadas
SHOW TABLES;

# Ver registros de ejemplo
SELECT COUNT(*) FROM atributos;
SELECT COUNT(*) FROM catalogos;
exit;
```

## Opción B: Usar contenedor Docker con MySQL

Si tienes Docker instalado:

```bash
# Iniciar contenedor MySQL
docker run --name mysql-datosejemplo -e MYSQL_ROOT_PASSWORD=root -p 3306:3306 -d mysql:8.0

# Esperar a que MySQL inicie (30 segundos aprox)
timeout /t 30

# Crear la base de datos
docker exec -it mysql-datosejemplo mysql -uroot -proot -e "CREATE DATABASE datosejemplo CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;"

# Importar el backup
docker exec -i mysql-datosejemplo mysql -uroot -proot datosejemplo < backup_bd_pim_marce.sql

# Verificar
docker exec -it mysql-datosejemplo mysql -uroot -proot datosejemplo -e "SHOW TABLES;"
```

## Opción C: Usar XAMPP (más simple para Windows)

1. Descargar XAMPP: https://www.apachefriends.org/
2. Instalar y arrancar MySQL desde el panel de control
3. Abrir phpMyAdmin en http://localhost/phpmyadmin
4. Crear nueva base de datos llamada "datosejemplo"
5. Ir a "Importar" y seleccionar `backup_bd_pim_marce.sql`
6. Click en "Continuar"

---

## Notas

- El archivo `backup_bd_pim_marce.sql` es de MySQL, no SQLite
- La conversión automática a SQLite es compleja debido a diferencias en sintaxis
- Para usar estos datos en la aplicación actual (que usa SQLite), sería necesario:
  1. Importar a MySQL primero
  2. Adaptar el modelo de datos al esquema actual del PIM
  3. Exportar desde MySQL y convertir a SQLite

## Alternativa: Solo para capturas de pantalla

Si solo necesitas los datos para tomar capturas, puedes usar la BD actual (`backend/pim.db`) que ya tiene:
- 18 productos
- 16 marcas
- 10 categorías

Esto es suficiente para documentar todas las funcionalidades.
