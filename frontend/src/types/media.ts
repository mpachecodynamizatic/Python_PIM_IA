export interface MediaAsset {
  id: string;
  sku: string | null;
  kind: string;
  url: string;
  filename: string | null;
  no_mostrar_en_b2b: string;
  metadata_extra: Record<string, unknown>;
  created_at: string;
}
