# Deployment en Coolify

Este documento describe cómo desplegar la aplicación PIM en Coolify.

## Prerequisitos

- Servidor con Coolify instalado
- Acceso al panel de Coolify
- Repositorio Git configurado (GitHub, GitLab, etc.)

## Configuración en Coolify

### 1. Crear Nuevo Proyecto

1. En Coolify, haz clic en **"Add New Resource"** → **"Docker Compose"**
2. Nombre: `PIM Application`
3. Conecta tu repositorio Git

### 2. Configurar Variables de Entorno

En la sección de **Environment Variables**, añade las siguientes variables:

**Requeridas:**
```bash
SECRET_KEY=<genera-una-clave-aleatoria-segura-de-al-menos-32-caracteres>
ADMIN_EMAIL=admin@tudominio.com
ADMIN_PASSWORD=<tu-contraseña-segura>
```

**Opcionales (CORS):**
```bash
CORS_ORIGINS=https://tudominio.com,https://www.tudominio.com
```

**Opcionales (Integración con PIM Externo):**
```bash
PIM_BASE_URL=https://pim.gruposvan.com:7005
PIM_MAIL=tu-email@example.com
PIM_PASSWORD=tu-contraseña-pim
PIM_SSL_VERIFY=true
```

### 3. Configurar Puerto

- En la configuración del servicio, establece el puerto público a **5006**
- Coolify automáticamente mapeará el puerto 5006 del contenedor

### 4. Configurar Volúmenes (Persistencia de Datos)

Para que la base de datos SQLite persista entre deployments:

1. Ve a **Storage** → **Add Volume**
2. Nombre: `pim-data`
3. Mount Path: `/app/backend`

Esto garantiza que `pim.db` no se pierda al reiniciar o redesplegar.

### 5. Configurar Dominio (Opcional)

Si quieres usar un dominio personalizado:

1. Ve a **Domains**
2. Añade tu dominio: `pim.tudominio.com`
3. Coolify configurará automáticamente SSL con Let's Encrypt

### 6. Desplegar

1. Haz clic en **"Deploy"**
2. Coolify:
   - Clonará el repositorio
   - Construirá la imagen Docker (multi-stage build)
   - Iniciará los servicios (nginx + uvicorn via supervisor)
   - Expondrá la aplicación en el puerto 5006

### 7. Verificar Deployment

Una vez desplegado, verifica que todo funcione:

- **Health Check**: `http://tu-servidor:5006/health`
- **Frontend**: `http://tu-servidor:5006/`
- **Login**: Usa las credenciales de `ADMIN_EMAIL` y `ADMIN_PASSWORD`

## Arquitectura del Deployment

```
┌─────────────────────────────────────────┐
│         Nginx (Puerto 5006)             │
│  ┌───────────────────────────────────┐  │
│  │  Frontend (React SPA)             │  │
│  │  /                                │  │
│  └───────────────────────────────────┘  │
│                                          │
│  ┌───────────────────────────────────┐  │
│  │  Backend API (FastAPI)            │  │
│  │  /api/v1/*                        │  │
│  │  ↓ Proxy → localhost:8000         │  │
│  └───────────────────────────────────┘  │
└─────────────────────────────────────────┘
         ↓
    SQLite Database
    (Volume persistente)
```

## Actualizar la Aplicación

Para actualizar a una nueva versión:

1. Haz push de los cambios a tu repositorio Git
2. En Coolify, haz clic en **"Redeploy"**
3. Coolify reconstruirá la imagen con los últimos cambios

**Nota**: Los datos de la base de datos se mantendrán gracias al volumen persistente.

## Troubleshooting

### La aplicación no arranca

**Verificar logs:**
```bash
# En Coolify, ve a "Logs" para ver:
# - nginx logs
# - uvicorn logs
# - supervisor logs
```

**Verificar variables de entorno:**
- Asegúrate de que `SECRET_KEY` esté configurada
- Verifica que `ADMIN_EMAIL` y `ADMIN_PASSWORD` sean válidos

### Error 502 Bad Gateway

Esto indica que nginx no puede conectar con uvicorn:

1. Verifica que ambos servicios estén corriendo (supervisor logs)
2. Comprueba que el puerto 8000 esté libre internamente

### Base de datos se pierde al redesplegar

Asegúrate de haber configurado correctamente el volumen persistente en `/app/backend`

### El frontend no carga o muestra errores de API

1. Verifica que `VITE_API_URL` se haya configurado correctamente durante el build (`/api/v1`)
2. Comprueba que nginx esté haciendo proxy correctamente de `/api` → `localhost:8000/api`

## Backup de la Base de Datos

Para hacer backup de la base de datos SQLite:

```bash
# Desde Coolify, ejecuta en el contenedor:
docker cp <container-id>:/app/backend/pim.db ./backup-$(date +%Y%m%d).db
```

O usa el sistema de backups de Coolify si está configurado para el volumen.

## Restaurar Base de Datos

```bash
# Copia el backup al contenedor:
docker cp ./backup-20260325.db <container-id>:/app/backend/pim.db

# Reinicia el contenedor:
# En Coolify: "Restart"
```

## Migrar a PostgreSQL (Opcional)

Si necesitas escalar y quieres usar PostgreSQL en lugar de SQLite:

1. Crea un servicio de PostgreSQL en Coolify
2. Cambia `DATABASE_URL` a: `postgresql+asyncpg://user:pass@postgres:5432/pim`
3. Añade `asyncpg` a `backend/requirements.txt`
4. Redesplegar

**Nota**: Las migraciones Alembic funcionan tanto con SQLite como PostgreSQL.

## Monitoring

Coolify proporciona métricas básicas. Para monitoring avanzado, considera:

- **Logs**: Coolify logs integrados
- **Uptime**: Health check endpoint (`/api/v1/health`)
- **Métricas**: CPU, RAM, Disco desde el panel de Coolify

## Seguridad

### Consideraciones de Producción

1. **SECRET_KEY**: Usa un generador de claves aleatorias seguro
   ```bash
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

2. **Contraseñas**: Nunca uses contraseñas por defecto en producción

3. **CORS**: Limita `CORS_ORIGINS` solo a tus dominios permitidos

4. **HTTPS**: Coolify configura automáticamente SSL con Let's Encrypt

5. **Firewall**: Asegúrate de que solo el puerto 5006 esté expuesto públicamente

## Costos Estimados

Recursos recomendados:
- **CPU**: 2 vCPU
- **RAM**: 2 GB
- **Disco**: 20 GB (10 GB para aplicación + 10 GB para datos)

Rendimiento esperado:
- ~100 usuarios concurrentes
- ~10,000 productos
- Importaciones: ~1000 productos/minuto

Para más productos o usuarios, escala verticalmente o migra a PostgreSQL + múltiples workers de Uvicorn.

## Soporte

Para problemas de deployment:
- Revisa los logs en Coolify
- Consulta CLAUDE.md para comandos de testing local
- Verifica la documentación de Coolify: https://coolify.io/docs
