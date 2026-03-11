# Manual de Usuario - PIM (Product Information Management)

## Tabla de contenidos

1. [Introduccion](#1-introduccion)
2. [Requisitos e instalacion](#2-requisitos-e-instalacion)
3. [Inicio de sesion](#3-inicio-de-sesion)
4. [Dashboard](#4-dashboard)
5. [Gestion de productos](#5-gestion-de-productos)
6. [Ficha de producto](#6-ficha-de-producto)
7. [Taxonomia de categorias](#7-taxonomia-de-categorias)
8. [Biblioteca de medios](#8-biblioteca-de-medios)
9. [Calidad de datos](#9-calidad-de-datos)
10. [Traducciones (I18N)](#10-traducciones-i18n)
11. [Historial y versionado](#11-historial-y-versionado)
12. [Importacion masiva](#12-importacion-masiva)
13. [Sincronizacion externa](#13-sincronizacion-externa)
14. [Administracion](#14-administracion)
15. [API REST](#15-api-rest)

---

## 1. Introduccion

PIM es una aplicacion de gestion de informacion de productos (Product Information Management) disenada para centralizar, enriquecer y distribuir datos de producto.

### Funcionalidades principales

- **Catalogo de productos** con SKU, marca, atributos flexibles y SEO
- **Taxonomia jerarquica** de categorias en arbol
- **Gestion multimedia** con subida de imagenes, videos y PDFs
- **Traducciones** multi-idioma por producto
- **Scoring de calidad** automatico sobre 6 dimensiones
- **Versionado completo** con historial, comparacion, restauracion y comentarios
- **Flujo de estados** configurable (borrador, en revision, aprobado, publicado, retirado)
- **Importacion masiva** desde Excel/CSV con plantillas de mapeo
- **Sincronizacion** a canales externos
- **Control de acceso** basado en roles y permisos granulares

### Arquitectura

| Componente | Tecnologia |
|------------|------------|
| Backend | Python 3.11+, FastAPI, SQLAlchemy 2.x async |
| Frontend | React 19, TypeScript, Material UI 7, Vite |
| Base de datos | SQLite (fichero local) |
| Autenticacion | JWT (access token + refresh token) |

---

## 2. Requisitos e instalacion

### Requisitos previos

- Python 3.11 o superior
- Node.js 18 o superior
- npm 9 o superior

### Instalacion del backend

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate          # Windows
# source .venv/bin/activate     # Linux/Mac
pip install -r requirements.txt
```

### Configuracion

Copiar el fichero de ejemplo de variables de entorno:

```bash
cp backend/.env.example backend/.env
```

Variables principales en `backend/.env`:

| Variable | Descripcion | Valor por defecto |
|----------|-------------|-------------------|
| `DATABASE_URL` | Cadena de conexion a la BD | `sqlite+aiosqlite:///./pim_new.db` |
| `SECRET_KEY` | Clave para firmar JWT | `change-me-in-production...` |
| `ADMIN_EMAIL` | Email del admin inicial | `admin@pim.local` |
| `ADMIN_PASSWORD` | Password del admin inicial | `admin` |
| `CORS_ORIGINS` | Origenes permitidos (frontend) | `["http://localhost:5173"]` |
| `RUN_DB_INIT` | Crear tablas al arrancar | `True` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Duracion del token de acceso | `30` |
| `REFRESH_TOKEN_EXPIRE_MINUTES` | Duracion del refresh token | `10080` (7 dias) |

### Instalacion del frontend

```bash
cd frontend
npm install
```

### Arrancar el sistema

**Opcion A: Script automatico (Windows)**
```bash
start.bat
```

**Opcion B: Manual (dos terminales)**

Terminal 1 (backend):
```bash
cd backend
.venv\Scripts\activate
python -m uvicorn app.main:app --reload --port 8000
```

Terminal 2 (frontend):
```bash
cd frontend
npm run dev
```

### Acceso

- **Frontend:** http://localhost:5173
- **API docs (Swagger):** http://localhost:8000/docs
- **Health check:** http://localhost:8000/health

### Inicializacion automatica

Al arrancar el backend por primera vez:
1. Se crean todas las tablas en SQLite
2. Se crea el usuario administrador (`admin@pim.local` / `admin`)
3. Se crea la carpeta `uploads/` para archivos multimedia

---

## 3. Inicio de sesion

### Acceder al sistema

1. Abrir http://localhost:5173 en el navegador
2. Introducir las credenciales:
   - **Email:** `admin@pim.local`
   - **Password:** `admin`
3. Pulsar **Entrar**

### Sesion y tokens

- Al iniciar sesion se genera un **token de acceso** (30 minutos) y un **refresh token** (7 dias)
- Cuando el token de acceso expira, se renueva automaticamente usando el refresh token
- Si el refresh token expira, se redirige al login
- Para cerrar sesion: clic en el icono de usuario (esquina superior derecha) y seleccionar **Cerrar sesion**

---

## 4. Dashboard

La pagina principal muestra un resumen del estado del catalogo con 4 tarjetas:

| Tarjeta | Descripcion | Al hacer clic |
|---------|-------------|---------------|
| **Total Productos** | Numero total de productos en el catalogo | Navega al listado de productos |
| **Borradores** | Productos en estado `draft` | Navega al listado filtrado por borradores |
| **Publicados** | Productos en estado `ready` | Navega al listado filtrado por publicados |
| **Categorias** | Numero total de categorias | Navega a la taxonomia |

---

## 5. Gestion de productos

### Listado de productos

Acceder desde el menu lateral: **Productos**

#### Busqueda y filtrado

- **Barra de busqueda:** Busca por SKU y marca (busqueda parcial)
- **Filtro de estado:** Desplegable con las opciones:
  - Todos
  - Borrador (`draft`)
  - Publicado (`ready`)
  - Retirado (`retired`)

#### Tabla de resultados

| Columna | Descripcion |
|---------|-------------|
| SKU | Identificador unico del producto |
| Marca | Nombre de la marca |
| Estado | Chip de color: naranja (borrador), verde (publicado), rojo (retirado) |
| Actualizado | Fecha de ultima modificacion |

- Clic en una fila para abrir la ficha del producto
- **Paginacion** configurable: 10, 20 o 50 productos por pagina

#### Crear un producto nuevo

1. Pulsar el boton **Nuevo Producto**
2. Rellenar los campos:
   - **SKU** (obligatorio): Identificador unico, por ejemplo `LAPTOP-X1-BLK`
   - **Marca** (obligatorio): Nombre de la marca
   - **Categoria** (obligatorio): Seleccionar del desplegable
3. Pulsar **Crear**

El producto se crea en estado `draft` (borrador).

---

## 6. Ficha de producto

Al hacer clic en un producto del listado se abre su ficha con toda la informacion organizada en pestanas.

### Cabecera

- **SKU** del producto (titulo)
- **Chip de estado** con color
- **Score de calidad** (porcentaje con color: verde >= 80%, naranja >= 50%, rojo < 50%)
- **Botones de transicion de estado** (varian segun el estado actual)

### Transiciones de estado

El producto sigue un ciclo de vida con transiciones validas:

```
draft (borrador) --> ready (publicado) --> retired (retirado)
                 <--                   <--
                 --> in_review --> approved --> ready
```

| Estado actual | Acciones disponibles |
|---------------|---------------------|
| `draft` | **Publicar** (pasar a `ready`) |
| `ready` | **Volver a borrador**, **Retirar** |
| `retired` | **Reactivar** (volver a `draft`) |

### Pestana: General

Campos editables:
- **Marca:** Campo de texto libre
- **Categoria:** Autocomplete con busqueda sobre las categorias del sistema

Campos informativos (solo lectura):
- **Creado:** Fecha de creacion
- **Actualizado:** Fecha de ultima modificacion

Pulsar **Guardar** para aplicar los cambios.

### Pestana: Atributos

Editor JSON con los atributos del producto. Permite definir cualquier estructura de datos flexible.

**Ejemplo de atributos:**
```json
{
  "color": "negro",
  "peso_kg": 1.5,
  "dimensiones": {
    "alto": 30,
    "ancho": 20,
    "profundidad": 5
  },
  "materiales": ["aluminio", "plastico"],
  "garantia_meses": 24
}
```

- El editor valida que el contenido sea JSON valido antes de guardar
- Si hay un error de sintaxis, se muestra el mensaje de error bajo el campo
- Pulsar **Guardar atributos** para aplicar los cambios

### Pestana: I18N (Traducciones)

Gestiona las traducciones del producto a diferentes idiomas.

**Ver traducciones existentes:**
- Cada traduccion muestra el codigo de idioma (chip) y el titulo traducido
- Boton de eliminar (papelera roja) para borrar una traduccion

**Agregar o editar una traduccion:**
1. Introducir el **Locale** (codigo de idioma, ej: `es`, `en`, `fr`, `de`)
2. Introducir el **Titulo** traducido
3. Pulsar **Guardar**

Si el locale ya existe, se actualiza. Si es nuevo, se crea.

### Pestana: SEO

Editor JSON con los metadatos SEO del producto.

**Ejemplo de datos SEO:**
```json
{
  "title": "Samsung Galaxy S24 - Negro",
  "description": "Smartphone Samsung Galaxy S24 con 128GB de almacenamiento",
  "keywords": ["samsung", "galaxy", "s24", "smartphone"],
  "canonical_url": "/productos/phone-s24-blk"
}
```

- Misma validacion JSON que la pestana de atributos
- Pulsar **Guardar SEO** para aplicar

### Pestana: Media

Gestiona los archivos multimedia vinculados al producto.

**Formatos admitidos:**
- Imagenes: JPEG, PNG, WebP, GIF, SVG
- Video: MP4
- Documentos: PDF

**Subir un archivo:**
1. Pulsar **Subir archivo**
2. Seleccionar el archivo del sistema
3. El archivo se sube y se vincula automaticamente al producto

**Vista de archivos:**
- Los archivos se muestran en una cuadricula responsive
- Las imagenes muestran una vista previa
- Los demas tipos muestran el tipo de fichero (VIDEO, PDF)
- Cada tarjeta tiene botones para:
  - **Abrir** en nueva pestana
  - **Eliminar** el archivo

### Pestana: Calidad

Muestra el score de calidad del producto calculado automaticamente sobre 6 dimensiones:

| Dimension | Criterio | Puntuacion |
|-----------|----------|------------|
| **Marca** | Campo marca no vacio | 0% o 100% |
| **Categoria** | Categoria asignada | 0% o 100% |
| **SEO** | Campos title y description rellenados | 0%, 50% o 100% |
| **Atributos** | Al menos un atributo definido | 0% o 100% |
| **Media** | Al menos un archivo multimedia | 0% o 100% |
| **Idiomas** | Al menos una traduccion | 0% o 100% |

- **Score global:** Media de las 6 dimensiones (0-100%)
- Cada dimension muestra una barra de progreso con color
- Boton **Recalcular** para refrescar el score

### Pestana: Historial

Ver seccion [11. Historial y versionado](#11-historial-y-versionado).

---

## 7. Taxonomia de categorias

Acceder desde el menu lateral: **Taxonomia**

### Arbol de categorias

Las categorias se muestran en una estructura de arbol jerarquico:
- Clic en una categoria para expandir/colapsar sus hijos
- Cada nodo muestra:
  - Icono de carpeta (abierta/cerrada)
  - Nombre de la categoria
  - Slug y numero de atributos en el esquema

### Crear una categoria

1. Pulsar **Nueva Categoria**
2. Rellenar:
   - **Nombre:** Nombre visible (ej: "Electronica")
   - **Slug:** Identificador URL-friendly (ej: "electronica"). Se auto-convierte a minusculas y reemplaza espacios por guiones
3. Pulsar **Crear**

### Esquema de atributos

Cada categoria puede definir un esquema de atributos esperados para sus productos. Este esquema se gestiona via API:

```json
{
  "peso_kg": { "type": "number", "required": true },
  "color": { "type": "enum", "options": ["rojo", "azul", "negro"] },
  "material": { "type": "string" }
}
```

---

## 8. Biblioteca de medios

Acceder desde el menu lateral: **Media**

### Vista general

La biblioteca muestra todos los archivos multimedia del sistema en una cuadricula responsive.

### Filtrar por SKU

- Introducir un SKU en el campo de filtro para ver solo los archivos vinculados a ese producto

### Subir un archivo

1. Pulsar **Subir archivo**
2. Seleccionar el archivo
3. Si hay un SKU en el filtro, el archivo se vincula automaticamente a ese producto

### Vincular a un producto

Para vincular un archivo existente a un producto:
1. Clic en el icono de enlace de la tarjeta
2. Introducir el SKU del producto destino
3. Pulsar **Vincular**

### Eliminar un archivo

- Clic en el icono de papelera roja en la tarjeta del archivo
- La eliminacion borra tanto el registro como el archivo fisico del servidor

---

## 9. Calidad de datos

Acceder desde el menu lateral: **Calidad**

### Dashboard de calidad

Vista global de la calidad de datos de todos los productos:

| Columna | Descripcion |
|---------|-------------|
| SKU | Identificador del producto |
| Estado | Chip de estado con color |
| Score | Barra de progreso con porcentaje y color |
| Dimensiones | Chips de color por cada dimension (verde=100%, naranja=parcial, gris=0%) |
| Acciones | Enlace para abrir la ficha del producto |

Las 6 dimensiones se muestran como chips con tooltips:
- **Marca, Categoria, SEO, Atributos, Media, Idiomas**

Paginacion de 20 productos por pagina con navegacion anterior/siguiente.

### Como mejorar el score

Para conseguir un score del 100% en un producto:

1. Rellenar la **marca** (tab General)
2. Asignar una **categoria** (tab General)
3. Rellenar `title` y `description` en el **SEO** (tab SEO)
4. Anadir al menos un **atributo** (tab Atributos)
5. Subir al menos un archivo **multimedia** (tab Media)
6. Crear al menos una **traduccion** (tab I18N)

---

## 10. Traducciones (I18N)

Acceder desde el menu lateral: **Traducciones**

### Encontrar productos sin traducir

1. Seleccionar el **idioma objetivo** en el desplegable (es, en, fr, de, pt, it)
2. Se muestra la lista de productos que **no tienen traduccion** en ese idioma
3. El contador indica: "X productos sin traduccion en LOCALE"

### Traducir un producto

1. Clic en el icono de **Traducir** (lapiz) junto al producto
2. En el dialogo, introducir el **titulo** en el idioma seleccionado
3. Pulsar **Guardar**
4. El producto desaparece de la lista de pendientes

### Acceso directo a la ficha

- Clic en el icono de **Ver producto** para abrir la ficha completa donde se pueden gestionar todas las traducciones

---

## 11. Historial y versionado

El sistema registra automaticamente cada cambio realizado en un producto (creacion, edicion, cambio de estado, restauracion) en un log de auditoria inmutable.

### Acceder al historial

Abrir la ficha de un producto y seleccionar la pestana **Historial**.

### Filtrar versiones

Los botones de filtro permiten ver solo ciertos tipos de cambio:
- **Creacion:** Registro de creacion del producto
- **Edicion:** Cambios en datos (marca, atributos, SEO, etc.)
- **Estado:** Transiciones de estado (borrador -> publicado, etc.)
- **Restauracion:** Restauraciones a versiones anteriores

Se pueden combinar multiples filtros.

### Informacion de cada version

Cada entrada del historial muestra:
- **Tipo de accion** (chip de color)
- **Fecha y hora** del cambio
- **Usuario** que realizo el cambio

### Ver snapshot (datos en ese momento)

1. Clic en el icono de **expandir** (flecha abajo) de una version
2. Se despliega un panel con el JSON completo de los datos del producto en ese instante
3. Volver a clic para colapsar

### Comparar dos versiones (diff)

1. Seleccionar dos versiones haciendo clic en el icono de **comparar** (flechas cruzadas) en cada una
2. Las versiones seleccionadas se resaltan con fondo azul
3. Aparece el boton **Comparar seleccionadas**
4. Se abre un dialogo con la comparacion lado a lado:
   - Se listan todos los campos
   - Los campos **modificados** se resaltan con borde naranja y chip "modificado"
   - La version A se muestra con fondo naranja claro
   - La version B se muestra con fondo azul claro
   - Los campos sin cambios se muestran con fondo gris

### Restaurar una version

1. Clic en **Restaurar** en la version deseada
2. Confirmar en el dialogo de confirmacion
3. El producto se actualiza con los datos de esa version

**Campos que se restauran:** marca, categoria, atributos, SEO
**Campos que NO se restauran:** estado (se preserva el estado actual para no romper el flujo de trabajo)

### Comentarios por version

1. Clic en el icono de **comentarios** (bocadillo) de una version
2. Se despliega la seccion de comentarios:
   - Se muestran los comentarios existentes con autor y fecha
   - Campo de texto para anadir un nuevo comentario
   - Enviar con el icono de enviar o pulsando **Enter**

Los comentarios por version son utiles para documentar revisiones, aprobaciones o motivos de cambio.

### Politica de retencion (solo admin, via API)

Los administradores pueden aplicar politicas de limpieza del historial:

```
POST /api/v1/products/{sku}/versions/retention
{
  "max_versions": 50,     // Mantener solo las 50 versiones mas recientes
  "max_age_days": 365     // Eliminar versiones de mas de 1 ano
}
```

La version mas reciente nunca se elimina.

---

## 12. Importacion masiva

La importacion masiva permite cargar productos desde archivos Excel (.xlsx) o CSV.

### Endpoint de importacion

```
POST /api/v1/ingest/uploads
```

Parametros (multipart/form-data):
- **file:** Archivo Excel o CSV (max 50 MB)
- **mapping_json:** Configuracion de mapeo de columnas (JSON)
- **dry_run:** `true` para simular sin guardar cambios
- **mode:** `upsert` (crear o actualizar) o `create_only` (solo crear nuevos)
- **template_id:** ID de una plantilla de mapeo guardada (opcional)

### Formato del mapeo de columnas

```json
[
  {
    "source_column": "Codigo",
    "target_field": "sku",
    "required": true
  },
  {
    "source_column": "Nombre Marca",
    "target_field": "brand",
    "transform": "strip"
  },
  {
    "source_column": "Titulo SEO",
    "target_field": "seo.title"
  }
]
```

Transformaciones disponibles: `strip`, `upper`, `lower`, `int`, `float`

Campos anidados se indican con punto: `seo.title`, `attributes.color`

### Plantillas de mapeo

Guardar configuraciones de mapeo para reutilizarlas:

```
POST /api/v1/ingest/mapping-templates
{
  "name": "Importacion catalogo principal",
  "description": "Mapeo para el Excel del proveedor X",
  "mappings": [...],
  "defaults": { "status": "draft" }
}
```

### Seguimiento del trabajo de importacion

```
GET /api/v1/ingest/jobs/{job_id}
```

Devuelve el progreso con:
- Estado: `pending` -> `running` -> `done` / `failed`
- Filas totales, procesadas, exitosas, fallidas
- Lista de errores con numero de fila y detalle

---

## 13. Sincronizacion externa

El modulo de sincronizacion permite exportar productos a canales externos (e-commerce, marketplaces, etc.).

### Crear un trabajo de sincronizacion

```
POST /api/v1/sync/jobs
{
  "channel": "shopify"
}
```

Solo accesible por administradores. Se ejecuta en segundo plano.

### Consultar estado

```
GET /api/v1/sync/jobs/{job_id}
```

Metricas disponibles:
- `total_products`: Total de productos procesados
- `exported`: Exportados con exito
- `skipped`: Omitidos (no elegibles)

### Listar trabajos

```
GET /api/v1/sync/jobs?channel=shopify&page=1&size=20
```

---

## 14. Administracion

### Gestion de usuarios

Solo accesible por usuarios con rol `admin`.

**Crear usuario:**
```
POST /api/v1/users
{
  "email": "editor@empresa.com",
  "password": "password-seguro",
  "full_name": "Juan Editor",
  "role": "editor",
  "scopes": ["products:read", "products:write", "media:write"]
}
```

**Listar usuarios:**
```
GET /api/v1/users?skip=0&limit=50
```

**Actualizar usuario:**
```
PATCH /api/v1/users/{user_id}
{
  "role": "admin",
  "scopes": ["products:read", "products:write", "media:write", "taxonomy:write"]
}
```

### Roles

| Rol | Descripcion |
|-----|-------------|
| `admin` | Acceso total. Ignora las restricciones de scopes |
| `editor` | Puede editar productos, media y categorias (segun sus scopes) |
| `viewer` | Solo lectura (rol por defecto) |

### Scopes (permisos granulares)

| Scope | Permite |
|-------|---------|
| `products:read` | Leer productos |
| `products:write` | Crear, editar y cambiar estado de productos |
| `media:write` | Subir y gestionar archivos multimedia |
| `taxonomy:write` | Crear, editar y eliminar categorias |
| `syndication:run` | Ejecutar trabajos de sincronizacion |
| `quality:read` | Consultar scores de calidad |

Los usuarios con rol `admin` tienen acceso a todo independientemente de sus scopes.

### Familias de atributos

Definir esquemas reutilizables de atributos por tipo de producto:

**Crear familia:**
```
POST /api/v1/attributes/families
{
  "code": "smartphones",
  "name": "Smartphones",
  "description": "Atributos para telefonos moviles",
  "category_id": "uuid-de-categoria"
}
```

**Anadir definicion de atributo:**
```
POST /api/v1/attributes/families/{family_id}/definitions
{
  "code": "pantalla_pulgadas",
  "label": "Tamano de pantalla (pulgadas)",
  "type": "number",
  "required": true
}
```

Tipos disponibles: `string`, `number`, `boolean`, `enum`

Para tipo `enum`, incluir las opciones:
```json
{
  "code": "color",
  "label": "Color",
  "type": "enum",
  "required": false,
  "options_json": "[\"rojo\",\"azul\",\"negro\",\"blanco\"]"
}
```

### Reglas de calidad personalizadas

Configurar requisitos de calidad personalizados:

**Crear conjunto de reglas:**
```
POST /api/v1/quality-rules/sets
{
  "name": "Reglas catalogo premium",
  "description": "Requisitos de calidad para productos premium",
  "active": false
}
```

**Activar conjunto:**
```
POST /api/v1/quality-rules/sets/{rule_set_id}/activate
```
Solo puede haber un conjunto activo a la vez.

**Anadir regla:**
```
POST /api/v1/quality-rules/sets/{rule_set_id}/rules
{
  "dimension": "media",
  "weight": 2.0,
  "min_score": 1.0,
  "required_status": "ready"
}
```

### Vistas guardadas

Los usuarios pueden guardar configuraciones de filtro personalizadas:

**Guardar vista:**
```
POST /api/v1/views/products
{
  "name": "Borradores sin media",
  "description": "Productos en borrador que necesitan imagenes",
  "filters": { "status": "draft" },
  "is_default": false
}
```

**Listar mis vistas:**
```
GET /api/v1/views/products
```

---

## 15. API REST

### Documentacion interactiva

La API completa esta documentada y se puede probar en:
- **Swagger UI:** http://localhost:8000/docs
- **ReDoc:** http://localhost:8000/redoc

### Autenticacion

Todas las peticiones (excepto login y refresh) requieren un token JWT en la cabecera:

```
Authorization: Bearer <access_token>
```

**Obtener token:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email": "admin@pim.local", "password": "admin"}'
```

**Refrescar token:**
```bash
curl -X POST http://localhost:8000/api/v1/auth/refresh \
  -H "Content-Type: application/json" \
  -d '{"refresh_token": "<refresh_token>"}'
```

### Resumen de endpoints

#### Autenticacion
| Metodo | Ruta | Descripcion |
|--------|------|-------------|
| POST | `/auth/login` | Iniciar sesion |
| POST | `/auth/refresh` | Renovar token |
| GET | `/auth/me` | Datos del usuario actual |

#### Productos
| Metodo | Ruta | Descripcion |
|--------|------|-------------|
| GET | `/products` | Listar productos (paginado, filtros) |
| POST | `/products` | Crear producto |
| GET | `/products/{sku}` | Obtener producto |
| PATCH | `/products/{sku}` | Actualizar producto |
| POST | `/products/{sku}/transitions` | Cambiar estado |
| POST | `/products/{sku}/workflow/submit` | Enviar a revision |
| POST | `/products/{sku}/workflow/approve` | Aprobar producto |
| GET | `/products/{sku}/audit` | Log de auditoria |
| GET | `/products/{sku}/versions` | Historial de versiones |
| POST | `/products/{sku}/versions/{id}/restore` | Restaurar version |
| POST | `/products/{sku}/versions/retention` | Aplicar retencion |
| GET | `/products/{sku}/comments` | Comentarios del producto |
| POST | `/products/{sku}/comments` | Anadir comentario |
| DELETE | `/products/{sku}/comments/{id}` | Eliminar comentario |
| GET | `/products/{sku}/versions/{id}/comments` | Comentarios de version |
| POST | `/products/{sku}/versions/{id}/comments` | Comentar version |

#### Traducciones
| Metodo | Ruta | Descripcion |
|--------|------|-------------|
| GET | `/i18n/locales` | Idiomas en uso |
| GET | `/i18n/missing?locale=es` | Productos sin traduccion |
| GET | `/products/{sku}/i18n` | Traducciones del producto |
| POST | `/products/{sku}/i18n/{locale}` | Crear/actualizar traduccion |
| DELETE | `/products/{sku}/i18n/{locale}` | Eliminar traduccion |

#### Categorias
| Metodo | Ruta | Descripcion |
|--------|------|-------------|
| GET | `/taxonomy/categories` | Listar categorias |
| GET | `/taxonomy/categories/tree` | Arbol completo |
| POST | `/taxonomy/categories` | Crear categoria |
| GET | `/taxonomy/categories/{id}` | Obtener categoria |
| GET | `/taxonomy/categories/{id}/schema` | Esquema de atributos |
| PATCH | `/taxonomy/categories/{id}` | Actualizar categoria |
| DELETE | `/taxonomy/categories/{id}` | Eliminar categoria |

#### Media
| Metodo | Ruta | Descripcion |
|--------|------|-------------|
| POST | `/media` | Subir archivo |
| GET | `/media` | Listar archivos |
| GET | `/media/{id}` | Obtener archivo |
| PATCH | `/media/{id}/link?sku=X` | Vincular a producto |
| DELETE | `/media/{id}` | Eliminar archivo |

#### Calidad
| Metodo | Ruta | Descripcion |
|--------|------|-------------|
| GET | `/quality/products/{sku}` | Score de producto |
| GET | `/quality/report` | Informe global |

#### Importacion
| Metodo | Ruta | Descripcion |
|--------|------|-------------|
| POST | `/ingest/uploads` | Importar Excel/CSV |
| GET | `/ingest/jobs` | Listar importaciones |
| GET | `/ingest/jobs/{id}` | Detalle de importacion |
| POST | `/ingest/mapping-templates` | Crear plantilla de mapeo |
| GET | `/ingest/mapping-templates` | Listar plantillas |
| DELETE | `/ingest/mapping-templates/{id}` | Eliminar plantilla |

#### Sincronizacion
| Metodo | Ruta | Descripcion |
|--------|------|-------------|
| POST | `/sync/jobs` | Crear trabajo de sync |
| GET | `/sync/jobs` | Listar trabajos |
| GET | `/sync/jobs/{id}` | Estado del trabajo |

#### Usuarios (admin)
| Metodo | Ruta | Descripcion |
|--------|------|-------------|
| POST | `/users` | Crear usuario |
| GET | `/users` | Listar usuarios |
| GET | `/users/{id}` | Obtener usuario |
| PATCH | `/users/{id}` | Actualizar usuario |

#### Familias de atributos (admin)
| Metodo | Ruta | Descripcion |
|--------|------|-------------|
| GET | `/attributes/families` | Listar familias |
| POST | `/attributes/families` | Crear familia |
| GET | `/attributes/families/{id}/definitions` | Listar definiciones |
| POST | `/attributes/families/{id}/definitions` | Crear definicion |

#### Reglas de calidad (admin)
| Metodo | Ruta | Descripcion |
|--------|------|-------------|
| GET | `/quality-rules/sets` | Listar conjuntos |
| POST | `/quality-rules/sets` | Crear conjunto |
| POST | `/quality-rules/sets/{id}/activate` | Activar conjunto |
| GET | `/quality-rules/sets/{id}/rules` | Listar reglas |
| POST | `/quality-rules/sets/{id}/rules` | Crear regla |

#### Vistas guardadas
| Metodo | Ruta | Descripcion |
|--------|------|-------------|
| GET | `/views/products` | Mis vistas guardadas |
| POST | `/views/products` | Crear vista |
| GET | `/views/products/{id}` | Obtener vista |
| DELETE | `/views/products/{id}` | Eliminar vista |

---

## Navegacion de la aplicacion

### Menu lateral (sidebar)

| Icono | Seccion | Ruta |
|-------|---------|------|
| Dashboard | Dashboard | `/` |
| Inventario | Productos | `/products` |
| Arbol | Taxonomia | `/categories` |
| Imagen | Media | `/media` |
| Check | Calidad | `/quality` |
| Idiomas | Traducciones | `/i18n` |

### Barra superior

- **Izquierda:** Titulo "PIM - Product Information Management"
- **Derecha:** Icono de usuario con menu desplegable (nombre, rol, cerrar sesion)
- **Movil:** Boton hamburguesa para mostrar/ocultar el menu lateral

---

*Manual generado para PIM v1.0 — Marzo 2026*
