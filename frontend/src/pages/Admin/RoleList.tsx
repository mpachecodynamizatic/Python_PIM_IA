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
  IconButton,
  Paper,
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
import { listRoles, createRole, updateRole, deleteRole } from '../../api/roles';
import type { Role, RoleCreate, RoleUpdate } from '../../types/role';

export default function RoleList() {
  const queryClient = useQueryClient();
  const [error, setError] = useState('');

  const [createOpen, setCreateOpen] = useState(false);
  const [newRole, setNewRole] = useState<RoleCreate>({
    name: '',
    description: '',
    permissions: {},
  });

  const [editTarget, setEditTarget] = useState<Role | null>(null);
  const [editForm, setEditForm] = useState<RoleUpdate>({});

  const [deleteTarget, setDeleteTarget] = useState<Role | null>(null);

  const { data: roles = [], isLoading } = useQuery({
    queryKey: ['roles'],
    queryFn: () => listRoles(false),
  });

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['roles'] });

  const createMutation = useMutation({
    mutationFn: (data: RoleCreate) => createRole(data),
    onSuccess: () => {
      invalidate();
      setCreateOpen(false);
      setNewRole({ name: '', description: '', permissions: {} });
      setError('');
    },
    onError: (err: any) => {
      const msg = err?.response?.data?.detail;
      setError(msg || 'Error al crear rol');
    },
  });

  const editMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: RoleUpdate }) => updateRole(id, data),
    onSuccess: () => {
      invalidate();
      setEditTarget(null);
      setError('');
    },
    onError: (err: any) => {
      const msg = err?.response?.data?.detail;
      setError(msg || 'Error al actualizar rol');
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => deleteRole(id),
    onSuccess: () => {
      invalidate();
      setDeleteTarget(null);
    },
    onError: (err: any) => {
      const msg = err?.response?.data?.detail;
      setError(msg || 'Error al eliminar rol');
    },
  });

  const openEdit = (role: Role) => {
    setEditTarget(role);
    setEditForm({
      name: role.name,
      description: role.description,
      is_active: role.is_active,
    });
    setError('');
  };

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
        <Box>
          <Typography variant="h4">Gestión de Roles</Typography>
          <Typography variant="body2" color="text.secondary">
            Administra los roles del sistema
          </Typography>
        </Box>
        <Button
          variant="contained"
          startIcon={<Add />}
          onClick={() => {
            setError('');
            setCreateOpen(true);
          }}
        >
          Nuevo Rol
        </Button>
      </Box>

      {error && (
        <Alert severity="error" onClose={() => setError('')} sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell>Nombre</TableCell>
              <TableCell>Descripción</TableCell>
              <TableCell>Estado</TableCell>
              <TableCell />
            </TableRow>
          </TableHead>
          <TableBody>
            {isLoading && (
              <TableRow>
                <TableCell colSpan={4} align="center">
                  Cargando...
                </TableCell>
              </TableRow>
            )}
            {!isLoading && roles.length === 0 && (
              <TableRow>
                <TableCell colSpan={4} align="center">
                  <Typography color="text.secondary">No hay roles</Typography>
                </TableCell>
              </TableRow>
            )}
            {roles.map((role) => (
              <TableRow key={role.id}>
                <TableCell>
                  <Box display="flex" alignItems="center" gap={1}>
                    <Typography fontWeight={500}>{role.name}</Typography>
                    {role.is_system && (
                      <Chip label="Sistema" size="small" color="primary" />
                    )}
                  </Box>
                </TableCell>
                <TableCell>
                  <Typography variant="body2" color="text.secondary">
                    {role.description || '-'}
                  </Typography>
                </TableCell>
                <TableCell>
                  <Chip
                    label={role.is_active ? 'Activo' : 'Inactivo'}
                    size="small"
                    color={role.is_active ? 'success' : 'default'}
                  />
                </TableCell>
                <TableCell align="right">
                  <Tooltip title="Editar">
                    <IconButton size="small" onClick={() => openEdit(role)}>
                      <Edit fontSize="small" />
                    </IconButton>
                  </Tooltip>
                  <Tooltip
                    title={
                      role.is_system
                        ? 'No se puede eliminar un rol del sistema'
                        : 'Eliminar'
                    }
                  >
                    <span>
                      <IconButton
                        size="small"
                        color="error"
                        disabled={role.is_system}
                        onClick={() => setDeleteTarget(role)}
                      >
                        <Delete fontSize="small" />
                      </IconButton>
                    </span>
                  </Tooltip>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Dialog: crear rol */}
      <Dialog open={createOpen} onClose={() => setCreateOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Nuevo Rol</DialogTitle>
        <DialogContent>
          <Box display="flex" flexDirection="column" gap={2} mt={1}>
            {error && <Alert severity="error">{error}</Alert>}
            <TextField
              label="Nombre del rol"
              value={newRole.name}
              onChange={(e) => setNewRole((p) => ({ ...p, name: e.target.value }))}
              autoFocus
              required
              helperText="Nombre único del rol (ej: manager, analyst)"
            />
            <TextField
              label="Descripción"
              value={newRole.description}
              onChange={(e) => setNewRole((p) => ({ ...p, description: e.target.value }))}
              multiline
              rows={2}
              helperText="Descripción del rol y sus responsabilidades"
            />
            <Alert severity="info">
              Los permisos se configurarán después en la sección "Permisos"
            </Alert>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateOpen(false)}>Cancelar</Button>
          <Button
            variant="contained"
            disabled={!newRole.name || createMutation.isPending}
            onClick={() => createMutation.mutate(newRole)}
          >
            {createMutation.isPending ? 'Creando...' : 'Crear'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Dialog: editar rol */}
      <Dialog open={!!editTarget} onClose={() => setEditTarget(null)} maxWidth="sm" fullWidth>
        <DialogTitle>Editar Rol</DialogTitle>
        <DialogContent>
          <Box display="flex" flexDirection="column" gap={2} mt={1}>
            {error && <Alert severity="error">{error}</Alert>}
            <TextField
              label="Nombre del rol"
              value={editForm.name ?? ''}
              onChange={(e) => setEditForm((p) => ({ ...p, name: e.target.value }))}
              disabled={editTarget?.is_system}
              helperText={
                editTarget?.is_system
                  ? 'No se puede cambiar el nombre de roles del sistema'
                  : 'Nombre único del rol'
              }
            />
            <TextField
              label="Descripción"
              value={editForm.description ?? ''}
              onChange={(e) => setEditForm((p) => ({ ...p, description: e.target.value }))}
              multiline
              rows={2}
            />
            {editTarget?.is_system && (
              <Alert severity="info">
                Este es un rol del sistema. Puedes editar sus permisos en la sección
                "Permisos", pero no puedes eliminarlo.
              </Alert>
            )}
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

      {/* Dialog: confirmar eliminación */}
      <Dialog open={!!deleteTarget} onClose={() => setDeleteTarget(null)}>
        <DialogTitle>Eliminar rol</DialogTitle>
        <DialogContent>
          <Typography>
            ¿Seguro que quieres eliminar el rol <strong>{deleteTarget?.name}</strong>?
            Esta acción no se puede deshacer.
          </Typography>
          {error && (
            <Alert severity="error" sx={{ mt: 1 }}>
              {error}
            </Alert>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDeleteTarget(null)}>Cancelar</Button>
          <Button
            variant="contained"
            color="error"
            disabled={deleteMutation.isPending}
            onClick={() => {
              if (deleteTarget) deleteMutation.mutate(deleteTarget.id);
            }}
          >
            {deleteMutation.isPending ? 'Eliminando...' : 'Eliminar'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
