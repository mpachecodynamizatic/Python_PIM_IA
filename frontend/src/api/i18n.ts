import client from './client';

export interface ProductI18n {
  locale: string;
  title: string;
  description_rich: Record<string, unknown> | null;
}

export interface MissingTranslation {
  sku: string;
  brand: string;
  status: string;
}

export interface MissingReport {
  locale: string;
  items: MissingTranslation[];
  total: number;
  page: number;
  size: number;
  pages: number;
}

export interface I18nStats {
  by_locale: {
    [locale: string]: {
      total: number;
      translated: number;
      pending: number;
      percentage: number;
    };
  };
  total_products: number;
  locales: string[];
}

export async function listLocales(): Promise<string[]> {
  const response = await client.get<string[]>('/i18n/locales');
  return response.data;
}

export async function getMissingTranslations(
  locale: string,
  page = 1,
  size = 20
): Promise<MissingReport> {
  const response = await client.get<MissingReport>(
    `/i18n/missing?locale=${encodeURIComponent(locale)}&page=${page}&size=${size}`
  );
  return response.data;
}

export async function getProductTranslations(sku: string): Promise<ProductI18n[]> {
  const response = await client.get<ProductI18n[]>(`/products/${sku}/i18n`);
  return response.data;
}

export async function upsertTranslation(
  sku: string,
  locale: string,
  data: { title: string; description_rich?: Record<string, unknown> | null }
): Promise<ProductI18n> {
  const response = await client.post<ProductI18n>(`/products/${sku}/i18n/${locale}`, {
    locale,
    ...data,
  });
  return response.data;
}

export async function deleteTranslation(sku: string, locale: string): Promise<void> {
  await client.delete(`/products/${sku}/i18n/${locale}`);
}

export async function getI18nStats(): Promise<I18nStats> {
  const response = await client.get<I18nStats>('/i18n/stats');
  return response.data;
}
