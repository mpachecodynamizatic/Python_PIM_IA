import client from './client';
import type {
  QualityReport,
  QualityRule,
  QualityRuleCreate,
  QualityRuleSet,
  QualityRuleSetCreate,
  QualityRuleSetUpdate,
  QualityRuleUpdate,
  QualityScore,
  SimulationResult,
} from '../types/quality';

export async function getProductQuality(sku: string): Promise<QualityScore> {
  const response = await client.get<QualityScore>(`/quality/products/${sku}`);
  return response.data;
}

export async function getQualityReport(page = 1, size = 20): Promise<QualityReport> {
  const response = await client.get<QualityReport>(`/quality/report?page=${page}&size=${size}`);
  return response.data;
}

// ── Quality Rules Admin ──

export async function listRuleSets(): Promise<QualityRuleSet[]> {
  const response = await client.get<QualityRuleSet[]>('/quality-rules/sets');
  return response.data;
}

export async function createRuleSet(data: QualityRuleSetCreate): Promise<QualityRuleSet> {
  const response = await client.post<QualityRuleSet>('/quality-rules/sets', data);
  return response.data;
}

export async function deleteRuleSet(id: string): Promise<void> {
  await client.delete(`/quality-rules/sets/${id}`);
}

export async function updateRuleSet(id: string, data: QualityRuleSetUpdate): Promise<QualityRuleSet> {
  const response = await client.patch<QualityRuleSet>(`/quality-rules/sets/${id}`, data);
  return response.data;
}

export async function activateRuleSet(id: string): Promise<void> {
  await client.post(`/quality-rules/sets/${id}/activate`);
}

export async function deactivateAllRuleSets(): Promise<void> {
  await client.post('/quality-rules/sets/deactivate-all');
}

export async function addRule(ruleSetId: string, data: QualityRuleCreate): Promise<QualityRule> {
  const response = await client.post<QualityRule>(`/quality-rules/sets/${ruleSetId}/rules`, data);
  return response.data;
}

export async function deleteRule(ruleId: string): Promise<void> {
  await client.delete(`/quality-rules/rules/${ruleId}`);
}

export async function updateRule(ruleId: string, data: QualityRuleUpdate): Promise<QualityRule> {
  const response = await client.patch<QualityRule>(`/quality-rules/rules/${ruleId}`, data);
  return response.data;
}

export async function simulateRuleSet(ruleSetId: string, page = 1, size = 20): Promise<SimulationResult> {
  const response = await client.get<SimulationResult>(
    `/quality/simulate/${ruleSetId}?page=${page}&size=${size}`,
  );
  return response.data;
}
