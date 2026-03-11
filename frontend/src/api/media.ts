import client from './client';
import type { MediaAsset } from '../types/media';

export async function uploadMedia(
  file: File,
  sku?: string,
  kind = 'image',
  media_type = 'other',
  sort_order = 0
): Promise<MediaAsset> {
  const form = new FormData();
  form.append('file', file);
  if (sku) form.append('sku', sku);
  form.append('kind', kind);
  form.append('media_type', media_type);
  form.append('sort_order', String(sort_order));
  const response = await client.post<MediaAsset>('/media', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  });
  return response.data;
}

export async function listMedia(sku?: string, kind?: string, media_type?: string): Promise<MediaAsset[]> {
  const params = new URLSearchParams();
  if (sku) params.append('sku', sku);
  if (kind) params.append('kind', kind);
  if (media_type) params.append('media_type', media_type);
  const response = await client.get<MediaAsset[]>(`/media?${params.toString()}`);
  return response.data;
}

export async function updateMedia(
  mediaId: string,
  data: { kind?: string; media_type?: string; sort_order?: number; no_mostrar_en_b2b?: string }
): Promise<MediaAsset> {
  const response = await client.patch<MediaAsset>(`/media/${mediaId}`, data);
  return response.data;
}

export async function linkMedia(mediaId: string, sku: string): Promise<MediaAsset> {
  const response = await client.patch<MediaAsset>(`/media/${mediaId}/link?sku=${encodeURIComponent(sku)}`);
  return response.data;
}

export async function deleteMedia(mediaId: string): Promise<void> {
  await client.delete(`/media/${mediaId}`);
}
