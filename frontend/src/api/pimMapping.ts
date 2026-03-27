import client from './client';

export interface PimFieldMapping {
  source_field: string;
  target_field: string;
  transform?: string;
  required: boolean;
  default_value?: string;
  fk_config?: Record<string, any>;
}

export interface PimResourceMapping {
  id: string;
  resource: string;
  is_active: boolean;
  mappings: PimFieldMapping[];
  defaults: Record<string, any>;
  transform_config: Record<string, any>;
  where_clause?: string;
  created_by: string;
  notes?: string;
  created_at: string;
  updated_at: string;
}

export interface MySQLTableInfo {
  table_name: string;
  engine: string | null;
  row_count: number;
  table_comment: string;
}

export interface MySQLConnectionStatus {
  success: boolean;
  version?: string;
  database?: string;
  host?: string;
  error?: string;
}

export interface MySQLColumnInfo {
  field_path: string;
  sample_value?: string;
  data_type: string;
  is_nullable: boolean;
}

export interface ResourceFieldSchema {
  field_path: string;
  label: string;
  data_type: string;
  is_required: boolean;
  is_readonly: boolean;
  fk_constraint?: Record<string, any>;
  choices?: string[];
}

// ── Recursos internos ──────────────────────────────────────────────────────────

export const listAvailableResources = async (): Promise<string[]> => {
  const { data } = await client.get('/pim-mappings/resources');
  return data;
};

export const getInternalFields = async (
  resource: string,
): Promise<ResourceFieldSchema[]> => {
  const { data } = await client.get(`/pim-mappings/resources/${resource}/internal-fields`);
  return data;
};

// ── MySQL ──────────────────────────────────────────────────────────────────────

export const getMysqlStatus = async (): Promise<MySQLConnectionStatus> => {
  const { data } = await client.get('/pim-mappings/mysql/status');
  return data;
};

export const listMysqlTables = async (): Promise<MySQLTableInfo[]> => {
  const { data } = await client.get('/pim-mappings/mysql/tables');
  return data;
};

export const getMysqlTableColumns = async (tableName: string): Promise<MySQLColumnInfo[]> => {
  const { data } = await client.get(`/pim-mappings/mysql/tables/${tableName}/columns`);
  return data;
};

export const proposeMysqlMapping = async (
  table: string,
  resource: string,
): Promise<PimFieldMapping[]> => {
  const { data } = await client.post('/pim-mappings/mysql/propose', { table, resource });
  return data;
};

// ── CRUD configuraciones ──────────────────────────────────────────────────────

export const getMappingByResource = async (
  resource: string,
): Promise<PimResourceMapping | null> => {
  const { data } = await client.get(`/pim-mappings/${resource}`);
  return data;
};

export const createMapping = async (payload: {
  resource: string;
  is_active: boolean;
  mappings: PimFieldMapping[];
  defaults: Record<string, any>;
  transform_config: Record<string, any>;
  where_clause?: string;
  notes?: string;
}): Promise<PimResourceMapping> => {
  const { data } = await client.post('/pim-mappings', payload);
  return data;
};

export const updateMapping = async (
  resource: string,
  payload: {
    is_active?: boolean;
    mappings?: PimFieldMapping[];
    defaults?: Record<string, any>;
    transform_config?: Record<string, any>;
    where_clause?: string;
    notes?: string;
  },
): Promise<PimResourceMapping> => {
  const { data } = await client.patch(`/pim-mappings/${resource}`, payload);
  return data;
};

export const deleteMapping = async (resource: string): Promise<void> => {
  await client.delete(`/pim-mappings/${resource}`);
};

export interface ImportStats {
  created: number;
  updated: number;
  skipped: number;
  errors: number;
}

export interface ImportResponse {
  message: string;
  stats: ImportStats;
}

export const importResource = async (resource: string): Promise<ImportResponse> => {
  const { data } = await client.post(`/pim-mappings/${resource}/import`);
  return data;
};

