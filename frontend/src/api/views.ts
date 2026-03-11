import client from './client';
import type { SavedView, SavedViewCreate, SavedViewUpdate } from '../types/savedView';

export async function listProductViews(): Promise<SavedView[]> {
  const response = await client.get<SavedView[]>('/views/products');
  return response.data;
}

export async function createProductView(data: SavedViewCreate): Promise<SavedView> {
  const response = await client.post<SavedView>('/views/products', data);
  return response.data;
}

export async function getProductView(viewId: string): Promise<SavedView> {
  const response = await client.get<SavedView>(`/views/products/${viewId}`);
  return response.data;
}

export async function updateProductView(viewId: string, data: SavedViewUpdate): Promise<SavedView> {
  const response = await client.patch<SavedView>(`/views/products/${viewId}`, data);
  return response.data;
}

export async function deleteProductView(viewId: string): Promise<void> {
  await client.delete(`/views/products/${viewId}`);
}
