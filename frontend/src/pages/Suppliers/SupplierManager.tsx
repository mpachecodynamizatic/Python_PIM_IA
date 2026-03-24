import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
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
import { Add, Delete, Edit, Visibility, FileUpload, FileDownload } from '@mui/icons-material';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { listSuppliers, createSupplier, updateSupplier, deleteSupplier } from '../../api/product_extras';
import type { Supplier } from '../../types/product';
import ImportDialog from '../../components/ImportDialog';
import ExportDialog from '../../components/ExportDialog';

type SupplierCreate = Omit<Supplier, 'id' | 'created_at' | 'updated_at'>;

const EMPTY_FORM: SupplierCreate = {
  name: '',
  code: '',
  country: '',
  contact_email: '',
  contact_phone: '',
  notes: '',
  active: true,
};

export default function SupplierManager() {
  const navigate = useNavigate();
  const queryClient = useQueryClient();
  const [mutError, setMutError] = useState('');

  const [createOpen, setCreateOpen] = useState(false);
  const [newForm, setNewForm] = useState<SupplierCreate>({ ...EMPTY_FORM });

  const [editTarget, setEditTarget] = useState<Supplier | null>(null);
  const [editForm, setEditForm] = useState<Partial<Supplier>>({});

  const [deleteTarget, setDeleteTarget] = useState<Supplier | null>(null);

  // Import/Export dialogs
  const [importOpen, setImportOpen] = useState(false);
  const [exportOpen, setExportOpen] = useState(false);

  const { data: suppliers = [], isLoading } = useQuery({
    queryKey: ['suppliers'],
    queryFn: () => listSuppliers(),
  });

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['suppliers'] });
  const onError = (err: unknown) => {
    const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
    setMutError(msg || 'Error inesperado.');
  };

  const createMutation = useMutation({
    mutationFn: (data: SupplierCreate) => createSupplier(data),
    onSuccess: () => {
      invalidate();
      setCreateOpen(false);
      setNewForm({ ...EMPTY_FORM });
      setMutError('');
    },
    onError,
  });

  const editMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Supplier> }) => updateSupplier(id, data),
    onSuccess: () => { invalidate(); setEditTarget(null); setMutError(''); },
    onError,
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => deleteSupplier(id),
    onSuccess: () => { invalidate(); setDeleteTarget(null); },
    onError,
  });

  const openEdit = (supplier: Supplier) => {
    setEditTarget(supplier);
    setEditForm({ ...supplier });
    setMutError('');
  };

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
        <Box>
          <Typography variant="h4">Proveedores</Typography>
          <Typography variant="body2" color="text.secondary">
            Gestiona el catalogo de proveedores para vincularlos a productos
          </Typography>
        </Box>
        <Box display="flex" gap={1}>
          <Button
            variant="outlined"
            startIcon={<FileUpload />}
            onClick={() => setImportOpen(true)}
          >
            Importar
          </Button>
          <Button
            variant="outlined"
            startIcon={<FileDownload />}
            onClick={() => setExportOpen(true)}
          >
            Exportar
          </Button>
          <Button
            variant="contained"
            startIcon={<Add />}
            onClick={() => { setMutError(''); setNewForm({ ...EMPTY_FORM }); setCreateOpen(true); }}
          >
            Nuevo Proveedor
          </Button>
        </Box>
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
              <TableCell>Codigo</TableCell>
              <TableCell>Pais</TableCell>
              <TableCell>Email</TableCell>
              <TableCell>Telefono</TableCell>
              <TableCell>Estado</TableCell>
              <TableCell />
            </TableRow>
          </TableHead>
          <TableBody>
            {isLoading && (
              <TableRow>
                <TableCell colSpan={7} align="center">Cargando...</TableCell>
              </TableRow>
            )}
            {!isLoading && suppliers.length === 0 && (
              <TableRow>
                <TableCell colSpan={7} align="center">
                  <Typography color="text.secondary">No hay proveedores. Crea el primero.</Typography>
                </TableCell>
              </TableRow>
            )}
            {suppliers.map((supplier) => (
              <TableRow key={supplier.id}>
                <TableCell>
                  <Typography fontWeight={500}>{supplier.name}</Typography>
                  {supplier.notes && (
                    <Typography variant="caption" color="text.secondary" display="block">
                      {supplier.notes}
                    </Typography>
                  )}
                </TableCell>
                <TableCell>
                  <Typography variant="body2" fontFamily="monospace" color="text.secondary">
                    {supplier.code || '-'}
                  </Typography>
                </TableCell>
                <TableCell>{supplier.country || '-'}</TableCell>
                <TableCell>
                  {supplier.contact_email ? (
                    <Typography variant="body2" component="a" href={`mailto:${supplier.contact_email}`} color="primary">
                      {supplier.contact_email}
                    </Typography>
                  ) : '-'}
                </TableCell>
                <TableCell>{supplier.contact_phone || '-'}</TableCell>
                <TableCell>
                  <Chip
                    label={supplier.active ? 'Activo' : 'Inactivo'}
                    size="small"
                    color={supplier.active ? 'success' : 'default'}
                  />
                </TableCell>
                <TableCell align="right">
                  <Tooltip title="Ver productos de este proveedor">
                    <IconButton size="small" onClick={() => navigate(`/products?supplier_id=${supplier.id}`)}>
                      <Visibility fontSize="small" />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="Editar">
                    <IconButton size="small" onClick={() => openEdit(supplier)}>
                      <Edit fontSize="small" />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="Eliminar">
                    <IconButton size="small" color="error" onClick={() => setDeleteTarget(supplier)}>
                      <Delete fontSize="small" />
                    </IconButton>
                  </Tooltip>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Dialog: crear proveedor */}
      <Dialog open={createOpen} onClose={() => setCreateOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Nuevo Proveedor</DialogTitle>
        <DialogContent>
          <Box display="flex" flexDirection="column" gap={2} mt={1}>
            {mutError && <Alert severity="error">{mutError}</Alert>}
            <TextField
              label="Nombre"
              value={newForm.name}
              onChange={(e) => setNewForm((p) => ({ ...p, name: e.target.value }))}
              autoFocus
              required
            />
            <TextField
              label="Codigo (unico)"
              value={newForm.code}
              onChange={(e) => setNewForm((p) => ({ ...p, code: e.target.value }))}
              helperText="Identificador interno del proveedor"
            />
            <TextField
              label="Pais (ISO 3166, ej: ES, FR, CN)"
              value={newForm.country}
              onChange={(e) => setNewForm((p) => ({ ...p, country: e.target.value }))}
              inputProps={{ maxLength: 2 }}
            />
            <TextField
              label="Email de contacto"
              value={newForm.contact_email}
              onChange={(e) => setNewForm((p) => ({ ...p, contact_email: e.target.value }))}
              type="email"
            />
            <TextField
              label="Telefono de contacto"
              value={newForm.contact_phone}
              onChange={(e) => setNewForm((p) => ({ ...p, contact_phone: e.target.value }))}
            />
            <TextField
              label="Notas"
              value={newForm.notes}
              onChange={(e) => setNewForm((p) => ({ ...p, notes: e.target.value }))}
              multiline
              rows={2}
            />
            <FormControlLabel
              control={
                <Switch
                  checked={newForm.active}
                  onChange={(e) => setNewForm((p) => ({ ...p, active: e.target.checked }))}
                />
              }
              label="Proveedor activo"
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateOpen(false)}>Cancelar</Button>
          <Button
            variant="contained"
            onClick={() => {
              setMutError('');
              createMutation.mutate({
                name: newForm.name.trim(),
                code: newForm.code?.trim() || null,
                country: newForm.country?.trim() || null,
                contact_email: newForm.contact_email?.trim() || null,
                contact_phone: newForm.contact_phone?.trim() || null,
                notes: newForm.notes?.trim() || null,
                active: newForm.active,
              });
            }}
            disabled={!newForm.name.trim() || createMutation.isPending}
          >
            Crear
          </Button>
        </DialogActions>
      </Dialog>

      {/* Dialog: editar proveedor */}
      <Dialog open={editTarget !== null} onClose={() => setEditTarget(null)} maxWidth="sm" fullWidth>
        <DialogTitle>Editar Proveedor</DialogTitle>
        <DialogContent>
          <Box display="flex" flexDirection="column" gap={2} mt={1}>
            {mutError && <Alert severity="error">{mutError}</Alert>}
            <TextField
              label="Nombre"
              value={editForm.name ?? ''}
              onChange={(e) => setEditForm((p) => ({ ...p, name: e.target.value }))}
              required
            />
            <TextField
              label="Codigo"
              value={editForm.code ?? ''}
              onChange={(e) => setEditForm((p) => ({ ...p, code: e.target.value }))}
            />
            <TextField
              label="Pais (ISO 3166)"
              value={editForm.country ?? ''}
              onChange={(e) => setEditForm((p) => ({ ...p, country: e.target.value }))}
              inputProps={{ maxLength: 2 }}
            />
            <TextField
              label="Email de contacto"
              value={editForm.contact_email ?? ''}
              onChange={(e) => setEditForm((p) => ({ ...p, contact_email: e.target.value }))}
              type="email"
            />
            <TextField
              label="Telefono de contacto"
              value={editForm.contact_phone ?? ''}
              onChange={(e) => setEditForm((p) => ({ ...p, contact_phone: e.target.value }))}
            />
            <TextField
              label="Notas"
              value={editForm.notes ?? ''}
              onChange={(e) => setEditForm((p) => ({ ...p, notes: e.target.value }))}
              multiline
              rows={2}
            />
            <FormControlLabel
              control={
                <Switch
                  checked={editForm.active ?? true}
                  onChange={(e) => setEditForm((p) => ({ ...p, active: e.target.checked }))}
                />
              }
              label="Proveedor activo"
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
                  name: (editForm.name ?? '').trim(),
                  code: (editForm.code ?? '').trim() || null,
                  country: (editForm.country ?? '').trim() || null,
                  contact_email: (editForm.contact_email ?? '').trim() || null,
                  contact_phone: (editForm.contact_phone ?? '').trim() || null,
                  notes: (editForm.notes ?? '').trim() || null,
                  active: editForm.active ?? true,
                },
              });
            }}
            disabled={!(editForm.name ?? '').trim() || editMutation.isPending}
          >
            Guardar
          </Button>
        </DialogActions>
      </Dialog>

      {/* Dialog: confirmar eliminar */}
      <Dialog open={deleteTarget !== null} onClose={() => setDeleteTarget(null)} maxWidth="xs" fullWidth>
        <DialogTitle>Eliminar Proveedor</DialogTitle>
        <DialogContent>
          <Typography>
            ¿Eliminar el proveedor <strong>{deleteTarget?.name}</strong>? Los vinculos con
            productos existentes tambien seran eliminados.
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

      {/* Dialog: importar */}
      <ImportDialog
        open={importOpen}
        onClose={() => setImportOpen(false)}
        resource="suppliers"
        resourceLabel="Proveedores"
        onSuccess={invalidate}
      />

      {/* Dialog: exportar */}
      <ExportDialog
        open={exportOpen}
        onClose={() => setExportOpen(false)}
        resource="suppliers"
        resourceLabel="Proveedores"
        totalRecords={suppliers.length}
      />
    </Box>
  );
}
