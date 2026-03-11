Rol y objetivo
Eres un equipo de ingeniería full‑stack. Debes diseñar e implementar un PIM (Product Information Management) enterprise‑grade con backend en Python (FastAPI), frontend web (React/Next.js) y persistencia en PostgreSQL. El sistema debe ser modular, auditable, seguro, multi‑idioma y escalable, integrándose con PLM, ERP (Microsoft Dynamics 365 Business Central) y canales externos (e‑commerce propio, Amazon, catálogos/CSV, etc.).
Arquitectura de referencia (requerida)

Backend: FastAPI, Pydantic v2, SQLAlchemy 2.x, Alembic (migraciones), Celery + Redis (tareas asíncronas), uvicorn/gunicorn.
DB: PostgreSQL 14+ (particionable), JSONB para atributos extensibles, FTS (tsvector) para SEO/ búsquedas.
Cache/colas: Redis.
Search opcional: OpenSearch/Elasticsearch para catálogo.
Storage multimedia (DAM): S3‑compatible con versionado, presigned URLs, thumbnails/derivadas vía workers.
Frontend: React/Next.js, TypeScript, MUI/Tailwind, TanStack Query, i18n.
AuthN/AuthZ: OAuth2/OIDC, tokens por cliente/API con RBAC granular y scopes (lectura/escritura/sync, por canal y colección). (Alinear con el evolutivo de tokens y permisos avanzados.) [Completado...uarios API | Outlook], [EVOLUTIVO...uarios API | Outlook], [RE: Comple...uarios API | Outlook]
Observabilidad: OpenTelemetry (trazas/metrics/logs), Prometheus + Grafana, structured logging, auditoría de cambios.
CICD: Contenedores (Docker), tests (pytest), Sonar/linters, despliegue en entornos INT/UAT/PROD con feature flags.


1) Onboarding / Ingesta
Objetivo: Importar datos de productos desde Excel/CSV, conectores de proveedores, PLM y fuentes internas (ERP BC).
Requisitos

Asistentes de importación con mapping configurable (column→atributo), pre‑validaciones y dry‑run.
Conectores:

PLM (pull incremental por updated_at, páginas de 1k, reintentos exponenciales).
ERP BC (jobs nocturnos + on‑demand), sincronización por marcas sincronizarConBC, gestión de KO/OK, timestamps, y resincronización inteligente. Basarse en el proceso actual de sincronización PIM ↔ BC para repuestos/sustitutos/ensamblados y reglas de KO/fechas. [Proceso si...puestos v3 | Word], [Proceso si...puestos v2 | Word]


Plantillas Excel/CSV por canal, con validación de caracteres/encoding para JSON/API.
Endpoints (ejemplo)

POST /ingest/uploads (multipart) → jobId
GET /ingest/jobs/{id} → progreso, errores por fila
POST /ingest/providers/{provider}/sync → dispara con filtros (fecha, categoría)
Criterios de aceptación


Importar 100k SKUs en < N horas con <0.5% fallos; reintentos y reporte detallado.
Reglas KO/OK y marca de resincronización según especificación vigente. [Proceso si...puestos v3 | Word], [Proceso si...puestos v2 | Word]


2) Clasificación / Taxonomía
Objetivo: Gestionar jerarquías, categorías y atributos por familia de producto, con herencia y atributos dinámicos (schema‑less).
Requisitos

Árbol de taxonomía (n niveles), plantillas de atributos por categoría, obligatoriedad/visibilidad por canal, tipos (string, rich text, enum, número, fecha, lista, media).
Multi‑idioma en atributos y literales (modelo value + locale). (Alinear con el evolutivo multi‑idioma en PIM/B2B). [evo_PIM_multiidioma | Word]
API

POST /taxonomy/categories
POST /taxonomy/attributes (definición con reglas y locales admitidos)
GET /taxonomy/categories/{id}/schema
Criterios


Cambiar un esquema no rompe el histórico (versionado de esquema + migradores)
Atributos “SEO‑critical” marcables a nivel de categoría (para gating de calidad).


3) Gestión y Gobernanza
Objetivo: Estados del ciclo de vida (draft/ready/retired), workflows, reglas de negocio y auditoría.
Requisitos

Transiciones controladas por RBAC + políticas (quién puede pasar de draft a ready).
Rules Engine (p.ej., simple DSL/JSON) para validar estándares internos (nombres, EAN/GTIN, marca, bundle/kit, etc.).
Auditoría: quién, cuándo, qué (antes/después) a nivel de producto, atributo y media.
API
POST /products/{sku}/transitions (motivo, checklist)
GET /products/{sku}/audit
Criterios
Ningún producto pasa a ready si no cumple data quality gates definidos.


4) Enriquecimiento
Objetivo: Edición rica (descripciones, storytelling, assets), traducciones, SEO.
Requisitos

Editor rich‑text con bloques (tablas, bullets, specs), campos SEO (title, meta‑desc, keywords), URIs canónicas.
Traducciones: cola async, glosarios, prioridad por canal e idioma, re‑uso de traducciones, detección de cambios y back‑translation opcional. (Conectar con el planteamiento multi‑idioma ya tratado en vuestros documentos). [evo_PIM_multiidioma | Word]
API

POST /products/{sku}/i18n/{locale} (upsert)
GET /products/{sku}?include=i18n,seo,media
Criterios


TTFB de ficha enriquecida < 200ms (cache + ETag) en lectura.
Control de versiones de descripciones y diff visual.


5) Control de Calidad (Data Quality)
Objetivo: Dashboards de completitud y bloqueo de publicación si faltan datos críticos.
Requisitos

“Data Quality Score” por SKU, por categoría y por canal.
Rules/Gates: EAN requerido, 3+ imágenes ≥ 1200px, marca, categoría, título SEO, atributos “must‑have”, traducciones obligatorias según mercados activos.
Paneles (por usuario/perfil) con filtros: pendientes, KO, near‑ready, “missing translations”, “SEO under threshold”.
API
GET /quality/completeness?category=...&channel=...
POST /quality/recalculate (batch)
Criterios
Ningún ready se sindica si su score < umbral de canal.


6) Gestión Multimedia (DAM)
Objetivo: Centralizar imágenes, vídeos, manuales y vincularlos a SKUs con controles de visibilidad por canal.
Requisitos

Ingesta masiva, generación de thumbnails/derivadas, etiquetado, deduplicación perceptual (pHash).
Control de visibilidad hacia B2B (checkbox noMostrarEnB2b) y resto de canales; reflejar en sincronizaciones. (Basado en el evolutivo de visibilidad multimedia). [evo_PIM_B2...tos_en_B2B | PDF]
API

POST /media (presigned upload)
PATCH /media/{id} (metadatos, visibilidad por canal)
POST /products/{sku}/media/link
Criterios


Latencia < 100ms en obtención de presigned URL; políticas de expiración y anti‑hotlink.


7) Distribución / Sindicación
Objetivo: Exportar datos adaptados a cada canal (Amazon, web propia, catálogos/CSV, comparadores).
Requisitos

Mappers por canal con validadores y test de contrato.
Programación de exportaciones (cron) + on‑demand + webhooks.
Generación automática de CSV para Minderest (job parametrizable, con layout esperado y evidencia de entrega). [EVOLUTIVO...Minderest | Outlook]
API

POST /syndication/{channel}/export (filters: colección, fecha cambio, idioma)
GET /syndication/jobs/{id} (estado, artefactos)
Criterios


100% conformidad de esquema por canal; reintentos y DLQ en fallos.


8) Seguridad, Tokens y Permisos (API)
Objetivo: Autenticación robusta, tokens con scopes y permisos por tipo de recurso y canal.
Requisitos

Emisión/rotación de tokens, auditoría de uso, rate‑limits por cliente, scopes granulares: products:read, products:write, media:write, syndication:run, quality:read, etc.
Políticas por rol: admin, editor, revisor calidad, integrador externo.
Criterios: pruebas de penetración básicas, logging de denegaciones, separación de datos por tenant.
(Respaldado por vuestros evolutivos de Tokens/Permisos API.) [Completado...uarios API | Outlook], [EVOLUTIVO...uarios API | Outlook]


9) Integraciones clave (BC, PLM, e‑commerce)
BC: Respetar vuestras reglas de sincronización para productos y tablas relacionadas, controlando KO/OK, timestamps y reintentos; exponer contadores y logs de lotes. 
PLM: Pull incremental con hashing de payload y reconciliación de atributos técnicos.
B2B / Web: Accesos y API para partners (ej., AYCO), con posibilidad de acceso al PIM y/o endpoints de catálogo, evitando procesos manuales. (Enhebrar la necesidad expresada por partners de acceso/API del PIM). [Proceso si...puestos v3 | Word], [Proceso si...puestos v2 | Word] [Re: MHD -...UCTOS SVAN | Outlook]

10) Modelado de datos (resumen mínimo en PostgreSQL)
SQL-- Productos (cabecera)CREATE TABLE products (  sku TEXT PRIMARY KEY,  brand TEXT NOT NULL,  status TEXT CHECK (status IN ('draft','ready','retired')) NOT NULL DEFAULT 'draft',  category_id UUID NOT NULL,  seo JSONB DEFAULT '{}'::jsonb,  attributes JSONB NOT NULL DEFAULT '{}'::jsonb, -- extensible por taxonomía  updated_at TIMESTAMP NOT NULL,  created_at TIMESTAMP NOT NULL);-- I18N desacoplado (opcional si no se usa JSONB por-locale)CREATE TABLE product_i18n (  sku TEXT REFERENCES products(sku) ON DELETE CASCADE,  locale TEXT NOT NULL,  title TEXT NOT NULL,  description_rich JSONB,  UNIQUE(sku, locale));-- Multimedia (DAM)CREATE TABLE media_assets (  id UUID PRIMARY KEY,  sku TEXT REFERENCES products(sku),  kind TEXT CHECK (kind IN ('image','video','pdf','manual')),  url TEXT NOT NULL,  no_mostrar_en_b2b CHAR(1) NOT NULL DEFAULT 'N', -- visibilidad B2B  metadata JSONB DEFAULT '{}'::jsonb);-- Sincronización (jobs)CREATE TABLE sync_jobs (  id UUID PRIMARY KEY,  channel TEXT NOT NULL,  status TEXT CHECK (status IN ('queued','running','ok','ko')),  started_at TIMESTAMP, finished_at TIMESTAMP,  metrics JSONB);-- AuditoríaCREATE TABLE audits (  id UUID PRIMARY KEY,  resource TEXT, resource_id TEXT, actor TEXT, action TEXT,  before JSONB, after JSONB, created_at TIMESTAMP);``Mostrar más líneas

11) API (contratos esenciales en FastAPI – ejemplo OpenAPI YAML abreviado)
SQLopenapi: 3.0.3info:  title: PIM API  version: 1.0.0paths:  /products:    get:      parameters: [{name: q, in: query, schema: {type: string}}]      responses: { '200': { description: OK }}    post:      security: [{ OAuth2: [products:write] }]      requestBody: { required: true }      responses: { '201': { description: Created }}  /products/{sku}:    get: { responses: { '200': { description: OK }}}    patch:      security: [{ OAuth2: [products:write] }]      responses: { '200': { description: Updated }}  /taxonomy/categories:    post:      security: [{ OAuth2: [taxonomy:write] }]      responses: { '201': { description: Created }}  /media:    post:      security: [{ OAuth2: [media:write] }]      responses: { '201': { description: Uploaded }}  /quality/completeness:    get:      responses: { '200': { description: OK }}  /syndication/{channel}/export:    post:      security: [{ OAuth2: [syndication:run] }]      responses: { '202': { description: Accepted }}components:  securitySchemes:    OAuth2:      type: oauth2      flows:        clientCredentials:          tokenUrl: /oauth/token          scopes:            products:read: Lectura catálogo            products:write: Escritura catálogo            media:write: Gestión media            taxonomy:write: Gestión taxonomía            syndication:run: Lanzar exportacionesMostrar más líneas

12) UI/UX (resumen)

Paneles: “Mi trabajo hoy” (pendientes por estado), Completitud por canal, “Errores de sincronización BC/PLM”, “Assets faltantes”.
Ficha SKU: pestañas General, Atributos, I18N, SEO, Media, Calidad, Auditoría.
Asistentes: importación Excel/CSV (con preview), mapeos guardables, reglas aplicadas en tiempo real.
(Referirse al documento de interfaces PIM para consistencia de patrones de formularios/tablas/alertas). [Documentac...ynamizatic | Word]


13) Rendimiento, seguridad y compliance

NFRs: P95 < 250ms en lectura catálogos, exportaciones 50k SKUs < N min con colas y particiones.
Seguridad: CSP, HTTPS estricto, secretos en vault, RBAC por scope, rate limiting, logs de acceso/denegación, trazas OTel. (Alineado con vuestros tokens y permisos API). [Completado...uarios API | Outlook], [EVOLUTIVO...uarios API | Outlook]
Backups y DR: PITR en Postgres, versionado de objetos en DAM, restauración de catálogos por rango de fechas.


14) Casos de uso y pruebas esenciales (checklist)

Ingesta Excel con mapping + dry‑run + KO detallado.
Pull PLM incremental; sync BC con reglas de KO/OK; resincronización y auditoría. [Proceso si...puestos v3 | Word], [Proceso si...puestos v2 | Word]
Enriquecimiento multi‑idioma con jobs de traducción y re‑render SEO. [evo_PIM_multiidioma | Word]
Gestión DAM: subida, derivadas, no mostrar en B2B y propagación a exportadores. [evo_PIM_B2...tos_en_B2B | PDF]
Export CSV Minderest programado y on‑demand con evidencias. [EVOLUTIVO...Minderest | Outlook]
API externa para partners (lectura catálogos, filtros, imágenes), con tokens y scopes por cliente. (Necesidad expresada por partners). [Re: MHD -...UCTOS SVAN | Outlook]


15) Entregables

Repo mono o multi con backend, frontend, infraestructura (IaC opcional).
OpenAPI completo + SDK (Python/TS).
Colecciones de postman + datos de ejemplo.
Guías: despliegue, operación, runbooks de sincronización, troubleshooting BC/PLM, manual de usuario.
Dashboards de calidad y de exportaciones por canal.