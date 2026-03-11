import client from './client';

export interface AttributeFamily {
  id: string;
  code: string;
  name: string;
  description: string | null;
  category_id: string | null;
}

export interface AttributeDefinition {
  id: string;
  code: string;
  label: string;
  type: 'string' | 'number' | 'boolean' | 'enum';
  required: boolean;
  options_json: string | null;
}

export interface AttributeFamilyCreate {
  code: string;
  name: string;
  description?: string;
  category_id?: string;
}

export interface AttributeDefinitionCreate {
  code: string;
  label: string;
  type: string;
  required: boolean;
  options_json?: string;
}

export async function listFamilies(): Promise<AttributeFamily[]> {
  const response = await client.get<AttributeFamily[]>('/attributes/families');
  return response.data;
}

export async function createFamily(data: AttributeFamilyCreate): Promise<AttributeFamily> {
  const response = await client.post<AttributeFamily>('/attributes/families', data);
  return response.data;
}

export async function listDefinitions(familyId: string): Promise<AttributeDefinition[]> {
  const response = await client.get<AttributeDefinition[]>(`/attributes/families/${familyId}/definitions`);
  return response.data;
}

export async function addDefinition(familyId: string, data: AttributeDefinitionCreate): Promise<AttributeDefinition> {
  const response = await client.post<AttributeDefinition>(`/attributes/families/${familyId}/definitions`, data);
  return response.data;
}

export async function updateFamily(familyId: string, data: Partial<AttributeFamilyCreate>): Promise<AttributeFamily> {
  const response = await client.patch<AttributeFamily>(`/attributes/families/${familyId}`, data);
  return response.data;
}

export async function deleteFamily(familyId: string): Promise<void> {
  await client.delete(`/attributes/families/${familyId}`);
}

export async function updateDefinition(
  familyId: string, defId: string, data: Partial<AttributeDefinitionCreate>,
): Promise<AttributeDefinition> {
  const response = await client.patch<AttributeDefinition>(`/attributes/families/${familyId}/definitions/${defId}`, data);
  return response.data;
}

export async function deleteDefinition(familyId: string, defId: string): Promise<void> {
  await client.delete(`/attributes/families/${familyId}/definitions/${defId}`);
}
