import client from './client';
import type { DashboardStats } from '../types/dashboard';

export async function getDashboardStats(): Promise<DashboardStats> {
  const r = await client.get<DashboardStats>('/dashboard/stats');
  return r.data;
}
