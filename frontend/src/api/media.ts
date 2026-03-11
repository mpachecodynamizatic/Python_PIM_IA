import client from './client';
import type { MediaAsset } from '../types/media';

export async function uploadMedia(
  file: File,
  sku?: string,
  kind = 'image'
): Promise<MediaAsset> {
  const form = new FormData();
  form.append('file', file);
  if (sku) form.append('sku', sku);
  form.append('kind', kind);
  const response = await client.post<MediaAsset>('/media', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
}

export async function listMedia(sku?: string, kind?: string): Promise<MediaAsset[]> {
  const params = new URLSearchParams();
  if (sku) params.append('sku', sku);
  if (kind) params.append('kind', kind);
  const response = await client.get<MediaAsset[]>(`/media?${params.toString()}`);
  return response.data;
}

export async function linkMedia(mediaId: string, sku: string): Promise<MediaAsset> {
  const response = await client.patch<MediaAsset>(`/media/${mediaId}/link?sku=${encodeURIComponent(sku)}`);
  return response.data;
}

export async function deleteMedia(mediaId: string): Promise<void> {
  await client.delete(`/media/${mediaId}`);
}
