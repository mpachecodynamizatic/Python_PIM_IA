import { useCallback, useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Alert,
  Box,
  Button,
  Collapse,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControl,
  IconButton,
  InputLabel,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  MenuItem,
  Paper,
  Select,
  TextField,
  Tooltip,
  Typography,
} from '@mui/material';
import {
  Add as AddIcon,
  Delete,
  Edit,
  ExpandLess,
  ExpandMore,
  Folder,
  FolderOpen,
  Visibility,
} from '@mui/icons-material';
import {
  createCategory,
  deleteCategory,
  getCategoryTree,
  listCategories,
  updateCategory,
} from '../../api/categories';
import type { Category, CategoryTree as CategoryTreeType } from '../../types/category';

/** Collect a node's ID and all descendant IDs recursively. */
function collectCategoryIds(node: CategoryTreeType): string[] {
  const ids = [node.id];
  for (const child of node.children) {
    ids.push(...collectCategoryIds(child));
  }
  return ids;
}

function TreeNode({
  node,
  level = 0,
  onEdit,
  onDelete,
  onViewProducts,
}: {
  node: CategoryTreeType;
  level?: number;
  onEdit: (node: CategoryTreeType) => void;
  onDelete: (node: CategoryTreeType) => void;
  onViewProducts: (node: CategoryTreeType) => void;
}) {
  const [open, setOpen] = useState(false);
  const hasChildren = node.children && node.children.length > 0;

  return (
    <>
      <ListItemButton
        sx={{ pl: 2 + level * 3 }}
        onClick={() => setOpen(!open)}
      >
        <ListItemIcon>{open ? <FolderOpen /> : <Folder />}</ListItemIcon>
        <ListItemText
          primary={node.name}
          secondary={`slug: ${node.slug} | atributos: ${Object.keys(node.attribute_schema).length}`}
        />
        {hasChildren && (open ? <ExpandLess /> : <ExpandMore />)}
        <Tooltip title={hasChildren ? "Ver productos de esta categoria y subcategorias" : "Ver productos de esta categoria"}>
          <IconButton
            size="small"
            onClick={(e) => { e.stopPropagation(); onViewProducts(node); }}
            sx={{ ml: 1 }}
          >
            <Visibility fontSize="small" />
          </IconButton>
        </Tooltip>
        <Tooltip title="Editar categoria">
          <IconButton
            size="small"
            onClick={(e) => { e.stopPropagation(); onEdit(node); }}
          >
            <Edit fontSize="small" />
          </IconButton>
        </Tooltip>
        <Tooltip title="Eliminar categoria">
          <IconButton
            size="small"
            color="error"
            onClick={(e) => { e.stopPropagation(); onDelete(node); }}
          >
            <Delete fontSize="small" />
          </IconButton>
        </Tooltip>
      </ListItemButton>
      {hasChildren && (
        <Collapse in={open} timeout="auto" unmountOnExit>
          <List disablePadding>
            {node.children.map((child) => (
              <TreeNode key={child.id} node={child} level={level + 1} onEdit={onEdit} onDelete={onDelete} onViewProducts={onViewProducts} />
            ))}
          </List>
        </Collapse>
      )}
    </>
  );
}

export default function CategoryTreePage() {
  const navigate = useNavigate();
  const [tree, setTree] = useState<CategoryTreeType[]>([]);
  const [flatList, setFlatList] = useState<Category[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  const handleViewProducts = (node: CategoryTreeType) => {
    const ids = collectCategoryIds(node);
    if (ids.length === 1) {
      navigate(`/products?category_id=${ids[0]}`);
    } else {
      navigate(`/products?category_ids=${ids.join(',')}`);
    }
  };

  // Create dialog
  const [dialogOpen, setDialogOpen] = useState(false);
  const [newCat, setNewCat] = useState({ name: '', slug: '', parent_id: '' });

  // Edit dialog
  const [editTarget, setEditTarget] = useState<CategoryTreeType | null>(null);
  const [editName, setEditName] = useState('');
  const [editSlug, setEditSlug] = useState('');
  const [editDesc, setEditDesc] = useState('');
  const [editParentId, setEditParentId] = useState('');

  // Delete confirm
  const [deleteTarget, setDeleteTarget] = useState<CategoryTreeType | null>(null);

  const fetchTree = useCallback(async () => {
    try {
      const [treeData, flat] = await Promise.all([getCategoryTree(), listCategories()]);
      setTree(treeData);
      setFlatList(flat);
    } catch {
      // Tree will remain as-is
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchTree(); }, [fetchTree]);

  const handleCreate = async () => {
    setError('');
    try {
      await createCategory({
        name: newCat.name,
        slug: newCat.slug,
        parent_id: newCat.parent_id || undefined,
      });
      setDialogOpen(false);
      setNewCat({ name: '', slug: '', parent_id: '' });
      fetchTree();
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(msg || 'Error al crear la categoria.');
    }
  };

  const openEdit = (node: CategoryTreeType) => {
    setEditTarget(node);
    setEditName(node.name);
    setEditSlug(node.slug);
    setEditDesc(node.description || '');
    setEditParentId(node.parent_id || '');
    setError('');
  };

  const handleEdit = async () => {
    if (!editTarget) return;
    setError('');
    try {
      await updateCategory(editTarget.id, {
        name: editName,
        slug: editSlug,
        description: editDesc || null,
        parent_id: editParentId || null,
      });
      setEditTarget(null);
      fetchTree();
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(msg || 'Error al actualizar la categoria.');
    }
  };

  const handleDelete = async () => {
    if (!deleteTarget) return;
    setError('');
    try {
      await deleteCategory(deleteTarget.id);
      setDeleteTarget(null);
      fetchTree();
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(msg || 'Error al eliminar la categoria.');
    }
  };

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h4">Taxonomia</Typography>
        <Button variant="contained" startIcon={<AddIcon />} onClick={() => { setError(''); setDialogOpen(true); }}>
          Nueva Categoria
        </Button>
      </Box>

      {error && (
        <Alert severity="error" onClose={() => setError('')} sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Paper>
        {loading ? (
          <Box p={3}>
            <Typography>Cargando...</Typography>
          </Box>
        ) : tree.length === 0 ? (
          <Box p={3}>
            <Typography color="text.secondary">No hay categorias. Crea la primera.</Typography>
          </Box>
        ) : (
          <List>
            {tree.map((node) => (
              <TreeNode key={node.id} node={node} onEdit={openEdit} onDelete={setDeleteTarget} onViewProducts={handleViewProducts} />
            ))}
          </List>
        )}
      </Paper>

      {/* Dialog: crear categoria */}
      <Dialog
        open={dialogOpen}
        onClose={() => { setDialogOpen(false); setNewCat({ name: '', slug: '', parent_id: '' }); }}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Nueva Categoria</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            label="Nombre"
            value={newCat.name}
            onChange={(e) => setNewCat({ ...newCat, name: e.target.value })}
            margin="normal"
            required
          />
          <TextField
            fullWidth
            label="Slug"
            value={newCat.slug}
            onChange={(e) => setNewCat({ ...newCat, slug: e.target.value.toLowerCase().replace(/\s+/g, '-') })}
            margin="normal"
            required
            helperText="Identificador URL (ej: electronica, muebles-salon)"
          />
          <FormControl fullWidth margin="normal">
            <InputLabel>Categoria padre (opcional)</InputLabel>
            <Select
              value={newCat.parent_id}
              label="Categoria padre (opcional)"
              onChange={(e) => setNewCat({ ...newCat, parent_id: e.target.value })}
            >
              <MenuItem value="">Sin padre (raiz)</MenuItem>
              {flatList.map((cat) => (
                <MenuItem key={cat.id} value={cat.id}>{cat.name}</MenuItem>
              ))}
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => { setDialogOpen(false); setNewCat({ name: '', slug: '', parent_id: '' }); }}>Cancelar</Button>
          <Button
            variant="contained"
            onClick={handleCreate}
            disabled={!newCat.name || !newCat.slug}
          >
            Crear
          </Button>
        </DialogActions>
      </Dialog>

      {/* Dialog: editar categoria */}
      <Dialog
        open={editTarget !== null}
        onClose={() => setEditTarget(null)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Editar Categoria</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            label="Nombre"
            value={editName}
            onChange={(e) => setEditName(e.target.value)}
            margin="normal"
            required
          />
          <TextField
            fullWidth
            label="Slug"
            value={editSlug}
            onChange={(e) => setEditSlug(e.target.value.toLowerCase().replace(/\s+/g, '-'))}
            margin="normal"
            required
          />
          <TextField
            fullWidth
            label="Descripcion (opcional)"
            value={editDesc}
            onChange={(e) => setEditDesc(e.target.value)}
            margin="normal"
            multiline
            rows={2}
          />
          <FormControl fullWidth margin="normal">
            <InputLabel>Categoria padre (opcional)</InputLabel>
            <Select
              value={editParentId}
              label="Categoria padre (opcional)"
              onChange={(e) => setEditParentId(e.target.value)}
            >
              <MenuItem value="">Sin padre (raiz)</MenuItem>
              {flatList
                .filter((cat) => cat.id !== editTarget?.id)
                .map((cat) => (
                  <MenuItem key={cat.id} value={cat.id}>{cat.name}</MenuItem>
                ))}
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditTarget(null)}>Cancelar</Button>
          <Button
            variant="contained"
            onClick={handleEdit}
            disabled={!editName || !editSlug}
          >
            Guardar
          </Button>
        </DialogActions>
      </Dialog>

      {/* Dialog: confirmar eliminacion */}
      <Dialog
        open={deleteTarget !== null}
        onClose={() => setDeleteTarget(null)}
        maxWidth="xs"
        fullWidth
      >
        <DialogTitle>Eliminar Categoria</DialogTitle>
        <DialogContent>
          <Typography>
            ¿Eliminar <strong>{deleteTarget?.name}</strong>? Esta accion no se puede deshacer. Las categorias hijo quedaran sin padre.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteTarget(null)}>Cancelar</Button>
          <Button variant="contained" color="error" onClick={handleDelete}>
            Eliminar
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
