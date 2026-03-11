export const MEDIA_TYPES = [
  'image_main',
  'image_secondary',
  'video',
  'pdf_manual',
  'pdf_safety',
  'render',
  'icon',
  'other',
] as const;

export type MediaTypeValue = typeof MEDIA_TYPES[number];

export const MEDIA_TYPE_LABELS: Record<MediaTypeValue, string> = {
  image_main: 'Imagen principal',
  image_secondary: 'Imagen secundaria',
  video: 'Video',
  pdf_manual: 'Manual PDF',
  pdf_safety: 'Ficha seguridad PDF',
  render: 'Render 3D',
  icon: 'Icono',
  other: 'Otro',
};

export interface MediaAsset {
  id: string;
  sku: string | null;
  kind: string;
  media_type: MediaTypeValue;
  sort_order: number;
  url: string;
  filename: string | null;
  no_mostrar_en_b2b: string;
  metadata_extra: Record<string, unknown>;
  created_at: string;
}
