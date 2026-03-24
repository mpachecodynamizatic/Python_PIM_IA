import client from './client';
import type {
  ExportFieldMeta,
  ExportRequest,
  ImportValidationResult,
  ImportResult,
  ResourceMeta,
} from '../types/export';

export async function listExportResources(): Promise<ResourceMeta[]> {
  const r = await client.get<ResourceMeta[]>('/export/resources');
  return r.data;
}

export async function getExportFields(resource: string): Promise<{
  fields: ExportFieldMeta[];
  user_selection: string[] | null;
}> {
  const r = await client.get<{
    fields: ExportFieldMeta[];
    user_selection: string[] | null;
  }>(`/export/${resource}/fields`);
  return r.data;
}

/** Trigger an xlsx export and download it in the browser. */
export async function downloadExport(resource: string, body: ExportRequest): Promise<void> {
  const r = await client.post(`/export/${resource}`, body, { responseType: 'blob' });
  const url = URL.createObjectURL(new Blob([r.data]));
  const ts = new Date().toISOString().replace(/[:.]/g, '-').slice(0, 19);
  const a = document.createElement('a');
  a.href = url;
  a.download = `${resource}_${ts}.xlsx`;
  a.click();
  URL.revokeObjectURL(url);
}

/** Download an empty xlsx template. */
export async function downloadTemplate(
  resource: string,
  fields?: string[],
): Promise<void> {
  const params = fields ? `?${fields.map((f) => `fields=${encodeURIComponent(f)}`).join('&')}` : '';
  const r = await client.get(`/export/${resource}/template${params}`, { responseType: 'blob' });
  const url = URL.createObjectURL(new Blob([r.data]));
  const a = document.createElement('a');
  a.href = url;
  a.download = `${resource}_template.xlsx`;
  a.click();
  URL.revokeObjectURL(url);
}

/** Dry-run validation — does not save anything. */
export async function validateImport(
  resource: string,
  file: File,
): Promise<ImportValidationResult> {
  const form = new FormData();
  form.append('file', file);
  const r = await client.post<ImportValidationResult>(
    `/export/${resource}/import/validate`,
    form,
    { headers: { 'Content-Type': 'multipart/form-data' } },
  );
  return r.data;
}

/** Validate + apply import. Returns 422 if there are blocking errors. */
export async function applyImport(resource: string, file: File): Promise<ImportResult> {
  const form = new FormData();
  form.append('file', file);
  const r = await client.post<ImportResult>(
    `/export/${resource}/import`,
    form,
    { headers: { 'Content-Type': 'multipart/form-data' } },
  );
  return r.data;
}
