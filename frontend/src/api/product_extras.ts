import client from './client';
import type {
  ProductLogistics,
  ProductCompliance,
  Channel,
  ProductChannel,
  ProductSupplier,
  Supplier,
  ExternalTaxonomy,
  ProductTaxonomy,
} from '../types/product';

// Logistics
export async function getLogistics(sku: string): Promise<ProductLogistics> {
  const r = await client.get<ProductLogistics>(`/products/${sku}/logistics`);
  return r.data;
}

export async function updateLogistics(sku: string, data: Partial<ProductLogistics>): Promise<ProductLogistics> {
  const r = await client.put<ProductLogistics>(`/products/${sku}/logistics`, data);
  return r.data;
}

// Compliance
export async function getCompliance(sku: string): Promise<ProductCompliance> {
  const r = await client.get<ProductCompliance>(`/products/${sku}/compliance`);
  return r.data;
}

export async function updateCompliance(sku: string, data: Partial<ProductCompliance>): Promise<ProductCompliance> {
  const r = await client.put<ProductCompliance>(`/products/${sku}/compliance`, data);
  return r.data;
}

// Channel catalog
export async function listChannelCatalog(activeOnly = false): Promise<Channel[]> {
  const r = await client.get<Channel[]>(`/channels?active_only=${activeOnly}`);
  return r.data;
}

export async function createChannelCatalog(data: {
  name: string;
  code: string;
  description?: string | null;
  active?: boolean;
  connection_type?: string | null;
  connection_config?: Record<string, unknown>;
}): Promise<Channel> {
  const r = await client.post<Channel>('/channels', data);
  return r.data;
}

export async function updateChannelCatalog(id: string, data: {
  name?: string;
  description?: string | null;
  active?: boolean;
  connection_type?: string | null;
  connection_config?: Record<string, unknown>;
}): Promise<Channel> {
  const r = await client.patch<Channel>(`/channels/${id}`, data);
  return r.data;
}

export async function deleteChannelCatalog(id: string): Promise<void> {
  await client.delete(`/channels/${id}`);
}

// Channels
export async function listChannels(sku: string): Promise<ProductChannel[]> {
  const r = await client.get<ProductChannel[]>(`/products/${sku}/channels`);
  return r.data;
}

export async function upsertChannel(sku: string, data: Partial<ProductChannel> & { channel_id: string }): Promise<ProductChannel> {
  const r = await client.put<ProductChannel>(`/products/${sku}/channels`, data);
  return r.data;
}

export async function deleteChannel(sku: string, channelId: string): Promise<void> {
  await client.delete(`/products/${sku}/channels/${channelId}`);
}

// Suppliers catalog
export async function listSuppliers(activeOnly = false): Promise<Supplier[]> {
  const r = await client.get<Supplier[]>(`/suppliers?active_only=${activeOnly}`);
  return r.data;
}

export async function createSupplier(data: Omit<Supplier, 'id' | 'created_at' | 'updated_at'>): Promise<Supplier> {
  const r = await client.post<Supplier>('/suppliers', data);
  return r.data;
}

export async function updateSupplier(id: string, data: Partial<Supplier>): Promise<Supplier> {
  const r = await client.patch<Supplier>(`/suppliers/${id}`, data);
  return r.data;
}

export async function deleteSupplier(id: string): Promise<void> {
  await client.delete(`/suppliers/${id}`);
}

// Product <-> Supplier links
export async function listProductSuppliers(sku: string): Promise<ProductSupplier[]> {
  const r = await client.get<ProductSupplier[]>(`/products/${sku}/suppliers`);
  return r.data;
}

export async function addProductSupplier(sku: string, data: { supplier_id: string; is_primary?: boolean; supplier_sku?: string; moq?: number; lead_time_days?: number; country_of_origin?: string; purchase_price?: number; currency?: string; notes?: string }): Promise<ProductSupplier> {
  const r = await client.post<ProductSupplier>(`/products/${sku}/suppliers`, data);
  return r.data;
}

export async function updateProductSupplier(sku: string, linkId: string, data: Partial<ProductSupplier>): Promise<ProductSupplier> {
  const r = await client.patch<ProductSupplier>(`/products/${sku}/suppliers/${linkId}`, data);
  return r.data;
}

export async function removeProductSupplier(sku: string, linkId: string): Promise<void> {
  await client.delete(`/products/${sku}/suppliers/${linkId}`);
}

// External taxonomies catalog
export async function listExternalTaxonomies(): Promise<ExternalTaxonomy[]> {
  const r = await client.get<ExternalTaxonomy[]>('/external-taxonomies');
  return r.data;
}

export async function createExternalTaxonomy(data: { name: string; provider: string; description?: string }): Promise<ExternalTaxonomy> {
  const r = await client.post<ExternalTaxonomy>('/external-taxonomies', data);
  return r.data;
}

export async function deleteExternalTaxonomy(id: string): Promise<void> {
  await client.delete(`/external-taxonomies/${id}`);
}

// Product <-> External taxonomy mappings
export async function listProductTaxonomies(sku: string): Promise<ProductTaxonomy[]> {
  const r = await client.get<ProductTaxonomy[]>(`/products/${sku}/external-taxonomies`);
  return r.data;
}

export async function upsertProductTaxonomy(sku: string, data: { taxonomy_id: string; node_code?: string; node_name?: string; node_path?: string }): Promise<ProductTaxonomy> {
  const r = await client.put<ProductTaxonomy>(`/products/${sku}/external-taxonomies`, data);
  return r.data;
}

export async function removeProductTaxonomy(sku: string, mappingId: string): Promise<void> {
  await client.delete(`/products/${sku}/external-taxonomies/${mappingId}`);
}
