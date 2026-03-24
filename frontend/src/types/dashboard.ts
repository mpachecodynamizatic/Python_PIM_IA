export interface DashboardStats {
  products: ProductStats;
  quality: QualityStats;
  sync: SyncStats;
  activity: ActivityStats;
  workflow: WorkflowStats;
  coverage: CoverageStats;
}

export interface ProductStats {
  total: number;
  by_status: {
    draft: number;
    in_review: number;
    approved: number;
    ready: number;
    retired: number;
  };
  without_media: number;
  without_i18n: number;
  without_channels: number;
}

export interface QualityStats {
  avg_score: number;
  below_threshold: number;
  critical_errors: number;
}

export interface SyncStats {
  total_channels: number;
  channels_ok: number;
  channels_error: number;
  last_failures: SyncFailure[];
  pending_sync: number;
}

export interface SyncFailure {
  channel: string;
  error: string;
  time: string | null;
}

export interface ActivityStats {
  unresolved_comments: number;
  pending_mentions: number;
  edits_today: number;
  recent_activity: ActivityItem[];
}

export interface ActivityItem {
  id: string;
  resource: string;
  resource_id: string;
  action: string;
  actor: string;
  created_at: string | null;
}

export interface WorkflowStats {
  avg_time_to_publish: number;
  in_review: number;
  approved_pending: number;
}

export interface CoverageStats {
  total_categories: number;
  empty_categories: number;
  brands_low_products: BrandCount[];
  top_categories: CategoryCount[];
  growth_this_month: number;
}

export interface BrandCount {
  name: string;
  count: number;
}

export interface CategoryCount {
  name: string;
  count: number;
}
