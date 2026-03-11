import client from './client';
import type {
  PaginatedResponse,
  Product,
  ProductCreate,
  ProductListItem,
  ProductUpdate,
  ProductVersion,
} from '../types/product';

export interface ProductFilters {
  page?: number;
  size?: number;
  status?: string;
  brand?: string;
  category_id?: string;
  q?: string;
  created_from?: string;
  created_to?: string;
  updated_from?: string;
  updated_to?: string;
  has_media?: boolean;
  has_i18n?: boolean;
}

export async function listProducts(
  filters: ProductFilters = {}
): Promise<PaginatedResponse<ProductListItem>> {
  const params = new URLSearchParams();
  Object.entries(filters).forEach(([key, value]) => {
    if (value !== undefined && value !== '') {
      params.append(key, String(value));
    }
  });
  const response = await client.get<PaginatedResponse<ProductListItem>>(
    `/products?${params.toString()}`
  );
  return response.data;
}

export async function getProduct(sku: string): Promise<Product> {
  const response = await client.get<Product>(`/products/${sku}`);
  return response.data;
}

export async function createProduct(data: ProductCreate): Promise<Product> {
  const response = await client.post<Product>('/products', data);
  return response.data;
}

export async function updateProduct(
  sku: string,
  data: ProductUpdate
): Promise<Product> {
  const response = await client.patch<Product>(`/products/${sku}`, data);
  return response.data;
}

export async function transitionProduct(
  sku: string,
  newStatus: string,
  reason?: string
): Promise<Product> {
  const response = await client.post<Product>(`/products/${sku}/transitions`, {
    new_status: newStatus,
    reason,
  });
  return response.data;
}

export async function submitForReview(
  sku: string,
  reason?: string,
): Promise<Product> {
  const response = await client.post<Product>(`/products/${sku}/workflow/submit`, { reason });
  return response.data;
}

export async function approveProduct(
  sku: string,
  reason?: string,
): Promise<Product> {
  const response = await client.post<Product>(`/products/${sku}/workflow/approve`, { reason });
  return response.data;
}

export async function rejectProduct(
  sku: string,
  reason?: string,
): Promise<Product> {
  const response = await client.post<Product>(`/products/${sku}/workflow/reject`, { reason });
  return response.data;
}

export async function getProductVersions(
  sku: string,
  actionFilter?: string,
): Promise<ProductVersion[]> {
  const params = actionFilter ? { action: actionFilter } : undefined;
  const response = await client.get<ProductVersion[]>(`/products/${sku}/versions`, { params });
  return response.data;
}

export async function restoreProductVersion(
  sku: string,
  versionId: string
): Promise<Product> {
  const response = await client.post<Product>(`/products/${sku}/versions/${versionId}/restore`);
  return response.data;
}

export interface RetentionPolicy {
  max_versions?: number;
  max_age_days?: number;
}

export interface RetentionResult {
  deleted: number;
  remaining: number;
}

export async function applyRetentionPolicy(
  sku: string,
  policy: RetentionPolicy,
): Promise<RetentionResult> {
  const response = await client.post<RetentionResult>(`/products/${sku}/versions/retention`, policy);
  return response.data;
}

export interface VersionComment {
  id: string;
  sku: string;
  user_id: string;
  author_name: string;
  body: string;
  version_id: string | null;
  parent_id: string | null;
  reply_count: number;
  tags: string[] | null;
  created_at: string;
  updated_at: string | null;
}

export async function getVersionComments(
  sku: string,
  versionId: string,
): Promise<VersionComment[]> {
  const response = await client.get<VersionComment[]>(`/products/${sku}/versions/${versionId}/comments`);
  return response.data;
}

export async function createVersionComment(
  sku: string,
  versionId: string,
  body: string,
): Promise<VersionComment> {
  const response = await client.post<VersionComment>(`/products/${sku}/versions/${versionId}/comments`, { body });
  return response.data;
}

// Product-level comments
export interface CommentFilters {
  author_id?: string;
  tag?: string;
  since?: string;
  until?: string;
}

export async function getProductComments(sku: string, filters?: CommentFilters): Promise<VersionComment[]> {
  const response = await client.get<VersionComment[]>(`/products/${sku}/comments`, { params: filters });
  return response.data;
}

export async function createProductComment(sku: string, body: string, parentId?: string, tags?: string[]): Promise<VersionComment> {
  const response = await client.post<VersionComment>(`/products/${sku}/comments`, { body, parent_id: parentId, tags });
  return response.data;
}

export async function updateProductComment(
  sku: string,
  commentId: string,
  data: { body?: string; tags?: string[] },
): Promise<VersionComment> {
  const response = await client.patch<VersionComment>(`/products/${sku}/comments/${commentId}`, data);
  return response.data;
}

export async function getCommentReplies(sku: string, commentId: string): Promise<VersionComment[]> {
  const response = await client.get<VersionComment[]>(`/products/${sku}/comments/${commentId}/replies`);
  return response.data;
}

export async function deleteProductComment(sku: string, commentId: string): Promise<void> {
  await client.delete(`/products/${sku}/comments/${commentId}`);
}
