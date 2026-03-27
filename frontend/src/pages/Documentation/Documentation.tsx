import { useState } from 'react';
import {
  Box,
  Paper,
  Typography,
  List,
  ListItemButton,
  ListItemText,
  Divider,
  Chip,
  Alert,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Button,
  Card,
  CardMedia,
  CardContent,
} from '@mui/material';
import {
  Dashboard,
  Inventory,
  Category,
  Translate,
  PhotoLibrary,
  BarChart,
  SyncAlt,
  FileDownload,
  FileUpload,
  People,
  Storefront,
  LocalShipping,
  Hub,
  HelpOutline,
  Print,
  School,
} from '@mui/icons-material';

interface Section {
  id: string;
  title: string;
  icon: JSX.Element;
  content: JSX.Element;
}

// Componente auxiliar para mostrar capturas de pantalla
function Screenshot({ src, alt, caption }: { src: string; alt: string; caption?: string }) {
  return (
    <Card sx={{ mb: 3, mt: 2 }}>
      <CardMedia
        component="img"
        image={src}
        alt={alt}
        sx={{
          maxHeight: 500,
          objectFit: 'contain',
          backgroundColor: '#f5f5f5',
          border: '1px solid #e0e0e0',
        }}
        onError={(e: any) => {
          // Si la imagen no existe, mostrar placeholder
          e.target.style.display = 'none';
        }}
      />
      {caption && (
        <CardContent>
          <Typography variant="caption" color="text.secondary" sx={{ fontStyle: 'italic' }}>
            {caption}
          </Typography>
        </CardContent>
      )}
    </Card>
  );
}

export default function Documentation() {
  const [selectedSection, setSelectedSection] = useState('intro');

  const handlePrint = () => {
    window.print();
  };

  const sections: Section[] = [
    {
      id: 'intro',
      title: 'Introducción',
      icon: <Dashboard fontSize="small" />,
      content: (
        <>
          <Typography variant="h4" gutterBottom>
            Bienvenido al PIM (Product Information Management)
          </Typography>

          <Alert severity="info" sx={{ mb: 3 }}>
            Este manual te guiará a través de todas las funcionalidades del sistema PIM para gestionar tu catálogo de productos de manera eficiente.
          </Alert>

          <Typography variant="h5" gutterBottom sx={{ mt: 3 }}>
            ¿Qué es un PIM?
          </Typography>
          <Typography paragraph>
            Un PIM (Product Information Management) es un sistema centralizado para gestionar toda la información de productos de una empresa.
            Permite mantener datos consistentes, enriquecer contenido, traducir a múltiples idiomas, y distribuir información a diferentes canales de venta.
          </Typography>

          <Typography variant="h5" gutterBottom sx={{ mt: 3 }}>
            Funcionalidades Principales
          </Typography>
          <List dense>
            <ListItemText primary="• Gestión centralizada de productos con SKU único" />
            <ListItemText primary="• Workflow de aprobación (Draft → Revisión → Aprobado → Publicado)" />
            <ListItemText primary="• Taxonomía jerárquica con categorías y subcategorías" />
            <ListItemText primary="• Traducciones multi-idioma (i18n)" />
            <ListItemText primary="• Biblioteca multimedia (DAM) con gestión de imágenes y archivos" />
            <ListItemText primary="• Sistema de calidad con reglas y scoring automático" />
            <ListItemText primary="• Sincronización con canales externos (Amazon, Shopify, WooCommerce)" />
            <ListItemText primary="• Exportación e importación masiva en Excel" />
            <ListItemText primary="• Gestión de usuarios con permisos granulares (RBAC)" />
            <ListItemText primary="• Dashboard con indicadores de rendimiento" />
          </List>

          <Typography variant="h5" gutterBottom sx={{ mt: 3 }}>
            Navegación
          </Typography>
          <Typography paragraph>
            Utiliza el menú lateral para acceder a las diferentes secciones:
          </Typography>
          <List dense>
            <ListItemText primary="• Dashboard: Vista general del catálogo" />
            <ListItemText primary="• Productos: Gestión del catálogo de productos" />
            <ListItemText primary="• Marcas, Proveedores, Canales: Maestros de datos" />
            <ListItemText primary="• Taxonomía: Categorías jerárquicas" />
            <ListItemText primary="• Media: Biblioteca multimedia" />
            <ListItemText primary="• Calidad: Reglas y scoring" />
            <ListItemText primary="• Traducciones: Gestión de i18n" />
            <ListItemText primary="• Sincronización: Conectores con canales externos" />
            <ListItemText primary="• Administración: Usuarios, roles y permisos (solo admins)" />
          </List>
        </>
      ),
    },
    {
      id: 'dashboard',
      title: 'Dashboard',
      icon: <Dashboard fontSize="small" />,
      content: (
        <>
          <Typography variant="h4" gutterBottom>
            Dashboard
          </Typography>

          <Typography paragraph>
            El Dashboard proporciona una vista general del estado de tu catálogo de productos con indicadores clave de rendimiento (KPIs).
          </Typography>

          <Screenshot
            src="/docs/dashboard-overview.png"
            alt="Vista general del Dashboard mostrando KPIs y gráficos"
            caption="Vista principal del Dashboard con indicadores de rendimiento, gráficos interactivos y acciones pendientes"
          />

          <Typography variant="h5" gutterBottom sx={{ mt: 3 }}>
            KPIs Principales
          </Typography>
          <TableContainer component={Paper} sx={{ mb: 3 }}>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell><strong>Indicador</strong></TableCell>
                  <TableCell><strong>Descripción</strong></TableCell>
                  <TableCell><strong>Acción al Click</strong></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                <TableRow>
                  <TableCell>Total Productos</TableCell>
                  <TableCell>Número total de productos en el catálogo</TableCell>
                  <TableCell>Navega a listado de productos</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Score Promedio</TableCell>
                  <TableCell>Calidad promedio del catálogo (0-100)</TableCell>
                  <TableCell>Navega a panel de calidad</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>% Publicados</TableCell>
                  <TableCell>Productos en estado "ready"</TableCell>
                  <TableCell>Filtra productos publicados</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Completitud</TableCell>
                  <TableCell>Porcentaje de datos completos</TableCell>
                  <TableCell>-</TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </TableContainer>

          <Typography variant="h5" gutterBottom sx={{ mt: 3 }}>
            Gráficos Interactivos
          </Typography>
          <List>
            <ListItemText
              primary="Estado del Workflow"
              secondary="Gráfico de donut que muestra la distribución de productos por estado (draft, in_review, approved, ready, retired)"
            />
            <ListItemText
              primary="Distribución de Calidad"
              secondary="Gráfico de barras que categoriza productos según su score de calidad (Excelente, Aceptable, Crítico)"
            />
            <ListItemText
              primary="Traducciones por Idioma"
              secondary="Gráfico de barras apiladas que muestra traducciones completadas vs pendientes por idioma. Click en una barra para ver traducciones pendientes de ese idioma."
            />
          </List>

          <Screenshot
            src="/docs/dashboard-translations-chart.png"
            alt="Gráfico interactivo de traducciones por idioma"
            caption="Gráfico de barras apiladas que muestra el estado de las traducciones. Al hacer click en una barra, se navega automáticamente a la vista de traducciones pendientes filtrada por ese idioma."
          />

          <Typography variant="h5" gutterBottom sx={{ mt: 3 }}>
            Acciones Pendientes
          </Typography>
          <Typography paragraph>
            El dashboard muestra alertas de acciones que requieren atención:
          </Typography>
          <List dense>
            <ListItemText primary="• Productos con calidad crítica" />
            <ListItemText primary="• Menciones sin leer en comentarios" />
            <ListItemText primary="• Canales con errores de sincronización" />
            <ListItemText primary="• Productos en revisión pendientes de aprobación" />
          </List>
        </>
      ),
    },
    {
      id: 'products',
      title: 'Gestión de Productos',
      icon: <Inventory fontSize="small" />,
      content: (
        <>
          <Typography variant="h4" gutterBottom>
            Gestión de Productos
          </Typography>

          <Typography variant="h5" gutterBottom sx={{ mt: 3 }}>
            Listado de Productos
          </Typography>
          <Typography paragraph>
            El listado de productos muestra todos los SKUs del catálogo con funcionalidades avanzadas de filtrado y búsqueda.
          </Typography>

          <Screenshot
            src="/docs/products-list.png"
            alt="Listado de productos con filtros y búsqueda"
            caption="Vista del listado de productos con panel de filtros avanzados, vistas guardadas y opciones de exportación"
          />

          <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>
            Filtros Disponibles
          </Typography>
          <List dense>
            <ListItemText primary="• Búsqueda por SKU, nombre o marca" />
            <ListItemText primary="• Estado del workflow (draft, in_review, approved, ready, retired)" />
            <ListItemText primary="• Marca" />
            <ListItemText primary="• Categoría (incluyendo subcategorías)" />
            <ListItemText primary="• Proveedor" />
            <ListItemText primary="• Rango de fechas (creación/actualización)" />
            <ListItemText primary="• Con/sin media" />
            <ListItemText primary="• Con/sin traducciones" />
          </List>

          <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>
            Vistas Guardadas
          </Typography>
          <Typography paragraph>
            Puedes guardar combinaciones de filtros como "vistas" para reutilizarlas:
          </Typography>
          <List dense>
            <ListItemText primary="1. Aplica los filtros deseados" />
            <ListItemText primary="2. Click en 'Guardar Vista'" />
            <ListItemText primary="3. Asigna nombre y marca como predeterminada o pública" />
            <ListItemText primary="4. Las vistas aparecen como chips clickeables arriba de la tabla" />
          </List>

          <Typography variant="h5" gutterBottom sx={{ mt: 3 }}>
            Ficha de Producto
          </Typography>
          <Typography paragraph>
            Al hacer click en un producto, accedes a su ficha detallada con las siguientes pestañas:
          </Typography>

          <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>
            Pestaña General
          </Typography>
          <List dense>
            <ListItemText primary="• SKU (identificador único)" />
            <ListItemText primary="• Nombre del producto" />
            <ListItemText primary="• Marca" />
            <ListItemText primary="• Categoría" />
            <ListItemText primary="• Familia de atributos" />
            <ListItemText primary="• Estado del workflow" />
            <ListItemText primary="• Códigos: EAN/GTIN, DUN-14, Ref. Proveedor" />
            <ListItemText primary="• Descripciones: corta, larga, argumento de venta" />
          </List>

          <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>
            Pestaña Atributos
          </Typography>
          <Typography paragraph>
            Atributos dinámicos según la familia asignada. Los atributos se validan automáticamente según las reglas de calidad configuradas.
          </Typography>

          <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>
            Pestaña I18N (Traducciones)
          </Typography>
          <Typography paragraph>
            Gestiona traducciones del producto a diferentes idiomas. Cada traducción incluye título y descripción rica.
          </Typography>

          <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>
            Pestaña SEO
          </Typography>
          <List dense>
            <ListItemText primary="• Meta título" />
            <ListItemText primary="• Meta descripción" />
            <ListItemText primary="• Keywords" />
            <ListItemText primary="• URL canónica" />
          </List>

          <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>
            Pestaña Media
          </Typography>
          <Typography paragraph>
            Vincula imágenes, videos y documentos al producto. Gestiona orden y visibilidad por canal.
          </Typography>

          <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>
            Pestaña Calidad
          </Typography>
          <Typography paragraph>
            Muestra el score de calidad del producto y el detalle de las reglas que aplican (pasadas/falladas).
          </Typography>

          <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>
            Pestaña Comentarios
          </Typography>
          <Typography paragraph>
            Colabora con tu equipo añadiendo comentarios, menciones (@usuario) y tags. Soporta hilos de conversación.
          </Typography>

          <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>
            Pestaña Historial
          </Typography>
          <Typography paragraph>
            Auditoría completa de cambios: quién, cuándo, qué cambió. Permite comparar versiones y restaurar estados anteriores.
          </Typography>

          <Screenshot
            src="/docs/product-detail.png"
            alt="Ficha detallada de producto con todas las pestañas"
            caption="Vista de la ficha de producto mostrando las 8 pestañas disponibles: General, Atributos, I18N, SEO, Media, Calidad, Comentarios e Historial"
          />

          <Typography variant="h5" gutterBottom sx={{ mt: 3 }}>
            Workflow de Aprobación
          </Typography>
          <TableContainer component={Paper} sx={{ mb: 3 }}>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell><strong>Estado</strong></TableCell>
                  <TableCell><strong>Descripción</strong></TableCell>
                  <TableCell><strong>Transiciones</strong></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                <TableRow>
                  <TableCell><Chip label="Draft" size="small" color="warning" /></TableCell>
                  <TableCell>Producto en creación o edición</TableCell>
                  <TableCell>→ In Review</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell><Chip label="In Review" size="small" color="info" /></TableCell>
                  <TableCell>En revisión por el equipo</TableCell>
                  <TableCell>→ Approved / Reject (vuelve a Draft)</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell><Chip label="Approved" size="small" color="secondary" /></TableCell>
                  <TableCell>Aprobado, pendiente de publicación</TableCell>
                  <TableCell>→ Ready</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell><Chip label="Ready" size="small" color="success" /></TableCell>
                  <TableCell>Publicado en canales</TableCell>
                  <TableCell>→ Retired</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell><Chip label="Retired" size="small" color="error" /></TableCell>
                  <TableCell>Producto retirado del catálogo</TableCell>
                  <TableCell>-</TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </TableContainer>
        </>
      ),
    },
    {
      id: 'taxonomy',
      title: 'Taxonomía y Categorías',
      icon: <Category fontSize="small" />,
      content: (
        <>
          <Typography variant="h4" gutterBottom>
            Taxonomía y Categorías
          </Typography>

          <Typography paragraph>
            La taxonomía permite organizar productos en una jerarquía de categorías y subcategorías de múltiples niveles.
          </Typography>

          <Typography variant="h5" gutterBottom sx={{ mt: 3 }}>
            Árbol de Categorías
          </Typography>
          <Typography paragraph>
            La vista en árbol muestra todas las categorías con sus relaciones jerárquicas. Puedes:
          </Typography>
          <List dense>
            <ListItemText primary="• Expandir/colapsar ramas del árbol" />
            <ListItemText primary="• Ver productos de una categoría específica" />
            <ListItemText primary="• Ver productos de una categoría y todas sus subcategorías" />
            <ListItemText primary="• Crear, editar y eliminar categorías" />
            <ListItemText primary="• Reorganizar mediante drag & drop (si disponible)" />
          </List>

          <Typography variant="h5" gutterBottom sx={{ mt: 3 }}>
            Campos de Categoría
          </Typography>
          <List dense>
            <ListItemText primary="• Nombre: Identificador legible" />
            <ListItemText primary="• Slug: URL-friendly (ej: 'electronica-hogar')" />
            <ListItemText primary="• Descripción: Texto descriptivo opcional" />
            <ListItemText primary="• Categoría Padre: Para jerarquías" />
            <ListItemText primary="• Orden: Para ordenación manual" />
          </List>

          <Typography variant="h5" gutterBottom sx={{ mt: 3 }}>
            Navegación a Productos
          </Typography>
          <Alert severity="info" sx={{ mt: 2 }}>
            Usa el botón "Ver productos" en cada categoría para filtrar automáticamente la lista de productos.
            Si la categoría tiene hijos, se mostrarán productos de toda la rama.
          </Alert>

          <Typography variant="h5" gutterBottom sx={{ mt: 3 }}>
            Exportación/Importación
          </Typography>
          <Typography paragraph>
            Las categorías se pueden exportar e importar en Excel manteniendo la jerarquía mediante el campo parent_id.
          </Typography>
        </>
      ),
    },
    {
      id: 'i18n',
      title: 'Traducciones (I18N)',
      icon: <Translate fontSize="small" />,
      content: (
        <>
          <Typography variant="h4" gutterBottom>
            Gestión de Traducciones (I18N)
          </Typography>

          <Typography paragraph>
            El módulo de traducciones permite mantener versiones del contenido de productos en múltiples idiomas.
          </Typography>

          <Screenshot
            src="/docs/i18n-missing.png"
            alt="Vista de traducciones pendientes"
            caption="Listado de productos pendientes de traducción para un idioma específico, con opciones para traducir o ver el producto completo"
          />

          <Typography variant="h5" gutterBottom sx={{ mt: 3 }}>
            Vista de Traducciones Pendientes
          </Typography>
          <Typography paragraph>
            Muestra productos que no tienen traducción para un idioma seleccionado:
          </Typography>
          <List dense>
            <ListItemText primary="1. Selecciona el idioma del desplegable (ES, EN, FR, etc.)" />
            <ListItemText primary="2. La tabla muestra productos sin traducción" />
            <ListItemText primary="3. Click en el botón 'Traducir' para añadir la traducción" />
            <ListItemText primary="4. Click en 'Ver producto' para acceder a la ficha completa" />
          </List>

          <Typography variant="h5" gutterBottom sx={{ mt: 3 }}>
            Navegación desde Dashboard
          </Typography>
          <Alert severity="success" sx={{ mt: 2 }}>
            En el Dashboard, el gráfico de "Traducciones por Idioma" es interactivo.
            Click en una barra para navegar directamente a las traducciones pendientes de ese idioma.
          </Alert>

          <Typography variant="h5" gutterBottom sx={{ mt: 3 }}>
            Campos de Traducción
          </Typography>
          <List dense>
            <ListItemText primary="• Locale: Código del idioma (es, en, fr, de, etc.)" />
            <ListItemText primary="• Título: Nombre del producto en ese idioma" />
            <ListItemText primary="• Descripción Rica: Contenido HTML/rich text (opcional)" />
          </List>

          <Typography variant="h5" gutterBottom sx={{ mt: 3 }}>
            Estadísticas
          </Typography>
          <Typography paragraph>
            El Dashboard muestra:
          </Typography>
          <List dense>
            <ListItemText primary="• Total de productos por idioma" />
            <ListItemText primary="• Traducciones completadas" />
            <ListItemText primary="• Traducciones pendientes" />
            <ListItemText primary="• Porcentaje de completitud" />
          </List>

          <Typography variant="h5" gutterBottom sx={{ mt: 3 }}>
            Mejores Prácticas
          </Typography>
          <List dense>
            <ListItemText primary="• Mantén el título conciso (máx 100 caracteres)" />
            <ListItemText primary="• Usa la descripción rica para contenido estructurado" />
            <ListItemText primary="• Revisa traducciones antes de publicar productos" />
            <ListItemText primary="• Establece idiomas prioritarios según canales de venta" />
          </List>
        </>
      ),
    },
    {
      id: 'media',
      title: 'Biblioteca Multimedia',
      icon: <PhotoLibrary fontSize="small" />,
      content: (
        <>
          <Typography variant="h4" gutterBottom>
            Biblioteca Multimedia (DAM)
          </Typography>

          <Typography paragraph>
            El módulo de media centraliza todos los archivos multimedia (imágenes, videos, PDFs, manuales) asociados a productos.
          </Typography>

          <Typography variant="h5" gutterBottom sx={{ mt: 3 }}>
            Tipos de Media
          </Typography>
          <List dense>
            <ListItemText primary="• Imágenes: JPG, PNG, WebP (productos, packaging, uso)" />
            <ListItemText primary="• Videos: MP4, YouTube/Vimeo links" />
            <ListItemText primary="• PDFs: Fichas técnicas, manuales, certificados" />
            <ListItemText primary="• Otros: Archivos CAD, renders 3D" />
          </List>

          <Typography variant="h5" gutterBottom sx={{ mt: 3 }}>
            Subida de Archivos
          </Typography>
          <List dense>
            <ListItemText primary="1. Click en 'Subir Archivo' o drag & drop" />
            <ListItemText primary="2. Selecciona archivo(s) desde tu ordenador" />
            <ListItemText primary="3. Asocia a un SKU (opcional)" />
            <ListItemText primary="4. Añade etiquetas y descripción" />
            <ListItemText primary="5. Configura visibilidad por canal" />
          </List>

          <Typography variant="h5" gutterBottom sx={{ mt: 3 }}>
            Gestión desde Ficha de Producto
          </Typography>
          <Typography paragraph>
            En la pestaña "Media" de cada producto puedes:
          </Typography>
          <List dense>
            <ListItemText primary="• Ver todos los archivos vinculados" />
            <ListItemText primary="• Cambiar el orden (imagen principal primero)" />
            <ListItemText primary="• Añadir nuevos archivos" />
            <ListItemText primary="• Eliminar vinculaciones" />
            <ListItemText primary="• Marcar visibilidad por canal (ej: ocultar en B2B)" />
          </List>

          <Typography variant="h5" gutterBottom sx={{ mt: 3 }}>
            Optimizaciones Automáticas
          </Typography>
          <Typography paragraph>
            El sistema puede generar automáticamente:
          </Typography>
          <List dense>
            <ListItemText primary="• Thumbnails (miniaturas)" />
            <ListItemText primary="• Versiones responsive (diferentes tamaños)" />
            <ListItemText primary="• Conversión a formatos optimizados (WebP)" />
          </List>

          <Typography variant="h5" gutterBottom sx={{ mt: 3 }}>
            Visibilidad por Canal
          </Typography>
          <Alert severity="warning" sx={{ mt: 2 }}>
            Algunos archivos pueden ocultarse para canales específicos (ej: manuales técnicos no visibles en B2B).
            Configura la visibilidad en las opciones de cada archivo.
          </Alert>
        </>
      ),
    },
    {
      id: 'quality',
      title: 'Control de Calidad',
      icon: <BarChart fontSize="small" />,
      content: (
        <>
          <Typography variant="h4" gutterBottom>
            Control de Calidad
          </Typography>

          <Typography paragraph>
            El sistema de calidad evalúa automáticamente cada producto según reglas configurables, asignando un score de 0 a 100.
          </Typography>

          <Screenshot
            src="/docs/quality-dashboard.png"
            alt="Dashboard de control de calidad"
            caption="Vista del dashboard de calidad mostrando el score de cada producto, reglas aplicadas y distribución por categorías"
          />

          <Typography variant="h5" gutterBottom sx={{ mt: 3 }}>
            Dashboard de Calidad
          </Typography>
          <Typography paragraph>
            Muestra una tabla con todos los productos y su score de calidad:
          </Typography>
          <List dense>
            <ListItemText primary="• Score actual (0-100)" />
            <ListItemText primary="• Reglas aplicadas (pasadas/falladas)" />
            <ListItemText primary="• Filtros por score mínimo" />
            <ListItemText primary="• Ordenación por score" />
            <ListItemText primary="• Acceso directo a ficha de producto" />
          </List>

          <Typography variant="h5" gutterBottom sx={{ mt: 3 }}>
            Conjuntos de Reglas (Rule Sets)
          </Typography>
          <Typography paragraph>
            Las reglas se agrupan en "conjuntos". Solo un conjunto puede estar activo a la vez.
          </Typography>

          <Typography variant="h5" gutterBottom sx={{ mt: 3 }}>
            Tipos de Reglas
          </Typography>
          <TableContainer component={Paper} sx={{ mb: 3 }}>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell><strong>Dimensión</strong></TableCell>
                  <TableCell><strong>Validación</strong></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                <TableRow>
                  <TableCell>brand</TableCell>
                  <TableCell>Marca presente y válida</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>category</TableCell>
                  <TableCell>Categoría asignada</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>seo</TableCell>
                  <TableCell>Meta título, descripción, keywords</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>attributes</TableCell>
                  <TableCell>Atributos obligatorios completos</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>media</TableCell>
                  <TableCell>Mínimo de imágenes/videos</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>i18n</TableCell>
                  <TableCell>Traducciones en idiomas requeridos</TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </TableContainer>

          <Typography variant="h5" gutterBottom sx={{ mt: 3 }}>
            Administración de Reglas
          </Typography>
          <Typography paragraph>
            Los administradores pueden:
          </Typography>
          <List dense>
            <ListItemText primary="• Crear nuevos conjuntos de reglas" />
            <ListItemText primary="• Añadir reglas con peso y score mínimo" />
            <ListItemText primary="• Limitar reglas a categorías específicas" />
            <ListItemText primary="• Activar/desactivar conjuntos" />
            <ListItemText primary="• Simular impacto antes de aplicar (what-if)" />
          </List>

          <Typography variant="h5" gutterBottom sx={{ mt: 3 }}>
            Cálculo del Score
          </Typography>
          <Typography paragraph>
            El score se calcula como:
          </Typography>
          <Alert severity="info" sx={{ mt: 2, mb: 2 }}>
            <code>Score = Σ(regla_pasada ? peso : 0) / Σ(peso_total) * 100</code>
          </Alert>
          <Typography paragraph>
            Una regla se considera "pasada" si el score calculado para esa dimensión es ≥ min_score configurado.
          </Typography>

          <Typography variant="h5" gutterBottom sx={{ mt: 3 }}>
            Blocking de Publicación
          </Typography>
          <Alert severity="warning" sx={{ mt: 2 }}>
            Productos con score inferior al umbral configurado no pueden transicionar a "ready" (publicado).
            Esto garantiza que solo productos de calidad aceptable lleguen a canales de venta.
          </Alert>
        </>
      ),
    },
    {
      id: 'sync',
      title: 'Sincronización',
      icon: <SyncAlt fontSize="small" />,
      content: (
        <>
          <Typography variant="h4" gutterBottom>
            Sincronización con Canales Externos
          </Typography>

          <Typography paragraph>
            El módulo de sincronización permite exportar productos a canales externos como Amazon, Shopify, WooCommerce, o via CSV/HTTP.
          </Typography>

          <Screenshot
            src="/docs/sync-dashboard.png"
            alt="Dashboard de sincronización"
            caption="Vista del dashboard de sincronización mostrando el estado de los trabajos, conectores configurados, y métricas de sincronización por canal"
          />

          <Typography variant="h5" gutterBottom sx={{ mt: 3 }}>
            Dashboard de Sincronización
          </Typography>
          <Typography paragraph>
            Vista general de todos los trabajos de sincronización:
          </Typography>
          <List dense>
            <ListItemText primary="• Estado de última ejecución (OK/KO/Running)" />
            <ListItemText primary="• Fecha y hora de última sincronización" />
            <ListItemText primary="• Productos sincronizados/errores" />
            <ListItemText primary="• Botón para ejecutar sincronización manual" />
            <ListItemText primary="• Historial de ejecuciones" />
          </List>

          <Typography variant="h5" gutterBottom sx={{ mt: 3 }}>
            Tipos de Conectores
          </Typography>
          <TableContainer component={Paper} sx={{ mb: 3 }}>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell><strong>Conector</strong></TableCell>
                  <TableCell><strong>Uso</strong></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                <TableRow>
                  <TableCell>CSV</TableCell>
                  <TableCell>Genera archivo CSV con estructura personalizable</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>HTTP POST</TableCell>
                  <TableCell>Envía datos vía API REST a URL configurada</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Shopify</TableCell>
                  <TableCell>Sincroniza con tienda Shopify (API nativa)</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Amazon</TableCell>
                  <TableCell>Sincroniza con Amazon Seller Central</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>WooCommerce</TableCell>
                  <TableCell>Sincroniza con tienda WooCommerce (WordPress)</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Script</TableCell>
                  <TableCell>Ejecuta script personalizado (Python, Bash)</TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </TableContainer>

          <Typography variant="h5" gutterBottom sx={{ mt: 3 }}>
            Programación (Schedules)
          </Typography>
          <Typography paragraph>
            Puedes programar sincronizaciones automáticas usando expresiones cron:
          </Typography>
          <List dense>
            <ListItemText primary="• Diario a las 2:00 AM: 0 2 * * *" />
            <ListItemText primary="• Cada hora: 0 * * * *" />
            <ListItemText primary="• Lunes a viernes a las 18:00: 0 18 * * 1-5" />
          </List>

          <Typography variant="h5" gutterBottom sx={{ mt: 3 }}>
            Filtros de Sincronización
          </Typography>
          <Typography paragraph>
            Cada trabajo puede filtrar qué productos sincronizar:
          </Typography>
          <List dense>
            <ListItemText primary="• Por estado (solo 'ready')" />
            <ListItemText primary="• Por categoría" />
            <ListItemText primary="• Por marca" />
            <ListItemText primary="• Por fecha de actualización (delta)" />
            <ListItemText primary="• Por canal asignado" />
          </List>

          <Typography variant="h5" gutterBottom sx={{ mt: 3 }}>
            Estado por Producto
          </Typography>
          <Typography paragraph>
            En la ficha de cada producto, la pestaña de sincronización muestra el estado por canal:
          </Typography>
          <List dense>
            <ListItemText primary="• Synced: Sincronizado correctamente" />
            <ListItemText primary="• Error: Último intento falló" />
            <ListItemText primary="• Pending: Pendiente de sincronización" />
          </List>

          <Typography variant="h5" gutterBottom sx={{ mt: 3 }}>
            Reintentos Automáticos
          </Typography>
          <Alert severity="info" sx={{ mt: 2 }}>
            El sistema reintenta automáticamente sincronizaciones fallidas con backoff exponencial
            (5 segundos, 25 segundos, 125 segundos, etc.) hasta alcanzar el máximo de reintentos configurado.
          </Alert>
        </>
      ),
    },
    {
      id: 'export-import',
      title: 'Exportación/Importación',
      icon: <FileDownload fontSize="small" />,
      content: (
        <>
          <Typography variant="h4" gutterBottom>
            Exportación e Importación Excel
          </Typography>

          <Typography paragraph>
            El sistema permite exportar e importar datos masivamente en formato Excel (.xlsx) para facilitar la gestión de grandes volúmenes.
          </Typography>

          <Screenshot
            src="/docs/export-dialog.png"
            alt="Diálogo de exportación a Excel"
            caption="Diálogo de configuración de exportación permitiendo seleccionar campos, aplicar filtros y descargar datos en formato Excel"
          />

          <Typography variant="h5" gutterBottom sx={{ mt: 3 }}>
            Recursos Exportables
          </Typography>
          <List dense>
            <ListItemText primary="• Productos (products)" />
            <ListItemText primary="• Categorías (categories)" />
            <ListItemText primary="• Marcas (brands)" />
            <ListItemText primary="• Proveedores (suppliers)" />
            <ListItemText primary="• Canales (channels)" />
            <ListItemText primary="• Traducciones (product_i18n)" />
            <ListItemText primary="• Media (media_assets)" />
            <ListItemText primary="• Usuarios (users)" />
            <ListItemText primary="• Reglas de Calidad (quality_rules)" />
            <ListItemText primary="• Familias de Atributos (attribute_families)" />
            <ListItemText primary="• Y más..." />
          </List>

          <Typography variant="h5" gutterBottom sx={{ mt: 3 }}>
            Exportación
          </Typography>
          <Typography paragraph>
            Proceso de exportación:
          </Typography>
          <List dense>
            <ListItemText primary="1. Click en botón 'Exportar' en cualquier listado (Productos, Marcas, etc.)" />
            <ListItemText primary="2. Selecciona los campos a exportar (usa tus preferencias guardadas o personaliza)" />
            <ListItemText primary="3. Aplica filtros activos (opcional)" />
            <ListItemText primary="4. Click en 'Exportar' o 'Descargar Plantilla Vacía'" />
            <ListItemText primary="5. Se descarga archivo Excel con los datos" />
          </List>

          <Alert severity="info" sx={{ mt: 2, mb: 2 }}>
            Las exportaciones incluyen una hoja oculta "_meta" con metadatos de los campos para facilitar la importación.
          </Alert>

          <Typography variant="h5" gutterBottom sx={{ mt: 3 }}>
            Importación
          </Typography>
          <Typography paragraph>
            Proceso de importación (wizard de 3 pasos):
          </Typography>

          <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>
            Paso 1: Subir Archivo
          </Typography>
          <List dense>
            <ListItemText primary="• Click en 'Importar' en el listado correspondiente" />
            <ListItemText primary="• Arrastra archivo Excel o selecciona desde ordenador" />
            <ListItemText primary="• Formatos soportados: .xlsx" />
          </List>

          <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>
            Paso 2: Validación (Dry-Run)
          </Typography>

          <Screenshot
            src="/docs/import-validation.png"
            alt="Wizard de importación - Paso de validación"
            caption="Paso de validación del wizard de importación mostrando errores, warnings y preview de los datos a importar"
          />

          <Typography paragraph>
            El sistema valida el archivo sin modificar la base de datos:
          </Typography>
          <List dense>
            <ListItemText primary="• Validación de tipos de datos" />
            <ListItemText primary="• Comprobación de foreign keys (referencias)" />
            <ListItemText primary="• Validación de campos requeridos" />
            <ListItemText primary="• Detección de duplicados" />
            <ListItemText primary="• Identificación de modo: CREATE o UPDATE (upsert)" />
          </List>
          <Typography paragraph>
            Muestra:
          </Typography>
          <List dense>
            <ListItemText primary="• Tabla de errores (bloquean la importación)" />
            <ListItemText primary="• Tabla de warnings (no bloquean)" />
            <ListItemText primary="• Preview de primeras 10 filas" />
            <ListItemText primary="• Resumen: Total, Válidos, Errores" />
          </List>

          <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>
            Paso 3: Aplicar Cambios
          </Typography>
          <Typography paragraph>
            Si la validación es exitosa (sin errores bloqueantes):
          </Typography>
          <List dense>
            <ListItemText primary="• Click en 'Importar' para aplicar cambios" />
            <ListItemText primary="• Se procesan todas las filas válidas" />
            <ListItemText primary="• Modo upsert: crea nuevos registros o actualiza existentes" />
            <ListItemText primary="• Resultado: Creados / Actualizados / Omitidos" />
          </List>

          <Typography variant="h5" gutterBottom sx={{ mt: 3 }}>
            Tipos de Validación
          </Typography>
          <TableContainer component={Paper} sx={{ mb: 3 }}>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell><strong>Validación</strong></TableCell>
                  <TableCell><strong>Descripción</strong></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                <TableRow>
                  <TableCell>Tipo de dato</TableCell>
                  <TableCell>String, int, float, bool, date, datetime, JSON, enum</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Campos requeridos</TableCell>
                  <TableCell>No pueden estar vacíos</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Foreign keys</TableCell>
                  <TableCell>Referencias deben existir (ej: category_id → categories)</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Longitud máxima</TableCell>
                  <TableCell>Strings no exceden max_length</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Enums</TableCell>
                  <TableCell>Valores dentro de opciones permitidas</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Formato JSON</TableCell>
                  <TableCell>Campos JSON son válidos y parseables</TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </TableContainer>

          <Typography variant="h5" gutterBottom sx={{ mt: 3 }}>
            Modo Upsert
          </Typography>
          <Typography paragraph>
            La importación usa "upsert" (insert or update):
          </Typography>
          <List dense>
            <ListItemText primary="• Si el registro existe (según upsert_key): se actualiza" />
            <ListItemText primary="• Si no existe: se crea nuevo" />
            <ListItemText primary="• Upsert key por recurso: products→sku, categories→slug, brands→slug, etc." />
          </List>

          <Typography variant="h5" gutterBottom sx={{ mt: 3 }}>
            Campos Especiales
          </Typography>
          <List dense>
            <ListItemText primary="• Readonly: Solo exportación (ej: created_at, id auto-generado)" />
            <ListItemText primary="• Default include: Incluidos por defecto en exportaciones" />
            <ListItemText primary="• FK: Se validan contra tabla referenciada" />
          </List>

          <Typography variant="h5" gutterBottom sx={{ mt: 3 }}>
            Mejores Prácticas
          </Typography>
          <Alert severity="success" sx={{ mt: 2 }}>
            <strong>Recomendaciones:</strong>
            <List dense>
              <ListItemText primary="• Descarga una plantilla vacía para ver la estructura correcta" />
              <ListItemText primary="• Exporta datos actuales antes de importar cambios (backup)" />
              <ListItemText primary="• Valida en entorno de prueba antes de producción" />
              <ListItemText primary="• No modifiques campos readonly (se ignoran)" />
              <ListItemText primary="• Usa valores válidos para campos enum (ej: status)" />
              <ListItemText primary="• Asegura que foreign keys existen antes de importar" />
            </List>
          </Alert>
        </>
      ),
    },
    {
      id: 'masters',
      title: 'Maestros de Datos',
      icon: <Storefront fontSize="small" />,
      content: (
        <>
          <Typography variant="h4" gutterBottom>
            Maestros de Datos
          </Typography>

          <Typography paragraph>
            Los maestros de datos son catálogos de referencia utilizados en la gestión de productos.
          </Typography>

          <Typography variant="h5" gutterBottom sx={{ mt: 3 }}>
            Marcas (Brands)
          </Typography>
          <Typography paragraph>
            Gestiona el catálogo de marcas comerciales:
          </Typography>
          <List dense>
            <ListItemText primary="• Nombre de la marca" />
            <ListItemText primary="• Slug (URL-friendly)" />
            <ListItemText primary="• Descripción" />
            <ListItemText primary="• Sitio web" />
            <ListItemText primary="• Logo (URL)" />
            <ListItemText primary="• Estado: Activa/Inactiva" />
          </List>
          <Alert severity="info" sx={{ mt: 2, mb: 3 }}>
            Usa el botón "Ver productos" para filtrar productos de una marca específica.
          </Alert>

          <Typography variant="h5" gutterBottom sx={{ mt: 3 }}>
            Proveedores (Suppliers)
          </Typography>
          <Typography paragraph>
            Gestiona proveedores y fabricantes:
          </Typography>
          <List dense>
            <ListItemText primary="• Nombre del proveedor" />
            <ListItemText primary="• Código único" />
            <ListItemText primary="• País (código ISO)" />
            <ListItemText primary="• Email de contacto" />
            <ListItemText primary="• Teléfono" />
            <ListItemText primary="• Notas internas" />
            <ListItemText primary="• Estado: Activo/Inactivo" />
          </List>
          <Alert severity="info" sx={{ mt: 2, mb: 3 }}>
            Usa el botón "Ver productos" para filtrar productos de un proveedor.
          </Alert>

          <Typography variant="h5" gutterBottom sx={{ mt: 3 }}>
            Canales (Channels)
          </Typography>
          <Typography paragraph>
            Define canales de venta y distribución:
          </Typography>
          <List dense>
            <ListItemText primary="• Nombre del canal" />
            <ListItemText primary="• Código único" />
            <ListItemText primary="• Descripción" />
            <ListItemText primary="• Estado: Activo/Inactivo" />
          </List>
          <Typography paragraph>
            Los canales se usan para:
          </Typography>
          <List dense>
            <ListItemText primary="• Asignar productos a canales específicos" />
            <ListItemText primary="• Configurar visibilidad de media por canal" />
            <ListItemText primary="• Sincronización selectiva" />
            <ListItemText primary="• Reportes por canal" />
          </List>

          <Typography variant="h5" gutterBottom sx={{ mt: 3 }}>
            Funcionalidades Comunes
          </Typography>
          <Typography paragraph>
            Todos los maestros tienen:
          </Typography>
          <List dense>
            <ListItemText primary="• Búsqueda y filtrado" />
            <ListItemText primary="• Exportación a Excel" />
            <ListItemText primary="• Importación masiva" />
            <ListItemText primary="• Crear, editar, eliminar" />
            <ListItemText primary="• Navegación a productos relacionados" />
          </List>
        </>
      ),
    },
    {
      id: 'admin',
      title: 'Administración',
      icon: <People fontSize="small" />,
      content: (
        <>
          <Typography variant="h4" gutterBottom>
            Administración de Usuarios y Permisos
          </Typography>

          <Alert severity="warning" sx={{ mb: 3 }}>
            Sección disponible solo para usuarios con rol "admin".
          </Alert>

          <Screenshot
            src="/docs/admin-users.png"
            alt="Panel de administración de usuarios"
            caption="Vista del panel de administración mostrando gestión de usuarios y matriz de permisos por recurso"
          />

          <Typography variant="h5" gutterBottom sx={{ mt: 3 }}>
            Gestión de Usuarios
          </Typography>
          <Typography paragraph>
            Administra cuentas de usuario del sistema:
          </Typography>
          <List dense>
            <ListItemText primary="• Crear nuevos usuarios con email y contraseña" />
            <ListItemText primary="• Asignar rol (admin, editor, viewer)" />
            <ListItemText primary="• Activar/desactivar usuarios" />
            <ListItemText primary="• Editar información de perfil" />
            <ListItemText primary="• Eliminar usuarios (excepto a sí mismo)" />
          </List>

          <Typography variant="h5" gutterBottom sx={{ mt: 3 }}>
            Roles Predefinidos
          </Typography>
          <TableContainer component={Paper} sx={{ mb: 3 }}>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell><strong>Rol</strong></TableCell>
                  <TableCell><strong>Permisos</strong></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                <TableRow>
                  <TableCell><Chip label="Admin" size="small" color="error" /></TableCell>
                  <TableCell>Acceso completo (write) a todos los recursos</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell><Chip label="Editor" size="small" color="primary" /></TableCell>
                  <TableCell>Write a productos/categorías/media/marcas/canales/proveedores/sync/calidad/i18n. Read a users/settings.</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell><Chip label="Viewer" size="small" color="default" /></TableCell>
                  <TableCell>Read (solo lectura) a todos los recursos</TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </TableContainer>

          <Typography variant="h5" gutterBottom sx={{ mt: 3 }}>
            Sistema de Permisos Granulares (RBAC)
          </Typography>
          <Typography paragraph>
            El sistema implementa Control de Acceso Basado en Roles con 11 recursos y 3 niveles:
          </Typography>

          <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>
            Recursos
          </Typography>
          <List dense>
            <ListItemText primary="• products (productos)" />
            <ListItemText primary="• categories (taxonomía)" />
            <ListItemText primary="• media (multimedia)" />
            <ListItemText primary="• brands (marcas)" />
            <ListItemText primary="• channels (canales)" />
            <ListItemText primary="• suppliers (proveedores)" />
            <ListItemText primary="• sync (sincronización)" />
            <ListItemText primary="• quality (calidad)" />
            <ListItemText primary="• i18n (traducciones)" />
            <ListItemText primary="• users (usuarios)" />
            <ListItemText primary="• settings (configuración)" />
          </List>

          <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>
            Niveles de Acceso
          </Typography>
          <List dense>
            <ListItemText primary="• None: Sin acceso" />
            <ListItemText primary="• Read: Solo lectura" />
            <ListItemText primary="• Write: Lectura y escritura" />
          </List>

          <Typography variant="h5" gutterBottom sx={{ mt: 3 }}>
            Gestión de Roles (Role Manager)
          </Typography>
          <Typography paragraph>
            Vista matricial para asignar permisos personalizados:
          </Typography>
          <List dense>
            <ListItemText primary="• Filas: Usuarios del sistema" />
            <ListItemText primary="• Columnas: Recursos (products, categories, etc.)" />
            <ListItemText primary="• Celdas: Selector none/read/write" />
            <ListItemText primary="• Los permisos personalizados sobrescriben defaults del rol" />
            <ListItemText primary="• Los admins tienen siempre acceso write (no editable)" />
          </List>

          <Typography variant="h5" gutterBottom sx={{ mt: 3 }}>
            Scopes en API
          </Typography>
          <Typography paragraph>
            Los permisos se validan en backend con formato "recurso:nivel":
          </Typography>
          <List dense>
            <ListItemText primary="• products:read → puede leer productos" />
            <ListItemText primary="• products:write → puede crear/editar productos" />
            <ListItemText primary="• media:write → puede subir archivos multimedia" />
            <ListItemText primary="• users:write → puede gestionar usuarios (solo admins)" />
          </List>

          <Typography variant="h5" gutterBottom sx={{ mt: 3 }}>
            Seguridad
          </Typography>
          <Alert severity="error" sx={{ mt: 2 }}>
            <strong>Importante:</strong>
            <List dense>
              <ListItemText primary="• No puedes eliminar tu propia cuenta" />
              <ListItemText primary="• Solo admins pueden acceder a /admin/*" />
              <ListItemText primary="• Todos los endpoints validan permisos en backend" />
              <ListItemText primary="• Las sesiones expiran automáticamente (tokens JWT)" />
            </List>
          </Alert>
        </>
      ),
    },
    {
      id: 'quickstart',
      title: 'Tutorial Rápido',
      icon: <School fontSize="small" />,
      content: (
        <>
          <Typography variant="h4" gutterBottom>
            Tutorial Rápido - Primeros Pasos
          </Typography>

          <Alert severity="success" sx={{ mb: 3 }}>
            Guía paso a paso para comenzar a usar el PIM en 15 minutos.
          </Alert>

          <Screenshot
            src="/docs/tutorial-overview.png"
            alt="Vista general de la interfaz del PIM"
            caption="Interfaz principal del sistema PIM mostrando el menú de navegación lateral y la vista del dashboard"
          />

          <Typography variant="h5" gutterBottom sx={{ mt: 3 }}>
            Paso 1: Familiarízate con el Dashboard
          </Typography>
          <Box sx={{ pl: 2, mb: 3 }}>
            <Typography paragraph>
              <strong>Tiempo estimado: 2 minutos</strong>
            </Typography>
            <List dense>
              <ListItemText primary="1. Inicia sesión con tus credenciales (admin@pim.local / admin para testing)" />
              <ListItemText primary="2. Observa los 4 KPIs principales en la parte superior" />
              <ListItemText primary="3. Revisa el gráfico de 'Estado del Workflow' para entender la distribución" />
              <ListItemText primary="4. Verifica si hay 'Acciones Pendientes' en la alerta naranja" />
            </List>
          </Box>

          <Typography variant="h5" gutterBottom sx={{ mt: 3 }}>
            Paso 2: Crea tu Primera Marca
          </Typography>
          <Box sx={{ pl: 2, mb: 3 }}>
            <Typography paragraph>
              <strong>Tiempo estimado: 2 minutos</strong>
            </Typography>
            <List dense>
              <ListItemText primary="1. Click en 'Marcas' en el menú lateral" />
              <ListItemText primary="2. Click en botón azul 'Nueva Marca' (esquina superior derecha)" />
              <ListItemText primary="3. Completa: Nombre (ej: 'Nike'), Slug (ej: 'nike'), Descripción (opcional)" />
              <ListItemText primary="4. Click en 'Crear'" />
              <ListItemText primary="5. ✓ Tu primera marca está creada" />
            </List>
          </Box>

          <Typography variant="h5" gutterBottom sx={{ mt: 3 }}>
            Paso 3: Crea una Categoría
          </Typography>
          <Box sx={{ pl: 2, mb: 3 }}>
            <Typography paragraph>
              <strong>Tiempo estimado: 2 minutos</strong>
            </Typography>
            <List dense>
              <ListItemText primary="1. Click en 'Taxonomía' en el menú lateral" />
              <ListItemText primary="2. Click en botón 'Nueva Categoría Raíz' (o 'Nueva Subcategoría' si ya existe una)" />
              <ListItemText primary="3. Completa: Nombre (ej: 'Electrónica'), Slug (ej: 'electronica')" />
              <ListItemText primary="4. Click en 'Crear'" />
              <ListItemText primary="5. ✓ Tu primera categoría está creada" />
            </List>
          </Box>

          <Typography variant="h5" gutterBottom sx={{ mt: 3 }}>
            Paso 4: Crea tu Primer Producto
          </Typography>
          <Box sx={{ pl: 2, mb: 3 }}>
            <Typography paragraph>
              <strong>Tiempo estimado: 3 minutos</strong>
            </Typography>
            <List dense>
              <ListItemText primary="1. Click en 'Productos' en el menú lateral" />
              <ListItemText primary="2. Click en botón verde 'Nuevo Producto'" />
              <ListItemText primary="3. Completa datos obligatorios:" />
              <Box sx={{ pl: 4 }}>
                <ListItemText primary="• SKU: Código único (ej: 'PROD-001')" />
                <ListItemText primary="• Nombre: Nombre del producto (ej: 'iPhone 15 Pro')" />
                <ListItemText primary="• Marca: Selecciona la marca creada en Paso 2" />
                <ListItemText primary="• Categoría: Selecciona la categoría del Paso 3" />
              </Box>
              <ListItemText primary="4. Añade descripciones (opcional pero recomendado)" />
              <ListItemText primary="5. Click en 'Guardar'" />
              <ListItemText primary="6. ✓ Tu primer producto está en estado 'Draft'" />
            </List>
          </Box>

          <Typography variant="h5" gutterBottom sx={{ mt: 3 }}>
            Paso 5: Añade una Imagen al Producto
          </Typography>
          <Box sx={{ pl: 2, mb: 3 }}>
            <Typography paragraph>
              <strong>Tiempo estimado: 2 minutos</strong>
            </Typography>
            <List dense>
              <ListItemText primary="1. Desde la ficha del producto, click en pestaña 'Media'" />
              <ListItemText primary="2. Click en 'Añadir Archivo' o arrastra imagen" />
              <ListItemText primary="3. Selecciona imagen desde tu ordenador" />
              <ListItemText primary="4. Espera a que se suba" />
              <ListItemText primary="5. ✓ Imagen vinculada al producto" />
            </List>
          </Box>

          <Typography variant="h5" gutterBottom sx={{ mt: 3 }}>
            Paso 6: Añade una Traducción
          </Typography>
          <Box sx={{ pl: 2, mb: 3 }}>
            <Typography paragraph>
              <strong>Tiempo estimado: 2 minutos</strong>
            </Typography>
            <List dense>
              <ListItemText primary="1. En la ficha del producto, click en pestaña 'I18N'" />
              <ListItemText primary="2. Click en 'Nueva Traducción'" />
              <ListItemText primary="3. Selecciona idioma (ej: 'en' para inglés)" />
              <ListItemText primary="4. Completa título en ese idioma" />
              <ListItemText primary="5. Click en 'Guardar'" />
              <ListItemText primary="6. ✓ Producto traducido" />
            </List>
          </Box>

          <Typography variant="h5" gutterBottom sx={{ mt: 3 }}>
            Paso 7: Publica el Producto
          </Typography>
          <Box sx={{ pl: 2, mb: 3 }}>
            <Typography paragraph>
              <strong>Tiempo estimado: 2 minutos</strong>
            </Typography>
            <List dense>
              <ListItemText primary="1. Vuelve a pestaña 'General' del producto" />
              <ListItemText primary="2. Verifica que todos los datos estén completos" />
              <ListItemText primary="3. Click en selector de estado (arriba a la derecha)" />
              <ListItemText primary="4. Selecciona 'In Review' (enviar a revisión)" />
              <ListItemText primary="5. Si eres admin, puedes aprobar: selecciona 'Approved'" />
              <ListItemText primary="6. Finalmente, selecciona 'Ready' para publicar" />
              <ListItemText primary="7. ✓ Producto publicado y listo para sincronización" />
            </List>
          </Box>

          <Alert severity="success" sx={{ mt: 3 }}>
            <strong>¡Felicitaciones!</strong><br />
            Has completado el tutorial rápido. Ahora sabes cómo:
            <List dense>
              <ListItemText primary="✓ Navegar por el sistema" />
              <ListItemText primary="✓ Crear marcas y categorías" />
              <ListItemText primary="✓ Crear y enriquecer productos" />
              <ListItemText primary="✓ Gestionar media y traducciones" />
              <ListItemText primary="✓ Publicar productos" />
            </List>
          </Alert>

          <Typography variant="h5" gutterBottom sx={{ mt: 3 }}>
            Próximos Pasos Recomendados
          </Typography>
          <List dense>
            <ListItemText primary="• Explora las reglas de calidad en la sección 'Calidad'" />
            <ListItemText primary="• Configura un canal de sincronización en 'Sincronización'" />
            <ListItemText primary="• Prueba la exportación/importación masiva en Excel" />
            <ListItemText primary="• Invita a tu equipo creando usuarios en 'Administración'" />
          </List>
        </>
      ),
    },
    {
      id: 'faqs',
      title: 'Preguntas Frecuentes',
      icon: <HelpOutline fontSize="small" />,
      content: (
        <>
          <Typography variant="h4" gutterBottom>
            Preguntas Frecuentes (FAQs)
          </Typography>

          <Typography variant="h5" gutterBottom sx={{ mt: 3 }}>
            General
          </Typography>

          <Box sx={{ mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              ¿Qué es un SKU?
            </Typography>
            <Typography paragraph>
              SKU (Stock Keeping Unit) es el identificador único de cada producto en el catálogo.
              Puede ser alfanumérico y debe ser único por producto. Ejemplo: "PROD-001", "NIKE-AIR-MAX-42".
            </Typography>
          </Box>

          <Box sx={{ mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              ¿Puedo cambiar el SKU de un producto después de crearlo?
            </Typography>
            <Typography paragraph>
              No. El SKU es la clave primaria y no puede modificarse una vez creado el producto.
              Si necesitas cambiar el SKU, debes crear un nuevo producto y eliminar/retirar el anterior.
            </Typography>
          </Box>

          <Box sx={{ mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              ¿Cuántos productos puedo tener en el PIM?
            </Typography>
            <Typography paragraph>
              No hay límite técnico en el número de productos. El sistema está diseñado para manejar
              catálogos de 100k+ SKUs con buen rendimiento.
            </Typography>
          </Box>

          <Divider sx={{ my: 3 }} />

          <Typography variant="h5" gutterBottom>
            Workflow y Estados
          </Typography>

          <Box sx={{ mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              ¿Puedo publicar un producto directamente sin aprobación?
            </Typography>
            <Typography paragraph>
              Sí, si tienes permisos de admin puedes cambiar el estado directamente a "Ready".
              Sin embargo, se recomienda seguir el workflow (Draft → In Review → Approved → Ready)
              para mantener control de calidad.
            </Typography>
          </Box>

          <Box sx={{ mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              ¿Qué pasa si intento publicar un producto con score de calidad bajo?
            </Typography>
            <Typography paragraph>
              El sistema bloqueará la transición a "Ready" si el producto no cumple con el umbral
              mínimo de calidad configurado. Debes completar los datos faltantes primero.
            </Typography>
          </Box>

          <Box sx={{ mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              ¿Puedo volver un producto de "Ready" a "Draft"?
            </Typography>
            <Typography paragraph>
              Sí, puedes hacer la transición Ready → Draft. Sin embargo, esto puede afectar
              sincronizaciones activas. Se recomienda usar "Retired" para productos que ya no se venden.
            </Typography>
          </Box>

          <Divider sx={{ my: 3 }} />

          <Typography variant="h5" gutterBottom>
            Traducciones
          </Typography>

          <Box sx={{ mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              ¿Qué idiomas puedo usar?
            </Typography>
            <Typography paragraph>
              Puedes usar cualquier código de idioma estándar (es, en, fr, de, pt, it, etc.).
              Los idiomas configurados aparecen automáticamente en los selectores de la aplicación.
            </Typography>
          </Box>

          <Box sx={{ mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              ¿Las traducciones son obligatorias?
            </Typography>
            <Typography paragraph>
              Depende de las reglas de calidad configuradas. Puedes configurar que ciertos idiomas
              sean obligatorios para productos de categorías específicas.
            </Typography>
          </Box>

          <Divider sx={{ my: 3 }} />

          <Typography variant="h5" gutterBottom>
            Exportación/Importación
          </Typography>

          <Box sx={{ mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              ¿Qué formato de archivo debo usar para importar?
            </Typography>
            <Typography paragraph>
              Solo se soporta formato Excel (.xlsx). Descarga una plantilla vacía desde el botón
              "Descargar Plantilla" para ver la estructura correcta.
            </Typography>
          </Box>

          <Box sx={{ mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              ¿Qué pasa si mi importación tiene errores?
            </Typography>
            <Typography paragraph>
              El sistema valida primero sin modificar datos (dry-run). Te mostrará una tabla
              con todos los errores y warnings. Solo puedes aplicar la importación si no hay errores bloqueantes.
            </Typography>
          </Box>

          <Box sx={{ mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              ¿Puedo importar para actualizar productos existentes?
            </Typography>
            <Typography paragraph>
              Sí, el sistema usa "upsert": si el SKU (u otra clave única) ya existe, actualiza;
              si no existe, crea nuevo. El modo se detecta automáticamente y se muestra en el preview.
            </Typography>
          </Box>

          <Divider sx={{ my: 3 }} />

          <Typography variant="h5" gutterBottom>
            Sincronización
          </Typography>

          <Box sx={{ mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              ¿Con qué frecuencia se sincronizan los productos?
            </Typography>
            <Typography paragraph>
              Depende de la programación configurada para cada canal. Puedes configurar expresiones
              cron para sincronización automática (ej: cada hora, diaria, etc.) o ejecutar manualmente.
            </Typography>
          </Box>

          <Box sx={{ mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              ¿Qué pasa si una sincronización falla?
            </Typography>
            <Typography paragraph>
              El sistema reintenta automáticamente con backoff exponencial (5s, 25s, 125s...) hasta
              alcanzar el máximo de reintentos. Los errores se registran en el Dashboard de Sync.
            </Typography>
          </Box>

          <Box sx={{ mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              ¿Puedo sincronizar solo productos específicos?
            </Typography>
            <Typography paragraph>
              Sí, cada trabajo de sincronización puede tener filtros: por estado (solo "ready"),
              por categoría, por marca, por fecha de actualización, etc.
            </Typography>
          </Box>

          <Divider sx={{ my: 3 }} />

          <Typography variant="h5" gutterBottom>
            Permisos y Usuarios
          </Typography>

          <Box sx={{ mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              ¿Qué diferencia hay entre Admin, Editor y Viewer?
            </Typography>
            <Typography paragraph>
              <strong>Admin:</strong> Acceso completo (write) a todo.<br />
              <strong>Editor:</strong> Puede crear/editar productos, categorías, media, etc. pero solo leer usuarios y configuración.<br />
              <strong>Viewer:</strong> Solo lectura en todo el sistema.
            </Typography>
          </Box>

          <Box sx={{ mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              ¿Puedo personalizar permisos por usuario?
            </Typography>
            <Typography paragraph>
              Sí, los admins pueden ir a "Administración → Permisos" y configurar permisos granulares
              por recurso (products, categories, media, etc.) con niveles none/read/write.
            </Typography>
          </Box>

          <Box sx={{ mb: 3 }}>
            <Typography variant="h6" gutterBottom>
              ¿Puedo eliminar mi propia cuenta?
            </Typography>
            <Typography paragraph>
              No, por seguridad el sistema previene la auto-eliminación. Otro administrador debe
              eliminar tu cuenta si es necesario.
            </Typography>
          </Box>

          <Divider sx={{ my: 3 }} />

          <Alert severity="info" sx={{ mt: 3 }}>
            <strong>¿No encuentras tu pregunta?</strong><br />
            Consulta las demás secciones de la documentación o contacta con tu administrador de sistema.
          </Alert>
        </>
      ),
    },
    {
      id: 'shortcuts',
      title: 'Atajos y Tips',
      icon: <Dashboard fontSize="small" />,
      content: (
        <>
          <Typography variant="h4" gutterBottom>
            Atajos y Consejos Útiles
          </Typography>

          <Typography variant="h5" gutterBottom sx={{ mt: 3 }}>
            Navegación Rápida
          </Typography>
          <List dense>
            <ListItemText primary="• Dashboard → Click en cualquier KPI para ir a vista filtrada" />
            <ListItemText primary="• Gráficos → Click en secciones para aplicar filtros" />
            <ListItemText primary="• Traducciones → Click en barra de idioma para ver pendientes" />
            <ListItemText primary="• Maestros → Botón 'Ver productos' filtra automáticamente" />
          </List>

          <Typography variant="h5" gutterBottom sx={{ mt: 3 }}>
            Productividad
          </Typography>
          <List dense>
            <ListItemText primary="• Guarda vistas personalizadas con filtros frecuentes" />
            <ListItemText primary="• Usa exportación/importación para cambios masivos" />
            <ListItemText primary="• Programa sincronizaciones en horarios de bajo tráfico" />
            <ListItemText primary="• Revisa Dashboard diariamente para detectar problemas" />
            <ListItemText primary="• Usa comentarios para colaborar con el equipo" />
          </List>

          <Typography variant="h5" gutterBottom sx={{ mt: 3 }}>
            Workflow Recomendado
          </Typography>
          <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>
            1. Creación de Producto
          </Typography>
          <List dense>
            <ListItemText primary="a) Crear producto en estado 'draft'" />
            <ListItemText primary="b) Completar información básica (SKU, nombre, marca, categoría)" />
            <ListItemText primary="c) Añadir atributos según familia" />
            <ListItemText primary="d) Subir imágenes y media" />
            <ListItemText primary="e) Completar SEO" />
          </List>

          <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>
            2. Enriquecimiento
          </Typography>
          <List dense>
            <ListItemText primary="a) Añadir traducciones a idiomas prioritarios" />
            <ListItemText primary="b) Completar descripciones largas" />
            <ListItemText primary="c) Añadir beneficios clave y claims" />
            <ListItemText primary="d) Verificar score de calidad" />
          </List>

          <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>
            3. Aprobación
          </Typography>
          <List dense>
            <ListItemText primary="a) Transicionar a 'in_review'" />
            <ListItemText primary="b) Revisor verifica completitud" />
            <ListItemText primary="c) Aprobar o rechazar con comentarios" />
            <ListItemText primary="d) Si aprobado, marcar como 'ready'" />
          </List>

          <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>
            4. Publicación
          </Typography>
          <List dense>
            <ListItemText primary="a) Producto en 'ready' queda disponible para sincronización" />
            <ListItemText primary="b) Sincronización automática o manual a canales" />
            <ListItemText primary="c) Verificar estado de sincronización por canal" />
            <ListItemText primary="d) Monitorear errores en Dashboard de Sync" />
          </List>

          <Typography variant="h5" gutterBottom sx={{ mt: 3 }}>
            Mantenimiento
          </Typography>
          <List dense>
            <ListItemText primary="• Revisa productos con calidad crítica semanalmente" />
            <ListItemText primary="• Completa traducciones pendientes por prioridad de mercado" />
            <ListItemText primary="• Audita errores de sincronización diariamente" />
            <ListItemText primary="• Actualiza reglas de calidad según evolución del catálogo" />
            <ListItemText primary="• Haz backups mediante exportación periódica" />
          </List>

          <Typography variant="h5" gutterBottom sx={{ mt: 3 }}>
            Solución de Problemas
          </Typography>
          <TableContainer component={Paper} sx={{ mb: 3 }}>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell><strong>Problema</strong></TableCell>
                  <TableCell><strong>Solución</strong></TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                <TableRow>
                  <TableCell>No puedo publicar un producto</TableCell>
                  <TableCell>Verifica score de calidad en pestaña Calidad. Completa campos faltantes.</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Sincronización falla</TableCell>
                  <TableCell>Revisa logs en Dashboard de Sync. Verifica configuración de conexión del canal.</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Traducción no aparece</TableCell>
                  <TableCell>Verifica que el locale esté en la lista de idiomas configurados.</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Error al importar Excel</TableCell>
                  <TableCell>Revisa tabla de errores. Verifica foreign keys y tipos de datos.</TableCell>
                </TableRow>
                <TableRow>
                  <TableCell>Usuario sin permisos</TableCell>
                  <TableCell>Admin debe asignar permisos en Role Manager.</TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </TableContainer>

          <Alert severity="success" sx={{ mt: 3 }}>
            <strong>¿Necesitas ayuda?</strong><br />
            Consulta con tu administrador o contacta al equipo de soporte técnico.
          </Alert>
        </>
      ),
    },
  ];

  const selectedSectionData = sections.find((s) => s.id === selectedSection);

  return (
    <Box sx={{ display: 'flex', height: 'calc(100vh - 64px)' }}>
      {/* Sidebar con índice */}
      <Paper
        sx={{
          width: 280,
          borderRadius: 0,
          borderRight: 1,
          borderColor: 'divider',
          overflowY: 'auto',
        }}
      >
        <Box sx={{ p: 2 }}>
          <Typography variant="h6" gutterBottom>
            Manual de Usuario
          </Typography>
          <Typography variant="caption" color="text.secondary">
            PIM v1.0 - Guía Completa
          </Typography>
          <Box sx={{ mt: 2 }}>
            <Button
              variant="outlined"
              size="small"
              fullWidth
              startIcon={<Print />}
              onClick={handlePrint}
            >
              Exportar a PDF
            </Button>
          </Box>
        </Box>
        <Divider />
        <List dense>
          {sections.map((section) => (
            <ListItemButton
              key={section.id}
              selected={selectedSection === section.id}
              onClick={() => setSelectedSection(section.id)}
            >
              <ListItemText primary={section.title} />
            </ListItemButton>
          ))}
        </List>
      </Paper>

      {/* Contenido principal */}
      <Box sx={{ flex: 1, overflowY: 'auto', p: 4 }}>
        {selectedSectionData && selectedSectionData.content}
      </Box>
    </Box>
  );
}
