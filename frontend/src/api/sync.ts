import client from './client';
import type {
  SyncJob,
  SyncJobCreate,
  SyncJobList,
  SyncScheduleUpdate,
  ProductSyncHistoryList,
  ProductSyncStatus,
} from '../types/sync';

export async function getChannels(): Promise<string[]> {
  const response = await client.get<string[]>('/sync/channels');
  return response.data;
}

export async function createSyncJob(data: SyncJobCreate): Promise<SyncJob> {
  const response = await client.post<SyncJob>('/sync/jobs', data);
  return response.data;
}

export async function listSyncJobs(
  page = 1,
  size = 20,
  channel?: string,
  status?: string,
): Promise<SyncJobList> {
  const params = new URLSearchParams({ page: String(page), size: String(size) });
  if (channel) params.set('channel', channel);
  if (status) params.set('status', status);
  const response = await client.get<SyncJobList>(`/sync/jobs?${params}`);
  return response.data;
}

export async function getSyncJob(jobId: string): Promise<SyncJob> {
  const response = await client.get<SyncJob>(`/sync/jobs/${jobId}`);
  return response.data;
}

export async function retrySyncJob(jobId: string): Promise<SyncJob> {
  const response = await client.post<SyncJob>(`/sync/jobs/${jobId}/retry`);
  return response.data;
}

export async function updateJobSchedule(jobId: string, data: SyncScheduleUpdate): Promise<SyncJob> {
  const response = await client.put<SyncJob>(`/sync/jobs/${jobId}/schedule`, data);
  return response.data;
}

export async function getProductSyncHistory(
  sku: string,
  page = 1,
  size = 20,
  channel?: string,
): Promise<ProductSyncHistoryList> {
  const params = new URLSearchParams({ page: String(page), size: String(size) });
  if (channel) params.set('channel', channel);
  const response = await client.get<ProductSyncHistoryList>(`/sync/history/product/${encodeURIComponent(sku)}?${params}`);
  return response.data;
}

export async function getProductSyncStatus(sku: string): Promise<ProductSyncStatus[]> {
  const response = await client.get<ProductSyncStatus[]>(`/sync/history/product/${encodeURIComponent(sku)}/status`);
  return response.data;
}

export async function getChannelSyncHistory(
  channel: string,
  page = 1,
  size = 20,
): Promise<ProductSyncHistoryList> {
  const params = new URLSearchParams({ page: String(page), size: String(size) });
  const response = await client.get<ProductSyncHistoryList>(`/sync/history/channel/${encodeURIComponent(channel)}?${params}`);
  return response.data;
}
