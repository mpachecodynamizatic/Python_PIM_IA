export interface SavedView {
  id: string;
  resource: string;
  name: string;
  description: string | null;
  filters: Record<string, unknown>;
  is_default: boolean;
}

export interface SavedViewCreate {
  name: string;
  description?: string | null;
  filters: Record<string, unknown>;
  is_default?: boolean;
}

export interface SavedViewUpdate {
  name?: string;
  description?: string | null;
  filters?: Record<string, unknown>;
  is_default?: boolean;
}
