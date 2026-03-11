export interface Product {
  sku: string;
  brand: string;
  status: 'draft' | 'in_review' | 'approved' | 'ready' | 'retired';
  category_id: string;
  family_id: string | null;
  seo: Record<string, unknown>;
  attributes: Record<string, unknown>;
  created_at: string;
  updated_at: string;
  translations?: ProductI18n[];
}

export interface ProductListItem {
  sku: string;
  brand: string;
  status: string;
  category_id: string;
  updated_at: string;
}

export interface ProductI18n {
  locale: string;
  title: string;
  description_rich?: Record<string, unknown> | null;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface ProductCreate {
  sku: string;
  brand: string;
  category_id: string;
  status?: string;
  seo?: Record<string, unknown>;
  attributes?: Record<string, unknown>;
}

export interface ProductUpdate {
  brand?: string;
  category_id?: string;
  family_id?: string | null;
  seo?: Record<string, unknown>;
  attributes?: Record<string, unknown>;
}

export interface ProductVersion {
  id: string;
  sku: string;
  actor: string;
  action: string;
  created_at: string;
  snapshot?: Record<string, unknown> | null;
}
