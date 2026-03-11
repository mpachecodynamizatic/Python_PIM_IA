## Plan de trabajo - Versionado de productos

### Objetivo
Implementar un sistema de **historial y versionado** para productos que permita:
- Consultar la evolución de un producto a lo largo del tiempo.
- Restaurar un producto a una versión anterior de forma segura.

### Fases

1. **Historial legible de cambios (backend)**
   - Reutilizar la tabla `audits` para construir una vista de "versiones" por SKU.
   - Nuevo endpoint `GET /api/v1/products/{sku}/versions` que devuelva una lista ordenada cronológicamente de cambios relevantes del producto.
   - Cada versión incluirá: `id`, `sku`, `actor`, `action`, `created_at` y un `snapshot` de los datos del producto en ese momento.

2. **Restauración de versiones (rollback controlado)**
   - Nuevo endpoint `POST /api/v1/products/{sku}/versions/{version_id}/restore`.
   - Política inicial: restaurar únicamente campos de contenido (`brand`, `category_id`, `seo`, `attributes`) dejando el `status` gestionado por las reglas de transición existentes.
   - Registrar en `audits` una acción específica (`restore`) para mantener trazabilidad.

3. **Integración con frontend**
   - En la vista de detalle de producto (`/products/:sku`), pestaña "Historial" que consume el endpoint de versiones.
   - Línea de tiempo con actor, acción, fecha y posibilidad de ver el snapshot.
   - Botón de "Restaurar" con confirmación que llama al endpoint de rollback.

4. **Mejoras avanzadas**
   - **4a. Filtrado del historial por tipo de cambio:**
     - Query param `?action=create,update,transition,restore` en `GET /products/{sku}/versions`.
     - Frontend: `ToggleButtonGroup` para filtrar por tipo (Creación, Edición, Estado, Restauración).
   - **4b. Visualización del snapshot:**
     - Cada versión es expandible en el frontend para mostrar el JSON completo del snapshot.
   - **4c. Comparación visual entre versiones (diff):**
     - Seleccionar dos versiones con el icono de comparar y abrir un diálogo con diff lado a lado.
     - Los campos modificados se resaltan visualmente.
   - **4d. Comentarios asociados a versiones:**
     - Columna `version_id` (nullable) en `product_comments` para vincular comentarios a versiones específicas.
     - Endpoints: `GET/POST /products/{sku}/versions/{version_id}/comments`.
     - Los comentarios a nivel producto y a nivel versión están aislados entre sí.
   - **4e. Políticas de retención:**
     - Endpoint `POST /products/{sku}/versions/retention` (solo admin).
     - Acepta `max_versions` y/o `max_age_days`.
     - Nunca elimina la versión más reciente.
     - Devuelve `{ deleted, remaining }`.

### Endpoints añadidos en Fase 4

| Método | Endpoint | Auth | Descripción |
|--------|----------|------|-------------|
| GET | `/products/{sku}/versions?action=...` | user | Historial filtrable por tipo de acción |
| POST | `/products/{sku}/versions/retention` | admin | Aplicar política de retención |
| GET | `/products/{sku}/versions/{id}/comments` | user | Listar comentarios de una versión |
| POST | `/products/{sku}/versions/{id}/comments` | user | Añadir comentario a una versión |

### Frontend (pestaña Historial)

- **Filtros:** Botones toggle para filtrar por tipo de cambio (Creación, Edición, Estado, Restauración).
- **Cada entrada muestra:** Chip coloreado por tipo de acción, fecha, actor, y botones de acción.
- **Acciones por versión:**
  - Expandir/colapsar snapshot (JSON formateado).
  - Seleccionar para comparar (máx 2 a la vez).
  - Ver/añadir comentarios inline.
  - Restaurar (con confirmación, deshabilitado para transiciones).
- **Diálogo de comparación:** Vista lado a lado con campos modificados resaltados en color.

### Tests
- `tests/test_product_versions.py` — 11 tests cubriendo filtrado, snapshots, retención y comentarios por versión.
- Todos los tests existentes (`test_products.py`) siguen pasando sin regresiones.

### Estado actual
- Fase 1 completada.
- Fase 2 completada.
- Fase 3 completada.
- Fase 4 completada.
