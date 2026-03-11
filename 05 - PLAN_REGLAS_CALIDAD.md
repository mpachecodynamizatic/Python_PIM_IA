## Plan de trabajo - Reglas de calidad configurables por negocio

### Objetivo
Permitir que el negocio defina **reglas de calidad configurables** (por ejemplo, “para estado ready, imagen obligatoria y título > 20 caracteres”) y que el motor de calidad las utilice para calcular el score.

### Fases

1. **Modelo de reglas y API de configuración (backend)**  
   - Añadir modelos para representar reglas de calidad:
     - `QualityRuleSet`: agrupa reglas por contexto (`name`, `description`, `active`, ámbito por defecto).  
     - `QualityRule`: condiciones y pesos por dimensión (ej: `dimension="media"`, `min_score=1.0`, `weight=2.0`, condición opcional basada en estado).  
   - API REST para que un administrador pueda listar, crear y activar/desactivar conjuntos de reglas.

2. **Adaptar el motor de calidad (backend)**  
   - Extender `quality_service` para:
     - Calcular las **dimensiones base** como hasta ahora (`brand`, `category`, `seo`, `attributes`, `media`, `i18n`).  
     - Aplicar el conjunto de reglas activo para recalcular el `overall` con pesos y umbrales según negocio.  
     - Exponer en la respuesta qué regla/conjunto se ha usado.

3. **Integración con frontend**  
   - Añadir en el área de configuración una pantalla simple para administrar reglas de calidad (solo lectura o edición básica).  
   - Mostrar en el dashboard de calidad qué conjunto de reglas está activo y quizás un resumen de los umbrales clave.

4. **Refinamientos posteriores**  
   - Reglas por canal o por categoría/familia de atributos.  
   - Simulaciones “what-if” (cómo cambiaría el score si ajusto tal regla).  
   - Programar cambios de reglas en el tiempo (versionado de reglas).

### Estado actual

**Fase 1 - Modelo de reglas y API de configuración: COMPLETADA**
- Modelo `QualityRuleSet` (name, description, active, rules relationship) con `UUIDMixin` + `TimestampMixin`.
- Modelo `QualityRule` (dimension, weight, min_score, required_status) con FK a rule_set.
- Schemas Pydantic: `QualityRuleSetCreate` (con reglas inline), `QualityRuleSetRead` (con reglas anidadas), `QualityRuleCreate`, `QualityRuleRead`.
- Endpoints REST (todos `admin`):
  - `GET    /api/v1/quality-rules/sets` — lista todos los conjuntos con sus reglas.
  - `POST   /api/v1/quality-rules/sets` — crea conjunto (opcionalmente con reglas inline).
  - `GET    /api/v1/quality-rules/sets/{id}` — detalle de un conjunto.
  - `DELETE /api/v1/quality-rules/sets/{id}` — elimina conjunto (cascade a reglas).
  - `POST   /api/v1/quality-rules/sets/{id}/activate` — activa un conjunto (desactiva los demás).
  - `POST   /api/v1/quality-rules/sets/deactivate-all` — desactiva todos (vuelve a cálculo por defecto).
  - `GET    /api/v1/quality-rules/sets/{id}/rules` — lista reglas de un conjunto.
  - `POST   /api/v1/quality-rules/sets/{id}/rules` — agrega regla a un conjunto.
  - `DELETE /api/v1/quality-rules/rules/{id}` — elimina una regla individual.

**Fase 2 - Adaptar el motor de calidad: COMPLETADA**
- `quality_service.py` refactorizado:
  - `_compute_dimensions(product)` calcula las 6 dimensiones base (0.0–1.0).
  - `_apply_rules(dimensions, rules, product_status)` aplica pesos, umbrales y condiciones por estado.
  - Si `base_score < min_score` → la dimensión se marca como violación y contribuye 0.0 al overall ponderado.
  - Si `required_status` no coincide con el estado del producto → la regla se ignora.
  - Sin conjunto activo → media aritmética por defecto (retrocompatible).
- La respuesta de `/quality/products/{sku}` incluye `rule_set` (id + name) y `violations` (dimensiones que no cumplen umbral).
- La respuesta de `/quality/report` incluye `active_rule_set` global.

**Fase 3 - Integración con frontend: COMPLETADA**
- Tipos TypeScript ampliados: `QualityRule`, `QualityRuleCreate`, `QualityRuleSet`, `QualityRuleSetCreate` en `types/quality.ts`.
- API client ampliado: `listRuleSets`, `createRuleSet`, `deleteRuleSet`, `activateRuleSet`, `deactivateAllRuleSets`, `addRule`, `deleteRule`.
- Nueva página `QualityRulesAdmin` (`/quality/rules`):
  - Lista de conjuntos en accordions expandibles con estado (activo/inactivo).
  - Tabla de reglas por conjunto (dimensión, peso, score mínimo, estado requerido).
  - Acciones: crear conjunto, agregar regla, activar/desactivar, eliminar conjunto o regla.
  - Alerta informativa indicando el conjunto activo o que se usa cálculo por defecto.
- `QualityDashboard` actualizado: muestra nombre del conjunto activo + botón "Reglas" para navegar a configuración.
- Ruta `/quality/rules` registrada en `App.tsx`.

**Datos de ejemplo (seed.py):**
- 3 conjuntos de reglas: "Ecommerce Estandar" (activo, 6 reglas con media/SEO peso doble), "Catalogo Basico" (3 reglas mínimas), "Marketplace Premium" (6 reglas exigentes).

**Fase 4 - Refinamientos posteriores: COMPLETADA**
- **Reglas por categoría:** campo `scope_category_id` (FK a `categories`) en `QualityRule`. Las reglas con categoría específica tienen prioridad sobre las generales para la misma dimensión. Si `scope_category_id` no coincide con el producto, la regla se ignora.
- **Simulación what-if:**
  - `simulate_rule_set(db, rule_set_id)` en `quality_service.py`: calcula scores con un conjunto hipotético y los compara contra el cálculo actual (reglas activas o defecto). Devuelve `current_overall`, `simulated_overall`, `diff` y `simulated_violations` por producto.
  - Endpoint `GET /api/v1/quality/simulate/{rule_set_id}` con paginación.
  - Frontend: botón "Simular" en cada conjunto de `QualityRulesAdmin`, diálogo con tabla comparativa (score actual vs simulado, diferencia con flechas de color, violaciones). Muestra media de cambio global.
  - Tipos TypeScript: `SimulationItem`, `SimulationResult`. API client: `simulateRuleSet()`.
- **Tests:** 14 tests en `test_quality_rules.py` cubriendo CRUD de conjuntos/reglas, activación/desactivación, motor de scoring con pesos y umbrales, violaciones, report con ruleset activo, simulación what-if.
- Versionado de reglas en el tiempo queda como mejora futura opcional.

