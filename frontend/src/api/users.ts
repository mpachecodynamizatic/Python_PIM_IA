import client from './client';
import type { User, UserCreate, UserUpdate, PasswordChange, PermissionSystem } from '../types/user';

export async function listUsers(): Promise<User[]> {
  const { data } = await client.get('/users');
  return data;
}

export async function getUser(userId: string): Promise<User> {
  const { data } = await client.get(`/users/${userId}`);
  return data;
}

export async function createUser(userData: UserCreate): Promise<User> {
  const { data } = await client.post('/users', userData);
  return data;
}

export async function updateUser(userId: string, userData: UserUpdate): Promise<User> {
  const { data } = await client.patch(`/users/${userId}`, userData);
  return data;
}

export async function deleteUser(userId: string): Promise<void> {
  await client.delete(`/users/${userId}`);
}

export async function changePassword(userId: string, passwordData: PasswordChange): Promise<void> {
  await client.patch(`/users/${userId}/password`, passwordData);
}

export async function getPermissionResources(): Promise<PermissionSystem> {
  const { data} = await client.get('/users/permissions/resources');
  return data;
}
