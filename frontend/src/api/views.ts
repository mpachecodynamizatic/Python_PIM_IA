import client from './client';
import type { SavedView, SavedViewCreate, SavedViewExport, SavedViewUpdate } from '../types/savedView';

// ---------------------------------------------------------------------------
// Generic resource views (products, media, quality, i18n, …)
// ---------------------------------------------------------------------------

export async function listViews(resource: string): Promise<SavedView[]> {
  const response = await client.get<SavedView[]>(`/views/${resource}`);
  return response.data;
}

export async function createView(resource: string, data: SavedViewCreate): Promise<SavedView> {
  const response = await client.post<SavedView>(`/views/${resource}`, data);
  return response.data;
}

export async function getView(resource: string, viewId: string): Promise<SavedView> {
  const response = await client.get<SavedView>(`/views/${resource}/${viewId}`);
  return response.data;
}

export async function updateView(resource: string, viewId: string, data: SavedViewUpdate): Promise<SavedView> {
  const response = await client.patch<SavedView>(`/views/${resource}/${viewId}`, data);
  return response.data;
}

export async function deleteView(resource: string, viewId: string): Promise<void> {
  await client.delete(`/views/${resource}/${viewId}`);
}

export async function exportView(resource: string, viewId: string): Promise<SavedViewExport> {
  const response = await client.get<SavedViewExport>(`/views/${resource}/${viewId}/export`);
  return response.data;
}

export async function importView(resource: string, data: SavedViewExport): Promise<SavedView> {
  const response = await client.post<SavedView>(`/views/${resource}/import`, data);
  return response.data;
}

// ---------------------------------------------------------------------------
// Product-specific aliases (backward compatibility)
// ---------------------------------------------------------------------------

export const listProductViews = () => listViews('products');
export const createProductView = (data: SavedViewCreate) => createView('products', data);
export const getProductView = (viewId: string) => getView('products', viewId);
export const updateProductView = (viewId: string, data: SavedViewUpdate) => updateView('products', viewId, data);
export const deleteProductView = (viewId: string) => deleteView('products', viewId);
export const exportProductView = (viewId: string) => exportView('products', viewId);
export const importProductView = (data: SavedViewExport) => importView('products', data);

