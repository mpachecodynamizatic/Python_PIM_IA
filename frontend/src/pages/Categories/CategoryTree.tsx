import { useEffect, useState } from 'react';
import {
  Box,
  Button,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Collapse,
  Paper,
  TextField,
  Typography,
} from '@mui/material';
import {
  Add as AddIcon,
  ExpandLess,
  ExpandMore,
  Folder,
  FolderOpen,
} from '@mui/icons-material';
import { getCategoryTree, createCategory } from '../../api/categories';
import type { CategoryTree as CategoryTreeType } from '../../types/category';

function TreeNode({ node, level = 0 }: { node: CategoryTreeType; level?: number }) {
  const [open, setOpen] = useState(false);
  const hasChildren = node.children && node.children.length > 0;

  return (
    <>
      <ListItemButton sx={{ pl: 2 + level * 3 }} onClick={() => setOpen(!open)}>
        <ListItemIcon>{open ? <FolderOpen /> : <Folder />}</ListItemIcon>
        <ListItemText
          primary={node.name}
          secondary={`slug: ${node.slug} | atributos: ${Object.keys(node.attribute_schema).length}`}
        />
        {hasChildren && (open ? <ExpandLess /> : <ExpandMore />)}
      </ListItemButton>
      {hasChildren && (
        <Collapse in={open} timeout="auto" unmountOnExit>
          <List disablePadding>
            {node.children.map((child) => (
              <TreeNode key={child.id} node={child} level={level + 1} />
            ))}
          </List>
        </Collapse>
      )}
    </>
  );
}

export default function CategoryTreePage() {
  const [tree, setTree] = useState<CategoryTreeType[]>([]);
  const [loading, setLoading] = useState(true);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [newCat, setNewCat] = useState({ name: '', slug: '' });

  const fetchTree = async () => {
    try {
      const data = await getCategoryTree();
      setTree(data);
    } catch {
      // Tree will remain empty
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchTree();
  }, []);

  const handleCreate = async () => {
    await createCategory(newCat);
    setDialogOpen(false);
    setNewCat({ name: '', slug: '' });
    fetchTree();
  };

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h4">Taxonomia</Typography>
        <Button variant="contained" startIcon={<AddIcon />} onClick={() => setDialogOpen(true)}>
          Nueva Categoria
        </Button>
      </Box>

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
              <TreeNode key={node.id} node={node} />
            ))}
          </List>
        )}
      </Paper>

      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="sm" fullWidth>
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
            onChange={(e) =>
              setNewCat({
                ...newCat,
                slug: e.target.value.toLowerCase().replace(/\s+/g, '-'),
              })
            }
            margin="normal"
            required
            helperText="Identificador URL (ej: electronica, muebles-salon)"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>Cancelar</Button>
          <Button
            variant="contained"
            onClick={handleCreate}
            disabled={!newCat.name || !newCat.slug}
          >
            Crear
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
