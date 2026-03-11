import client from './client';
import type { SyncJob, SyncJobCreate, SyncJobList } from '../types/sync';

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
