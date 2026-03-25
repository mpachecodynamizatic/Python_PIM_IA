# PIM (Product Information Management)

Sistema completo de gestión de información de productos con frontend React, backend FastAPI y sistema de importación/exportación configurable.

## 🚀 Características

- **Gestión de Productos**: CRUD completo con soporte para atributos dinámicos, i18n, SEO y media
- **Sistema de Calidad**: Reglas configurables para validación automática de productos
- **Sincronización**: Conectores para exportar/importar a plataformas externas (Shopify, WooCommerce, Amazon, etc.)
- **Mapeo de Campos**: Configuración visual de mapeo de campos desde PIM externo
- **Control de Versiones**: Historial completo de cambios en productos
- **Multi-idioma**: Soporte para traducciones (i18n)
- **Gestión de Usuarios**: Sistema de roles y permisos granulares
- **Exportación/Importación**: CSV, JSON con mapeo configurable

## 📋 Requisitos

- **Backend**: Python 3.11+
- **Frontend**: Node.js 20+
- **Base de Datos**: SQLite (desarrollo) o PostgreSQL (producción)

## 🛠️ Instalación Local

### 1. Clonar el repositorio

```bash
git clone <url-del-repositorio>
cd Python_PIM_IA
```

### 2. Backend

```bash
cd backend

# Crear entorno virtual
python -m venv .venv
.venv\Scripts\activate          # Windows
source .venv/bin/activate       # Linux/Mac

# Instalar dependencias
pip install -r requirements.txt

# Configurar variables de entorno
cp .env.example .env
# Editar .env con tus configuraciones

# Ejecutar migraciones (opcional - se crean automáticamente al arrancar)
python -m alembic upgrade head

# Arrancar servidor
python -m uvicorn app.main:app --reload --port 8000
```

El backend estará disponible en: http://localhost:8000

### 3. Frontend

```bash
cd frontend

# Instalar dependencias
npm install

# Configurar variables de entorno
cp .env.example .env
# Por defecto usa http://localhost:8000/api/v1

# Arrancar servidor de desarrollo
npm run dev
```

El frontend estará disponible en: http://localhost:5173

### 4. Arrancar todo (Windows)

Desde la raíz del proyecto:

```bash
start.bat
```

## 🔑 Credenciales por Defecto

- **Email**: admin@pim.local
- **Password**: admin

⚠️ **Cambiar en producción**

## 📦 Deployment en Coolify

Para desplegar en Coolify, consulta [DEPLOYMENT.md](DEPLOYMENT.md) que incluye:

- Configuración de Docker Compose
- Variables de entorno requeridas
- Configuración de puertos y volúmenes
- Instrucciones paso a paso

## 🏗️ Arquitectura

```
┌──────────────────────────────────────┐
│         Frontend (React)             │
│  - Vite + TypeScript                 │
│  - Material-UI v7                    │
│  - React Query (TanStack)            │
└──────────────────────────────────────┘
           │
           ↓ HTTP (Axios)
┌──────────────────────────────────────┐
│        Backend (FastAPI)             │
│  - Python 3.11                       │
│  - SQLAlchemy 2.x (Async)            │
│  - JWT Authentication                │
│  - Alembic Migrations                │
└──────────────────────────────────────┘
           │
           ↓ SQLAlchemy ORM
┌──────────────────────────────────────┐
│      Base de Datos (SQLite)          │
│  - Desarrollo: pim.db (local)        │
│  - Producción: PostgreSQL (opt)      │
└──────────────────────────────────────┘
```

## 📚 Documentación Técnica

### Backend

- **Modelos**: SQLAlchemy 2.x con async support
- **API**: RESTful endpoints en `/api/v1`
- **Auth**: JWT con refresh tokens
- **Permisos**: Sistema granular de roles y scopes
- **Tests**: 146+ tests con pytest

### Frontend

- **Routing**: React Router v6
- **State**: React Query + React Context
- **Forms**: Material-UI components
- **API Client**: Axios con interceptors
- **Type Safety**: TypeScript estricto

### Base de Datos

Principales tablas:
- `users` - Usuarios y autenticación
- `products` - Información de productos
- `categories` - Taxonomía de categorías
- `product_i18n` - Traducciones
- `media_assets` - Archivos multimedia
- `quality_rules` - Reglas de validación
- `sync_jobs` - Trabajos de sincronización
- `pim_resource_mappings` - Mapeos de campos PIM

Ver [CLAUDE.md](CLAUDE.md) para más detalles de arquitectura.

## 🧪 Tests

### Backend

```bash
cd backend

# Ejecutar todos los tests
python -m pytest tests/ -v

# Ejecutar un test específico
python -m pytest tests/test_products.py::test_create_product -v

# Con cobertura
python -m pytest tests/ --cov=app --cov-report=html
```

### Frontend

```bash
cd frontend

# Type checking
npx tsc --noEmit

# Build test
npm run build
```

## 📖 Comandos Útiles

### Backend

```bash
# Crear migración
python -m alembic revision --autogenerate -m "descripcion"

# Aplicar migraciones
python -m alembic upgrade head

# Rollback última migración
python -m alembic downgrade -1

# Seed de datos (opcional)
python -m seed
```

### Frontend

```bash
# Build para producción
npm run build

# Preview del build
npm run preview

# Lint
npm run lint
```

## 🔧 Configuración

### Variables de Entorno Backend

Ver `backend/.env.example` para la lista completa. Principales:

```bash
DATABASE_URL=sqlite:///./pim.db
SECRET_KEY=your-secret-key
ADMIN_EMAIL=admin@pim.local
ADMIN_PASSWORD=admin
CORS_ORIGINS=http://localhost:5173,http://localhost:5006
```

### Variables de Entorno Frontend

```bash
VITE_API_URL=http://localhost:8000/api/v1
```

## 🐳 Docker

### Build local

```bash
docker build -t pim-app .
docker run -p 5006:5006 pim-app
```

### Docker Compose

```bash
docker-compose up -d
```

La aplicación estará disponible en: http://localhost:5006

## 🔐 Seguridad

- JWT con refresh tokens
- Contraseñas hasheadas con bcrypt
- CORS configurado
- Validación de inputs con Pydantic
- Sistema de permisos granulares (11 recursos × 3 niveles)
- Audit logs inmutables

## 📈 Rendimiento

- Async/await en todo el backend
- Connection pooling (SQLAlchemy)
- Eager loading de relaciones
- Índices en campos críticos
- Frontend code splitting con Vite

## 🤝 Contribuir

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/AmazingFeature`)
3. Commit tus cambios (`git commit -m 'Add some AmazingFeature'`)
4. Push a la rama (`git push origin feature/AmazingFeature`)
5. Abre un Pull Request

## 📄 Licencia

Este proyecto es privado y propietario.

## 📞 Soporte

Para problemas o preguntas:
- Revisa [CLAUDE.md](CLAUDE.md) para guía técnica
- Consulta [DEPLOYMENT.md](DEPLOYMENT.md) para deployment
- Revisa los logs del backend y frontend
- Ejecuta los tests para verificar integridad

## 🗺️ Roadmap

- [ ] Migración a PostgreSQL para producción
- [ ] Autenticación OAuth2 (Google, Microsoft)
- [ ] Notificaciones en tiempo real (WebSockets)
- [ ] API GraphQL (complementario a REST)
- [ ] Exportación a más plataformas (eBay, Etsy)
- [ ] Dashboard analytics avanzado
- [ ] Mobile app (React Native)
