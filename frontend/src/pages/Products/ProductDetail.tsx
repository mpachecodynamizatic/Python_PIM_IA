import { useCallback, useEffect, useRef, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import {
  Alert,
  Box,
  Button,
  Card,
  CardMedia,
  CardActions,
  Chip,
  CircularProgress,
  Collapse,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Divider,
  Grid,
  IconButton,
  LinearProgress,
  Paper,
  Tab,
  Tabs,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  ToggleButton,
  ToggleButtonGroup,
  Tooltip,
  Typography,
  Autocomplete,
  FormControlLabel,
  MenuItem,
  Switch,
} from '@mui/material';
import { ArrowBack, Delete, Link, UploadFile, ExpandMore, ExpandLess, CompareArrows, Comment, Send, Reply, Edit, Check, Close, FilterList, Label } from '@mui/icons-material';
import { getProduct, updateProduct, transitionProduct, getProductVersions, restoreProductVersion, getVersionComments, createVersionComment, getProductComments, createProductComment, updateProductComment, deleteProductComment, getCommentReplies, submitForReview, approveProduct, rejectProduct } from '../../api/products';
import type { VersionComment, CommentFilters } from '../../api/products';
import { listMedia, uploadMedia, deleteMedia } from '../../api/media';
import { getProductTranslations, upsertTranslation, deleteTranslation } from '../../api/i18n';
import { getProductQuality } from '../../api/quality';
import { API_ORIGIN } from '../../api/client';
import type { Product, ProductVersion } from '../../types/product';
import type { MediaAsset } from '../../types/media';
import type { ProductI18n } from '../../api/i18n';
import type { QualityScore } from '../../types/quality';
import { listCategories } from '../../api/categories';
import type { Category } from '../../types/category';
import { listFamilies, listDefinitions } from '../../api/attributes';
import type { AttributeFamily, AttributeDefinition } from '../../api/attributes';
import { listBrands } from '../../api/brands';
import type { Brand } from '../../types/brand';
import { getProductSyncHistory, getProductSyncStatus } from '../../api/sync';
import type { ProductSyncHistory, ProductSyncStatus } from '../../types/sync';

const DIMENSION_LABELS: Record<string, string> = {
  brand: 'Marca',
  category: 'Categoria',
  seo: 'SEO',
  attributes: 'Atributos',
  media: 'Media',
  i18n: 'Idiomas',
};

export default function ProductDetail() {
  const { sku } = useParams<{ sku: string }>();
  const navigate = useNavigate();
  const fileRef = useRef<HTMLInputElement>(null);

  const [product, setProduct] = useState<Product | null>(null);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState(0);
  const [editBrand, setEditBrand] = useState('');
  const [editCategoryId, setEditCategoryId] = useState('');
  const [editAttributes, setEditAttributes] = useState('');
  const [editAttributesErr, setEditAttributesErr] = useState('');
  const [editSeo, setEditSeo] = useState('');
  const [editSeoErr, setEditSeoErr] = useState('');
  const [categories, setCategories] = useState<Category[]>([]);
  const [brands, setBrands] = useState<Brand[]>([]);
  const [families, setFamilies] = useState<AttributeFamily[]>([]);
  const [familyDefs, setFamilyDefs] = useState<AttributeDefinition[]>([]);
  const [editFamilyId, setEditFamilyId] = useState<string | null>(null);
  const [structuredAttrs, setStructuredAttrs] = useState<Record<string, unknown>>({});
  const [saving, setSaving] = useState(false);
  const [message, setMessage] = useState('');
  const [errMsg, setErrMsg] = useState('');

  const [media, setMedia] = useState<MediaAsset[]>([]);
  const [uploading, setUploading] = useState(false);

  const [translations, setTranslations] = useState<ProductI18n[]>([]);
  const [editLocale, setEditLocale] = useState('');
  const [editTitle, setEditTitle] = useState('');
  const [savingI18n, setSavingI18n] = useState(false);

  const [quality, setQuality] = useState<QualityScore | null>(null);
  const [versions, setVersions] = useState<ProductVersion[]>([]);
  const [restoringVersionId, setRestoringVersionId] = useState<string | null>(null);

  // Fase 4: filtrado, snapshot, diff, comentarios
  const [actionFilter, setActionFilter] = useState<string[]>([]);
  const [expandedVersionId, setExpandedVersionId] = useState<string | null>(null);
  const [diffSelection, setDiffSelection] = useState<[string | null, string | null]>([null, null]);
  const [showDiffDialog, setShowDiffDialog] = useState(false);
  const [versionComments, setVersionComments] = useState<Record<string, VersionComment[]>>({});
  const [commentInputs, setCommentInputs] = useState<Record<string, string>>({});
  const [showCommentsFor, setShowCommentsFor] = useState<string | null>(null);
  // Product-level comments
  const [productComments, setProductComments] = useState<VersionComment[]>([]);
  const [newComment, setNewComment] = useState('');
  const [newCommentTags, setNewCommentTags] = useState('');
  // Edit mode
  const [editingCommentId, setEditingCommentId] = useState<string | null>(null);
  const [editCommentBody, setEditCommentBody] = useState('');
  const [editCommentTags, setEditCommentTags] = useState('');
  // Filters
  const [commentFilters, setCommentFilters] = useState<CommentFilters>({});
  const [showCommentFilters, setShowCommentFilters] = useState(false);
  const [filterAuthorId, setFilterAuthorId] = useState('');
  const [filterTag, setFilterTag] = useState('');
  const [filterSince, setFilterSince] = useState('');
  const [filterUntil, setFilterUntil] = useState('');
  // Threaded replies
  const [replyingTo, setReplyingTo] = useState<string | null>(null);
  const [replyText, setReplyText] = useState('');
  const [replies, setReplies] = useState<Record<string, VersionComment[]>>({});
  const [expandedReplies, setExpandedReplies] = useState<Set<string>>(new Set());

  // Sync history
  const [syncHistory, setSyncHistory] = useState<ProductSyncHistory[]>([]);
  const [syncStatuses, setSyncStatuses] = useState<ProductSyncStatus[]>([]);

  const refreshSyncHistory = useCallback(async () => {
    if (!sku) return;
    const [hist, st] = await Promise.all([
      getProductSyncHistory(sku).catch(() => ({ items: [], total: 0, page: 1, size: 20, pages: 0 })),
      getProductSyncStatus(sku).catch(() => []),
    ]);
    setSyncHistory(hist.items);
    setSyncStatuses(st);
  }, [sku]);

  const refreshProductComments = useCallback(async (filters?: CommentFilters) => {
    if (!sku) return;
    setProductComments(await getProductComments(sku, filters).catch(() => []));
  }, [sku]);

  const refreshMedia = useCallback(async () => {
    if (!sku) return;
    setMedia(await listMedia(sku));
  }, [sku]);

  const refreshTranslations = useCallback(async () => {
    if (!sku) return;
    setTranslations(await getProductTranslations(sku));
  }, [sku]);

  const refreshQuality = useCallback(async () => {
    if (!sku) return;
    try {
      setQuality(await getProductQuality(sku));
    } catch { /* ignore */ }
  }, [sku]);

  // Refetch versiones cuando cambia el filtro (no en mount, ya se carga en el Promise.all)
  const filterInitRef = useRef(true);
  useEffect(() => {
    if (filterInitRef.current) {
      filterInitRef.current = false;
      return;
    }
    if (!sku) return;
    const filter = actionFilter.length > 0 ? actionFilter.join(',') : undefined;
    getProductVersions(sku, filter).then(setVersions).catch(() => setVersions([]));
  }, [sku, actionFilter]);

  const refreshVersions = useCallback(async () => {
    if (!sku) return;
    const filter = actionFilter.length > 0 ? actionFilter.join(',') : undefined;
    setVersions(await getProductVersions(sku, filter).catch(() => []));
  }, [sku, actionFilter]);

  // Load family definitions when editFamilyId changes
  const familyInitRef = useRef(true);
  useEffect(() => {
    if (familyInitRef.current) {
      familyInitRef.current = false;
      return;
    }
    if (!editFamilyId) {
      setFamilyDefs([]);
      return;
    }
    listDefinitions(editFamilyId).then(setFamilyDefs).catch(() => setFamilyDefs([]));
  }, [editFamilyId]);

  useEffect(() => {
    if (!sku) return;
    setLoading(true);
    Promise.all([
      getProduct(sku),
      listMedia(sku),
      getProductTranslations(sku),
      getProductQuality(sku).catch(() => null),
      getProductVersions(sku).catch(() => []),
      listCategories().catch(() => []),
      listFamilies().catch(() => []),
      getProductComments(sku).catch(() => []),
      listBrands().catch(() => []),
    ])
      .then(async ([p, m, t, q, v, cats, fams, comments, brs]) => {
        setProduct(p);
        setEditBrand(p.brand);
        setEditCategoryId(p.category_id);
        setEditAttributes(JSON.stringify(p.attributes, null, 2));
        setEditSeo(JSON.stringify(p.seo, null, 2));
        setMedia(m);
        setTranslations(t);
        setQuality(q);
        setVersions(v);
        setCategories(cats);
        setFamilies(fams);
        setProductComments(comments);
        setBrands(brs);
        setEditFamilyId(p.family_id || null);
        setStructuredAttrs(p.attributes || {});
        // Load definitions if product has a family
        if (p.family_id) {
          try {
            const defs = await listDefinitions(p.family_id);
            setFamilyDefs(defs);
          } catch { /* ignore */ }
        }
        // Load sync history
        await refreshSyncHistory();
      })
      .catch(() => navigate('/products'))
      .finally(() => setLoading(false));
  }, [sku, navigate]);

  if (loading || !product) {
    return (
      <Box display="flex" justifyContent="center" mt={4}>
        <CircularProgress />
      </Box>
    );
  }

  const handleSave = async () => {
    if (!sku) return;
    setSaving(true);
    try {
      const updated = await updateProduct(sku, { brand: editBrand, category_id: editCategoryId, family_id: editFamilyId });
      setProduct(updated);
      setMessage('Producto actualizado');
      refreshQuality();
    } catch {
      setErrMsg('Error al actualizar');
    } finally {
      setSaving(false);
    }
  };

  const handleSaveAttributes = async () => {
    if (!sku) return;
    try {
      const parsed = JSON.parse(editAttributes);
      setEditAttributesErr('');
      setSaving(true);
      const updated = await updateProduct(sku, { attributes: parsed });
      setProduct(updated);
      setEditAttributes(JSON.stringify(updated.attributes, null, 2));
      setMessage('Atributos actualizados');
      refreshQuality();
    } catch (e) {
      if (e instanceof SyntaxError) {
        setEditAttributesErr('JSON invalido: ' + e.message);
        return;
      }
      setErrMsg('Error al actualizar atributos');
    } finally {
      setSaving(false);
    }
  };

  const handleSaveStructuredAttrs = async () => {
    if (!sku) return;
    setSaving(true);
    try {
      // Clean undefined values
      const clean: Record<string, unknown> = {};
      for (const [k, v] of Object.entries(structuredAttrs)) {
        if (v !== undefined && v !== '') clean[k] = v;
      }
      const updated = await updateProduct(sku, { attributes: clean });
      setProduct(updated);
      setStructuredAttrs(updated.attributes || {});
      setEditAttributes(JSON.stringify(updated.attributes, null, 2));
      setMessage('Atributos actualizados');
      refreshQuality();
    } catch {
      setErrMsg('Error al actualizar atributos');
    } finally {
      setSaving(false);
    }
  };

  const handleSaveSeo = async () => {
    if (!sku) return;
    try {
      const parsed = JSON.parse(editSeo);
      setEditSeoErr('');
      setSaving(true);
      const updated = await updateProduct(sku, { seo: parsed });
      setProduct(updated);
      setEditSeo(JSON.stringify(updated.seo, null, 2));
      setMessage('SEO actualizado');
      refreshQuality();
    } catch (e) {
      if (e instanceof SyntaxError) {
        setEditSeoErr('JSON invalido: ' + e.message);
        return;
      }
      setErrMsg('Error al actualizar SEO');
    } finally {
      setSaving(false);
    }
  };

  const handleTransition = async (newStatus: string) => {
    if (!sku) return;
    try {
      setProduct(await transitionProduct(sku, newStatus));
      setMessage(`Estado cambiado a ${newStatus}`);
    } catch (err: unknown) {
      setErrMsg(err instanceof Error ? err.message : 'Error en transicion');
    }
  };

  const handleSubmitReview = async () => {
    if (!sku) return;
    try {
      setProduct(await submitForReview(sku));
      setMessage('Producto enviado a revision');
    } catch (err: unknown) {
      setErrMsg(err instanceof Error ? err.message : 'Error al enviar a revision');
    }
  };

  const handleApprove = async () => {
    if (!sku) return;
    try {
      setProduct(await approveProduct(sku));
      setMessage('Producto aprobado');
    } catch (err: unknown) {
      setErrMsg(err instanceof Error ? err.message : 'Error al aprobar');
    }
  };

  const handleReject = async () => {
    if (!sku) return;
    try {
      setProduct(await rejectProduct(sku));
      setMessage('Producto devuelto a borrador');
    } catch (err: unknown) {
      setErrMsg(err instanceof Error ? err.message : 'Error al rechazar');
    }
  };

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file || !sku) return;
    setUploading(true);
    try {
      await uploadMedia(file, sku);
      await refreshMedia();
      await refreshQuality();
      setMessage('Imagen subida');
    } catch {
      setErrMsg('Error al subir imagen');
    } finally {
      setUploading(false);
      if (fileRef.current) fileRef.current.value = '';
    }
  };

  const handleDeleteMedia = async (asset: MediaAsset) => {
    try {
      await deleteMedia(asset.id);
      await refreshMedia();
      await refreshQuality();
      setMessage('Asset eliminado');
    } catch {
      setErrMsg('Error al eliminar');
    }
  };

  const handleSaveI18n = async () => {
    if (!sku || !editLocale || !editTitle.trim()) return;
    setSavingI18n(true);
    try {
      await upsertTranslation(sku, editLocale, { title: editTitle });
      await refreshTranslations();
      await refreshQuality();
      setMessage('Traduccion guardada');
      setEditLocale('');
      setEditTitle('');
    } catch {
      setErrMsg('Error al guardar traduccion');
    } finally {
      setSavingI18n(false);
    }
  };

  const handleDeleteI18n = async (locale: string) => {
    if (!sku) return;
    try {
      await deleteTranslation(sku, locale);
      await refreshTranslations();
      await refreshQuality();
      setMessage(`Traduccion '${locale}' eliminada`);
    } catch {
      setErrMsg('Error al eliminar traduccion');
    }
  };

  const statusColors: Record<string, 'warning' | 'success' | 'error' | 'info' | 'primary'> = {
    draft: 'warning',
    in_review: 'info',
    approved: 'primary',
    ready: 'success',
    retired: 'error',
  };

  const isImage = (a: MediaAsset) =>
    a.kind === 'image' || /\.(jpe?g|png|webp|gif|svg)$/i.test(a.url);

  const handleRestoreVersion = async (versionId: string) => {
    if (!sku) return;
    const confirmRestore = window.confirm('¿Restaurar el producto a esta versión?');
    if (!confirmRestore) return;
    setRestoringVersionId(versionId);
    try {
      const updated = await restoreProductVersion(sku, versionId);
      setProduct(updated);
      setMessage('Producto restaurado a la versión seleccionada');
      refreshQuality();
      await refreshVersions();
    } catch {
      setErrMsg('Error al restaurar versión');
    } finally {
      setRestoringVersionId(null);
    }
  };

  const handleToggleDiffSelect = (versionId: string) => {
    setDiffSelection(([a, b]) => {
      if (a === versionId) return [b, null];
      if (b === versionId) return [a, null];
      if (a === null) return [versionId, null];
      if (b === null) return [a, versionId];
      return [b, versionId];
    });
  };

  const getDiffData = () => {
    const [aId, bId] = diffSelection;
    const a = versions.find((v) => v.id === aId);
    const b = versions.find((v) => v.id === bId);
    return { a, b };
  };

  const loadComments = async (versionId: string) => {
    if (!sku) return;
    const comments = await getVersionComments(sku, versionId).catch(() => []);
    setVersionComments((prev) => ({ ...prev, [versionId]: comments }));
  };

  const handleToggleComments = (versionId: string) => {
    if (showCommentsFor === versionId) {
      setShowCommentsFor(null);
    } else {
      setShowCommentsFor(versionId);
      if (!versionComments[versionId]) loadComments(versionId);
    }
  };

  const handleSubmitComment = async (versionId: string) => {
    if (!sku) return;
    const body = (commentInputs[versionId] || '').trim();
    if (!body) return;
    try {
      await createVersionComment(sku, versionId, body);
      setCommentInputs((prev) => ({ ...prev, [versionId]: '' }));
      await loadComments(versionId);
    } catch {
      setErrMsg('Error al añadir comentario');
    }
  };

  const handleSubmitProductComment = async () => {
    if (!sku) return;
    const body = newComment.trim();
    if (!body) return;
    const tags = newCommentTags.split(',').map((t) => t.trim()).filter(Boolean);
    try {
      await createProductComment(sku, body, undefined, tags.length ? tags : undefined);
      setNewComment('');
      setNewCommentTags('');
      await refreshProductComments(commentFilters);
    } catch {
      setErrMsg('Error al añadir comentario');
    }
  };

  const handleSubmitReply = async (parentId: string) => {
    if (!sku) return;
    const body = replyText.trim();
    if (!body) return;
    try {
      await createProductComment(sku, body, parentId);
      setReplyText('');
      setReplyingTo(null);
      await refreshProductComments(commentFilters);
      const freshReplies = await getCommentReplies(sku, parentId);
      setReplies((prev) => ({ ...prev, [parentId]: freshReplies }));
      setExpandedReplies((prev) => new Set(prev).add(parentId));
    } catch {
      setErrMsg('Error al añadir respuesta');
    }
  };

  const handleToggleReplies = async (commentId: string) => {
    if (!sku) return;
    if (expandedReplies.has(commentId)) {
      setExpandedReplies((prev) => { const n = new Set(prev); n.delete(commentId); return n; });
    } else {
      const data = await getCommentReplies(sku, commentId).catch(() => []);
      setReplies((prev) => ({ ...prev, [commentId]: data }));
      setExpandedReplies((prev) => new Set(prev).add(commentId));
    }
  };

  const handleDeleteComment = async (commentId: string) => {
    if (!sku) return;
    try {
      await deleteProductComment(sku, commentId);
      await refreshProductComments(commentFilters);
      setMessage('Comentario eliminado');
    } catch {
      setErrMsg('Error al eliminar comentario');
    }
  };

  const handleStartEditComment = (c: VersionComment) => {
    setEditingCommentId(c.id);
    setEditCommentBody(c.body);
    setEditCommentTags((c.tags || []).join(', '));
  };

  const handleSaveEditComment = async (commentId: string) => {
    if (!sku) return;
    const tags = editCommentTags.split(',').map((t) => t.trim()).filter(Boolean);
    try {
      await updateProductComment(sku, commentId, { body: editCommentBody, tags: tags.length ? tags : [] });
      setEditingCommentId(null);
      await refreshProductComments(commentFilters);
      setMessage('Comentario actualizado');
    } catch {
      setErrMsg('Error al editar comentario');
    }
  };

  const handleApplyCommentFilters = () => {
    const filters: CommentFilters = {};
    if (filterAuthorId.trim()) filters.author_id = filterAuthorId.trim();
    if (filterTag.trim()) filters.tag = filterTag.trim();
    if (filterSince.trim()) filters.since = new Date(filterSince).toISOString();
    if (filterUntil.trim()) filters.until = new Date(filterUntil).toISOString();
    setCommentFilters(filters);
    refreshProductComments(filters);
  };

  const handleClearCommentFilters = () => {
    setFilterAuthorId('');
    setFilterTag('');
    setFilterSince('');
    setFilterUntil('');
    setCommentFilters({});
    refreshProductComments({});
  };

  return (
    <Box>
      <Button startIcon={<ArrowBack />} onClick={() => navigate('/products')} sx={{ mb: 2 }}>
        Volver
      </Button>

      <Box display="flex" alignItems="center" gap={2} mb={2}>
        <Typography variant="h4">{product.sku}</Typography>
        <Chip
          label={{ draft: 'Borrador', in_review: 'En revision', approved: 'Aprobado', ready: 'Publicado', retired: 'Retirado' }[product.status] || product.status}
          color={statusColors[product.status] || 'default'}
        />
        {quality && (
          <Chip
            label={`Calidad ${quality.overall}%`}
            color={quality.overall >= 80 ? 'success' : quality.overall >= 50 ? 'warning' : 'error'}
            variant="outlined"
          />
        )}
      </Box>

      {message && (
        <Alert severity="success" onClose={() => setMessage('')} sx={{ mb: 2 }}>
          {message}
        </Alert>
      )}
      {errMsg && (
        <Alert severity="error" onClose={() => setErrMsg('')} sx={{ mb: 2 }}>
          {errMsg}
        </Alert>
      )}

      <Box display="flex" gap={1} mb={3}>
        {product.status === 'draft' && (
          <>
            <Button variant="contained" color="info" onClick={handleSubmitReview}>
              Enviar a revision
            </Button>
            <Button variant="contained" color="success" onClick={() => handleTransition('ready')}>
              Publicar directo
            </Button>
          </>
        )}
        {product.status === 'in_review' && (
          <>
            <Button variant="contained" color="primary" onClick={handleApprove}>
              Aprobar
            </Button>
            <Button variant="outlined" color="error" onClick={handleReject}>
              Rechazar
            </Button>
          </>
        )}
        {product.status === 'approved' && (
          <>
            <Button variant="contained" color="success" onClick={() => handleTransition('ready')}>
              Publicar
            </Button>
            <Button variant="outlined" onClick={() => handleTransition('draft')}>
              Volver a borrador
            </Button>
          </>
        )}
        {product.status === 'ready' && (
          <>
            <Button variant="outlined" onClick={() => handleTransition('draft')}>
              Volver a borrador
            </Button>
            <Button variant="contained" color="error" onClick={() => handleTransition('retired')}>
              Retirar
            </Button>
          </>
        )}
        {product.status === 'retired' && (
          <Button variant="outlined" onClick={() => handleTransition('draft')}>
            Reactivar
          </Button>
        )}
      </Box>

      <Paper sx={{ mb: 2 }}>
        <Tabs value={tab} onChange={(_, v) => setTab(v)}>
          <Tab label="General" />
          <Tab label="Atributos" />
          <Tab label={`I18N (${translations.length})`} />
          <Tab label="SEO" />
          <Tab label={`Media (${media.length})`} />
          <Tab label="Calidad" />
          <Tab label={`Comentarios (${productComments.length})`} />
          <Tab label="Historial" />
          <Tab label="Sync" />
        </Tabs>
      </Paper>

      {tab === 0 && (
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>Informacion General</Typography>
          <TextField
            select
            fullWidth
            label="Marca"
            value={editBrand}
            onChange={(e) => setEditBrand(e.target.value)}
            margin="normal"
          >
            {brands.filter((b) => b.active || b.name === editBrand).map((b) => (
              <MenuItem key={b.id} value={b.name}>{b.name}</MenuItem>
            ))}
          </TextField>
          <Autocomplete
            options={categories}
            getOptionLabel={(opt) => opt.name}
            value={categories.find((c) => c.id === editCategoryId) || null}
            onChange={(_, val) => setEditCategoryId(val?.id || '')}
            isOptionEqualToValue={(opt, val) => opt.id === val.id}
            renderInput={(params) => (
              <TextField {...params} fullWidth label="Categoria" margin="normal" />
            )}
          />
          <Autocomplete
            options={families}
            getOptionLabel={(opt) => `${opt.name} (${opt.code})`}
            value={families.find((f) => f.id === editFamilyId) || null}
            onChange={(_, val) => setEditFamilyId(val?.id || null)}
            isOptionEqualToValue={(opt, val) => opt.id === val.id}
            renderInput={(params) => (
              <TextField {...params} fullWidth label="Familia de atributos" margin="normal" helperText="Define los atributos estructurados del producto" />
            )}
          />
          <TextField fullWidth label="Creado" value={new Date(product.created_at).toLocaleString()} margin="normal" disabled />
          <TextField fullWidth label="Actualizado" value={new Date(product.updated_at).toLocaleString()} margin="normal" disabled />
          <Divider sx={{ my: 2 }} />
          <Button variant="contained" onClick={handleSave} disabled={saving}>
            {saving ? 'Guardando...' : 'Guardar'}
          </Button>
        </Paper>
      )}

      {tab === 1 && (
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>Atributos</Typography>
          {familyDefs.length > 0 ? (
            <>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                Familia: {families.find((f) => f.id === editFamilyId)?.name || editFamilyId}
              </Typography>
              {familyDefs.map((def) => {
                const value = structuredAttrs[def.code];
                let options: string[] = [];
                if (def.type === 'enum' && def.options_json) {
                  try { options = JSON.parse(def.options_json); } catch { /* ignore */ }
                }
                return (
                  <Box key={def.id} sx={{ mb: 2 }}>
                    {def.type === 'boolean' ? (
                      <FormControlLabel
                        control={
                          <Switch
                            checked={!!value}
                            onChange={(e) => setStructuredAttrs((prev) => ({ ...prev, [def.code]: e.target.checked }))}
                          />
                        }
                        label={`${def.label}${def.required ? ' *' : ''}`}
                      />
                    ) : def.type === 'enum' ? (
                      <TextField
                        fullWidth select
                        label={`${def.label}${def.required ? ' *' : ''}`}
                        value={typeof value === 'string' ? value : ''}
                        onChange={(e) => setStructuredAttrs((prev) => ({ ...prev, [def.code]: e.target.value }))}
                        size="small"
                        margin="dense"
                      >
                        <MenuItem value="">— sin seleccionar —</MenuItem>
                        {options.map((opt) => (
                          <MenuItem key={opt} value={opt}>{opt}</MenuItem>
                        ))}
                      </TextField>
                    ) : def.type === 'number' ? (
                      <TextField
                        fullWidth type="number"
                        label={`${def.label}${def.required ? ' *' : ''}`}
                        value={value ?? ''}
                        onChange={(e) => setStructuredAttrs((prev) => ({ ...prev, [def.code]: e.target.value === '' ? undefined : Number(e.target.value) }))}
                        size="small"
                        margin="dense"
                      />
                    ) : (
                      <TextField
                        fullWidth
                        label={`${def.label}${def.required ? ' *' : ''}`}
                        value={typeof value === 'string' ? value : (value ?? '')}
                        onChange={(e) => setStructuredAttrs((prev) => ({ ...prev, [def.code]: e.target.value }))}
                        size="small"
                        margin="dense"
                      />
                    )}
                  </Box>
                );
              })}
              <Divider sx={{ my: 2 }} />
              <Button variant="contained" onClick={handleSaveStructuredAttrs} disabled={saving}>
                {saving ? 'Guardando...' : 'Guardar atributos'}
              </Button>
            </>
          ) : (
            <>
              <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
                {editFamilyId ? 'La familia no tiene atributos definidos. Edita en JSON.' : 'Sin familia asignada. Edita los atributos en JSON.'}
              </Typography>
              <TextField
                fullWidth multiline rows={12}
                value={editAttributes}
                onChange={(e) => { setEditAttributes(e.target.value); setEditAttributesErr(''); }}
                margin="normal"
                error={!!editAttributesErr}
                helperText={editAttributesErr}
                slotProps={{ input: { sx: { fontFamily: 'monospace', fontSize: '0.85rem' } } }}
              />
              <Divider sx={{ my: 2 }} />
              <Button variant="contained" onClick={handleSaveAttributes} disabled={saving}>
                {saving ? 'Guardando...' : 'Guardar atributos'}
              </Button>
            </>
          )}
        </Paper>
      )}

      {tab === 2 && (
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>Traducciones</Typography>
          {translations.map((t) => (
            <Box
              key={t.locale}
              sx={{ mb: 2, p: 2, border: '1px solid #eee', borderRadius: 1, display: 'flex', alignItems: 'flex-start', justifyContent: 'space-between' }}
            >
              <Box>
                <Chip label={t.locale.toUpperCase()} size="small" sx={{ mb: 0.5 }} />
                <Typography>{t.title}</Typography>
              </Box>
              <IconButton size="small" color="error" onClick={() => handleDeleteI18n(t.locale)}>
                <Delete fontSize="small" />
              </IconButton>
            </Box>
          ))}
          {translations.length === 0 && (
            <Typography color="text.secondary" sx={{ mb: 2 }}>Sin traducciones</Typography>
          )}
          <Divider sx={{ my: 2 }} />
          <Typography variant="subtitle2" gutterBottom>Agregar / editar traduccion</Typography>
          <Box display="flex" gap={2} flexWrap="wrap">
            <TextField
              label="Locale (ej: es, en)" size="small"
              value={editLocale} onChange={(e) => setEditLocale(e.target.value)}
              sx={{ width: 160 }}
            />
            <TextField
              label="Titulo" size="small"
              value={editTitle} onChange={(e) => setEditTitle(e.target.value)}
              sx={{ flexGrow: 1, minWidth: 200 }}
            />
            <Button
              variant="contained"
              disabled={!editLocale.trim() || !editTitle.trim() || savingI18n}
              onClick={handleSaveI18n}
            >
              Guardar
            </Button>
          </Box>
        </Paper>
      )}

      {tab === 3 && (
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>SEO</Typography>
          <TextField
            fullWidth multiline rows={8}
            value={editSeo}
            onChange={(e) => { setEditSeo(e.target.value); setEditSeoErr(''); }}
            margin="normal"
            error={!!editSeoErr}
            helperText={editSeoErr}
            slotProps={{ input: { sx: { fontFamily: 'monospace', fontSize: '0.85rem' } } }}
          />
          <Divider sx={{ my: 2 }} />
          <Button variant="contained" onClick={handleSaveSeo} disabled={saving}>
            {saving ? 'Guardando...' : 'Guardar SEO'}
          </Button>
        </Paper>
      )}

      {tab === 4 && (
        <Paper sx={{ p: 3 }}>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
            <Typography variant="h6">Media ({media.length})</Typography>
            <Box>
              <input
                ref={fileRef} type="file"
                accept="image/*,video/mp4,application/pdf"
                style={{ display: 'none' }}
                onChange={handleUpload}
              />
              <Button
                variant="contained" startIcon={<UploadFile />}
                onClick={() => fileRef.current?.click()} disabled={uploading}
              >
                {uploading ? 'Subiendo...' : 'Subir archivo'}
              </Button>
            </Box>
          </Box>
          {media.length === 0 ? (
            <Typography color="text.secondary">Sin archivos multimedia.</Typography>
          ) : (
            <Grid container spacing={2}>
              {media.map((asset) => (
                <Grid key={asset.id} size={{ xs: 12, sm: 6, md: 4 }}>
                  <Card>
                    {isImage(asset) ? (
                      <CardMedia
                        component="img"
                        height="160"
                        image={`${API_ORIGIN}${asset.url}`}
                        alt={asset.filename || asset.id}
                        sx={{ objectFit: 'cover' }}
                      />
                    ) : (
                      <Box height={160} display="flex" alignItems="center" justifyContent="center" bgcolor="grey.100">
                        <Typography variant="h6" color="text.secondary">{asset.kind.toUpperCase()}</Typography>
                      </Box>
                    )}
                    <CardActions>
                      <Tooltip title="Abrir">
                        <IconButton
                          size="small"
                          component="a"
                          href={`${API_ORIGIN}${asset.url}`}
                          target="_blank"
                          rel="noreferrer"
                        >
                          <Link />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Eliminar">
                        <IconButton size="small" color="error" onClick={() => handleDeleteMedia(asset)}>
                          <Delete />
                        </IconButton>
                      </Tooltip>
                      <Typography variant="caption" noWrap sx={{ flexGrow: 1, ml: 1 }}>
                        {asset.filename || asset.url}
                      </Typography>
                    </CardActions>
                  </Card>
                </Grid>
              ))}
            </Grid>
          )}
        </Paper>
      )}

      {tab === 5 && (
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>Calidad de Datos</Typography>
          {quality ? (
            <Box>
              <Box display="flex" alignItems="center" gap={2} mb={3}>
                <Typography
                  variant="h3"
                  color={quality.overall >= 80 ? 'success.main' : quality.overall >= 50 ? 'warning.main' : 'error.main'}
                >
                  {quality.overall}%
                </Typography>
                <Typography variant="body2" color="text.secondary">score global</Typography>
              </Box>
              {Object.entries(quality.dimensions).map(([key, val]) => (
                <Box key={key} sx={{ mb: 2 }}>
                  <Box display="flex" justifyContent="space-between" mb={0.5}>
                    <Typography variant="body2">{DIMENSION_LABELS[key] ?? key}</Typography>
                    <Typography variant="body2">{Math.round(val * 100)}%</Typography>
                  </Box>
                  <LinearProgress
                    variant="determinate" value={val * 100}
                    color={val === 1 ? 'success' : val > 0 ? 'warning' : 'error'}
                    sx={{ height: 8, borderRadius: 4 }}
                  />
                </Box>
              ))}
              <Button variant="outlined" sx={{ mt: 2 }} onClick={refreshQuality}>
                Recalcular
              </Button>
            </Box>
          ) : (
            <Typography color="text.secondary">Sin datos de calidad disponibles</Typography>
          )}
        </Paper>
      )}

      {tab === 6 && (
        <Paper sx={{ p: 3 }}>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
            <Typography variant="h6">Comentarios</Typography>
            <Tooltip title="Filtrar comentarios">
              <IconButton onClick={() => setShowCommentFilters((v) => !v)}>
                <FilterList color={Object.keys(commentFilters).length > 0 ? 'primary' : 'inherit'} />
              </IconButton>
            </Tooltip>
          </Box>
          <Typography variant="body2" color="text.secondary" mb={2}>
            Discusion general sobre este producto entre los miembros del equipo.
          </Typography>

          {/* Filter panel */}
          <Collapse in={showCommentFilters}>
            <Box sx={{ mb: 2, p: 2, bgcolor: 'grey.50', borderRadius: 1, display: 'flex', flexWrap: 'wrap', gap: 1, alignItems: 'flex-end' }}>
              <TextField
                label="ID de autor"
                size="small"
                value={filterAuthorId}
                onChange={(e) => setFilterAuthorId(e.target.value)}
                sx={{ width: 200 }}
              />
              <TextField
                label="Etiqueta"
                size="small"
                value={filterTag}
                onChange={(e) => setFilterTag(e.target.value)}
                sx={{ width: 160 }}
              />
              <TextField
                label="Desde"
                size="small"
                type="datetime-local"
                value={filterSince}
                onChange={(e) => setFilterSince(e.target.value)}
                InputLabelProps={{ shrink: true }}
                sx={{ width: 200 }}
              />
              <TextField
                label="Hasta"
                size="small"
                type="datetime-local"
                value={filterUntil}
                onChange={(e) => setFilterUntil(e.target.value)}
                InputLabelProps={{ shrink: true }}
                sx={{ width: 200 }}
              />
              <Button variant="contained" size="small" onClick={handleApplyCommentFilters}>Aplicar</Button>
              {Object.keys(commentFilters).length > 0 && (
                <Button size="small" onClick={handleClearCommentFilters}>Limpiar</Button>
              )}
            </Box>
          </Collapse>

          {/* Input nuevo comentario */}
          <Box sx={{ mb: 1 }}>
            <Box display="flex" gap={1} mb={1}>
              <TextField
                size="small"
                placeholder="Escribe un comentario..."
                value={newComment}
                onChange={(e) => setNewComment(e.target.value)}
                fullWidth
                multiline
                maxRows={4}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    handleSubmitProductComment();
                  }
                }}
              />
              <IconButton
                color="primary"
                onClick={handleSubmitProductComment}
                disabled={!newComment.trim()}
              >
                <Send />
              </IconButton>
            </Box>
            <TextField
              size="small"
              placeholder="Etiquetas (separadas por coma, ej: pendiente revision, aprobado)"
              value={newCommentTags}
              onChange={(e) => setNewCommentTags(e.target.value)}
              fullWidth
              sx={{ mb: 2 }}
              InputProps={{ startAdornment: <Label fontSize="small" sx={{ mr: 1, color: 'text.secondary' }} /> }}
            />
          </Box>

          {productComments.length === 0 ? (
            <Typography color="text.secondary" textAlign="center" py={4}>
              Sin comentarios. Se el primero en comentar.
            </Typography>
          ) : (
            <Box>
              {productComments.map((c) => (
                <Box
                  key={c.id}
                  sx={{ mb: 2, p: 2, border: '1px solid #eee', borderRadius: 1 }}
                >
                  <Box display="flex" justifyContent="space-between" alignItems="center" mb={0.5}>
                    <Typography variant="subtitle2">
                      {c.author_name}
                      <Typography component="span" variant="caption" color="text.secondary" sx={{ ml: 1 }}>
                        {new Date(c.created_at).toLocaleString()}
                        {c.updated_at && c.updated_at !== c.created_at && (
                          <Typography component="span" variant="caption" color="text.secondary" sx={{ ml: 0.5 }}>
                            (editado)
                          </Typography>
                        )}
                      </Typography>
                    </Typography>
                    <Box>
                      <Tooltip title="Responder">
                        <IconButton size="small" onClick={() => { setReplyingTo(replyingTo === c.id ? null : c.id); setReplyText(''); }}>
                          <Reply fontSize="small" />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Editar comentario">
                        <IconButton size="small" onClick={() => handleStartEditComment(c)}>
                          <Edit fontSize="small" />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Eliminar comentario">
                        <IconButton size="small" onClick={() => handleDeleteComment(c.id)}>
                          <Delete fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    </Box>
                  </Box>

                  {/* Edit mode */}
                  {editingCommentId === c.id ? (
                    <Box>
                      <TextField
                        size="small"
                        value={editCommentBody}
                        onChange={(e) => setEditCommentBody(e.target.value)}
                        fullWidth
                        multiline
                        maxRows={4}
                        sx={{ mb: 1 }}
                      />
                      <TextField
                        size="small"
                        label="Etiquetas (coma separadas)"
                        value={editCommentTags}
                        onChange={(e) => setEditCommentTags(e.target.value)}
                        fullWidth
                        sx={{ mb: 1 }}
                      />
                      <Box display="flex" gap={1}>
                        <IconButton size="small" color="primary" onClick={() => handleSaveEditComment(c.id)} disabled={!editCommentBody.trim()}>
                          <Check fontSize="small" />
                        </IconButton>
                        <IconButton size="small" onClick={() => setEditingCommentId(null)}>
                          <Close fontSize="small" />
                        </IconButton>
                      </Box>
                    </Box>
                  ) : (
                    <>
                      <Typography variant="body2" sx={{ whiteSpace: 'pre-wrap' }}>{c.body}</Typography>
                      {c.tags && c.tags.length > 0 && (
                        <Box display="flex" flexWrap="wrap" gap={0.5} mt={0.5}>
                          {c.tags.map((tag) => (
                            <Chip key={tag} label={tag} size="small" variant="outlined" color="primary" sx={{ fontSize: '0.7rem' }} />
                          ))}
                        </Box>
                      )}
                    </>
                  )}

                  {/* Reply count / toggle */}
                  {c.reply_count > 0 && (
                    <Button
                      size="small"
                      sx={{ mt: 1, textTransform: 'none' }}
                      startIcon={expandedReplies.has(c.id) ? <ExpandLess /> : <ExpandMore />}
                      onClick={() => handleToggleReplies(c.id)}
                    >
                      {expandedReplies.has(c.id) ? 'Ocultar' : 'Ver'} {c.reply_count} {c.reply_count === 1 ? 'respuesta' : 'respuestas'}
                    </Button>
                  )}

                  {/* Reply input */}
                  {replyingTo === c.id && (
                    <Box display="flex" gap={1} mt={1} ml={2}>
                      <TextField
                        size="small"
                        placeholder="Escribe una respuesta..."
                        value={replyText}
                        onChange={(e) => setReplyText(e.target.value)}
                        fullWidth
                        multiline
                        maxRows={3}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter' && !e.shiftKey) {
                            e.preventDefault();
                            handleSubmitReply(c.id);
                          }
                        }}
                      />
                      <IconButton color="primary" onClick={() => handleSubmitReply(c.id)} disabled={!replyText.trim()}>
                        <Send />
                      </IconButton>
                    </Box>
                  )}

                  {/* Replies list */}
                  <Collapse in={expandedReplies.has(c.id)}>
                    <Box ml={3} mt={1} borderLeft="2px solid #e0e0e0" pl={2}>
                      {(replies[c.id] || []).map((r) => (
                        <Box key={r.id} sx={{ mb: 1, p: 1 }}>
                          <Box display="flex" justifyContent="space-between" alignItems="center">
                            <Typography variant="subtitle2" fontSize="0.8rem">
                              {r.author_name}
                              <Typography component="span" variant="caption" color="text.secondary" sx={{ ml: 1 }}>
                                {new Date(r.created_at).toLocaleString()}
                              </Typography>
                            </Typography>
                            <Tooltip title="Eliminar respuesta">
                              <IconButton size="small" onClick={() => handleDeleteComment(r.id)}>
                                <Delete fontSize="small" />
                              </IconButton>
                            </Tooltip>
                          </Box>
                          <Typography variant="body2" fontSize="0.85rem" sx={{ whiteSpace: 'pre-wrap' }}>{r.body}</Typography>
                        </Box>
                      ))}
                    </Box>
                  </Collapse>
                </Box>
              ))}
            </Box>
          )}
        </Paper>
      )}

      {tab === 7 && (
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>
            Historial de versiones
          </Typography>

          {/* Filtros por tipo de acción */}
          <Box sx={{ mb: 2 }}>
            <Typography variant="body2" color="text.secondary" sx={{ mb: 1 }}>
              Filtrar por tipo de cambio:
            </Typography>
            <ToggleButtonGroup
              size="small"
              value={actionFilter}
              onChange={(_, val) => setActionFilter(val)}
            >
              <ToggleButton value="create">Creacion</ToggleButton>
              <ToggleButton value="update">Edicion</ToggleButton>
              <ToggleButton value="transition">Estado</ToggleButton>
              <ToggleButton value="restore">Restauracion</ToggleButton>
            </ToggleButtonGroup>
          </Box>

          {/* Botón de comparar */}
          {diffSelection[0] && diffSelection[1] && (
            <Button
              variant="contained"
              size="small"
              startIcon={<CompareArrows />}
              onClick={() => setShowDiffDialog(true)}
              sx={{ mb: 2 }}
            >
              Comparar seleccionadas
            </Button>
          )}

          {versions.length === 0 ? (
            <Typography color="text.secondary">Sin cambios registrados.</Typography>
          ) : (
            <Box component="ul" sx={{ listStyle: 'none', p: 0, m: 0 }}>
              {versions
                .slice()
                .reverse()
                .map((v) => {
                  const isExpanded = expandedVersionId === v.id;
                  const isSelectedForDiff = diffSelection.includes(v.id);
                  const commentsOpen = showCommentsFor === v.id;
                  const comments = versionComments[v.id] || [];

                  return (
                    <Box
                      key={v.id}
                      component="li"
                      sx={{
                        py: 1.5,
                        borderBottom: '1px solid #eee',
                        bgcolor: isSelectedForDiff ? 'action.selected' : 'transparent',
                        px: 1,
                        borderRadius: 1,
                      }}
                    >
                      <Box display="flex" justifyContent="space-between" alignItems="center">
                        <Box display="flex" alignItems="center" gap={1}>
                          <Chip
                            label={v.action}
                            size="small"
                            color={
                              v.action === 'create' ? 'success'
                              : v.action === 'update' ? 'primary'
                              : v.action === 'transition' ? 'warning'
                              : v.action === 'restore' ? 'info'
                              : 'default'
                            }
                            variant="outlined"
                          />
                          <Typography variant="body2">
                            {new Date(v.created_at).toLocaleString()} — {v.actor}
                          </Typography>
                        </Box>
                        <Box display="flex" gap={0.5}>
                          <Tooltip title="Seleccionar para comparar">
                            <IconButton
                              size="small"
                              color={isSelectedForDiff ? 'primary' : 'default'}
                              onClick={() => handleToggleDiffSelect(v.id)}
                            >
                              <CompareArrows fontSize="small" />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title={commentsOpen ? 'Ocultar comentarios' : 'Comentarios'}>
                            <IconButton size="small" onClick={() => handleToggleComments(v.id)}>
                              <Comment fontSize="small" />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title={isExpanded ? 'Ocultar snapshot' : 'Ver snapshot'}>
                            <IconButton
                              size="small"
                              onClick={() => setExpandedVersionId(isExpanded ? null : v.id)}
                            >
                              {isExpanded ? <ExpandLess fontSize="small" /> : <ExpandMore fontSize="small" />}
                            </IconButton>
                          </Tooltip>
                          <Button
                            variant="outlined"
                            size="small"
                            onClick={() => handleRestoreVersion(v.id)}
                            disabled={restoringVersionId === v.id || v.action === 'transition'}
                          >
                            {restoringVersionId === v.id ? 'Restaurando...' : 'Restaurar'}
                          </Button>
                        </Box>
                      </Box>

                      {/* Snapshot expandible */}
                      <Collapse in={isExpanded}>
                        <Box sx={{ mt: 1, p: 2, bgcolor: 'grey.50', borderRadius: 1, maxHeight: 300, overflow: 'auto' }}>
                          <Typography variant="caption" color="text.secondary" display="block" gutterBottom>
                            Snapshot de datos:
                          </Typography>
                          <pre style={{ margin: 0, fontSize: '0.75rem', whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                            {JSON.stringify(v.snapshot, null, 2)}
                          </pre>
                        </Box>
                      </Collapse>

                      {/* Comentarios por versión */}
                      <Collapse in={commentsOpen}>
                        <Box sx={{ mt: 1, pl: 2, borderLeft: '3px solid #ddd' }}>
                          {comments.length === 0 && (
                            <Typography variant="caption" color="text.secondary">Sin comentarios</Typography>
                          )}
                          {comments.map((c) => (
                            <Box key={c.id} sx={{ mb: 1 }}>
                              <Typography variant="caption" color="text.secondary">
                                {c.author_name} — {new Date(c.created_at).toLocaleString()}
                              </Typography>
                              <Typography variant="body2">{c.body}</Typography>
                            </Box>
                          ))}
                          <Box display="flex" gap={1} mt={1}>
                            <TextField
                              size="small"
                              placeholder="Añadir comentario..."
                              value={commentInputs[v.id] || ''}
                              onChange={(e) => setCommentInputs((prev) => ({ ...prev, [v.id]: e.target.value }))}
                              fullWidth
                              onKeyDown={(e) => { if (e.key === 'Enter') handleSubmitComment(v.id); }}
                            />
                            <IconButton
                              size="small"
                              color="primary"
                              onClick={() => handleSubmitComment(v.id)}
                              disabled={!(commentInputs[v.id] || '').trim()}
                            >
                              <Send fontSize="small" />
                            </IconButton>
                          </Box>
                        </Box>
                      </Collapse>
                    </Box>
                  );
                })}
            </Box>
          )}

          {/* Dialog de comparación de versiones */}
          <Dialog
            open={showDiffDialog}
            onClose={() => setShowDiffDialog(false)}
            maxWidth="lg"
            fullWidth
          >
            <DialogTitle>Comparacion de versiones</DialogTitle>
            <DialogContent>
              {(() => {
                const { a, b } = getDiffData();
                if (!a || !b) return <Typography>Selecciona dos versiones para comparar.</Typography>;

                const keysA = Object.keys(a.snapshot || {});
                const keysB = Object.keys(b.snapshot || {});
                const allKeys = [...new Set([...keysA, ...keysB])].sort();

                return (
                  <Box>
                    <Box display="flex" gap={2} mb={2}>
                      <Chip label={`${a.action} — ${new Date(a.created_at).toLocaleString()}`} size="small" color="primary" variant="outlined" />
                      <Typography variant="body2">vs</Typography>
                      <Chip label={`${b.action} — ${new Date(b.created_at).toLocaleString()}`} size="small" color="secondary" variant="outlined" />
                    </Box>
                    <Box sx={{ maxHeight: 500, overflow: 'auto' }}>
                      {allKeys.map((key) => {
                        const valA = JSON.stringify((a.snapshot || {})[key], null, 2) ?? 'N/A';
                        const valB = JSON.stringify((b.snapshot || {})[key], null, 2) ?? 'N/A';
                        const changed = valA !== valB;
                        return (
                          <Box key={key} sx={{ mb: 2, p: 1.5, bgcolor: changed ? 'warning.50' : 'grey.50', border: changed ? '1px solid' : '1px solid transparent', borderColor: changed ? 'warning.main' : 'transparent', borderRadius: 1 }}>
                            <Typography variant="subtitle2" sx={{ fontWeight: 'bold', mb: 0.5 }}>
                              {key} {changed && <Chip label="modificado" size="small" color="warning" sx={{ ml: 1 }} />}
                            </Typography>
                            <Box display="flex" gap={2}>
                              <Box flex={1}>
                                <Typography variant="caption" color="text.secondary">Version A</Typography>
                                <pre style={{ margin: 0, fontSize: '0.7rem', whiteSpace: 'pre-wrap', wordBreak: 'break-word', backgroundColor: changed ? '#fff3e0' : '#fafafa', padding: 8, borderRadius: 4 }}>
                                  {valA}
                                </pre>
                              </Box>
                              <Box flex={1}>
                                <Typography variant="caption" color="text.secondary">Version B</Typography>
                                <pre style={{ margin: 0, fontSize: '0.7rem', whiteSpace: 'pre-wrap', wordBreak: 'break-word', backgroundColor: changed ? '#e3f2fd' : '#fafafa', padding: 8, borderRadius: 4 }}>
                                  {valB}
                                </pre>
                              </Box>
                            </Box>
                          </Box>
                        );
                      })}
                    </Box>
                  </Box>
                );
              })()}
            </DialogContent>
            <DialogActions>
              <Button onClick={() => setShowDiffDialog(false)}>Cerrar</Button>
            </DialogActions>
          </Dialog>
        </Paper>
      )}

      {tab === 8 && (
        <Paper sx={{ p: 3 }}>
          <Typography variant="h6" gutterBottom>Estado de publicacion por canal</Typography>

          {syncStatuses.length === 0 ? (
            <Typography color="text.secondary">Este producto no ha sido publicado en ningun canal.</Typography>
          ) : (
            <TableContainer component={Paper} variant="outlined" sx={{ mb: 3 }}>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Canal</TableCell>
                    <TableCell>Estado</TableCell>
                    <TableCell>Ultima sync</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {syncStatuses.map((s) => (
                    <TableRow key={s.channel}>
                      <TableCell><Chip label={s.channel} size="small" variant="outlined" /></TableCell>
                      <TableCell>
                        <Chip
                          label={s.status}
                          size="small"
                          color={s.status === 'published' ? 'success' : s.status === 'failed' ? 'error' : 'default'}
                        />
                      </TableCell>
                      <TableCell>
                        {s.synced_at ? new Date(s.synced_at).toLocaleString('es-ES') : '-'}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}

          <Typography variant="h6" gutterBottom sx={{ mt: 2 }}>Historial de sincronizaciones</Typography>
          {syncHistory.length === 0 ? (
            <Typography color="text.secondary">Sin historial de sincronizacion.</Typography>
          ) : (
            <TableContainer component={Paper} variant="outlined">
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Canal</TableCell>
                    <TableCell>Estado</TableCell>
                    <TableCell>Error</TableCell>
                    <TableCell>Fecha</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {syncHistory.map((h) => (
                    <TableRow key={h.id} hover>
                      <TableCell><Chip label={h.channel} size="small" variant="outlined" /></TableCell>
                      <TableCell>
                        <Chip
                          label={h.status}
                          size="small"
                          color={h.status === 'published' ? 'success' : h.status === 'failed' ? 'error' : 'default'}
                        />
                      </TableCell>
                      <TableCell>
                        <Typography variant="caption" color="error">{h.error_message ?? '-'}</Typography>
                      </TableCell>
                      <TableCell>
                        {h.synced_at ? new Date(h.synced_at).toLocaleString('es-ES') : '-'}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          )}
        </Paper>
      )}
    </Box>
  );
}
