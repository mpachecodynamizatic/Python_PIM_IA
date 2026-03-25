import client from './client';
import type { DatabaseOperationResult } from '../types/database';

export async function purgeAllData(): Promise<DatabaseOperationResult> {
  const { data } = await client.post('/database/purge-all');
  return data;
}

export async function purgeProductsData(): Promise<DatabaseOperationResult> {
  const { data } = await client.post('/database/purge-products');
  return data;
}

export async function seedSampleData(): Promise<DatabaseOperationResult> {
  const { data } = await client.post('/database/seed');
  return data;
}
