import { useCallback, useRef, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Card,
  CardMedia,
  CardContent,
  CardActions,
  Chip,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Grid,
  IconButton,
  TextField,
  Tooltip,
  Typography,
} from '@mui/material';
import { Delete, Link, UploadFile } from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { listMedia, uploadMedia, linkMedia, deleteMedia } from '../../api/media';
import { API_ORIGIN } from '../../api/client';
import type { MediaAsset } from '../../types/media';

export default function MediaLibrary() {
  const qc = useQueryClient();
  const fileRef = useRef<HTMLInputElement>(null);
  const [skuFilter, setSkuFilter] = useState('');
  const [linkDialog, setLinkDialog] = useState<MediaAsset | null>(null);
  const [linkSku, setLinkSku] = useState('');
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');

  const { data: assets = [], isLoading } = useQuery({
    queryKey: ['media', skuFilter],
    queryFn: () => listMedia(skuFilter || undefined),
  });

  const uploadMutation = useMutation({
    mutationFn: (file: File) => uploadMedia(file, skuFilter || undefined),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['media'] });
      setMessage('Archivo subido correctamente');
    },
    onError: () => setError('Error al subir el archivo'),
  });

  const linkMutation = useMutation({
    mutationFn: ({ id, sku }: { id: string; sku: string }) => linkMedia(id, sku),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['media'] });
      setLinkDialog(null);
      setLinkSku('');
      setMessage('Asset vinculado al producto');
    },
    onError: () => setError('Error al vincular'),
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => deleteMedia(id),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: ['media'] });
      setMessage('Asset eliminado');
    },
    onError: () => setError('Error al eliminar'),
  });

  const onFileChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const file = e.target.files?.[0];
      if (file) uploadMutation.mutate(file);
      if (fileRef.current) fileRef.current.value = '';
    },
    [uploadMutation]
  );

  const isImage = (asset: MediaAsset) =>
    asset.kind === 'image' || /\.(jpe?g|png|webp|gif|svg)$/i.test(asset.url);

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Biblioteca de Medios
      </Typography>

      {message && (
        <Alert severity="success" onClose={() => setMessage('')} sx={{ mb: 2 }}>
          {message}
        </Alert>
      )}
      {error && (
        <Alert severity="error" onClose={() => setError('')} sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      <Box display="flex" gap={2} mb={3} alignItems="center">
        <TextField
          label="Filtrar por SKU"
          size="small"
          value={skuFilter}
          onChange={(e) => setSkuFilter(e.target.value)}
          sx={{ width: 240 }}
        />
        <input
          ref={fileRef}
          type="file"
          accept="image/*,video/mp4,application/pdf"
          style={{ display: 'none' }}
          onChange={onFileChange}
        />
        <Button
          variant="contained"
          startIcon={<UploadFile />}
          onClick={() => fileRef.current?.click()}
          disabled={uploadMutation.isPending}
        >
          {uploadMutation.isPending ? 'Subiendo...' : 'Subir archivo'}
        </Button>
        <Typography variant="body2" color="text.secondary">
          {assets.length} assets
        </Typography>
      </Box>

      {isLoading ? (
        <Box display="flex" justifyContent="center" mt={4}>
          <CircularProgress />
        </Box>
      ) : assets.length === 0 ? (
        <Typography color="text.secondary">No hay assets. Sube el primero.</Typography>
      ) : (
        <Grid container spacing={2}>
          {assets.map((asset) => (
            <Grid key={asset.id} size={{ xs: 12, sm: 6, md: 4, lg: 3 }}>
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
                  <Box
                    height={160}
                    display="flex"
                    alignItems="center"
                    justifyContent="center"
                    bgcolor="grey.100"
                  >
                    <Typography variant="h6" color="text.secondary">
                      {asset.kind.toUpperCase()}
                    </Typography>
                  </Box>
                )}
                <CardContent sx={{ pb: 0 }}>
                  <Typography variant="body2" noWrap title={asset.filename || asset.url}>
                    {asset.filename || asset.url}
                  </Typography>
                  {asset.sku && (
                    <Chip label={`SKU: ${asset.sku}`} size="small" sx={{ mt: 0.5 }} />
                  )}
                </CardContent>
                <CardActions>
                  <Tooltip title="Vincular a producto">
                    <IconButton size="small" onClick={() => { setLinkDialog(asset); setLinkSku(asset.sku || ''); }}>
                      <Link />
                    </IconButton>
                  </Tooltip>
                  <Tooltip title="Eliminar">
                    <IconButton
                      size="small"
                      color="error"
                      onClick={() => deleteMutation.mutate(asset.id)}
                      disabled={deleteMutation.isPending}
                    >
                      <Delete />
                    </IconButton>
                  </Tooltip>
                </CardActions>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      {/* Link dialog */}
      <Dialog open={!!linkDialog} onClose={() => setLinkDialog(null)}>
        <DialogTitle>Vincular a producto</DialogTitle>
        <DialogContent>
          <TextField
            autoFocus
            fullWidth
            label="SKU del producto"
            value={linkSku}
            onChange={(e) => setLinkSku(e.target.value)}
            sx={{ mt: 1 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setLinkDialog(null)}>Cancelar</Button>
          <Button
            variant="contained"
            disabled={!linkSku.trim() || linkMutation.isPending}
            onClick={() => linkDialog && linkMutation.mutate({ id: linkDialog.id, sku: linkSku.trim() })}
          >
            Vincular
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
