## Plan de trabajo - Exportación / Importación Excel (estilo RapidStart)

### Objetivo

Implementar un motor genérico de **exportación e importación Excel** inspirado en el concepto RapidStart de Business Central:

- Exportar **cualquier tabla** a Excel eligiendo los campos a incluir y aplicando filtros previos.
- Descargar una **plantilla vacía** con las cabeceras configuradas para facilitar la preparación de datos.
- Importar un fichero Excel que siga la misma configuración de campos, con **validaciones completas** antes de confirmar la carga:
  - Tipos de dato y formatos.
  - Valores obligatorios y unicidad.
  - Integridad referencial (FK: si el SKU de un producto no existe, error).
  - Reglas de negocio específicas (transiciones de estado, categorías activas, etc.).
- Presentar al usuario un **informe de validación** (fila a fila) antes de confirmar la importación.
- Soporte inicial para: `products`, `categories`, `product_i18n`, `media_assets`, `users`, `quality_rules`, `attribute_families`.

---

### Analogía con RapidStart / BC

| Concepto BC | Equivalente PIM |
|-------------|-----------------|
| Paquete de configuración | `ExportConfig` por recurso |
| Hoja de paquete | Pestaña Excel por recurso |
| Selección de campos | Checkboxes en diálogo de exportación |
| Filtro de registros | Panel de filtros reutilizado de las vistas guardadas |
| Validación de paquete | `POST /export/{resource}/import/validate` (dry-run) |
| Aplicar paquete | `POST /export/{resource}/import` |
| Plantilla vacía | `GET /export/{resource}/template` |

---

### Fases

#### Fase 1 — Motor de exportación (backend)

1. **Dependencia:** Añadir `openpyxl` a `requirements.txt`.

2. **`ExportConfig` (por recurso):**
   Definir en `app/export/configs.py` un diccionario `EXPORT_CONFIGS` con un `ExportConfig` para cada recurso soportado. Cada `ExportConfig` contiene:
   - `resource`: identificador único (`"products"`, `"categories"`, etc.)
   - `label`: nombre legible para la UI
   - `fields`: lista ordenada de `ExportField`:
     - `key`: nombre del atributo Python / columna BD
     - `label`: cabecera en Excel
     - `type`: `str | int | float | bool | date | datetime | json | enum`
     - `required`: bool (para importación)
     - `default_include`: bool (campo incluido por defecto en la selección)
     - `readonly`: bool (se exporta pero no se acepta en importación — p.ej. `created_at`)
     - `fk`: `FKConstraint | None` — recurso + campo al que apunta para validar FK
   - `filters`: referencia al servicio de listado existente para aplicar filtros previos
   - `upsert_key`: campo(s) que identifican un registro para decidir crear vs. actualizar (p.ej. `["sku"]` para productos)

3. **Servicio `export_service.py`:**
   - `get_config(resource)` — devuelve `ExportConfig` o lanza 404.
   - `list_fields(resource)` — devuelve metadatos de campos para la UI.
   - `export_to_excel(resource, selected_fields, filters, db)`:
     - Llama al servicio de listado del recurso con los filtros indicados (reutiliza `product_service.list_products`, etc.).
     - Construye un `Workbook` con `openpyxl`:
       - Fila 1: cabeceras con estilo (fondo azul, negrita, filtro automático).
       - Filas 2–N: datos serializados según el tipo de cada campo.
       - Los campos `json` se serializan como string JSON.
       - `datetime` en formato `YYYY-MM-DD HH:MM`.
     - Devuelve el `BytesIO` del fichero.
   - `generate_template(resource, selected_fields)`:
     - Workbook solo con la fila de cabeceras + fila de ejemplo (valores de ayuda en gris).
     - Hoja adicional oculta `_meta` con la lista de campos, tipos y validaciones para que el importador la use.

4. **Endpoints (router `app/api/v1/export.py`):**

   | Método | Ruta | Auth | Descripción |
   |--------|------|------|-------------|
   | GET | `/export/{resource}/fields` | user | Metadatos de campos disponibles |
   | POST | `/export/{resource}` | user | Exportar → descarga Excel |
   | GET | `/export/{resource}/template` | user | Descargar plantilla vacía |

   Body de `POST /export/{resource}`:
   ```json
   {
     "fields": ["sku", "name", "status", "brand"],
     "filters": { "status": "draft", "has_media": false }
   }
   ```
   Respuesta: `StreamingResponse` con `Content-Type: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet` y `Content-Disposition: attachment; filename="{resource}_{timestamp}.xlsx"`.

---

#### Fase 2 — Motor de importación con validación (backend)

1. **Servicio `import_excel_service.py`:**

   - `parse_excel(file_bytes, resource)`:
     - Lee el fichero con `openpyxl` (modo lectura-only).
     - Detecta cabeceras en fila 1 y las mapea a `key` del `ExportConfig`.
     - Devuelve lista de dicts crudos (fila → dict).
     - Error si las cabeceras no coinciden con ningún campo configurado.

   - `validate_rows(resource, rows, db)` → `ImportValidationResult`:
     - Procesa cada fila independientemente:
       - **Campos requeridos:** valor vacío en campo `required=True` → error.
       - **Tipos:** intenta convertir el valor al tipo declarado → error con descripción.
       - **Enums:** comprueba que el valor pertenece al conjunto permitido.
       - **FK:** para cada campo con `fk` definido, consulta la BD → error si no existe. Ej: `category_id` debe existir en `categories`; `sku` en `product_i18n` debe existir en `products`.
       - **Unicidad / upsert:** si `upsert_key` ya existe → modo *update*; si no existe → modo *create*. Se indica en el resultado por fila.
       - **Reglas de negocio:** para `products` con campo `status` presente, si el registro ya existe se comprueba que la transición sea válida.
     - Resultado agregado: `{ total, valid, errors: [{ row, field, code, message }], preview: [...] }`.

   - `apply_import(resource, validated_rows, db)`:
     - Solo ejecutable si `validated_rows.errors == []` (sin errores bloqueantes).
     - Itera sobre las filas validadas ejecutando INSERT o UPDATE en transacción.
     - Registra en `audits` cada operación con `action="import"`.
     - Devuelve `{ created, updated, skipped }`.

2. **Endpoints:**

   | Método | Ruta | Auth | Descripción |
   |--------|------|------|-------------|
   | POST | `/export/{resource}/import/validate` | user | Dry-run: valida sin guardar |
   | POST | `/export/{resource}/import` | user | Importar y guardar |

   Body: `multipart/form-data` con campo `file` (`.xlsx`).

   Respuesta de validate:
   ```json
   {
     "total": 42,
     "valid": 40,
     "errors": [
       { "row": 5, "field": "category_id", "code": "fk_not_found", "message": "La categoría 'abc123' no existe" },
       { "row": 12, "field": "status", "code": "invalid_transition", "message": "No se puede pasar de 'retired' a 'draft' directamente" }
     ],
     "preview": [
       { "row": 1, "mode": "create", "sku": "PROD-001", "name": "Producto nuevo" },
       { "row": 2, "mode": "update", "sku": "PROD-002", "name": "Nombre actualizado" }
     ]
   }
   ```

3. **Warnings vs. Errors:**
   - `code` prefijado con `error_` es bloqueante (no se puede importar).
   - `code` prefijado con `warn_` es no bloqueante (se puede importar pero el usuario confirma).
   - Ej: `warn_sku_exists` si hay upsert (se sobreescribirá un registro existente).

---

#### Fase 3 — Exportación en el frontend

1. **Botón "Exportar" en la barra de herramientas** de cada página de listado (`ProductList`, `CategoryList`, etc.).

2. **Diálogo de exportación (`ExportDialog`):**
   - Carga la lista de campos con `GET /export/{resource}/fields`.
   - Muestra un **campo de selección múltiple** tipo checkbox-list agrupado por categoría (campos básicos, atributos, metadatos, timestamps).
   - Botones "Seleccionar todos" / "Deseleccionar todos".
   - Campo informativo del número de registros que se exportarán (aplica los filtros activos de la vista actual).
   - Opción "Incluir solo registros visibles con los filtros actuales" (checkbox, activado por defecto).
   - Botón "Exportar" → llama `POST /export/{resource}` → descarga el fichero.
   - Botón "Descargar plantilla vacía" → llama `GET /export/{resource}/template`.

3. **Tipos TypeScript:**
   - `ExportField`, `ExportConfig`, `ExportRequest` en `types/export.ts`.
   - `exportResource(resource, request)`, `downloadTemplate(resource)`, `getExportFields(resource)` en `api/export.ts`.

---

#### Fase 4 — Importación en el frontend

1. **Botón "Importar" en la barra de herramientas** junto al botón "Exportar".

2. **Diálogo de importación (`ImportDialog`) — 3 pasos tipo wizard:**

   **Paso 1 — Seleccionar fichero:**
   - Dropzone para subir fichero `.xlsx`.
   - Mensaje de ayuda con enlace "Descargar plantilla" para que el usuario prepare el fichero con el formato correcto.
   - Botón "Validar" → llama `POST /export/{resource}/import/validate`.

   **Paso 2 — Informe de validación:**
   - Resumen: `X registros, Y válidos, Z errores, W avisos`.
   - Tabla de errores con columnas: Fila, Campo, Código, Descripción.
   - Tabla de preview (primeras 10 filas) con indicador de modo (`CREATE` en verde / `UPDATE` en naranja).
   - Si hay errores bloqueantes: el botón "Importar" está deshabilitado con tooltip explicativo.
   - Si solo hay avisos: el botón "Importar" muestra badge con el número de avisos y pide confirmación.

   **Paso 3 — Resultado:**
   - Muestra `{ created, updated, skipped }`.
   - Botón "Cerrar" que recarga la tabla con los nuevos datos.

3. **Tipos TypeScript:**
   - `ImportValidationError`, `ImportPreviewRow`, `ImportValidationResult`, `ImportResult` en `types/export.ts`.
   - `validateImport(resource, file)`, `applyImport(resource, file)` en `api/export.ts`.

---

### Recursos soportados (configuración inicial)

| Resource | Upsert key | FK validadas | Campos export por defecto |
|----------|------------|--------------|---------------------------|
| `products` | `sku` | `category_id → categories.id` | sku, name, status, brand, category_id, description, created_at |
| `categories` | `id` | `parent_id → categories.id` | id, name, description, parent_id, created_at |
| `product_i18n` | `sku + locale` | `sku → products.sku` | sku, locale, name, description, seo_title, seo_desc |
| `media_assets` | `id` | `sku → products.sku` | id, sku, filename, media_type, url, created_at |
| `users` | `email` | — | id, email, role, is_active, created_at |
| `quality_rules` | `id` | — | id, name, field, condition, value, severity, is_active |
| `attribute_families` | `id` | — | id, name, description, attributes (JSON) |

---

### Validaciones por tipo de dato

| Tipo | Validación |
|------|-----------|
| `str` | Longitud máxima si el campo la tiene |
| `int` / `float` | Conversión numérica estricta |
| `bool` | Acepta `true/false`, `1/0`, `sí/no`, `yes/no` (case-insensitive) |
| `date` | Formatos `YYYY-MM-DD`, `DD/MM/YYYY` |
| `datetime` | ISO 8601 o `YYYY-MM-DD HH:MM` |
| `enum` | Valor debe pertenecer al conjunto declarado en `ExportField.choices` |
| `json` | JSON válido (para campos como `attributes`, `seo`, `tags`) |
| FK | Consulta en BD dentro de la misma transacción de validación |

---

### Arquitectura de ficheros nuevos

```
backend/app/
├── export/
│   ├── __init__.py
│   ├── configs.py          # EXPORT_CONFIGS: dict[str, ExportConfig]
│   ├── export_service.py   # export_to_excel(), generate_template()
│   ├── import_service.py   # parse_excel(), validate_rows(), apply_import()
│   └── validators.py       # Validadores por tipo + FK checker
backend/app/api/v1/
│   └── export.py           # Router con todos los endpoints
frontend/src/
├── api/
│   └── export.ts           # Funciones API
├── types/
│   └── export.ts           # Tipos TS
└── components/
    ├── ExportDialog.tsx     # Diálogo de exportación
    └── ImportDialog.tsx     # Wizard de importación (3 pasos)
```

---

### Tests

- `tests/test_export.py` — tests del motor de exportación:
  - Exportar productos con filtros → Excel con cabeceras y datos correctos.
  - Exportar con selección parcial de campos.
  - Descargar plantilla vacía → Excel con cabeceras y hoja `_meta`.

- `tests/test_import.py` — tests del motor de importación:
  - Validar Excel correcto → sin errores, preview con modos create/update.
  - Validar con FK inválida → error `fk_not_found`.
  - Validar con tipo incorrecto → error de tipo.
  - Validar con campo requerido vacío → error `required`.
  - Validar transición de estado inválida → error `invalid_transition`.
  - Importar correctamente → `{ created: N, updated: M }` + registro en `audits`.
  - Importar `product_i18n` con SKU inexistente → error bloqueante.

---

### Dependencias a añadir

```
openpyxl>=3.1.2
```

En frontend:
```
# No se requiere librería adicional; la descarga usar Blob + URL.createObjectURL
```

---

### Estado actual

- Fase 1 — Motor de exportación backend: **COMPLETADO** ✅
- Fase 2 — Motor de importación con validación backend: **COMPLETADO** ✅
- Fase 3 — Exportación en frontend: **COMPLETADO** ✅
- Fase 4 — Importación en frontend (wizard): **COMPLETADO** ✅

**Plan COMPLETADO** — 20/20 tests pasando (9 exportación + 11 importación).
