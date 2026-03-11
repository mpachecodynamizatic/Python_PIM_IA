## Plan de trabajo - Gestión avanzada de atributos por familia

### Objetivo
Permitir definir **familias de atributos** reutilizables (p. ej. electrónica, moda, alimentación) y validar los `attributes` de los productos contra el esquema de la familia asociada (o de su categoría).

### Fases

1. **Modelo de datos y API de familias (backend)**  
   - Mantener el enfoque actual donde `Category` tiene un `attribute_schema` en JSON, pero introducir un modelo explícito de **familia de atributos**:
     - `AttributeFamily`: `id`, `code`, `name`, `description`, asociación opcional a `category_id`.
     - `AttributeDefinition`: definición de cada atributo (código, etiqueta, tipo, requerido, opciones).  
   - Exponer endpoints REST para gestionar familias y definiciones (CRUD básico) bajo `/api/v1/attributes` o similar.

2. **Validación de atributos de producto (backend)**  
   - En `product_service.create_product` y `update_product`:
     - Determinar la familia aplicable (por `category_id` o familia explícita cuando exista).  
     - Validar el diccionario `attributes` del producto contra las definiciones:
       - Atributos requeridos presentes.  
       - Tipos compatibles (string, number, boolean, enum).  
       - En enums, el valor debe estar dentro de las opciones permitidas.  
     - Devolver errores 422 con mensajes claros cuando la validación falle.

3. **Evolución del modelo de producto (opcional, backend)**  
   - Añadir un campo `family_id` opcional en `Product` para desacoplar categoría y familia cuando sea necesario.  
   - Estrategia de compatibilidad: si `family_id` es nulo, se sigue usando el esquema de la `category.attribute_schema`; si no, se usa la familia explícita.

4. **Integración en frontend**  
   - En la UI de categorías o configuración, añadir una pantalla para definir familias y sus atributos.  
   - En el formulario de producto, mostrar dinámicamente los campos basados en la familia asociada (en vez de un JSON libre).  
   - Resaltar en tiempo real qué campos son obligatorios o tienen errores de tipo.

### Estado actual
- **Fase 1**: Completada. Modelos `AttributeFamily` y `AttributeDefinition` creados. Endpoints CRUD bajo `/api/v1/attributes/` (familias y definiciones).
- **Fase 2**: Completada. Validacion de atributos integrada en `create_product` y `update_product`. Valida campos requeridos, tipos (string/number/boolean/enum) y opciones de enum. Devuelve 422 con errores detallados.
- **Fase 3**: Completada. Campo `family_id` (FK nullable) añadido al modelo `Product` y schemas. Estrategia: si `family_id` presente se usa esa familia; si no, se busca familia asociada a la categoria.
- **Fase 4**: Completada. Pagina de gestion de familias (`/attributes`) con creacion de familias y definiciones. Formulario dinamico en ficha de producto: cuando el producto tiene familia con definiciones, muestra campos tipados (texto, numero, booleano con switch, enum con select) con indicador de obligatoriedad. Fallback a editor JSON cuando no hay familia o no tiene definiciones.

