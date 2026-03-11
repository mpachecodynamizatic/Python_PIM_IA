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

# Migraciones Alembic
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
│   └── dependencies.py # get_current_user, require_scopes(), require_roles()
├── models/         # SQLAlchemy 2.x ORM (Base + mixins en base.py)
├── schemas/        # Pydantic v2 (separados por entidad)
├── services/       # Lógica de negocio (entre API y modelos)
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
- Transiciones de estado válidas: `draft→ready`, `ready→draft`, `ready→retired`, `retired→draft`

**Auth:** JWT con `python-jose`. Los admins (`role="admin"`) bypass todos los scope checks en `require_scopes()`.

### Frontend

```
frontend/src/
├── api/            # Funciones axios por entidad (client.ts tiene interceptor JWT + auto-refresh)
├── contexts/       # AuthContext (estado de sesión global)
├── pages/          # Páginas por ruta
├── components/     # Layout (sidebar+topbar), ProtectedRoute
└── types/          # Tipos TypeScript espejo de los schemas Pydantic
```

**Rutas:** `/` Dashboard, `/products` lista, `/products/:sku` detalle (tabs General/Atributos/I18N/SEO), `/categories` árbol taxonomía.

### Base de datos (SQLite)

Fichero: `backend/pim.db` (se crea al arrancar). Tablas principales:
- `users` — autenticación y RBAC
- `categories` — árbol con `parent_id` self-referencial
- `products` — SKU como PK (text), atributos en JSON, FK a categories
- `product_i18n` — traducciones (sku + locale, unique)
- `media_assets` — multimedia vinculada a SKUs
- `audits` — log de cambios (resource, actor, before/after JSON)
- `sync_jobs` — estado de sincronizaciones externas

### Tests

Los tests usan **SQLite en memoria** (`aiosqlite`), sin necesidad de PostgreSQL ni de levantar servicios externos. El `conftest.py` recrea las tablas en cada test y sobreescribe la dependency `get_db`.

## Variables de entorno (backend/.env)

Copiar `backend/.env.example` a `backend/.env`. Por defecto usa SQLite local, no requiere configuración adicional para desarrollo.
