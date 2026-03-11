import client from './client';
import type { Brand, BrandCreate, BrandUpdate } from '../types/brand';

export async function listBrands(activeOnly = false): Promise<Brand[]> {
  const response = await client.get<Brand[]>('/brands', { params: { active_only: activeOnly } });
  return response.data;
}

export async function getBrand(id: string): Promise<Brand> {
  const response = await client.get<Brand>(`/brands/${id}`);
  return response.data;
}

export async function createBrand(data: BrandCreate): Promise<Brand> {
  const response = await client.post<Brand>('/brands', data);
  return response.data;
}

export async function updateBrand(id: string, data: BrandUpdate): Promise<Brand> {
  const response = await client.patch<Brand>(`/brands/${id}`, data);
  return response.data;
}

export async function deleteBrand(id: string): Promise<void> {
  await client.delete(`/brands/${id}`);
}
