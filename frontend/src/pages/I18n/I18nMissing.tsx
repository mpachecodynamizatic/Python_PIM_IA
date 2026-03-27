import { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import {
  Alert,
  Box,
  Button,
  Chip,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  IconButton,
  MenuItem,
  Paper,
  Select,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  TextField,
  Tooltip,
  Typography,
} from '@mui/material';
import { ChevronLeft, ChevronRight, Edit, OpenInNew } from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  getMissingTranslations,
  listLocales,
  upsertTranslation,
} from '../../api/i18n';
import type { MissingTranslation } from '../../api/i18n';

const COMMON_LOCALES = ['es', 'en', 'fr', 'de', 'pt', 'it'];

const STATUS_COLORS: Record<string, 'warning' | 'success' | 'error' | 'default'> = {
  draft: 'warning',
  ready: 'success',
  retired: 'error',
};

interface TranslateDialogProps {
  open: boolean;
  product: MissingTranslation | null;
  locale: string;
  onClose: () => void;
  onSaved: () => void;
}

function TranslateDialog({ open, product, locale, onClose, onSaved }: TranslateDialogProps) {
  const [title, setTitle] = useState('');
  const [error, setError] = useState('');

  const mutation = useMutation({
    mutationFn: () => upsertTranslation(product!.sku, locale, { title }),
    onSuccess: () => {
      setTitle('');
      onSaved();
    },
    onError: () => setError('Error al guardar la traduccion'),
  });

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>
        Traducir {product?.sku} — {locale.toUpperCase()}
      </DialogTitle>
      <DialogContent>
        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
        <TextField
          autoFocus
          fullWidth
          label="Título"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          sx={{ mt: 1 }}
        />
      </DialogContent>
      <DialogActions>
        <Button onClick={onClose}>Cancelar</Button>
        <Button
          variant="contained"
          disabled={!title.trim() || mutation.isPending}
          onClick={() => mutation.mutate()}
        >
          Guardar
        </Button>
      </DialogActions>
    </Dialog>
  );
}

export default function I18nMissing() {
  const navigate = useNavigate();
  const qc = useQueryClient();
  const [searchParams] = useSearchParams();
  const [locale, setLocale] = useState('es');
  const [page, setPage] = useState(1);
  const [translateTarget, setTranslateTarget] = useState<MissingTranslation | null>(null);
  const [savedMsg, setSavedMsg] = useState('');
  const size = 20;

  const { data: usedLocales = [] } = useQuery({
    queryKey: ['locales'],
    queryFn: listLocales,
  });

  // Aplicar filtro de locale desde URL
  useEffect(() => {
    const localeParam = searchParams.get('locale');
    if (localeParam && localeParam !== locale) {
      setLocale(localeParam);
      setPage(1);
    }
  }, [searchParams]);

  const { data, isLoading } = useQuery({
    queryKey: ['missing-translations', locale, page],
    queryFn: () => getMissingTranslations(locale, page, size),
  });

  const allLocales = Array.from(new Set([...COMMON_LOCALES, ...usedLocales])).sort();
  const items = data?.items ?? [];
  const totalPages = data?.pages ?? 1;

  const handleSaved = () => {
    setTranslateTarget(null);
    setSavedMsg('Traduccion guardada');
    qc.invalidateQueries({ queryKey: ['missing-translations'] });
  };

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Traducciones Pendientes
      </Typography>

      {savedMsg && (
        <Alert severity="success" onClose={() => setSavedMsg('')} sx={{ mb: 2 }}>
          {savedMsg}
        </Alert>
      )}

      <Box display="flex" gap={2} alignItems="center" mb={3}>
        <Typography variant="body1">Locale:</Typography>
        <Select
          size="small"
          value={locale}
          onChange={(e) => { setLocale(e.target.value); setPage(1); }}
          sx={{ minWidth: 120 }}
        >
          {allLocales.map((l) => (
            <MenuItem key={l} value={l}>
              {l.toUpperCase()}
            </MenuItem>
          ))}
        </Select>
        <Typography variant="body2" color="text.secondary">
          {data?.total ?? 0} productos sin traducción en {locale.toUpperCase()}
        </Typography>
      </Box>

      {isLoading ? (
        <Box display="flex" justifyContent="center" mt={4}>
          <CircularProgress />
        </Box>
      ) : items.length === 0 ? (
        <Paper sx={{ p: 3, textAlign: 'center' }}>
          <Typography color="text.secondary">
            Todos los productos tienen traduccion en {locale.toUpperCase()}
          </Typography>
        </Paper>
      ) : (
        <TableContainer component={Paper}>
          <Table size="small">
            <TableHead>
              <TableRow>
                <TableCell>SKU</TableCell>
                <TableCell>Marca</TableCell>
                <TableCell>Estado</TableCell>
                <TableCell align="right">Acciones</TableCell>
              </TableRow>
            </TableHead>
            <TableBody>
              {items.map((item) => (
                <TableRow key={item.sku} hover>
                  <TableCell>
                    <Typography variant="body2" fontWeight={500}>
                      {item.sku}
                    </Typography>
                  </TableCell>
                  <TableCell>{item.brand}</TableCell>
                  <TableCell>
                    <Chip
                      label={item.status}
                      size="small"
                      color={STATUS_COLORS[item.status] ?? 'default'}
                    />
                  </TableCell>
                  <TableCell align="right">
                    <Tooltip title="Traducir">
                      <IconButton size="small" onClick={() => setTranslateTarget(item)}>
                        <Edit fontSize="small" />
                      </IconButton>
                    </Tooltip>
                    <Tooltip title="Ver producto">
                      <IconButton size="small" onClick={() => navigate(`/products/${item.sku}`)}>
                        <OpenInNew fontSize="small" />
                      </IconButton>
                    </Tooltip>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </TableContainer>
      )}

      <Box display="flex" justifyContent="flex-end" alignItems="center" gap={1} mt={2}>
        <Typography variant="body2">
          Página {page} de {totalPages}
        </Typography>
        <IconButton size="small" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
          <ChevronLeft />
        </IconButton>
        <IconButton size="small" disabled={page >= totalPages} onClick={() => setPage((p) => p + 1)}>
          <ChevronRight />
        </IconButton>
      </Box>

      <TranslateDialog
        open={!!translateTarget}
        product={translateTarget}
        locale={locale}
        onClose={() => setTranslateTarget(null)}
        onSaved={handleSaved}
      />
    </Box>
  );
}
