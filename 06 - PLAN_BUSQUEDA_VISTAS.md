## Plan de trabajo - Búsqueda avanzada y guardado de vistas

### Objetivo
Permitir búsquedas más ricas sobre productos y **guardar vistas** (combinaciones de filtros/ordenación) para reutilizarlas fácilmente desde la UI.

### Fases

1. **Modelo de vistas guardadas (backend)**  
   - Crear un modelo `SavedView` asociado a usuario (`user_id`), con:
     - `resource` (por ahora, `"products"`), `name`, `description`, `filters` (JSON), `is_default`.  
   - API REST para que cada usuario pueda listar/crear/actualizar/eliminar sus vistas guardadas de productos.

2. **Extensión de filtros de búsqueda (backend)**  
   - Ampliar los filtros de `list_products` para soportar:
     - Rangos de fechas (`created_from`, `created_to`, `updated_from`, `updated_to`).  
     - Opcionalmente filtros adicionales (`min_quality`, `max_quality`, etc.) usando el servicio de calidad.  
   - Permitir que el frontend envíe un `view_id` o directamente el JSON de filtros guardados.

3. **Integración en frontend**  
   - En la lista de productos, añadir:
     - Panel de filtros avanzados (estado, categoría, texto, rangos de fecha, etc.).  
     - Selector de “vista guardada” con opción de guardar la vista actual (nombre + descripción).  
   - Recordar y aplicar la vista por defecto del usuario al entrar en la pantalla.

4. **Refinamientos posteriores**  
   - Compartir vistas entre usuarios (p.ej. vistas de equipo).  
   - Vistas para otros recursos (medios, calidad, i18n, etc.).  
   - Exportar/importar definiciones de vistas.

### Estado actual

**Fase 1 - Modelo de vistas guardadas: COMPLETADA**
- Modelo `SavedView` (user_id, resource, name, description, filters JSON, is_default) con `UUIDMixin` + `TimestampMixin`.
- Schema Pydantic: `SavedViewCreate`, `SavedViewUpdate`, `SavedViewRead` con `ConfigDict(from_attributes=True)`.
- Endpoints REST (por usuario autenticado):
  - `GET    /api/v1/views/products` — lista vistas del usuario.
  - `POST   /api/v1/views/products` — crea vista (con auto-unset de default anterior).
  - `GET    /api/v1/views/products/{id}` — detalle de una vista.
  - `PATCH  /api/v1/views/products/{id}` — actualiza vista (nombre, filtros, is_default).
  - `DELETE /api/v1/views/products/{id}` — elimina una vista.

**Fase 2 - Extension de filtros de busqueda: COMPLETADA**
- Filtros avanzados en `list_products`:
  - `created_from`, `created_to` — rango de fecha de creacion (ISO 8601).
  - `updated_from`, `updated_to` — rango de fecha de actualizacion.
  - `has_media` (bool) — productos con/sin media vinculada.
  - `has_i18n` (bool) — productos con/sin traducciones.
  - Filtros existentes mantenidos: `status`, `brand`, `category_id`, `q` (texto).
- `product_service.list_products()` actualizado con subqueries para `has_media`/`has_i18n`.

**Fase 3 - Integracion en frontend: COMPLETADA**
- Tipos TypeScript: `SavedView`, `SavedViewCreate`, `SavedViewUpdate` en `types/savedView.ts`.
- API client: `listProductViews`, `createProductView`, `getProductView`, `updateProductView`, `deleteProductView` en `api/views.ts`.
- `ProductFilters` ampliado con `created_from`, `created_to`, `updated_from`, `updated_to`, `has_media`, `has_i18n`.
- `ProductList.tsx` reescrito con:
  - Barra de vistas guardadas: chips clicables con estrella para default, boton eliminar.
  - Filtros basicos: busqueda texto, estado, categoria.
  - Panel de filtros avanzados (expandible): marca, rangos de fecha (date pickers), has_media, has_i18n.
  - Boton "Guardar vista" para persistir los filtros actuales con nombre, descripcion y opcion de default.
  - Boton "Limpiar filtros" para resetear todos los filtros.
  - Vista por defecto se aplica automaticamente al entrar en la pantalla.
- Tests: 11 tests en `test_saved_views.py` cubriendo CRUD de vistas, logica de default, y filtros avanzados (marca, categoria, rangos de fecha, has_i18n).

**Fase 4 - Refinamientos posteriores: PENDIENTE**
- Compartir vistas entre usuarios (vistas de equipo).
- Vistas para otros recursos (medios, calidad, i18n, etc.).
- Exportar/importar definiciones de vistas.

