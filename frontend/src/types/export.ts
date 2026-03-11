// Types mirroring the backend export/import schemas

export interface ExportFieldMeta {
  key: string;
  label: string;
  type: string;
  required: boolean;
  readonly: boolean;
  default_include: boolean;
  choices: string[] | null;
}

export interface ResourceMeta {
  resource: string;
  label: string;
}

export interface ExportRequest {
  fields: string[] | null;
  filters: Record<string, unknown> | null;
}

// Import validation

export interface ImportIssue {
  row: number;
  field_key: string;
  code: string;
  message: string;
}

export interface ImportPreviewRow {
  row: number;
  mode: 'create' | 'update';
  data: Record<string, unknown>;
}

export interface ImportValidationResult {
  total: number;
  valid: number;
  errors: ImportIssue[];
  warnings: ImportIssue[];
  preview: ImportPreviewRow[];
  has_blocking_errors: boolean;
}

export interface ImportResult {
  created: number;
  updated: number;
  skipped: number;
}
