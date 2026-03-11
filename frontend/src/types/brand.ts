export interface Brand {
  id: string;
  name: string;
  slug: string;
  description: string | null;
  website: string | null;
  logo_url: string | null;
  active: boolean;
  created_at: string;
  updated_at: string;
}

export interface BrandCreate {
  name: string;
  slug: string;
  description?: string | null;
  website?: string | null;
  logo_url?: string | null;
  active?: boolean;
}

export interface BrandUpdate {
  name?: string;
  slug?: string;
  description?: string | null;
  website?: string | null;
  logo_url?: string | null;
  active?: boolean;
}
