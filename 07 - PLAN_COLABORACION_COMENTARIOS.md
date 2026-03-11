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

**Fase 1 - Modelo y API de comentarios: COMPLETADA**
- Modelo `ProductComment` (sku, user_id, version_id, parent_id, body, mentions JSON) con `UUIDMixin` + `TimestampMixin`.
- Schema Pydantic: `ProductCommentCreate(body, mentions, parent_id)`, `ProductCommentRead(id, sku, user_id, author_name, body, mentions, version_id, parent_id, reply_count, created_at)`.
- Service `product_comment_service` con `list_comments`, `get_replies`, `create_comment`, `delete_comment`.
- Endpoints REST:
  - `GET    /api/v1/products/{sku}/comments` — lista comentarios top-level del producto.
  - `POST   /api/v1/products/{sku}/comments` — crea comentario (con `parent_id` opcional para respuestas).
  - `GET    /api/v1/products/{sku}/comments/{id}/replies` — lista respuestas a un comentario.
  - `DELETE /api/v1/products/{sku}/comments/{id}` — elimina (solo autor o admin).
  - `GET    /api/v1/products/{sku}/versions/{vid}/comments` — comentarios de version.
  - `POST   /api/v1/products/{sku}/versions/{vid}/comments` — crear comentario de version.
- Respuestas incluyen `author_name` (join con `users`), `reply_count` (subquery), y `parent_id`.

**Fase 2 - Hilos y respuestas: COMPLETADA**
- Campo `parent_id` (FK self-referencial a `product_comments.id`, ON DELETE CASCADE) en el modelo.
- `list_comments` filtra solo comentarios top-level por defecto (`parent_id IS NULL`).
- `get_replies(sku, comment_id)` devuelve las respuestas a un comentario especifico.
- `reply_count` calculado via subquery en `list_comments` para cada comentario top-level.
- Validacion: crear respuesta a un `parent_id` inexistente retorna 404.

**Fase 3 - Integracion en frontend: COMPLETADA**
- API client: `getProductComments`, `createProductComment(sku, body, parentId?)`, `deleteProductComment`, `getCommentReplies` en `api/products.ts`.
- Tipo `VersionComment` ampliado con `parent_id` y `reply_count`.
- Nueva pestana "Comentarios" en `ProductDetail.tsx` (tab 6) con:
  - Formulario de nuevo comentario con envio via Enter o boton Send.
  - Lista de comentarios top-level con autor, fecha, cuerpo y boton eliminar.
  - Boton "Responder" por comentario que despliega campo de respuesta inline.
  - Contador de respuestas con boton expandir/colapsar que carga respuestas bajo demanda.
  - Respuestas mostradas con indentacion y borde izquierdo para jerarquia visual.

**Fase 4 - Refinamientos posteriores: PENDIENTE**
- Notificaciones por email al ser mencionado.
- Edicion de comentarios.
- Etiquetas/tags por comentario.
- Filtros por autor o fecha en el listado de comentarios.

**Tests: 13 tests en `test_comments.py`**
- CRUD basico: crear, listar, eliminar comentario.
- Hilos: crear respuesta, listar respuestas, reply_count, parent inexistente 404, top-level excluye replies.
- Permisos: editor no puede borrar comentario ajeno, admin puede borrar cualquiera.
- Validacion: body vacio rechazado, producto inexistente 404.
