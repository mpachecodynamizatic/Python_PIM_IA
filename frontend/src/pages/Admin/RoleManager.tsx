import { useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Chip,
  FormControl,
  MenuItem,
  Paper,
  Select,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from '@mui/material';
import { Save } from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { getPermissionResources } from '../../api/users';
import { listRoles, updateRole } from '../../api/roles';
import type { PermissionSystem } from '../../types/user';
import type { Role } from '../../types/role';

const RESOURCE_LABELS: Record<string, string> = {
  products: 'Productos',
  categories: 'Categorías',
  media: 'Multimedia',
  brands: 'Marcas',
  channels: 'Canales',
  suppliers: 'Proveedores',
  sync: 'Sincronización',
  quality: 'Calidad',
  i18n: 'Traducción',
  users: 'Usuarios',
  settings: 'Configuración',
};

export default function RoleManager() {
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');
  const [modifiedRoles, setModifiedRoles] = useState<Record<string, Record<string, string>>>({});
  const queryClient = useQueryClient();

  const { data: roles = [], isLoading: rolesLoading } = useQuery({
    queryKey: ['roles'],
    queryFn: () => listRoles(true),
  });

  const { data: permSystem, isLoading: permLoading } = useQuery<PermissionSystem>({
    queryKey: ['permission-resources'],
    queryFn: getPermissionResources,
  });

  const updateMutation = useMutation({
    mutationFn: async (rolesToUpdate: Array<{ roleId: string; permissions: Record<string, string> }>) => {
      // Update all modified roles in parallel with better error handling
      const updatePromises = rolesToUpdate.map(({ roleId, permissions }) =>
        updateRole(roleId, { permissions }).catch((err) => {
          // Capture which role failed
          console.error(`Failed to update role ${roleId}:`, err);
          throw err;
        })
      );

      // Use allSettled to try all updates even if some fail
      const results = await Promise.allSettled(updatePromises);

      // Check if any failed
      const failures = results.filter((r) => r.status === 'rejected');
      if (failures.length > 0) {
        throw new Error(`Failed to update ${failures.length} role(s)`);
      }

      return results;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['roles'] });
      setModifiedRoles({});
      setError('');
      setSuccess('Permisos actualizados correctamente');
      setTimeout(() => setSuccess(''), 3000);
    },
    onError: (err: unknown) => {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(msg || 'Error al actualizar permisos');
    },
  });

  const setRolePermission = (roleId: string, resource: string, level: string) => {
    setModifiedRoles((prev) => ({
      ...prev,
      [roleId]: {
        ...(prev[roleId] || {}),
        [resource]: level,
      },
    }));
    setError('');
    setSuccess('');
  };

  const getCurrentPermission = (role: Role, resource: string): string => {
    // Check if there's a pending modification
    if (modifiedRoles[role.id]?.[resource] !== undefined) {
      return modifiedRoles[role.id][resource];
    }
    // Otherwise return the current saved value
    return role.permissions[resource] || 'none';
  };

  const handleSaveChanges = () => {
    // Build array of roles to update
    const rolesToUpdate = Object.entries(modifiedRoles).map(([roleId, permissions]) => {
      const role = roles.find((r) => r.id === roleId);
      if (!role) return null;

      // Merge current permissions with modifications
      const updatedPermissions = { ...role.permissions, ...permissions };
      return { roleId, permissions: updatedPermissions };
    }).filter((r) => r !== null) as Array<{ roleId: string; permissions: Record<string, string> }>;

    if (rolesToUpdate.length > 0) {
      updateMutation.mutate(rolesToUpdate);
    }
  };

  const handleCancelChanges = () => {
    setModifiedRoles({});
    setError('');
    setSuccess('');
  };

  const hasChanges = Object.keys(modifiedRoles).length > 0;
  const isLoading = rolesLoading || permLoading;

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
        <Box>
          <Typography variant="h4">Matriz de Permisos</Typography>
          <Typography variant="body2" color="text.secondary">
            Configura los permisos de acceso por rol y recurso
          </Typography>
        </Box>
        {hasChanges && (
          <Box display="flex" gap={1}>
            <Button
              variant="outlined"
              onClick={handleCancelChanges}
              disabled={updateMutation.isPending}
            >
              Cancelar
            </Button>
            <Button
              variant="contained"
              startIcon={<Save />}
              onClick={handleSaveChanges}
              disabled={updateMutation.isPending}
            >
              {updateMutation.isPending ? 'Guardando...' : 'Guardar Cambios'}
            </Button>
          </Box>
        )}
      </Box>

      {error && (
        <Alert severity="error" onClose={() => setError('')} sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {success && (
        <Alert severity="success" onClose={() => setSuccess('')} sx={{ mb: 2 }}>
          {success}
        </Alert>
      )}

      {isLoading ? (
        <Typography>Cargando...</Typography>
      ) : (
        <>
          <Paper sx={{ overflowX: 'auto' }}>
            <TableContainer>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell sx={{ minWidth: 150, position: 'sticky', left: 0, bgcolor: 'background.paper', zIndex: 2 }}>
                      <strong>Recurso</strong>
                    </TableCell>
                    {roles.map((role) => (
                      <TableCell key={role.id} sx={{ minWidth: 140 }}>
                        <Box display="flex" alignItems="center" gap={1}>
                          <strong>{role.name}</strong>
                          {role.is_system && (
                            <Chip label="Sistema" size="small" color="primary" />
                          )}
                          {modifiedRoles[role.id] && (
                            <Chip label="Modificado" size="small" color="warning" />
                          )}
                        </Box>
                      </TableCell>
                    ))}
                  </TableRow>
                </TableHead>
                <TableBody>
                  {permSystem?.resources.map((resource) => (
                    <TableRow key={resource.id} hover>
                      <TableCell sx={{ position: 'sticky', left: 0, bgcolor: 'background.paper', zIndex: 1 }}>
                        <Typography variant="body2" fontWeight={500}>
                          {RESOURCE_LABELS[resource.id] ?? resource.label}
                        </Typography>
                      </TableCell>
                      {roles.map((role) => {
                        const currentLevel = getCurrentPermission(role, resource.id);

                        return (
                          <TableCell key={role.id}>
                            <FormControl size="small" fullWidth>
                              <Select
                                value={currentLevel}
                                onChange={(e) => setRolePermission(role.id, resource.id, e.target.value)}
                                disabled={updateMutation.isPending}
                                sx={{ minWidth: 120 }}
                              >
                                <MenuItem value="none">
                                  <Chip label="Sin acceso" size="small" color="default" />
                                </MenuItem>
                                <MenuItem value="read">
                                  <Chip label="Lectura" size="small" color="info" />
                                </MenuItem>
                                <MenuItem value="write">
                                  <Chip label="Edición" size="small" color="success" />
                                </MenuItem>
                              </Select>
                            </FormControl>
                          </TableCell>
                        );
                      })}
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </Paper>

          <Alert severity="info" sx={{ mt: 2 }}>
            <strong>Nota:</strong> Todos los roles pueden ser editados, incluyendo los roles del sistema.
            Los cambios se aplican cuando haces clic en "Guardar Cambios" y afectan a todos los usuarios con ese rol.
          </Alert>
        </>
      )}
    </Box>
  );
}
