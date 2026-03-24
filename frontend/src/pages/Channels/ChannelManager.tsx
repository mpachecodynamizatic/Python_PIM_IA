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
  TableRow,
  TextField,
  Tooltip,
  Typography,
} from '@mui/material';
import { Add, Delete, Edit, FileUpload, FileDownload } from '@mui/icons-material';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { listChannelCatalog, createChannelCatalog, updateChannelCatalog, deleteChannelCatalog } from '../../api/product_extras';
import type { Channel } from '../../types/product';
import ImportDialog from '../../components/ImportDialog';
import ExportDialog from '../../components/ExportDialog';

type ChannelCreate = Omit<Channel, 'id' | 'created_at' | 'updated_at'>;

const EMPTY_FORM: ChannelCreate = {
  name: '',
  code: '',
  description: null,
  active: true,
};

export default function ChannelManager() {
  const queryClient = useQueryClient();
  const [mutError, setMutError] = useState('');

  const [createOpen, setCreateOpen] = useState(false);
  const [newForm, setNewForm] = useState<ChannelCreate>({ ...EMPTY_FORM });

  const [editTarget, setEditTarget] = useState<Channel | null>(null);
  const [editForm, setEditForm] = useState<Partial<Channel>>({});

  const [deleteTarget, setDeleteTarget] = useState<Channel | null>(null);

  // Import/Export dialogs
  const [importOpen, setImportOpen] = useState(false);
  const [exportOpen, setExportOpen] = useState(false);

  const { data: channels = [], isLoading } = useQuery({
    queryKey: ['channels-catalog'],
    queryFn: () => listChannelCatalog(),
  });

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['channels-catalog'] });
  const onError = (err: unknown) => {
    const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
    setMutError(msg || 'Error inesperado.');
  };

  const createMutation = useMutation({
    mutationFn: (data: ChannelCreate) => createChannelCatalog(data),
    onSuccess: () => {
      invalidate();
      setCreateOpen(false);
      setNewForm({ ...EMPTY_FORM });
      setMutError('');
    },
    onError,
  });

  const editMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: Partial<Channel> }) => updateChannelCatalog(id, data),
    onSuccess: () => { invalidate(); setEditTarget(null); setMutError(''); },
    onError,
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => deleteChannelCatalog(id),
    onSuccess: () => { invalidate(); setDeleteTarget(null); },
    onError,
  });

  const openEdit = (channel: Channel) => {
    setEditTarget(channel);
    setEditForm({ ...channel });
    setMutError('');
  };

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
        <Box>
          <Typography variant="h4">Canales</Typography>
          <Typography variant="body2" color="text.secondary">
            Gestiona el catalogo de canales de venta para vincularlos a productos
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
            Nuevo Canal
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
              <TableCell>Descripcion</TableCell>
              <TableCell>Estado</TableCell>
              <TableCell />
            </TableRow>
          </TableHead>
          <TableBody>
            {isLoading && (
              <TableRow>
                <TableCell colSpan={4} align="center">Cargando...</TableCell>
              </TableRow>
            )}
            {!isLoading && channels.length === 0 && (
              <TableRow>
                <TableCell colSpan={4} align="center">
                  <Typography color="text.secondary">No hay canales. Crea el primero.</Typography>
                </TableCell>
              </TableRow>
            )}
            {channels.map((channel) => (
              <TableRow key={channel.id}>
                <TableCell>
                  <Typography fontWeight={500}>{channel.name}</Typography>
                </TableCell>
                <TableCell>
                  <Typography variant="body2" fontFamily="monospace" color="text.secondary">
                    {channel.code}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Typography variant="body2" color="text.secondary">
                    {channel.description || '-'}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Chip
                    label={channel.active ? 'Activo' : 'Inactivo'}
                    size="small"
                    color={channel.active ? 'success' : 'default'}
                  />
                </TableCell>
                <TableCell align="right">
                  <Tooltip title="Editar">
                    <IconButton size="small" onClick={() => openEdit(channel)}>
                      <Edit fontSize="small" />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="Eliminar">
                    <IconButton size="small" color="error" onClick={() => setDeleteTarget(channel)}>
                      <Delete fontSize="small" />
                    </IconButton>
                  </Tooltip>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Dialog: crear canal */}
      <Dialog open={createOpen} onClose={() => setCreateOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Nuevo Canal</DialogTitle>
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
              helperText="Identificador interno del canal (ej: amazon, b2c, b2b)"
            />
            <TextField
              label="Descripcion"
              value={newForm.description ?? ''}
              onChange={(e) => setNewForm((p) => ({ ...p, description: e.target.value || null }))}
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
              label="Canal activo"
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateOpen(false)}>Cancelar</Button>
          <Button
            variant="contained"
            disabled={!newForm.name.trim() || !newForm.code.trim() || createMutation.isPending}
            onClick={() => createMutation.mutate(newForm)}
          >
            {createMutation.isPending ? 'Creando...' : 'Crear'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Dialog: editar canal */}
      <Dialog open={!!editTarget} onClose={() => setEditTarget(null)} maxWidth="sm" fullWidth>
        <DialogTitle>Editar Canal</DialogTitle>
        <DialogContent>
          <Box display="flex" flexDirection="column" gap={2} mt={1}>
            {mutError && <Alert severity="error">{mutError}</Alert>}
            <TextField
              label="Nombre"
              value={editForm.name ?? ''}
              onChange={(e) => setEditForm((p) => ({ ...p, name: e.target.value }))}
              autoFocus
            />
            <TextField
              label="Descripcion"
              value={editForm.description ?? ''}
              onChange={(e) => setEditForm((p) => ({ ...p, description: e.target.value || null }))}
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
              label="Canal activo"
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setEditTarget(null)}>Cancelar</Button>
          <Button
            variant="contained"
            disabled={editMutation.isPending}
            onClick={() => {
              if (!editTarget) return;
              editMutation.mutate({ id: editTarget.id, data: editForm });
            }}
          >
            {editMutation.isPending ? 'Guardando...' : 'Guardar'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Dialog: confirmar eliminacion */}
      <Dialog open={!!deleteTarget} onClose={() => setDeleteTarget(null)}>
        <DialogTitle>Eliminar canal</DialogTitle>
        <DialogContent>
          <Typography>
            ¿Seguro que quieres eliminar el canal <strong>{deleteTarget?.name}</strong>?
            Esta accion eliminara tambien todos los vinculos de este canal con productos.
          </Typography>
          {mutError && <Alert severity="error" sx={{ mt: 1 }}>{mutError}</Alert>}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteTarget(null)}>Cancelar</Button>
          <Button
            variant="contained"
            color="error"
            disabled={deleteMutation.isPending}
            onClick={() => { if (deleteTarget) deleteMutation.mutate(deleteTarget.id); }}
          >
            {deleteMutation.isPending ? 'Eliminando...' : 'Eliminar'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Dialog: importar */}
      <ImportDialog
        open={importOpen}
        onClose={() => setImportOpen(false)}
        resource="channels"
        resourceLabel="Canales"
        onSuccess={invalidate}
      />

      {/* Dialog: exportar */}
      <ExportDialog
        open={exportOpen}
        onClose={() => setExportOpen(false)}
        resource="channels"
        resourceLabel="Canales"
        totalRecords={channels.length}
      />
    </Box>
  );
}
