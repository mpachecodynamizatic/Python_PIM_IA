# Puntos pendientes por plan

Resumen consolidado de todas las fases y funcionalidades pendientes de implementacion en cada plan de trabajo.

> Generado: Marzo 2026
> Total de planes: 8
> Planes completados al 100%: 8 (01, 02, 03, 04, 05, 06, 07, 08)
> Planes con fases pendientes: 0

---

## 01 - Versionado de productos

**Estado: COMPLETADO**

Todas las fases implementadas:
- Fase 1: Modelo de versiones y snapshots automaticos
- Fase 2: Endpoints de consulta y restauracion
- Fase 3: Integracion en frontend (historial, snapshot, comparacion, restauracion)
- Fase 4: Filtrado por accion, diff visual, comentarios por version, retencion

---

## 02 - Workflows de aprobacion

**Estado: COMPLETADO**

Todas las fases implementadas:
- Fase 1: Estados y transiciones en backend
- Fase 2: Flujo submit/approve/reject
- Fase 3: Integracion en frontend
- Fase 4: Tests (59 tests backend pasando)

---

## 03 - Familias de atributos

**Estado: COMPLETADO**

Todas las fases implementadas:
- Fase 1: Modelo de familias y definiciones
- Fase 2: Asignacion de familia a producto
- Fase 3: Editor estructurado en frontend
- Fase 4: Validacion y scoring por atributos

---

## 04 - Publicacion multicanal

**Estado: COMPLETADO**

Todas las fases implementadas:
- Fase 1: Modelo de canales y conectores (CSV, HTTP)
- Fase 2: Flujo de publicacion y metricas
- Fase 3: Frontend basico (dashboard, creacion de jobs)
- Fase 4: Historial de sync por producto, reintentos con backoff exponencial, programacion cron, concurrencia por canal, conectores Shopify/Amazon/WooCommerce (29 tests)

---

## 05 - Reglas de calidad

**Estado: COMPLETADO**

Todas las fases implementadas:
- Fase 1: Modelo de conjuntos de reglas y reglas individuales
- Fase 2: Motor de scoring con pesos, min_score y scope por categoria
- Fase 3: Integracion en frontend (admin de reglas, activar/desactivar)
- Fase 4: Simulacion what-if, tests (14 tests)

---

## 06 - Busqueda avanzada y vistas guardadas

**Estado: COMPLETADO**

Todas las fases implementadas:
- Fase 1: Modelo SavedView, filtros avanzados en API (brand, category, date, has_i18n)
- Fase 2: Endpoint de busqueda unificado con paginacion y ordenacion
- Fase 3: Frontend con vistas guardadas, chips de vistas, filtros avanzados
- Fase 4: Vistas compartidas (is_public), endpoints genericos /{resource}, exportar/importar vistas JSON (23 tests)

---

## 07 - Colaboracion y comentarios

**Estado: COMPLETADO**

Todas las fases implementadas:
- Fase 1: Modelo ProductComment, endpoints REST (listar, crear, eliminar)
- Fase 2: Hilos con parent_id, reply_count, GET /replies
- Fase 3: Frontend con pestaña Comentarios, hilos expandibles, formulario de nuevo comentario
- Fase 4: Edición de comentarios (PATCH, solo autor), etiquetas/tags (JSON array), filtros por autor/tag/fecha, frontend con edit inline + chips de tags + panel de filtros (24 tests)

---

## 08 - Exportación / Importación Excel (estilo RapidStart)

**Estado: COMPLETADO**

Todas las fases implementadas:
- Fase 1: Motor de exportación backend (`ExportConfig`, `export_service.py`, endpoints)
- Fase 2: Motor de importación con validación backend (`import_service.py`, dry-run validate + apply)
- Fase 3: Frontend — `ExportDialog` con selector de campos y descarga de plantilla
- Fase 4: Frontend — `ImportDialog` wizard 3 pasos (subida → informe validación → resultado), integrado en ProductList
- 7 recursos soportados: products, categories, product_i18n, media_assets, users, quality_rules, attribute_families
- 20 tests pasando (9 exportación + 11 importación)

---

## Resumen global de pendientes

Todos los planes (01-08) han sido completados al 100%. No hay funcionalidades pendientes.

### Estadisticas

| Metrica | Valor |
|---------|-------|
| Total de planes | 8 |
| Planes completados (100%) | 8 |
| Planes con pendientes | 0 |
| Total fases pendientes | 0 |
| Total funcionalidades pendientes | 0 |
| Tests backend totales | 146 |
