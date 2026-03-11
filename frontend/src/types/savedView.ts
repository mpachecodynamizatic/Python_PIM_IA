export interface SavedView {
  id: string;
  user_id: string;
  resource: string;
  name: string;
  description: string | null;
  filters: Record<string, unknown>;
  is_default: boolean;
  is_public: boolean;
}

export interface SavedViewCreate {
  name: string;
  description?: string | null;
  filters: Record<string, unknown>;
  is_default?: boolean;
  is_public?: boolean;
}

export interface SavedViewUpdate {
  name?: string;
  description?: string | null;
  filters?: Record<string, unknown>;
  is_default?: boolean;
  is_public?: boolean;
}

export interface SavedViewExport {
  resource: string;
  name: string;
  description: string | null;
  filters: Record<string, unknown>;
  is_default: boolean;
  is_public: boolean;
}

