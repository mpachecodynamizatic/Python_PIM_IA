export interface SyncJobFilters {
  status?: string;
  category_id?: string;
  brand?: string;
  endpoint_url?: string;
}

export interface SyncJob {
  id: string;
  channel: string;
  status: string;
  filters: SyncJobFilters;
  started_at: string | null;
  finished_at: string | null;
  metrics: {
    total_products: number;
    exported: number;
    skipped: number;
    errors?: string[];
  };
  error_message: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface SyncJobCreate {
  channel: string;
  filters?: SyncJobFilters;
}

export interface SyncJobList {
  items: SyncJob[];
  total: number;
  page: number;
  size: number;
  pages: number;
}
