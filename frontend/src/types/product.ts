export interface Product {
  sku: string;
  brand: string;
  status: 'draft' | 'in_review' | 'approved' | 'ready' | 'retired';
  category_id: string;
  family_id: string | null;
  // Identity
  ean_gtin?: string | null;
  dun14?: string | null;
  supplier_ref?: string | null;
  // Naming / descriptions
  name?: string | null;
  short_description?: string | null;
  long_description?: string | null;
  key_benefits?: string[];
  sales_pitch?: string | null;
  marketing_claims?: string[];
  marketplace_text?: Record<string, string>;
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
  name?: string | null;
  ean_gtin?: string | null;
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
  ean_gtin?: string | null;
  dun14?: string | null;
  supplier_ref?: string | null;
  name?: string | null;
  short_description?: string | null;
  long_description?: string | null;
  key_benefits?: string[];
  sales_pitch?: string | null;
  marketing_claims?: string[];
  marketplace_text?: Record<string, string>;
  seo?: Record<string, unknown>;
  attributes?: Record<string, unknown>;
}

export interface ProductUpdate {
  brand?: string;
  category_id?: string;
  family_id?: string | null;
  ean_gtin?: string | null;
  dun14?: string | null;
  supplier_ref?: string | null;
  name?: string | null;
  short_description?: string | null;
  long_description?: string | null;
  key_benefits?: string[];
  sales_pitch?: string | null;
  marketing_claims?: string[];
  marketplace_text?: Record<string, string>;
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

// Logistics
export interface ProductLogistics {
  id: string;
  sku: string;
  base_unit?: string | null;
  box_units?: number | null;
  pallet_boxes?: number | null;
  pallet_units?: number | null;
  height_mm?: number | null;
  width_mm?: number | null;
  depth_mm?: number | null;
  weight_gross_g?: number | null;
  weight_net_g?: number | null;
  stackable: boolean;
  packaging_type?: string | null;
  transport_conditions?: string | null;
  adr: boolean;
  adr_class?: string | null;
  adr_un_number?: string | null;
  adr_details?: string | null;
  created_at: string;
  updated_at: string;
}

// Compliance
export interface ProductCompliance {
  id: string;
  sku: string;
  certifications: string[];
  technical_sheet_url?: string | null;
  safety_sheet_url?: string | null;
  legal_warnings?: string | null;
  min_age?: number | null;
  has_lot_traceability: boolean;
  has_expiry_date: boolean;
  country_of_origin?: string | null;
  hs_code?: string | null;
  created_at: string;
  updated_at: string;
}

// Channel catalog
export interface Channel {
  id: string;
  name: string;
  code: string;
  description: string | null;
  active: boolean;
  connection_type: string | null;
  connection_config: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

// Channels
export interface ProductChannel {
  id: string;
  sku: string;
  channel_id: string;
  channel?: Channel;
  name?: string | null;
  description?: string | null;
  active: boolean;
  country_restrictions: string[];
  marketplace_fields: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

// Suppliers
export interface Supplier {
  id: string;
  name: string;
  code?: string | null;
  country?: string | null;
  contact_email?: string | null;
  contact_phone?: string | null;
  notes?: string | null;
  active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ProductSupplier {
  id: string;
  sku: string;
  supplier_id: string;
  is_primary: boolean;
  supplier_sku?: string | null;
  moq?: number | null;
  lead_time_days?: number | null;
  country_of_origin?: string | null;
  purchase_price?: number | null;
  currency?: string | null;
  notes?: string | null;
  supplier?: Supplier | null;
  created_at: string;
  updated_at: string;
}

// External taxonomies
export interface ExternalTaxonomy {
  id: string;
  name: string;
  provider: string;
  description?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ProductTaxonomy {
  id: string;
  sku: string;
  taxonomy_id: string;
  node_code?: string | null;
  node_name?: string | null;
  node_path?: string | null;
  taxonomy?: ExternalTaxonomy | null;
  created_at: string;
  updated_at: string;
}

