## Plan de trabajo - Colaboración y comentarios por producto

### Objetivo
Permitir **comentarios por SKU** para que equipos (marketing, ventas, IT) puedan discutir sobre un producto en un mismo hilo, con trazabilidad de autor y opción de menciones.

### Fases

1. **Modelo y API de comentarios (backend)**  
   - Crear modelo `ProductComment`: `id`, `sku` (FK a products), `user_id` (autor), `body` (texto), `mentions` (JSON opcional con IDs o emails mencionados), timestamps.  
   - Endpoints REST:
     - `GET /api/v1/products/{sku}/comments` — listar comentarios del producto (ordenados por fecha).  
     - `POST /api/v1/products/{sku}/comments` — crear comentario (usuario autenticado).  
     - `DELETE /api/v1/products/{sku}/comments/{comment_id}` — eliminar (solo autor o admin).  
   - Respuestas incluyen autor (id, full_name o email) para mostrar en la UI.

2. **Hilos y respuestas (opcional)**  
   - Añadir `parent_id` opcional en `ProductComment` para permitir respuestas a un comentario y mostrar hilos en el frontend.

3. **Integración en frontend**  
   - En la vista de detalle de producto (`/products/:sku`), añadir pestaña o sección "Comentarios": listado de comentarios, formulario para nuevo comentario, y opción de eliminar los propios.  
   - Mostrar autor y fecha; soporte básico de menciones en el texto (por ejemplo, @email o @nombre).

4. **Refinamientos posteriores**  
   - Notificaciones por email al ser mencionado.  
   - Edición de comentarios.  
   - Etiquetas/tags por comentario (ej. "pendiente revisión", "aprobado").  
   - Filtros por autor o fecha en el listado de comentarios.

### Estado actual
- En curso: implementación de la Fase 1 (modelo `ProductComment` y API de comentarios).
