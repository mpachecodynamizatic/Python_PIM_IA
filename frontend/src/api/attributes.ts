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
