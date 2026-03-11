import { useEffect, useState } from 'react';
import {
  Box,
  Button,
  Checkbox,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Divider,
  FormControlLabel,
  Tooltip,
  Typography,
} from '@mui/material';
import { Download, FileDownload } from '@mui/icons-material';
import { getExportFields, downloadExport, downloadTemplate } from '../api/export';
import type { ExportFieldMeta } from '../types/export';

interface Props {
  open: boolean;
  onClose: () => void;
  resource: string;
  resourceLabel: string;
  /** Active filters from the parent list page, forwarded as export filters */
  filters?: Record<string, unknown>;
  /** Total records matching current filters (shown as informational count) */
  totalRecords?: number;
}

export default function ExportDialog({
  open,
  onClose,
  resource,
  resourceLabel,
  filters = {},
  totalRecords,
}: Props) {
  const [fields, setFields] = useState<ExportFieldMeta[]>([]);
  const [selected, setSelected] = useState<Set<string>>(new Set());
  const [useFilters, setUseFilters] = useState(true);
  const [loading, setLoading] = useState(false);
  const [loadingFields, setLoadingFields] = useState(false);

  // Load field metadata once when dialog opens
  useEffect(() => {
    if (!open) return;
    setLoadingFields(true);
    getExportFields(resource)
      .then((fetched) => {
        setFields(fetched);
        setSelected(new Set(fetched.filter((f) => f.default_include).map((f) => f.key)));
      })
      .catch(() => {})
      .finally(() => setLoadingFields(false));
  }, [open, resource]);

  const toggleField = (key: string) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(key)) next.delete(key);
      else next.add(key);
      return next;
    });
  };

  const selectAll = () => setSelected(new Set(fields.map((f) => f.key)));
  const deselectAll = () => setSelected(new Set());

  const handleExport = async () => {
    setLoading(true);
    try {
      await downloadExport(resource, {
        fields: selected.size > 0 ? [...selected] : null,
        filters: useFilters ? (filters as Record<string, unknown>) : null,
      });
      onClose();
    } catch {
      // Error handled globally by axios interceptor
    } finally {
      setLoading(false);
    }
  };

  const handleTemplate = async () => {
    setLoading(true);
    try {
      await downloadTemplate(resource, selected.size > 0 ? [...selected] : undefined);
    } catch {
    } finally {
      setLoading(false);
    }
  };

  // Split fields into writable and readonly groups
  const writableFields = fields.filter((f) => !f.readonly);
  const readonlyFields = fields.filter((f) => f.readonly);

  return (
    <Dialog open={open} onClose={onClose} maxWidth="sm" fullWidth>
      <DialogTitle>Exportar {resourceLabel}</DialogTitle>
      <DialogContent dividers>
        {loadingFields ? (
          <Box display="flex" justifyContent="center" py={3}>
            <CircularProgress />
          </Box>
        ) : (
          <>
            {/* Field selector */}
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
              <Typography variant="subtitle2">Campos a exportar</Typography>
              <Box>
                <Button size="small" onClick={selectAll}>Todos</Button>
                <Button size="small" onClick={deselectAll}>Ninguno</Button>
              </Box>
            </Box>

            {/* Writable fields */}
            <Box display="flex" flexWrap="wrap" gap={0}>
              {writableFields.map((f) => (
                <FormControlLabel
                  key={f.key}
                  sx={{ width: '50%', m: 0 }}
                  control={
                    <Checkbox
                      size="small"
                      checked={selected.has(f.key)}
                      onChange={() => toggleField(f.key)}
                    />
                  }
                  label={
                    <Typography variant="body2">
                      {f.label}
                      {f.required && (
                        <Typography component="span" color="error" variant="caption"> *</Typography>
                      )}
                    </Typography>
                  }
                />
              ))}
            </Box>

            {readonlyFields.length > 0 && (
              <>
                <Divider sx={{ my: 1 }} />
                <Typography variant="caption" color="text.secondary" sx={{ ml: 1 }}>
                  Campos de solo lectura (solo exportación)
                </Typography>
                <Box display="flex" flexWrap="wrap" gap={0}>
                  {readonlyFields.map((f) => (
                    <FormControlLabel
                      key={f.key}
                      sx={{ width: '50%', m: 0 }}
                      control={
                        <Checkbox
                          size="small"
                          checked={selected.has(f.key)}
                          onChange={() => toggleField(f.key)}
                        />
                      }
                      label={<Typography variant="body2" color="text.secondary">{f.label}</Typography>}
                    />
                  ))}
                </Box>
              </>
            )}

            <Divider sx={{ my: 2 }} />

            {/* Filters option */}
            <FormControlLabel
              control={
                <Checkbox
                  checked={useFilters}
                  onChange={(e) => setUseFilters(e.target.checked)}
                  size="small"
                />
              }
              label={
                <Typography variant="body2">
                  Aplicar filtros activos
                  {useFilters && totalRecords !== undefined && (
                    <Typography component="span" color="text.secondary" variant="caption">
                      {' '}({totalRecords} registros)
                    </Typography>
                  )}
                </Typography>
              }
            />
          </>
        )}
      </DialogContent>
      <DialogActions>
        <Tooltip title="Descargar plantilla vacía con las cabeceras seleccionadas">
          <Button
            startIcon={<FileDownload />}
            onClick={handleTemplate}
            disabled={loading || loadingFields}
            size="small"
          >
            Plantilla vacía
          </Button>
        </Tooltip>
        <Box flex={1} />
        <Button onClick={onClose} disabled={loading}>Cancelar</Button>
        <Button
          variant="contained"
          startIcon={loading ? <CircularProgress size={16} /> : <Download />}
          onClick={handleExport}
          disabled={loading || loadingFields || selected.size === 0}
        >
          Exportar
        </Button>
      </DialogActions>
    </Dialog>
  );
}
