# 🔐 Implementación del Sistema de Administración

## ✅ Completado

### Backend
1. **Endpoint DELETE de usuarios** - `backend/app/api/v1/users.py`
   - Previene auto-eliminación
   - Solo accesible por admins

2. **Sistema de permisos** - `backend/app/core/permissions.py`
   - 11 recursos: products, categories, media, brands, channels, suppliers, sync, quality, i18n, users, settings
   - 3 niveles: none, read, write
   - Permisos por rol predefinidos

3. **Endpoint de permisos** - `/users/permissions/resources`
   - Retorna recursos disponibles
   - Etiquetas en español
   - Permisos por rol

4. **Servicio de usuarios** - `backend/app/services/user_service.py`
   - Función `delete_user()` añadida

### Frontend
1. **Tipos TypeScript** - `frontend/src/types/user.ts`
   - User, UserCreate, UserUpdate
   - PermissionResource, PermissionSystem

2. **API Client** - `frontend/src/api/users.ts`
   - CRUD completo de usuarios
   - Get permission resources

3. **Página de Usuarios** - `frontend/src/pages/Admin/UserManager.tsx`
   - Tabla con todos los usuarios
   - Crear, editar, eliminar usuarios
   - Chips de rol y estado

## 📋 Pasos Restantes

### 1. Crear Página de Permisos

Crear `frontend/src/pages/Admin/RoleManager.tsx`:

```tsx
import { useState } from 'react';
import {
  Box, Typography, Paper, Table, TableBody, TableCell,
  TableHead, TableRow, Select, MenuItem, Alert
} from '@mui/material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { listUsers, getPermissionResources, updateUser } from '../../api/users';

export default function RoleManager() {
  const { data: users = [] } = useQuery({
    queryKey: ['users'],
    queryFn: listUsers,
  });

  const { data: permSystem } = useQuery({
    queryKey: ['permission-resources'],
    queryFn: getPermissionResources,
  });

  const queryClient = useQueryClient();
  const updateMutation = useMutation({
    mutationFn: ({ id, scopes }: { id: string; scopes: string[] }) =>
      updateUser(id, { scopes }),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['users'] }),
  });

  const getUserPermission = (user: any, resource: string): string => {
    const scope = user.scopes.find((s: string) => s.startsWith(`${resource}:`));
    if (scope) return scope.split(':')[1];
    // Fallback to role default
    return permSystem?.roles[user.role]?.[resource] || 'none';
  };

  const setUserPermission = (user: any, resource: string, level: string) => {
    const newScopes = user.scopes.filter((s: string) => !s.startsWith(`${resource}:`));
    if (level !== 'none') {
      newScopes.push(`${resource}:${level}`);
    }
    updateMutation.mutate({ id: user.id, scopes: newScopes });
  };

  return (
    <Box>
      <Typography variant="h4" mb={2}>Gestión de Permisos</Typography>
      <Paper sx={{ overflowX: 'auto' }}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Usuario</TableCell>
              {permSystem?.resources.map((res) => (
                <TableCell key={res.id}>{res.label}</TableCell>
              ))}
            </TableRow>
          </TableHead>
          <TableBody>
            {users.map((user) => (
              <TableRow key={user.id}>
                <TableCell>{user.full_name}</TableCell>
                {permSystem?.resources.map((res) => (
                  <TableCell key={res.id}>
                    <Select
                      size="small"
                      value={getUserPermission(user, res.id)}
                      onChange={(e) => setUserPermission(user, res.id, e.target.value)}
                      disabled={user.role === 'admin'}
                    >
                      <MenuItem value="none">Sin acceso</MenuItem>
                      <MenuItem value="read">Lectura</MenuItem>
                      <MenuItem value="write">Edición</MenuItem>
                    </Select>
                  </TableCell>
                ))}
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </Paper>
      {permSystem && (
        <Alert severity="info" sx={{ mt: 2 }}>
          Los administradores tienen acceso completo a todo el sistema.
          Los permisos personalizados sobrescriben los permisos por defecto del rol.
        </Alert>
      )}
    </Box>
  );
}
```

### 2. Actualizar Sidebar

En `frontend/src/components/Layout.tsx`, añadir en el menú:

```tsx
// Dentro del Drawer, después de las otras opciones:
{user?.role === 'admin' && (
  <>
    <Divider sx={{ my: 1 }} />
    <Typography variant="overline" sx={{ px: 2, py: 1, color: 'text.secondary' }}>
      Administración
    </Typography>
    <ListItemButton onClick={() => navigate('/admin/users')}>
      <ListItemIcon><PeopleIcon /></ListItemIcon>
      <ListItemText primary="Usuarios" />
    </ListItemButton>
    <ListItemButton onClick={() => navigate('/admin/roles')}>
      <ListItemIcon><SecurityIcon /></ListItemIcon>
      <ListItemText primary="Permisos" />
    </ListItemButton>
  </>
)}
```

Imports necesarios:
```tsx
import PeopleIcon from '@mui/icons-material/People';
import SecurityIcon from '@mui/icons-material/Security';
```

### 3. Añadir Rutas

En `frontend/src/App.tsx`, añadir:

```tsx
import UserManager from './pages/Admin/UserManager';
import RoleManager from './pages/Admin/RoleManager';

// Dentro de <Routes>:
<Route path="/admin/users" element={<ProtectedRoute><UserManager /></ProtectedRoute>} />
<Route path="/admin/roles" element={<ProtectedRoute><RoleManager /></ProtectedRoute>} />
```

## 🎯 Funcionalidades Implementadas

### Gestión de Usuarios
- ✅ Listar todos los usuarios
- ✅ Crear nuevo usuario (email, password, nombre, rol)
- ✅ Editar usuario (nombre, rol, estado activo/inactivo)
- ✅ Eliminar usuario (con prevención de auto-eliminación)
- ✅ Chips visuales para rol y estado

### Sistema de Permisos
- ✅ 11 recursos del sistema
- ✅ 3 niveles de acceso: Sin acceso, Lectura, Edición
- ✅ 3 roles predefinidos: Admin, Editor, Visor
- ✅ Permisos personalizables por usuario
- ✅ Admins tienen acceso total automático

### Recursos Gestionados
1. **Productos** - products
2. **Categorías** - categories
3. **Multimedia** - media
4. **Marcas** - brands
5. **Canales** - channels
6. **Proveedores** - suppliers
7. **Sincronización** - sync
8. **Calidad** - quality
9. **Traducción** - i18n
10. **Usuarios** - users
11. **Configuración** - settings

## 🔒 Seguridad

- Solo usuarios con rol "admin" pueden acceder a la sección de Administración
- No se puede eliminar el propio usuario (prevención de lockout)
- Los permisos se validan en el backend
- Las contraseñas se hashean con bcrypt
