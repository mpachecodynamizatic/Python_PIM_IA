## Plan de trabajo - Workflows de aprobación

### Objetivo
Diseñar e implementar un **flujo de aprobación de productos** que obligue a pasar por revisión antes de publicar, dejando trazabilidad clara de quién aprueba qué y cuándo.

### Fases

1. **Modelo de estados y transiciones (backend)** ✅ Completada
   - Ampliados los estados posibles del producto: `draft`, `in_review`, `approved`, `ready`, `retired`.
   - Tabla de transiciones válidas en `VALID_TRANSITIONS`:
     - `draft → in_review` (envío a revisión) o `draft → ready` (publicación directa, compatibilidad)
     - `in_review → approved` (aprobado) o `in_review → draft` (rechazado)
     - `approved → ready` (publicado) o `approved → in_review/draft` (devuelto)
     - `ready → draft` (vuelto a borrador) o `ready → retired` (retirado)
     - `retired → draft` (reactivado)
   - Todas las acciones registradas en `audits` con acción `transition`.

2. **Endpoints de workflow (backend)** ✅ Completada
   - `POST /{sku}/workflow/submit` — `draft → in_review` (requiere scope `products:write`)
   - `POST /{sku}/workflow/approve` — `in_review → approved` (requiere rol `admin`)
   - `POST /{sku}/workflow/reject` — `in_review → draft` (requiere rol `admin`)
   - Cuerpo con motivo opcional (`reason`) almacenado en el `AuditLog`.
   - El endpoint genérico `POST /{sku}/transitions` sigue disponible para transiciones directas.

3. **Integración con frontend** ✅ Completada
   - **Botones contextuales** en la ficha de producto según el estado:
     - `draft`: "Enviar a revisión" (azul) + "Publicar directo" (verde)
     - `in_review`: "Aprobar" (morado) + "Rechazar" (rojo)
     - `approved`: "Publicar" (verde) + "Volver a borrador"
     - `ready`: "Volver a borrador" + "Retirar" (rojo)
     - `retired`: "Reactivar"
   - **Chips de estado** con colores y labels en español:
     - Borrador (naranja), En revisión (azul), Aprobado (morado), Publicado (verde), Retirado (rojo)
   - **Funciones API dedicadas**: `submitForReview()`, `approveProduct()`, `rejectProduct()`
   - Mensajes claros de éxito/error en cada acción.

4. **Refinamientos de seguridad y reporting** ✅ Completada
   - **Scopes diferenciados**:
     - Cualquier usuario con `products:write` puede enviar a revisión
     - Solo usuarios con rol `admin` pueden aprobar o rechazar
   - **Filtros de estado** actualizados en el listado de productos:
     - Nuevo desplegable incluye: Todos, Borrador, En revisión, Aprobado, Publicado, Retirado
   - Los chips de estado en la tabla del listado muestran labels legibles en español.

### Flujo visual

```
  ┌─────────┐   Enviar a    ┌───────────┐   Aprobar   ┌───────────┐   Publicar   ┌─────────┐
  │  draft  │ ──────────>   │ in_review │ ─────────>  │ approved  │ ──────────>  │  ready  │
  │Borrador │               │En revisión│             │ Aprobado  │              │Publicado│
  └─────────┘               └───────────┘             └───────────┘              └─────────┘
       ^                         │                         │                          │
       │         Rechazar        │      Volver a borrador  │                          │
       └─────────────────────────┘                         │       Volver a borrador  │
       └───────────────────────────────────────────────────┘                          │
       └─────────────────────────────────────────────────────────────────────────────┘
                                                                                      │
                                                           Retirar                    v
                                                                              ┌───────────┐
                                                                              │  retired   │
                                                                              │ Retirado   │
                                                                              └───────────┘
                                                                                    │
                                                                     Reactivar      │
                                                              ┌─────────────────────┘
                                                              v
                                                         ┌─────────┐
                                                         │  draft  │
                                                         └─────────┘
```

### Archivos modificados

| Archivo | Cambios |
|---------|---------|
| `backend/app/services/product_service.py` | `VALID_TRANSITIONS` con 5 estados |
| `backend/app/api/v1/products.py` | Endpoints `workflow/submit`, `workflow/approve`, `workflow/reject` |
| `frontend/src/api/products.ts` | Funciones `submitForReview`, `approveProduct`, `rejectProduct` |
| `frontend/src/pages/Products/ProductDetail.tsx` | Botones contextuales, chips con colores/labels, handlers de workflow |
| `frontend/src/pages/Products/ProductList.tsx` | Filtro de estado con in_review/approved, labels en español |
| `frontend/src/types/product.ts` | Type `status` incluye `in_review` y `approved` |

### Estado actual
- **Todas las fases completadas.** Build frontend y 59 tests backend pasando.
