export interface QualityDimensions {
  brand: number;
  category: number;
  seo: number;
  attributes: number;
  media: number;
  i18n: number;
}

export interface QualityScore {
  sku: string;
  status: string;
  overall: number;
  dimensions: QualityDimensions;
  rule_set?: { id: string; name: string } | null;
  violations?: string[];
}

export interface QualityReport {
  items: QualityScore[];
  total: number;
  page: number;
  size: number;
  pages: number;
  active_rule_set?: { id: string; name: string } | null;
}

export interface QualityRule {
  id: string;
  dimension: string;
  weight: number;
  min_score: number;
  required_status: string | null;
}

export interface QualityRuleCreate {
  dimension: string;
  weight: number;
  min_score: number;
  required_status?: string | null;
}

export interface QualityRuleSet {
  id: string;
  name: string;
  description: string | null;
  active: boolean;
  rules: QualityRule[];
}

export interface QualityRuleSetCreate {
  name: string;
  description?: string | null;
  active?: boolean;
  rules?: QualityRuleCreate[];
}

export interface SimulationItem {
  sku: string;
  status: string;
  current_overall: number;
  simulated_overall: number;
  diff: number;
  simulated_violations: string[];
  dimensions: QualityDimensions;
}

export interface SimulationResult {
  rule_set: { id: string; name: string };
  compared_to: { id: string; name: string } | null;
  items: SimulationItem[];
  total: number;
  page: number;
  size: number;
  pages: number;
}
