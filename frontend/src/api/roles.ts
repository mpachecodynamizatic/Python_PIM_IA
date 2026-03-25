import client from './client';
import type { Role, RoleCreate, RoleUpdate } from '../types/role';

export async function listRoles(includeInactive = false): Promise<Role[]> {
  const { data } = await client.get('/roles', {
    params: { include_inactive: includeInactive },
  });
  return data;
}

export async function getRole(roleId: string): Promise<Role> {
  const { data } = await client.get(`/roles/${roleId}`);
  return data;
}

export async function createRole(roleData: RoleCreate): Promise<Role> {
  const { data } = await client.post('/roles', roleData);
  return data;
}

export async function updateRole(roleId: string, roleData: RoleUpdate): Promise<Role> {
  const { data } = await client.patch(`/roles/${roleId}`, roleData);
  return data;
}

export async function deleteRole(roleId: string): Promise<void> {
  await client.delete(`/roles/${roleId}`);
}
