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

const CONN_TYPE_LABELS: Record<string, string> = {
  ftp: 'FTP',
  ssh: 'SSH / SFTP',
  http_post: 'HTTP POST',
};

const EMPTY_FORM: ChannelCreate = {
  name: '',
  code: '',
  description: null,
  active: true,
  connection_type: null,
  connection_config: {},
};

function ConnectionConfigFields({
  connType,
  config,
  onChange,
}: {
  connType: string | null;
  config: Record<string, unknown>;
  onChange: (updated: Record<string, unknown>) => void;
}) {
  if (!connType) return null;
  const set = (key: string, val: unknown) => onChange({ ...config, [key]: val });

  if (connType === 'ftp' || connType === 'ssh') {
    return (
      <Box display="flex" flexDirection="column" gap={1.5}>
        <Box display="flex" gap={1}>
          <TextField
            label="Host"
            size="small"
            value={(config.host as string) ?? ''}
            onChange={(e) => set('host', e.target.value)}
            sx={{ flex: 3 }}
          />
          <TextField
            label="Puerto"
            size="small"
            type="number"
            value={(config.port as number) ?? (connType === 'ssh' ? 22 : 21)}
            onChange={(e) => set('port', Number(e.target.value))}
            sx={{ flex: 1 }}
          />
        </Box>
        <Box display="flex" gap={1}>
          <TextField
            label="Usuario"
            size="small"
            value={(config.username as string) ?? ''}
            onChange={(e) => set('username', e.target.value)}
            sx={{ flex: 1 }}
          />
          <TextField
            label="Contraseña"
            size="small"
            type="password"
            value={(config.password as string) ?? ''}
            onChange={(e) => set('password', e.target.value)}
            sx={{ flex: 1 }}
          />
        </Box>
        <TextField
          label="Ruta remota"
          size="small"
          value={(config.remote_path as string) ?? '/'}
          onChange={(e) => set('remote_path', e.target.value)}
          placeholder="/ruta/remota/"
          fullWidth
        />
        {connType === 'ftp' && (
          <FormControlLabel
            control={
              <Switch
                checked={(config.passive as boolean) ?? true}
                onChange={(e) => set('passive', e.target.checked)}
                size="small"
              />
            }
            label="Modo pasivo"
          />
        )}
        {connType === 'ssh' && (
          <TextField
            label="Clave privada SSH (opcional)"
            size="small"
            multiline
            rows={2}
            value={(config.private_key as string) ?? ''}
            onChange={(e) => set('private_key', e.target.value || null)}
            placeholder="-----BEGIN RSA PRIVATE KEY-----"
            fullWidth
          />
        )}
      </Box>
    );
  }

  if (connType === 'http_post') {
    const authType = (config.auth_type as string) ?? 'none';
    return (
      <Box display="flex" flexDirection="column" gap={1.5}>
        <TextField
          label="URL del endpoint"
          size="small"
          value={(config.url as string) ?? ''}
          onChange={(e) => set('url', e.target.value)}
          placeholder="https://api.example.com/products"
          fullWidth
        />
        <Box display="flex" gap={1}>
          <TextField
            label="Timeout (s)"
            size="small"
            type="number"
            value={(config.timeout as number) ?? 30}
            onChange={(e) => set('timeout', Number(e.target.value))}
            sx={{ width: 120 }}
          />
          <FormControl size="small" sx={{ flex: 1 }}>
            <InputLabel>Autenticación</InputLabel>
            <Select
              value={authType}
              label="Autenticación"
              onChange={(e) => set('auth_type', e.target.value)}
            >
              <MenuItem value="none">Sin autenticación</MenuItem>
              <MenuItem value="basic">Basic</MenuItem>
              <MenuItem value="bearer">Bearer token</MenuItem>
            </Select>
          </FormControl>
        </Box>
        {authType === 'bearer' && (
          <TextField
            label="Token"
            size="small"
            value={(config.token as string) ?? ''}
            onChange={(e) => set('token', e.target.value)}
            fullWidth
          />
        )}
        {authType === 'basic' && (
          <Box display="flex" gap={1}>
            <TextField
              label="Usuario"
              size="small"
              value={(config.username as string) ?? ''}
              onChange={(e) => set('username', e.target.value)}
              sx={{ flex: 1 }}
            />
            <TextField
              label="Contraseña"
              size="small"
              type="password"
              value={(config.password as string) ?? ''}
              onChange={(e) => set('password', e.target.value)}
              sx={{ flex: 1 }}
            />
          </Box>
        )}
      </Box>
    );
  }

  return null;
}

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
              <TableCell>Conexión</TableCell>
              <TableCell>Estado</TableCell>
              <TableCell />
            </TableRow>
          </TableHead>
          <TableBody>
            {isLoading && (
              <TableRow>
                <TableCell colSpan={5} align="center">Cargando...</TableCell>
              </TableRow>
            )}
            {!isLoading && channels.length === 0 && (
              <TableRow>
                <TableCell colSpan={5} align="center">
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
                  {channel.connection_type ? (
                    <Chip
                      label={CONN_TYPE_LABELS[channel.connection_type] ?? channel.connection_type}
                      size="small"
                      variant="outlined"
                      color="primary"
                    />
                  ) : (
                    <Typography variant="body2" color="text.secondary">-</Typography>
                  )}
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
            <FormControl fullWidth size="small">
              <InputLabel>Tipo de conexión</InputLabel>
              <Select
                value={newForm.connection_type ?? ''}
                label="Tipo de conexión"
                onChange={(e) => setNewForm((p) => ({
                  ...p,
                  connection_type: e.target.value || null,
                  connection_config: {},
                }))}
              >
                <MenuItem value="">Sin conexión</MenuItem>
                <MenuItem value="ftp">FTP</MenuItem>
                <MenuItem value="ssh">SSH / SFTP</MenuItem>
                <MenuItem value="http_post">HTTP POST</MenuItem>
              </Select>
            </FormControl>
            {newForm.connection_type && (
              <ConnectionConfigFields
                connType={newForm.connection_type}
                config={newForm.connection_config ?? {}}
                onChange={(cfg) => setNewForm((p) => ({ ...p, connection_config: cfg }))}
              />
            )}
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
            <FormControl fullWidth size="small">
              <InputLabel>Tipo de conexión</InputLabel>
              <Select
                value={editForm.connection_type ?? ''}
                label="Tipo de conexión"
                onChange={(e) => setEditForm((p) => ({
                  ...p,
                  connection_type: e.target.value || null,
                  connection_config: {},
                }))}
              >
                <MenuItem value="">Sin conexión</MenuItem>
                <MenuItem value="ftp">FTP</MenuItem>
                <MenuItem value="ssh">SSH / SFTP</MenuItem>
                <MenuItem value="http_post">HTTP POST</MenuItem>
              </Select>
            </FormControl>
            {editForm.connection_type && (
              <ConnectionConfigFields
                connType={editForm.connection_type ?? null}
                config={(editForm.connection_config ?? {}) as Record<string, unknown>}
                onChange={(cfg) => setEditForm((p) => ({ ...p, connection_config: cfg }))}
              />
            )}
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
