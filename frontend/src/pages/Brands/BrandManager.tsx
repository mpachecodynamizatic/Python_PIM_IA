import { useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Chip,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControlLabel,
  IconButton,
  Paper,
  Switch,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Tooltip,
  Typography,
} from '@mui/material';
import { Add, Delete, Edit } from '@mui/icons-material';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { createBrand, deleteBrand, listBrands, updateBrand } from '../../api/brands';
import type { Brand, BrandCreate, BrandUpdate } from '../../types/brand';

export default function BrandManager() {
  const queryClient = useQueryClient();
  const [mutError, setMutError] = useState('');

  // Create dialog
  const [createOpen, setCreateOpen] = useState(false);
  const [newName, setNewName] = useState('');
  const [newSlug, setNewSlug] = useState('');
  const [newDesc, setNewDesc] = useState('');
  const [newWebsite, setNewWebsite] = useState('');

  // Edit dialog
  const [editTarget, setEditTarget] = useState<Brand | null>(null);
  const [editName, setEditName] = useState('');
  const [editSlug, setEditSlug] = useState('');
  const [editDesc, setEditDesc] = useState('');
  const [editWebsite, setEditWebsite] = useState('');
  const [editActive, setEditActive] = useState(true);

  // Delete confirm
  const [deleteTarget, setDeleteTarget] = useState<Brand | null>(null);

  const { data: brands = [], isLoading } = useQuery({
    queryKey: ['brands'],
    queryFn: () => listBrands(),
  });

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['brands'] });
  const onError = (err: unknown) => {
    const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
    setMutError(msg || 'Error inesperado.');
  };

  const createMutation = useMutation({
    mutationFn: (data: BrandCreate) => createBrand(data),
    onSuccess: () => {
      invalidate();
      setCreateOpen(false);
      setNewName(''); setNewSlug(''); setNewDesc(''); setNewWebsite('');
    },
    onError,
  });

  const editMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: BrandUpdate }) => updateBrand(id, data),
    onSuccess: () => { invalidate(); setEditTarget(null); },
    onError,
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => deleteBrand(id),
    onSuccess: () => { invalidate(); setDeleteTarget(null); },
    onError,
  });

  const openEdit = (brand: Brand) => {
    setEditTarget(brand);
    setEditName(brand.name);
    setEditSlug(brand.slug);
    setEditDesc(brand.description || '');
    setEditWebsite(brand.website || '');
    setEditActive(brand.active);
    setMutError('');
  };

  const autoSlug = (name: string) =>
    name.toLowerCase().replace(/\s+/g, '-').replace(/[^a-z0-9-]/g, '');

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
        <Box>
          <Typography variant="h4">Marcas</Typography>
          <Typography variant="body2" color="text.secondary">
            Gestiona el catalogo de marcas disponibles para los productos
          </Typography>
        </Box>
        <Button
          variant="contained"
          startIcon={<Add />}
          onClick={() => { setMutError(''); setCreateOpen(true); }}
        >
          Nueva Marca
        </Button>
      </Box>

      {mutError && (
        <Alert severity="error" onClose={() => setMutError('')} sx={{ mb: 2 }}>
          {mutError}
        </Alert>
      )}

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Nombre</TableCell>
              <TableCell>Slug</TableCell>
              <TableCell>Descripcion</TableCell>
              <TableCell>Web</TableCell>
              <TableCell>Estado</TableCell>
              <TableCell />
            </TableRow>
          </TableHead>
          <TableBody>
            {isLoading && (
              <TableRow>
                <TableCell colSpan={6} align="center">Cargando...</TableCell>
              </TableRow>
            )}
            {!isLoading && brands.length === 0 && (
              <TableRow>
                <TableCell colSpan={6} align="center">
                  <Typography color="text.secondary">No hay marcas. Crea la primera.</Typography>
                </TableCell>
              </TableRow>
            )}
            {brands.map((brand) => (
              <TableRow key={brand.id}>
                <TableCell>
                  <Typography fontWeight={500}>{brand.name}</Typography>
                </TableCell>
                <TableCell>
                  <Typography variant="body2" fontFamily="monospace" color="text.secondary">
                    {brand.slug}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Typography variant="body2" color="text.secondary">
                    {brand.description || '-'}
                  </Typography>
                </TableCell>
                <TableCell>
                  {brand.website ? (
                    <Typography variant="body2" color="primary" component="a" href={brand.website} target="_blank" rel="noopener noreferrer">
                      {brand.website}
                    </Typography>
                  ) : '-'}
                </TableCell>
                <TableCell>
                  <Chip
                    label={brand.active ? 'Activa' : 'Inactiva'}
                    size="small"
                    color={brand.active ? 'success' : 'default'}
                  />
                </TableCell>
                <TableCell align="right">
                  <Tooltip title="Editar">
                    <IconButton size="small" onClick={() => openEdit(brand)}>
                      <Edit fontSize="small" />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="Eliminar">
                    <IconButton size="small" color="error" onClick={() => setDeleteTarget(brand)}>
                      <Delete fontSize="small" />
                    </IconButton>
                  </Tooltip>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Dialog: crear marca */}
      <Dialog
        open={createOpen}
        onClose={() => { setCreateOpen(false); setNewName(''); setNewSlug(''); setNewDesc(''); setNewWebsite(''); }}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Nueva Marca</DialogTitle>
        <DialogContent>
          <Box display="flex" flexDirection="column" gap={2} mt={1}>
            {mutError && <Alert severity="error">{mutError}</Alert>}
            <TextField
              label="Nombre"
              value={newName}
              onChange={(e) => {
                setNewName(e.target.value);
                setNewSlug(autoSlug(e.target.value));
              }}
              autoFocus
              required
            />
            <TextField
              label="Slug"
              value={newSlug}
              onChange={(e) => setNewSlug(autoSlug(e.target.value))}
              helperText="Identificador URL (se genera automaticamente)"
              required
            />
            <TextField
              label="Descripcion (opcional)"
              value={newDesc}
              onChange={(e) => setNewDesc(e.target.value)}
              multiline
              rows={2}
            />
            <TextField
              label="Sitio web (opcional)"
              value={newWebsite}
              onChange={(e) => setNewWebsite(e.target.value)}
              placeholder="https://..."
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => { setCreateOpen(false); setNewName(''); setNewSlug(''); setNewDesc(''); setNewWebsite(''); }}>
            Cancelar
          </Button>
          <Button
            variant="contained"
            onClick={() => {
              setMutError('');
              createMutation.mutate({
                name: newName.trim(),
                slug: newSlug.trim(),
                description: newDesc.trim() || null,
                website: newWebsite.trim() || null,
              });
            }}
            disabled={!newName.trim() || !newSlug.trim() || createMutation.isPending}
          >
            Crear
          </Button>
        </DialogActions>
      </Dialog>

      {/* Dialog: editar marca */}
      <Dialog open={editTarget !== null} onClose={() => setEditTarget(null)} maxWidth="sm" fullWidth>
        <DialogTitle>Editar Marca</DialogTitle>
        <DialogContent>
          <Box display="flex" flexDirection="column" gap={2} mt={1}>
            {mutError && <Alert severity="error">{mutError}</Alert>}
            <TextField
              label="Nombre"
              value={editName}
              onChange={(e) => setEditName(e.target.value)}
              required
            />
            <TextField
              label="Slug"
              value={editSlug}
              onChange={(e) => setEditSlug(autoSlug(e.target.value))}
              required
            />
            <TextField
              label="Descripcion (opcional)"
              value={editDesc}
              onChange={(e) => setEditDesc(e.target.value)}
              multiline
              rows={2}
            />
            <TextField
              label="Sitio web (opcional)"
              value={editWebsite}
              onChange={(e) => setEditWebsite(e.target.value)}
            />
            <FormControlLabel
              control={
                <Switch
                  checked={editActive}
                  onChange={(e) => setEditActive(e.target.checked)}
                />
              }
              label="Marca activa"
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditTarget(null)}>Cancelar</Button>
          <Button
            variant="contained"
            onClick={() => {
              if (!editTarget) return;
              setMutError('');
              editMutation.mutate({
                id: editTarget.id,
                data: {
                  name: editName.trim(),
                  slug: editSlug.trim(),
                  description: editDesc.trim() || null,
                  website: editWebsite.trim() || null,
                  active: editActive,
                },
              });
            }}
            disabled={!editName.trim() || !editSlug.trim() || editMutation.isPending}
          >
            Guardar
          </Button>
        </DialogActions>
      </Dialog>

      {/* Dialog: confirmar eliminar */}
      <Dialog open={deleteTarget !== null} onClose={() => setDeleteTarget(null)} maxWidth="xs" fullWidth>
        <DialogTitle>Eliminar Marca</DialogTitle>
        <DialogContent>
          <Typography>
            ¿Eliminar la marca <strong>{deleteTarget?.name}</strong>? Los productos que la usan
            conservarán el texto de la marca pero dejará de aparecer en los desplegables.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteTarget(null)}>Cancelar</Button>
          <Button
            variant="contained"
            color="error"
            onClick={() => deleteTarget && deleteMutation.mutate(deleteTarget.id)}
            disabled={deleteMutation.isPending}
          >
            Eliminar
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
