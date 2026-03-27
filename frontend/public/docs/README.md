# Capturas de Pantalla para Documentación

Esta carpeta contiene las imágenes que se muestran en la sección de Documentación de la aplicación.

## Capturas Necesarias

Toma las siguientes capturas de pantalla de la aplicación en funcionamiento y guárdalas en esta carpeta con los nombres exactos indicados:

### 1. Dashboard
**Archivo:** `dashboard-overview.png`
- **Qué capturar:** Vista principal del Dashboard
- **Incluir:** KPIs en la parte superior, gráficos (workflow, calidad) y acciones pendientes
- **Navegación:** Ir a `/` (página principal)
- **Tamaño recomendado:** 1920x1080 px

### 2. Gráfico de Traducciones
**Archivo:** `dashboard-translations-chart.png`
- **Qué capturar:** Gráfico de barras de traducciones por idioma
- **Incluir:** Hacer zoom al gráfico "Estado de Traducciones por Idioma"
- **Navegación:** Ir a `/` y hacer scroll al gráfico de traducciones
- **Tamaño recomendado:** 1200x600 px

### 3. Listado de Productos
**Archivo:** `products-list.png`
- **Qué capturar:** Vista del listado de productos con filtros
- **Incluir:** Panel de filtros lateral, tabla con productos, vistas guardadas (chips)
- **Navegación:** Ir a `/products`
- **Tamaño recomendado:** 1920x1080 px

### 4. Ficha de Producto
**Archivo:** `product-detail.png`
- **Qué capturar:** Detalle de un producto mostrando las pestañas
- **Incluir:** Las 8 pestañas visibles (General, Atributos, I18N, SEO, Media, Calidad, Comentarios, Historial)
- **Navegación:** Ir a `/products` → Click en un producto → Pestaña "General"
- **Tamaño recomendado:** 1920x1080 px

### 5. Traducciones Pendientes
**Archivo:** `i18n-missing.png`
- **Qué capturar:** Lista de productos pendientes de traducción
- **Incluir:** Selector de idioma, tabla con productos sin traducción
- **Navegación:** Ir a `/i18n`
- **Tamaño recomendado:** 1920x1080 px

### 6. Dashboard de Calidad
**Archivo:** `quality-dashboard.png`
- **Qué capturar:** Vista del control de calidad
- **Incluir:** Tabla con productos y sus scores de calidad, reglas aplicadas
- **Navegación:** Ir a `/quality`
- **Tamaño recomendado:** 1920x1080 px

### 7. Dashboard de Sincronización
**Archivo:** `sync-dashboard.png`
- **Qué capturar:** Vista de sincronización con canales externos
- **Incluir:** Lista de trabajos de sincronización, estados (OK/KO), métricas
- **Navegación:** Ir a `/sync`
- **Tamaño recomendado:** 1920x1080 px

### 8. Diálogo de Exportación
**Archivo:** `export-dialog.png`
- **Qué capturar:** Diálogo modal de exportación
- **Incluir:** Selector de campos, opciones de exportación
- **Navegación:** Ir a `/products` → Click en botón "Exportar"
- **Tamaño recomendado:** 1200x800 px

### 9. Wizard de Importación
**Archivo:** `import-validation.png`
- **Qué capturar:** Paso de validación del wizard de importación
- **Incluir:** Tablas de errores/warnings, preview de datos
- **Navegación:** Ir a `/products` → Click en "Importar" → Subir archivo → Vista de validación
- **Tamaño recomendado:** 1920x1080 px

### 10. Panel de Administración
**Archivo:** `admin-users.png`
- **Qué capturar:** Panel de usuarios y permisos
- **Incluir:** Tabla de usuarios con roles, matriz de permisos (si es posible)
- **Navegación:** Ir a `/admin/users` (requiere rol admin)
- **Tamaño recomendado:** 1920x1080 px

### 11. Vista General de la Interfaz
**Archivo:** `tutorial-overview.png`
- **Qué capturar:** Vista general mostrando el menú lateral
- **Incluir:** Menú de navegación completo, área de contenido
- **Navegación:** Cualquier página con menú visible (ej: `/products`)
- **Tamaño recomendado:** 1920x1080 px

## Consejos para Capturar

1. **Resolución:** Usa una resolución de pantalla de 1920x1080 o superior
2. **Datos de prueba:** Asegúrate de tener datos de ejemplo en la aplicación (productos, marcas, categorías, etc.)
3. **Idioma:** Capturas en español (idioma principal de la documentación)
4. **Limpieza:** Oculta información sensible (emails reales, datos de producción)
5. **Formato:** PNG para mejor calidad
6. **Nombres exactos:** Los nombres de archivo deben coincidir exactamente con los indicados

## Alternativa: Placeholder

Si no puedes capturar todas las imágenes inmediatamente, el componente `Screenshot` está configurado para ocultarse automáticamente si la imagen no existe, por lo que la documentación seguirá siendo funcional sin las capturas.

## Optimización

Las imágenes se pueden optimizar para web usando herramientas como:
- **TinyPNG** (https://tinypng.com/)
- **ImageOptim** (https://imageoptim.com/)
- **Squoosh** (https://squoosh.app/)

Objetivo: Mantener tamaño de archivo bajo 200KB por imagen cuando sea posible.
