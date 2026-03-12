export interface SyncJobFilters {
  status?: string;
  category_id?: string;
  brand?: string;
  endpoint_url?: string;
}

export interface SyncJob {
  id: string;
  channel_id: string;
  channel_code: string;
  channel_name: string;
  connection_type: string | null;
  connection_config: Record<string, unknown>;
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
  retry_count: number;
  max_retries: number;
  next_retry_at: string | null;
  scheduled: boolean;
  cron_expression: string | null;
  next_run_at: string | null;
  created_at: string | null;
  updated_at: string | null;
}

export interface SyncJobCreate {
  channel_id: string;
  connection_type?: string | null;
  connection_config?: Record<string, unknown> | null;
  filters?: SyncJobFilters;
  max_retries?: number;
  cron_expression?: string | null;
}

export interface SyncJobList {
  items: SyncJob[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface SyncScheduleUpdate {
  cron_expression: string | null;
  enabled: boolean;
}

export interface ProductSyncHistory {
  id: string;
  sku: string;
  channel: string;
  job_id: string | null;
  status: string;
  detail: Record<string, unknown>;
  error_message: string | null;
  synced_at: string | null;
}

export interface ProductSyncHistoryList {
  items: ProductSyncHistory[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface ProductSyncStatus {
  sku: string;
  channel: string;
  status: string;
  synced_at: string | null;
  job_id: string | null;
}