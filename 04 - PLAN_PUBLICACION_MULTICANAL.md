## Plan de trabajo - Publicación multicanal / conectores

### Objetivo
Usar la tabla `sync_jobs` para gestionar **sincronizaciones de productos a canales externos** (marketplaces, ecommerce, catálogos), con visibilidad del estado por canal.

### Fases

1. **API de jobs de sincronización (backend)**  
   - Crear esquemas Pydantic para `SyncJob` (lectura/resumen).  
   - Exponer endpoints REST:
     - `POST /api/v1/sync/jobs` para crear un nuevo job de sincronización por canal (parámetros básicos: `channel`, filtros opcionales de productos).  
     - `GET /api/v1/sync/jobs` para listar jobs (paginado, filtrable por canal/estado).  
     - `GET /api/v1/sync/jobs/{job_id}` para ver detalles y métricas.  
   - Implementar un “worker” simple en background que marque el job como `running` y luego `done` con métricas simuladas (número de productos considerados / enviados), dejando el conector real para fases posteriores.

2. **Conectores concretos por canal (backend)**  
   - Diseñar interfaz de conector (por ejemplo, clase o función `run_channel_sync(channel, job, params)` que devuelva métricas).  
   - Implementar al menos un conector real de ejemplo (p. ej. exportación a fichero CSV en disco o llamada a un endpoint HTTP configurable).  
   - Guardar en `metrics` información como: `{"total_products": X, "exported": Y, "skipped": Z}`.

3. **Integración en frontend**  
   - Pantalla de “Sincronizaciones” que liste jobs por canal, estado y fechas.  
   - Posibilidad de lanzar un nuevo job eligiendo canal y filtro de productos (p. ej. por estado `ready`).  
   - Ver detalle de un job con métricas y mensajes de error si los hubiera.

4. **Refinamientos futuros**  
   - Historial de sincronización a nivel de producto (qué SKU está en qué canal y con qué estado).  
   - Reintentos automáticos, programación (cron) y limitación de concurrencia por canal.

### Estado actual

**Fase 1 - API de jobs de sincronización: COMPLETADA**
- Modelo `SyncJob` con `UUIDMixin` + `TimestampMixin`, campos: `channel`, `status`, `filters` (JSON), `started_at`, `finished_at`, `metrics` (JSON), `error_message`.
- Schemas Pydantic: `SyncJobFilters` (status, category_id, brand), `SyncJobCreate`, `SyncJobRead`.
- Endpoints REST:
  - `GET  /api/v1/sync/channels` — lista canales disponibles.
  - `POST /api/v1/sync/jobs` — crea job con canal + filtros, lanza worker en background.
  - `GET  /api/v1/sync/jobs` — lista paginada, filtrable por canal y estado.
  - `GET  /api/v1/sync/jobs/{job_id}` — detalle con métricas.
  - `POST /api/v1/sync/jobs/{job_id}/retry` — re-encola un job fallido/finalizado.
- Worker en background con gestión de errores (`status: failed` + `error_message`).

**Fase 2 - Conectores por canal: COMPLETADA**
- Interfaz base `BaseConnector` (clase abstracta con método `run(db, filters) -> ConnectorResult`).
- `ConnectorResult` dataclass: `total_products`, `exported`, `skipped`, `errors`.
- Registro de conectores en `app/connectors/registry.py` con `get_connector()` y `list_channels()`.
- Conector **CSV** (`csv_connector.py`): exporta productos filtrados a `exports/products_YYYYMMDD_HHMMSS.csv` con traducciones es/en.
- Conector **HTTP** (`http_connector.py`): envía cada producto como JSON a endpoint configurable (por defecto httpbin.org), con gestión de errores por producto.
- Validación de canal al crear job (rechaza canales no registrados).

**Fase 3 - Integración en frontend: COMPLETADA**
- Tipos TypeScript: `SyncJob`, `SyncJobCreate`, `SyncJobFilters`, `SyncJobList` en `frontend/src/types/sync.ts`.
- API client: `frontend/src/api/sync.ts` con `getChannels`, `createSyncJob`, `listSyncJobs`, `getSyncJob`, `retrySyncJob`.
- Página `SyncDashboard` (`frontend/src/pages/Sync/SyncDashboard.tsx`):
  - Tabla de jobs con canal, estado (chip coloreado), filtros, métricas, fechas.
  - Filtros por canal y estado.
  - Auto-refresh cada 5 segundos para seguir jobs en curso.
  - Botón "Reintentar" en jobs fallidos/finalizados.
  - Dialog para crear nuevo job (selección de canal, filtros opcionales de estado y marca).
  - Alertas con mensajes de error de jobs fallidos.
  - Paginación.
- Ruta `/sync` registrada en `App.tsx`.
- Ítem "Sincronización" con icono `SyncAlt` en sidebar de navegación.

**Fase 4 - Refinamientos futuros: PENDIENTE**
- Historial de sincronización a nivel de producto (qué SKU está en qué canal y con qué estado).
- Reintentos automáticos, programación (cron) y limitación de concurrencia por canal.
- Conectores adicionales (Shopify, Amazon, etc.).

