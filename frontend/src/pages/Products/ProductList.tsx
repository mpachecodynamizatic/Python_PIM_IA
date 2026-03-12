import { useEffect, useState, useCallback } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  Accordion,
  AccordionDetails,
  AccordionSummary,
  Box,
  Button,
  Chip,
  CircularProgress,
  Collapse,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Alert,
  FormControl,
  FormControlLabel,
  IconButton,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  Switch,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TablePagination,
  TableRow,
  TextField,
  Tooltip,
  Typography,
} from '@mui/material';
import {
  Add as AddIcon,
  BookmarkBorder,
  Clear,
  Delete,
  ExpandMore,
  FilterList,
  FileDownload,
  FileUpload,
  Public,
  Save,
  Star,
  StarBorder,
  Upload,
} from '@mui/icons-material';
import { listProducts, createProduct, deleteProduct } from '../../api/products';
import type { ProductFilters } from '../../api/products';
import { listCategories } from '../../api/categories';
import { listBrands } from '../../api/brands';
import type { Brand } from '../../types/brand';
import {
  listProductViews, createProductView, deleteProductView, updateProductView,
  exportProductView, importProductView,
} from '../../api/views';
import type { ProductListItem } from '../../types/product';
import type { Category } from '../../types/category';
import type { SavedView, SavedViewExport } from '../../types/savedView';
import ExportDialog from '../../components/ExportDialog';
import ImportDialog from '../../components/ImportDialog';

const STATUS_LABELS: Record<string, string> = {
  draft: 'Borrador',
  in_review: 'En revision',
  approved: 'Aprobado',
  ready: 'Publicado',
  retired: 'Retirado',
};

const statusColors: Record<string, 'default' | 'warning' | 'success' | 'error' | 'info' | 'primary'> = {
  draft: 'warning',
  in_review: 'info',
  approved: 'primary',
  ready: 'success',
  retired: 'error',
};

interface Filters {
  q: string;
  status: string;
  brand: string;
  category_id: string;
  category_ids: string;
  created_from: string;
  created_to: string;
  updated_from: string;
  updated_to: string;
  has_media: string;
  has_i18n: string;
  supplier_id: string;
}

const EMPTY_FILTERS: Filters = {
  q: '',
  status: '',
  brand: '',
  category_id: '',
  category_ids: '',
  created_from: '',
  created_to: '',
  updated_from: '',
  updated_to: '',
  has_media: '',
  has_i18n: '',
  supplier_id: '',
};

function filtersToApiParams(f: Filters): ProductFilters {
  const params: ProductFilters = {};
  if (f.q) params.q = f.q;
  if (f.status) params.status = f.status;
  if (f.brand) params.brand = f.brand;
  if (f.category_ids) params.category_ids = f.category_ids;
  else if (f.category_id) params.category_id = f.category_id;
  if (f.created_from) params.created_from = f.created_from;
  if (f.created_to) params.created_to = f.created_to;
  if (f.updated_from) params.updated_from = f.updated_from;
  if (f.updated_to) params.updated_to = f.updated_to;
  if (f.has_media === 'true') params.has_media = true;
  if (f.has_media === 'false') params.has_media = false;
  if (f.has_i18n === 'true') params.has_i18n = true;
  if (f.has_i18n === 'false') params.has_i18n = false;
  if (f.supplier_id) params.supplier_id = f.supplier_id;
  return params;
}

function hasActiveFilters(f: Filters): boolean {
  return Object.values(f).some((v) => v !== '');
}

export default function ProductList() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const [products, setProducts] = useState<ProductListItem[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(0);
  const [size, setSize] = useState(20);
  const [filters, setFilters] = useState<Filters>({
    ...EMPTY_FILTERS,
    status: searchParams.get('status') || '',
    brand: searchParams.get('brand') || '',
    category_id: searchParams.get('category_id') || '',
    category_ids: searchParams.get('category_ids') || '',
    supplier_id: searchParams.get('supplier_id') || '',
  });
  const [showAdvanced, setShowAdvanced] = useState(false);
  const [categories, setCategories] = useState<Category[]>([]);
  const [brands, setBrands] = useState<Brand[]>([]);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [newProduct, setNewProduct] = useState({ sku: '', brand: '', category_id: '' });
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Saved views
  const [savedViews, setSavedViews] = useState<SavedView[]>([]);
  const [activeViewId, setActiveViewId] = useState<string | null>(null);
  const [saveDialogOpen, setSaveDialogOpen] = useState(false);
  const [viewName, setViewName] = useState('');
  const [viewDesc, setViewDesc] = useState('');
  const [viewDefault, setViewDefault] = useState(false);
  const [viewPublic, setViewPublic] = useState(false);

  // Export / Import dialogs
  const [exportOpen, setExportOpen] = useState(false);
  const [importOpen, setImportOpen] = useState(false);

  // Delete confirmation
  const [deleteConfirmSku, setDeleteConfirmSku] = useState<string | null>(null);

  const updateFilter = (key: keyof Filters, value: string) => {
    setFilters((prev) => ({ ...prev, [key]: value }));
    setPage(0);
    setActiveViewId(null);
  };

  const clearFilters = () => {
    setFilters(EMPTY_FILTERS);
    setPage(0);
    setActiveViewId(null);
  };

  const fetchProducts = useCallback(async () => {
    setLoading(true);
    setError('');
    try {
      const result = await listProducts({
        page: page + 1,
        size,
        ...filtersToApiParams(filters),
      });
      setProducts(result.items);
      setTotal(result.total);
    } catch {
      setError('Error al cargar productos');
      setProducts([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  }, [page, size, filters]);

  useEffect(() => {
    fetchProducts();
  }, [fetchProducts]);

  useEffect(() => {
    listCategories().then(setCategories).catch(() => {});
    listBrands().then(setBrands).catch(() => {});
    loadViews();
  }, []);

  const loadViews = async () => {
    try {
      const views = await listProductViews();
      setSavedViews(views);
      // Apply default view if exists and no manual filter set
      const defaultView = views.find((v) => v.is_default);
      if (defaultView && !hasActiveFilters(filters)) {
        applyView(defaultView);
      }
    } catch {
      // Ignore - views are optional
    }
  };

  const applyView = (view: SavedView) => {
    const f = view.filters as Partial<Filters>;
    setFilters({ ...EMPTY_FILTERS, ...f });
    setActiveViewId(view.id);
    setPage(0);
  };

  const handleSaveView = async () => {
    if (!viewName.trim()) return;
    const activeFilters: Record<string, unknown> = {};
    for (const [k, v] of Object.entries(filters)) {
      if (v !== '') activeFilters[k] = v;
    }
    await createProductView({
      name: viewName.trim(),
      description: viewDesc.trim() || null,
      filters: activeFilters,
      is_default: viewDefault,
      is_public: viewPublic,
    });
    setSaveDialogOpen(false);
    setViewName('');
    setViewDesc('');
    setViewDefault(false);
    setViewPublic(false);
    loadViews();
  };

  const handleExportView = async (view: SavedView) => {
    try {
      const exported = await exportProductView(view.id);
      const blob = new Blob([JSON.stringify(exported, null, 2)], { type: 'application/json' });
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = `vista-${view.name.replace(/\s+/g, '-').toLowerCase()}.json`;
      a.click();
      URL.revokeObjectURL(url);
    } catch {
      // Silently ignore export errors
    }
  };

  const handleImportView = async (file: File) => {
    try {
      const text = await file.text();
      const data: SavedViewExport = JSON.parse(text);
      await importProductView(data);
      loadViews();
    } catch {
      // Silently ignore parse/import errors
    }
  };

  const handleDeleteView = async (viewId: string) => {
    await deleteProductView(viewId);
    if (activeViewId === viewId) setActiveViewId(null);
    loadViews();
  };

  const handleToggleDefault = async (view: SavedView) => {
    await updateProductView(view.id, { is_default: !view.is_default });
    loadViews();
  };

  const handleCreate = async () => {
    setError('');
    try {
      await createProduct(newProduct);
      setDialogOpen(false);
      setNewProduct({ sku: '', brand: '', category_id: '' });
      fetchProducts();
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(msg || 'Error al crear el producto.');
    }
  };

  const handleDeleteProduct = async () => {
    if (!deleteConfirmSku) return;
    setError('');
    try {
      await deleteProduct(deleteConfirmSku);
      setDeleteConfirmSku(null);
      fetchProducts();
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(msg || 'Error al eliminar el producto.');
      setDeleteConfirmSku(null);
    }
  };

  const activeFilterCount = Object.values(filters).filter((v) => v !== '').length;

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h4">Productos</Typography>
        <Box display="flex" gap={1}>
          <Tooltip title="Importar productos desde Excel">
            <Button
              variant="outlined"
              size="small"
              startIcon={<FileUpload />}
              onClick={() => setImportOpen(true)}
            >
              Importar
            </Button>
          </Tooltip>
          <Tooltip title="Exportar productos a Excel">
            <Button
              variant="outlined"
              size="small"
              startIcon={<FileDownload />}
              onClick={() => setExportOpen(true)}
            >
              Exportar
            </Button>
          </Tooltip>
          <Button variant="contained" startIcon={<AddIcon />} onClick={() => setDialogOpen(true)}>
            Nuevo Producto
          </Button>
        </Box>
      </Box>

      {error && (
        <Alert severity="error" onClose={() => setError('')} sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {/* Saved views bar */}
      {savedViews.length > 0 && (
        <Box display="flex" gap={1} mb={2} alignItems="center" flexWrap="wrap">
          <BookmarkBorder fontSize="small" color="action" />
          {savedViews.map((view) => (
            <Chip
              key={view.id}
              label={
                <Box component="span" display="flex" alignItems="center" gap={0.5}>
                  {view.is_public && <Public sx={{ fontSize: 12 }} />}
                  {view.name}
                </Box>
              }
              size="small"
              color={activeViewId === view.id ? 'primary' : 'default'}
              variant={activeViewId === view.id ? 'filled' : 'outlined'}
              icon={view.is_default ? <Star fontSize="small" /> : undefined}
              onClick={() => applyView(view)}
              onDelete={() => handleDeleteView(view.id)}
              deleteIcon={<Delete fontSize="small" />}
            />
          ))}
          <Tooltip title="Importar vista desde archivo JSON">
            <IconButton
              size="small"
              component="label"
            >
              <Upload fontSize="small" />
              <input
                type="file"
                accept=".json"
                hidden
                onChange={(e) => {
                  const file = e.target.files?.[0];
                  if (file) handleImportView(file);
                  e.target.value = '';
                }}
              />
            </IconButton>
          </Tooltip>
        </Box>
      )}
      {savedViews.length === 0 && (
        <Box display="flex" gap={1} mb={2} alignItems="center">
          <Tooltip title="Importar vista desde archivo JSON">
            <IconButton size="small" component="label">
              <Upload fontSize="small" />
              <input
                type="file"
                accept=".json"
                hidden
                onChange={(e) => {
                  const file = e.target.files?.[0];
                  if (file) handleImportView(file);
                  e.target.value = '';
                }}
              />
            </IconButton>
          </Tooltip>
        </Box>
      )}

      {/* Basic filters row */}
      <Box display="flex" gap={2} mb={1} alignItems="center">
        <TextField
          size="small"
          label="Buscar"
          value={filters.q}
          onChange={(e) => updateFilter('q', e.target.value)}
          sx={{ minWidth: 250 }}
        />
        <FormControl size="small" sx={{ minWidth: 150 }}>
          <InputLabel>Estado</InputLabel>
          <Select
            value={filters.status}
            label="Estado"
            onChange={(e) => updateFilter('status', e.target.value)}
          >
            <MenuItem value="">Todos</MenuItem>
            <MenuItem value="draft">Borrador</MenuItem>
            <MenuItem value="in_review">En revision</MenuItem>
            <MenuItem value="approved">Aprobado</MenuItem>
            <MenuItem value="ready">Publicado</MenuItem>
            <MenuItem value="retired">Retirado</MenuItem>
          </Select>
        </FormControl>
        <FormControl size="small" sx={{ minWidth: 150 }}>
          <InputLabel>Categoria</InputLabel>
          <Select
            value={filters.category_id}
            label="Categoria"
            onChange={(e) => updateFilter('category_id', e.target.value)}
          >
            <MenuItem value="">Todas</MenuItem>
            {categories.map((cat) => (
              <MenuItem key={cat.id} value={cat.id}>{cat.name}</MenuItem>
            ))}
          </Select>
        </FormControl>
        <Button
          size="small"
          startIcon={<FilterList />}
          onClick={() => setShowAdvanced(!showAdvanced)}
          color={showAdvanced ? 'primary' : 'inherit'}
        >
          Avanzados{activeFilterCount > 2 ? ` (${activeFilterCount - 2})` : ''}
        </Button>
        {hasActiveFilters(filters) && (
          <>
            <Tooltip title="Guardar vista">
              <IconButton size="small" onClick={() => setSaveDialogOpen(true)}>
                <Save fontSize="small" />
              </IconButton>
            </Tooltip>
            {activeViewId && (
              <Tooltip title="Exportar vista activa como JSON">
                <IconButton
                  size="small"
                  onClick={() => {
                    const view = savedViews.find((v) => v.id === activeViewId);
                    if (view) handleExportView(view);
                  }}
                >
                  <StarBorder fontSize="small" />
                </IconButton>
              </Tooltip>
            )}
            <Tooltip title="Limpiar filtros">
              <IconButton size="small" onClick={clearFilters}>
                <Clear fontSize="small" />
              </IconButton>
            </Tooltip>
          </>
        )}
      </Box>

      {/* Advanced filters panel */}
      <Collapse in={showAdvanced}>
        <Paper variant="outlined" sx={{ p: 2, mb: 2 }}>
          <Box display="flex" gap={2} flexWrap="wrap">
            <TextField
              size="small"
              label="Marca"
              value={filters.brand}
              onChange={(e) => updateFilter('brand', e.target.value)}
              sx={{ minWidth: 150 }}
            />
            <TextField
              size="small"
              label="Creado desde"
              type="date"
              value={filters.created_from}
              onChange={(e) => updateFilter('created_from', e.target.value)}
              InputLabelProps={{ shrink: true }}
              sx={{ minWidth: 150 }}
            />
            <TextField
              size="small"
              label="Creado hasta"
              type="date"
              value={filters.created_to}
              onChange={(e) => updateFilter('created_to', e.target.value)}
              InputLabelProps={{ shrink: true }}
              sx={{ minWidth: 150 }}
            />
            <TextField
              size="small"
              label="Actualizado desde"
              type="date"
              value={filters.updated_from}
              onChange={(e) => updateFilter('updated_from', e.target.value)}
              InputLabelProps={{ shrink: true }}
              sx={{ minWidth: 150 }}
            />
            <TextField
              size="small"
              label="Actualizado hasta"
              type="date"
              value={filters.updated_to}
              onChange={(e) => updateFilter('updated_to', e.target.value)}
              InputLabelProps={{ shrink: true }}
              sx={{ minWidth: 150 }}
            />
            <FormControl size="small" sx={{ minWidth: 130 }}>
              <InputLabel>Media</InputLabel>
              <Select
                value={filters.has_media}
                label="Media"
                onChange={(e) => updateFilter('has_media', e.target.value)}
              >
                <MenuItem value="">Todos</MenuItem>
                <MenuItem value="true">Con media</MenuItem>
                <MenuItem value="false">Sin media</MenuItem>
              </Select>
            </FormControl>
            <FormControl size="small" sx={{ minWidth: 150 }}>
              <InputLabel>Traducciones</InputLabel>
              <Select
                value={filters.has_i18n}
                label="Traducciones"
                onChange={(e) => updateFilter('has_i18n', e.target.value)}
              >
                <MenuItem value="">Todos</MenuItem>
                <MenuItem value="true">Con traducciones</MenuItem>
                <MenuItem value="false">Sin traducciones</MenuItem>
              </Select>
            </FormControl>
          </Box>
        </Paper>
      </Collapse>

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>SKU</TableCell>
              <TableCell>Marca</TableCell>
              <TableCell>Estado</TableCell>
              <TableCell>Actualizado</TableCell>
              <TableCell />
            </TableRow>
          </TableHead>
          <TableBody>
            {loading && (
              <TableRow>
                <TableCell colSpan={5} align="center">
                  <CircularProgress size={24} />
                </TableCell>
              </TableRow>
            )}
            {!loading && products.map((product) => (
              <TableRow
                key={product.sku}
                hover
                sx={{ cursor: 'pointer' }}
                onClick={() => navigate(`/products/${product.sku}`)}
              >
                <TableCell>{product.sku}</TableCell>
                <TableCell>{product.brand}</TableCell>
                <TableCell>
                  <Chip label={STATUS_LABELS[product.status] || product.status} color={statusColors[product.status] || 'default'} size="small" />
                </TableCell>
                <TableCell>{new Date(product.updated_at).toLocaleDateString()}</TableCell>
                <TableCell align="right">
                  <Tooltip title="Eliminar producto">
                    <IconButton
                      size="small"
                      color="error"
                      onClick={(e) => { e.stopPropagation(); setDeleteConfirmSku(product.sku); }}
                    >
                      <Delete fontSize="small" />
                    </IconButton>
                  </Tooltip>
                </TableCell>
              </TableRow>
            ))}
            {!loading && products.length === 0 && (
              <TableRow>
                <TableCell colSpan={5} align="center">
                  No se encontraron productos
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
        <TablePagination
          component="div"
          count={total}
          page={page}
          rowsPerPage={size}
          onPageChange={(_, p) => setPage(p)}
          onRowsPerPageChange={(e) => {
            setSize(parseInt(e.target.value, 10));
            setPage(0);
          }}
          rowsPerPageOptions={[10, 20, 50]}
        />
      </TableContainer>

      {/* Dialog: nuevo producto */}
      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Nuevo Producto</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            label="SKU"
            value={newProduct.sku}
            onChange={(e) => setNewProduct({ ...newProduct, sku: e.target.value })}
            margin="normal"
            required
          />
          <FormControl fullWidth margin="normal" required>
            <InputLabel>Marca</InputLabel>
            <Select
              value={newProduct.brand}
              label="Marca"
              onChange={(e) => setNewProduct({ ...newProduct, brand: e.target.value })}
            >
              {brands.filter((b) => b.active).map((b) => (
                <MenuItem key={b.id} value={b.name}>{b.name}</MenuItem>
              ))}
            </Select>
          </FormControl>
          <FormControl fullWidth margin="normal" required>
            <InputLabel>Categoria</InputLabel>
            <Select
              value={newProduct.category_id}
              label="Categoria"
              onChange={(e) => setNewProduct({ ...newProduct, category_id: e.target.value })}
            >
              {categories.map((cat) => (
                <MenuItem key={cat.id} value={cat.id}>
                  {cat.name}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => { setDialogOpen(false); setNewProduct({ sku: '', brand: '', category_id: '' }); }}>Cancelar</Button>
          <Button
            variant="contained"
            onClick={handleCreate}
            disabled={!newProduct.sku || !newProduct.brand || !newProduct.category_id}
          >
            Crear
          </Button>
        </DialogActions>
      </Dialog>

      {/* Dialog: confirmar eliminar producto */}
      <Dialog open={deleteConfirmSku !== null} onClose={() => setDeleteConfirmSku(null)} maxWidth="xs" fullWidth>
        <DialogTitle>Eliminar Producto</DialogTitle>
        <DialogContent>
          <Typography>
            ¿Eliminar el producto <strong>{deleteConfirmSku}</strong>? Esta accion no se puede deshacer.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteConfirmSku(null)}>Cancelar</Button>
          <Button variant="contained" color="error" onClick={handleDeleteProduct}>Eliminar</Button>
        </DialogActions>
      </Dialog>

      {/* Dialog: guardar vista */}
      <Dialog open={saveDialogOpen} onClose={() => setSaveDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Guardar Vista</DialogTitle>
        <DialogContent>
          <Box display="flex" flexDirection="column" gap={2} mt={1}>
            <TextField
              label="Nombre"
              value={viewName}
              onChange={(e) => setViewName(e.target.value)}
              autoFocus
            />
            <TextField
              label="Descripcion (opcional)"
              value={viewDesc}
              onChange={(e) => setViewDesc(e.target.value)}
              multiline
              rows={2}
            />
            <FormControlLabel
              control={<Switch checked={viewDefault} onChange={(e) => setViewDefault(e.target.checked)} />}
              label="Vista por defecto (se aplica al entrar)"
            />
            <FormControlLabel
              control={<Switch checked={viewPublic} onChange={(e) => setViewPublic(e.target.checked)} />}
              label="Vista pública (visible para todos los usuarios)"
            />
            <Typography variant="body2" color="text.secondary">
              Filtros activos: {Object.entries(filters).filter(([, v]) => v !== '').map(([k]) => k).join(', ') || 'ninguno'}
            </Typography>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSaveDialogOpen(false)}>Cancelar</Button>
          <Button
            variant="contained"
            onClick={handleSaveView}
            disabled={!viewName.trim()}
          >
            Guardar
          </Button>
        </DialogActions>
      </Dialog>

      {/* Dialog: exportar productos */}
      <ExportDialog
        open={exportOpen}
        onClose={() => setExportOpen(false)}
        resource="products"
        resourceLabel="Productos"
        filters={filtersToApiParams(filters) as Record<string, unknown>}
        totalRecords={total}
      />

      {/* Dialog: importar productos */}
      <ImportDialog
        open={importOpen}
        onClose={() => setImportOpen(false)}
        resource="products"
        resourceLabel="Productos"
        onSuccess={fetchProducts}
      />
    </Box>
  );
}
