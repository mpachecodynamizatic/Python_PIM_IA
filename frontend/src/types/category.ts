export interface Category {
  id: string;
  name: string;
  slug: string;
  description: string | null;
  parent_id: string | null;
  attribute_schema: Record<string, unknown>;
  sort_order: number;
  created_at: string;
  updated_at: string;
}

export interface CategoryTree extends Category {
  children: CategoryTree[];
}

export interface CategoryCreate {
  name: string;
  slug: string;
  description?: string;
  parent_id?: string;
  attribute_schema?: Record<string, unknown>;
  sort_order?: number;
}

export interface CategoryUpdate {
  name?: string;
  slug?: string;
  description?: string | null;
  parent_id?: string | null;
  sort_order?: number;
}
