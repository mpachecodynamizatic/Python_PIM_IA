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
import { Add, Delete, Edit, VpnKey } from '@mui/icons-material';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { listUsers, createUser, updateUser, deleteUser, changePassword } from '../../api/users';
import { listRoles } from '../../api/roles';
import type { User, UserCreate, UserUpdate, PasswordChange } from '../../types/user';
import { useAuth } from '../../contexts/AuthContext';

export default function UserManager() {
  const { user: currentUser } = useAuth();
  const queryClient = useQueryClient();
  const [error, setError] = useState('');

  const [createOpen, setCreateOpen] = useState(false);
  const [newUser, setNewUser] = useState<UserCreate>({
    email: '',
    password: '',
    full_name: '',
    role: 'viewer',
  });

  const [editTarget, setEditTarget] = useState<User | null>(null);
  const [editForm, setEditForm] = useState<UserUpdate>({});

  const [deleteTarget, setDeleteTarget] = useState<User | null>(null);

  const [passwordTarget, setPasswordTarget] = useState<User | null>(null);
  const [passwordForm, setPasswordForm] = useState({
    current_password: '',
    new_password: '',
    confirm_password: '',
  });

  const { data: users = [], isLoading } = useQuery({
    queryKey: ['users'],
    queryFn: listUsers,
  });

  const { data: roles = [] } = useQuery({
    queryKey: ['roles'],
    queryFn: () => listRoles(false),
  });

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['users'] });

  const createMutation = useMutation({
    mutationFn: (data: UserCreate) => createUser(data),
    onSuccess: () => {
      invalidate();
      setCreateOpen(false);
      setNewUser({ email: '', password: '', full_name: '', role: 'viewer' });
      setError('');
    },
    onError: (err: unknown) => {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(msg || 'Error al crear usuario');
    },
  });

  const editMutation = useMutation({
    mutationFn: ({ id, data }: { id: string; data: UserUpdate }) => updateUser(id, data),
    onSuccess: () => {
      invalidate();
      setEditTarget(null);
      setError('');
    },
    onError: (err: unknown) => {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(msg || 'Error al actualizar usuario');
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => deleteUser(id),
    onSuccess: () => {
      invalidate();
      setDeleteTarget(null);
    },
    onError: (err: unknown) => {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(msg || 'Error al eliminar usuario');
    },
  });

  const passwordMutation = useMutation({
    mutationFn: (data: PasswordChange) => {
      if (!passwordTarget) throw new Error('No target user');
      return changePassword(passwordTarget.id, data);
    },
    onSuccess: () => {
      setPasswordTarget(null);
      setPasswordForm({ current_password: '', new_password: '', confirm_password: '' });
      setError('');
    },
    onError: (err: unknown) => {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(msg || 'Error al cambiar contraseña');
    },
  });

  const openEdit = (user: User) => {
    setEditTarget(user);
    setEditForm({
      full_name: user.full_name,
      role: user.role,
      is_active: user.is_active,
    });
    setError('');
  };

  const openPasswordChange = (user: User) => {
    setPasswordTarget(user);
    setPasswordForm({ current_password: '', new_password: '', confirm_password: '' });
    setError('');
  };

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
        <Box>
          <Typography variant="h4">Gestión de Usuarios</Typography>
          <Typography variant="body2" color="text.secondary">
            Administra los usuarios del sistema
          </Typography>
        </Box>
        <Button variant="contained" startIcon={<Add />} onClick={() => { setError(''); setCreateOpen(true); }}>
          Nuevo Usuario
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
              <TableCell>Email</TableCell>
              <TableCell>Rol</TableCell>
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
            {!isLoading && users.length === 0 && (
              <TableRow>
                <TableCell colSpan={5} align="center">
                  <Typography color="text.secondary">No hay usuarios</Typography>
                </TableCell>
              </TableRow>
            )}
            {users.map((user) => (
              <TableRow key={user.id}>
                <TableCell>
                  <Typography fontWeight={500}>{user.full_name}</Typography>
                </TableCell>
                <TableCell>
                  <Typography variant="body2" color="text.secondary">{user.email}</Typography>
                </TableCell>
                <TableCell>
                  <Chip
                    label={user.role}
                    size="small"
                    color="primary"
                  />
                </TableCell>
                <TableCell>
                  <Chip
                    label={user.is_active ? 'Activo' : 'Inactivo'}
                    size="small"
                    color={user.is_active ? 'success' : 'default'}
                  />
                </TableCell>
                <TableCell align="right">
                  <Tooltip title="Editar">
                    <IconButton size="small" onClick={() => openEdit(user)}>
                      <Edit fontSize="small" />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="Cambiar Contraseña">
                    <IconButton size="small" onClick={() => openPasswordChange(user)}>
                      <VpnKey fontSize="small" />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="Eliminar">
                    <IconButton size="small" color="error" onClick={() => setDeleteTarget(user)}>
                      <Delete fontSize="small" />
                    </IconButton>
                  </Tooltip>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Dialog: crear usuario */}
      <Dialog open={createOpen} onClose={() => setCreateOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Nuevo Usuario</DialogTitle>
        <DialogContent>
          <Box display="flex" flexDirection="column" gap={2} mt={1}>
            {error && <Alert severity="error">{error}</Alert>}
            <TextField
              label="Nombre completo"
              value={newUser.full_name}
              onChange={(e) => setNewUser((p) => ({ ...p, full_name: e.target.value }))}
              autoFocus
              required
            />
            <TextField
              label="Email"
              type="email"
              value={newUser.email}
              onChange={(e) => setNewUser((p) => ({ ...p, email: e.target.value }))}
              required
            />
            <TextField
              label="Contraseña"
              type="password"
              value={newUser.password}
              onChange={(e) => setNewUser((p) => ({ ...p, password: e.target.value }))}
              required
            />
            <FormControl fullWidth>
              <InputLabel>Rol</InputLabel>
              <Select
                value={newUser.role}
                label="Rol"
                onChange={(e) => setNewUser((p) => ({ ...p, role: e.target.value }))}
              >
                {roles.filter(r => r.is_active).map((role) => (
                  <MenuItem key={role.id} value={role.name}>
                    {role.name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateOpen(false)}>Cancelar</Button>
          <Button
            variant="contained"
            disabled={!newUser.email || !newUser.password || !newUser.full_name || createMutation.isPending}
            onClick={() => createMutation.mutate(newUser)}
          >
            {createMutation.isPending ? 'Creando...' : 'Crear'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Dialog: editar usuario */}
      <Dialog open={!!editTarget} onClose={() => setEditTarget(null)} maxWidth="sm" fullWidth>
        <DialogTitle>Editar Usuario</DialogTitle>
        <DialogContent>
          <Box display="flex" flexDirection="column" gap={2} mt={1}>
            {error && <Alert severity="error">{error}</Alert>}
            <TextField
              label="Nombre completo"
              value={editForm.full_name ?? ''}
              onChange={(e) => setEditForm((p) => ({ ...p, full_name: e.target.value }))}
              autoFocus
            />
            <FormControl fullWidth>
              <InputLabel>Rol</InputLabel>
              <Select
                value={editForm.role ?? ''}
                label="Rol"
                onChange={(e) => setEditForm((p) => ({ ...p, role: e.target.value }))}
              >
                {roles.filter(r => r.is_active).map((role) => (
                  <MenuItem key={role.id} value={role.name}>
                    {role.name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>
            <FormControlLabel
              control={
                <Switch
                  checked={editForm.is_active ?? true}
                  onChange={(e) => setEditForm((p) => ({ ...p, is_active: e.target.checked }))}
                />
              }
              label="Usuario activo"
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
        <DialogTitle>Eliminar usuario</DialogTitle>
        <DialogContent>
          <Typography>
            ¿Seguro que quieres eliminar el usuario <strong>{deleteTarget?.full_name}</strong>?
            Esta acción no se puede deshacer.
          </Typography>
          {error && <Alert severity="error" sx={{ mt: 1 }}>{error}</Alert>}
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

      {/* Dialog: cambiar contraseña */}
      <Dialog open={!!passwordTarget} onClose={() => setPasswordTarget(null)} maxWidth="sm" fullWidth>
        <DialogTitle>Cambiar Contraseña</DialogTitle>
        <DialogContent>
          <Box display="flex" flexDirection="column" gap={2} mt={1}>
            {error && <Alert severity="error">{error}</Alert>}
            {passwordTarget && currentUser && passwordTarget.id === currentUser.id && (
              <TextField
                label="Contraseña actual"
                type="password"
                value={passwordForm.current_password}
                onChange={(e) => setPasswordForm((p) => ({ ...p, current_password: e.target.value }))}
                autoFocus
                required
                helperText="Requerida cuando cambias tu propia contraseña"
              />
            )}
            <TextField
              label="Nueva contraseña"
              type="password"
              value={passwordForm.new_password}
              onChange={(e) => setPasswordForm((p) => ({ ...p, new_password: e.target.value }))}
              autoFocus={!passwordTarget || !currentUser || passwordTarget.id !== currentUser.id}
              required
            />
            <TextField
              label="Confirmar nueva contraseña"
              type="password"
              value={passwordForm.confirm_password}
              onChange={(e) => setPasswordForm((p) => ({ ...p, confirm_password: e.target.value }))}
              required
              error={passwordForm.confirm_password !== '' && passwordForm.new_password !== passwordForm.confirm_password}
              helperText={
                passwordForm.confirm_password !== '' && passwordForm.new_password !== passwordForm.confirm_password
                  ? 'Las contraseñas no coinciden'
                  : ''
              }
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setPasswordTarget(null)}>Cancelar</Button>
          <Button
            variant="contained"
            disabled={
              !passwordForm.new_password ||
              passwordForm.new_password !== passwordForm.confirm_password ||
              (passwordTarget && currentUser && passwordTarget.id === currentUser.id && !passwordForm.current_password) ||
              passwordMutation.isPending
            }
            onClick={() => {
              if (!passwordTarget) return;
              const data: PasswordChange = {
                new_password: passwordForm.new_password,
              };
              if (passwordTarget.id === currentUser?.id && passwordForm.current_password) {
                data.current_password = passwordForm.current_password;
              }
              passwordMutation.mutate(data);
            }}
          >
            {passwordMutation.isPending ? 'Cambiando...' : 'Cambiar Contraseña'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
