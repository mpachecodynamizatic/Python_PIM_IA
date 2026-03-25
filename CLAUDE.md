# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Comandos esenciales

### Backend (FastAPI)
```bash
cd backend

# Crear virtualenv e instalar dependencias (primera vez)
python -m venv .venv
.venv\Scripts\activate          # Windows
pip install -r requirements.txt

# Arrancar servidor de desarrollo
python -m uvicorn app.main:app --reload --port 8000

# Ejecutar todos los tests
python -m pytest tests/ -v

# Ejecutar un test concreto
python -m pytest tests/test_products.py::test_create_product -v

# Migraciones Alembic (nota: la autogeneración puede fallar por FKs cíclicas; para SQLite dev basta con ALTER TABLE manual o recrear la BD)
python -m alembic revision --autogenerate -m "descripcion"
python -m alembic upgrade head
python -m alembic downgrade -1
```

### Frontend (Vite + React)
```bash
cd frontend
npm install
npm run dev        # http://localhost:5173
npm run build
npx tsc --noEmit   # type-check sin compilar
```

### Arrancar todo
```
start.bat          # Desde la raiz del proyecto (Windows)
```

## Arquitectura

Monorepo con dos proyectos independientes: `backend/` y `frontend/`.

### Backend

```
backend/app/
├── core/           # Infraestructura transversal
│   ├── config.py      # Settings via pydantic-settings (lee .env)
│   ├── database.py    # Engine async SQLite, get_db() dependency
│   ├── security.py    # JWT encode/decode, hash_password/verify_password
│   ├── permissions.py # Sistema de permisos granulares (11 recursos, 3 niveles)
│   └── dependencies.py # get_current_user, require_scopes(), require_roles()
├── models/         # SQLAlchemy 2.x ORM (Base + mixins en base.py)
├── schemas/        # Pydantic v2 (separados por entidad)
├── services/       # Lógica de negocio (entre API y modelos)
├── connectors/     # Conectores de sincronización externa (CSV, HTTP, JSON, Shopify, Amazon, WooCommerce)
├── export/         # Sistema de exportación (configs.py con ExportConfig por recurso)
└── api/v1/         # Routers FastAPI agrupados en router.py
```

**Flujo de una petición:** `Router → Service → Model (SQLAlchemy) → SQLite`

**Patrones clave:**
- Los IDs son `str` (UUID v4 en formato string), NO `uuid.UUID` — SQLite no tiene tipo UUID nativo
- Los campos JSON usan `JSON` de SQLAlchemy (no `JSONB` — eso es solo PostgreSQL)
- `UUIDMixin` genera el id como `str(uuid.uuid4())` via `default=lambda`
- `TimestampMixin` usa `DateTime` sin timezone (SQLite no lo soporta)
- El admin `admin@pim.local / admin` se crea automáticamente en el lifespan si no existe
- La BD se crea automáticamente al arrancar (via `Base.metadata.create_all`)
- Audit log en cada `create_product`, `update_product` y `transition_product`
- Pydantic v2: usar `ConfigDict(from_attributes=True)`, NO la clase `Config` deprecada
- Al usar `selectinload` para relaciones eager-loaded después de `db.flush()`, re-query en vez de `db.refresh()` para evitar errores `MissingGreenlet`
- **Configuración de conexión de sync:** Se almacena en `sync_jobs`, NO en `channels`. Cada job puede tener su propia configuración de conexión (script o http_post)

**Transiciones de estado de productos:**
```
draft → in_review → approved → ready → retired
       ↖ reject ↙          ↖──────────────↙
                              (volver a draft)
```

**Auth:** JWT con `python-jose`. Los admins (`role="admin"`) bypass todos los scope checks en `require_scopes()`.

**Sistema de Permisos (core/permissions.py):**
- **11 recursos:** products, categories, media, brands, channels, suppliers, sync, quality, i18n, users, settings
- **3 niveles:** none, read, write
- **3 roles predefinidos:**
  - `admin`: acceso write a todo
  - `editor`: write a productos/categorías/media/marcas/canales/proveedores/sync/calidad/i18n, read a users/settings
  - `viewer`: read a todo
- **Permisos personalizables:** Los usuarios pueden tener scopes custom en formato `resource:level` (ej: `"products:read"`, `"categories:write"`)
- Los scopes personalizados sobrescriben los permisos del rol por defecto
- Función `has_permission(user, resource, required_level)` para validación

**Conectores (sincronización):**
- `BaseConnector` (abc) con método `async run(db, filters) → ConnectorResult`
- `ConnectorResult` incluye `sku_results: list[SkuResult]` para tracking per-producto
- Registro en `connectors/registry.py` — añadir nuevos conectores ahí
- Semáforo por canal en `connectors/concurrency.py` para limitar ejecución paralela

**Scheduler (background):**
- Loop cada 30-60s en `services/scheduler.py`, arrancado en el lifespan de `main.py`
- Procesa `SyncSchedule` con expresiones cron (via `croniter`)
- Reintentos automáticos con backoff exponencial: `5^retry_count` segundos

**Sistema de Exportación (export/configs.py):**
- Configuraciones de exportación por recurso usando `ExportConfig`
- Recursos exportables: products, categories, media_assets, brands, suppliers, channels, product_logistics, product_compliance, product_channels, y más
- Cada `ExportConfig` define: modelo, campos, PKs, FKs, validaciones, transformaciones
- Soporte para upsert con `upsert_key` para importación

### Frontend

```
frontend/src/
├── api/            # Funciones axios por entidad (client.ts tiene interceptor JWT + auto-refresh)
├── contexts/       # AuthContext (estado de sesión global)
├── pages/          # Páginas por ruta
├── components/     # Layout (sidebar+topbar), ProtectedRoute, ImportDialog, ExportDialog
└── types/          # Tipos TypeScript espejo de los schemas Pydantic
```

**Rutas principales:**
- `/` — Dashboard
- `/products` — Lista con vistas guardadas, filtros avanzados (fecha, media, i18n), exportación multi-recurso
- `/products/:sku` — Detalle (tabs: General, Atributos, I18N, SEO, Media, Calidad, Comentarios, Historial)
- `/categories` — Árbol de taxonomía
- `/media` — Biblioteca multimedia
- `/quality` — Dashboard de calidad + Admin de reglas (simulación what-if)
- `/i18n` — Traducciones pendientes
- `/sync` — Dashboard de sincronización + Schedules (connection config en jobs, no en channels)
- `/brands` — Gestión de marcas
- `/suppliers` — Gestión de proveedores
- `/channels` — Gestión de canales (sin connection config)
- `/admin/users` — CRUD de usuarios (solo admins)
- `/admin/roles` — Gestión de permisos granulares por usuario (solo admins)

**Sistema de Administración:**
- **UserManager** (`pages/Admin/UserManager.tsx`):
  - Crear usuarios con email, password, nombre, rol
  - Editar nombre, rol, estado activo/inactivo
  - Eliminar usuarios (con prevención de auto-eliminación)
  - Visualización con chips de rol (admin/editor/viewer) y estado
- **RoleManager** (`pages/Admin/RoleManager.tsx`):
  - Tabla matriz: usuarios (filas) × recursos (columnas)
  - Selects por celda: none/read/write
  - Los admins tienen acceso total (no editable)
  - Los scopes personalizados sobrescriben defaults del rol
- **Seguridad:**
  - Solo `user.role === 'admin'` puede acceder a `/admin/*`
  - Backend valida con `require_roles("admin")` en todos los endpoints
  - `delete_user()` previene auto-eliminación comparando IDs

### Base de datos (SQLite)

Fichero: `backend/pim.db` (se crea al arrancar). Tablas principales:

**Core:**
- `users` — autenticación y RBAC (roles: admin, editor, viewer)
- `products` — SKU como PK (text), atributos/seo en JSON, FK a categories y families
- `categories` — árbol con `parent_id` self-referencial
- `product_i18n` — traducciones (sku + locale, unique)
- `media_assets` — multimedia vinculada a SKUs
- `audits` — log de cambios inmutable (resource, actor, before/after JSON)
- `product_versions` — snapshots completos del producto en cada cambio

**Calidad:**
- `quality_rule_sets` — conjuntos de reglas (solo uno activo a la vez)
- `quality_rules` — reglas individuales (dimension, weight, min_score, scope_category_id)

**Colaboración:**
- `product_comments` — comentarios por SKU con `parent_id` (hilos), `tags` (JSON array), `mentions`

**Sincronización:**
- `sync_jobs` — trabajos de sync (channel, status, filters, metrics, max_retries, retry_count, **connection_type**, **connection_config**)
  - connection_type: "script" o "http_post"
  - connection_config: JSON con configuración específica (script_path, args, timeout para script; url, headers para http_post)
- `product_sync_statuses` — estado per-SKU per-canal (synced/error/pending)
- `sync_schedules` — programación cron (channel, cron_expression, enabled, next_run_at)

**Catálogo extendido:**
- `brands` — maestro de marcas
- `suppliers` — proveedores
- `channels` — canales de venta (name, code, description, active — sin connection config)
- `product_channels` — asignación producto-canal
- `product_logistics` — datos logísticos por producto
- `product_compliance` — datos de conformidad
- `attribute_families` / `attribute_definitions` — familias y definiciones de atributos
- `external_taxonomies` — taxonomías externas

**Vistas y configuración:**
- `saved_views` — filtros guardados por usuario (is_default, is_public, resource genérico)
- `mapping_templates` — plantillas de mapeo para importación

### Tests

146+ tests en 15 ficheros. Usan **SQLite en memoria** (`aiosqlite`), sin servicios externos.

El `conftest.py` recrea las tablas en cada test, sobreescribe `get_db`, y configura los session factories para tareas background:
```python
import app.services.import_service as _import_svc
_import_svc._session_factory = TestSessionLocal
import app.services.sync_service as _sync_svc
_sync_svc._session_factory = TestSessionLocal
```

**Ficheros de test:** `test_auth`, `test_products`, `test_categories`, `test_ingest`, `test_media`, `test_quality`, `test_i18n`, `test_product_versions`, `test_quality_rules`, `test_sync`, `test_saved_views`, `test_comments`, `test_export`, `test_import`.

## Variables de entorno (backend/.env)

Copiar `backend/.env.example` a `backend/.env`. Por defecto usa SQLite local, no requiere configuración adicional para desarrollo.

Variables principales: `DATABASE_URL`, `SECRET_KEY`, `ADMIN_EMAIL`, `ADMIN_PASSWORD`, `CORS_ORIGINS`, `ACCESS_TOKEN_EXPIRE_MINUTES`, `REFRESH_TOKEN_EXPIRE_MINUTES`.
