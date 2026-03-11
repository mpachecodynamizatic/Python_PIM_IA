# Puntos pendientes por plan

Resumen consolidado de todas las fases y funcionalidades pendientes de implementacion en cada plan de trabajo.

> Generado: Marzo 2026
> Total de planes: 7
> Planes completados al 100%: 5 (01, 02, 03, 04, 05)
> Planes con fases pendientes: 2 (06, 07)

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

**Estado: Fase 4 PENDIENTE**

Fases 1-3 completadas (modelo SavedView, filtros avanzados, frontend con vistas guardadas y filtros).

### Pendiente: Fase 4 - Refinamientos posteriores

| # | Funcionalidad | Descripcion | Prioridad |
|---|---------------|-------------|-----------|
| 1 | Vistas compartidas | Compartir vistas entre usuarios (vistas de equipo con visibilidad publica/privada) | Media |
| 2 | Vistas para otros recursos | Extender el sistema de vistas a media, calidad, i18n y otros listados | Baja |
| 3 | Exportar/importar vistas | Permitir exportar definiciones de vistas como JSON e importarlas en otro entorno | Baja |

---

## 07 - Colaboracion y comentarios

**Estado: Fase 4 PENDIENTE**

Fases 1-3 completadas (modelo ProductComment, hilos con parent_id, frontend con pestana de comentarios y respuestas).

### Pendiente: Fase 4 - Refinamientos posteriores

| # | Funcionalidad | Descripcion | Prioridad |
|---|---------------|-------------|-----------|
| 1 | Notificaciones por email | Enviar email cuando un usuario es mencionado en un comentario (@usuario) | Alta |
| 2 | Edicion de comentarios | Permitir editar el cuerpo de un comentario existente (solo autor) | Media |
| 3 | Etiquetas/tags | Anadir tags a los comentarios (ej. "pendiente revision", "aprobado", "urgente") | Baja |
| 4 | Filtros de comentarios | Filtrar comentarios por autor o rango de fecha en el listado | Baja |

---

## Resumen global de pendientes

### Por prioridad

**Alta:**
- Notificaciones por email al ser mencionado en comentarios

**Media:**
- Vistas compartidas entre usuarios (equipo)
- Edicion de comentarios

**Baja:**
- Vistas para otros recursos (media, calidad, i18n)
- Exportar/importar definiciones de vistas
- Etiquetas/tags en comentarios
- Filtros de comentarios por autor/fecha

### Estadisticas

| Metrica | Valor |
|---------|-------|
| Total de planes | 7 |
| Planes completados (100%) | 5 |
| Planes con pendientes | 2 |
| Total fases pendientes | 2 (todas son "Fase 4 - Refinamientos") |
| Total funcionalidades pendientes | 7 |
| Prioridad alta | 1 |
| Prioridad media | 2 |
| Prioridad baja | 4 |
| Tests backend totales | 126 |
