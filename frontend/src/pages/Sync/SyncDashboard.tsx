import { useState } from 'react';
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
  FormControl,
  IconButton,
  InputLabel,
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
import {
  Add,
  ChevronLeft,
  ChevronRight,
  Refresh,
  Replay,
} from '@mui/icons-material';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import { createSyncJob, getChannels, listSyncJobs, retrySyncJob } from '../../api/sync';
import type { SyncJob, SyncJobCreate } from '../../types/sync';

const STATUS_COLORS: Record<string, 'default' | 'info' | 'warning' | 'success' | 'error'> = {
  queued: 'default',
  running: 'info',
  done: 'success',
  failed: 'error',
};

function StatusChip({ status }: { status: string }) {
  return <Chip label={status} size="small" color={STATUS_COLORS[status] ?? 'default'} />;
}

function MetricsSummary({ job }: { job: SyncJob }) {
  const m = job.metrics;
  if (!m || m.total_products === undefined) return <Typography variant="body2">-</Typography>;
  return (
    <Box>
      <Typography variant="body2">
        {m.exported}/{m.total_products} exportados
        {m.skipped > 0 && `, ${m.skipped} omitidos`}
      </Typography>
      {m.errors && m.errors.length > 0 && (
        <Tooltip title={m.errors.join('\n')}>
          <Typography variant="caption" color="error">
            {m.errors.length} error(es)
          </Typography>
        </Tooltip>
      )}
    </Box>
  );
}

function formatDate(val: string | null): string {
  if (!val) return '-';
  return new Date(val).toLocaleString('es-ES', {
    day: '2-digit',
    month: '2-digit',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
    second: '2-digit',
  });
}

export default function SyncDashboard() {
  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const [filterChannel, setFilterChannel] = useState('');
  const [filterStatus, setFilterStatus] = useState('');
  const [dialogOpen, setDialogOpen] = useState(false);
  const [newChannel, setNewChannel] = useState('');
  const [newFilterStatus, setNewFilterStatus] = useState('');
  const [newFilterBrand, setNewFilterBrand] = useState('');
  const size = 20;

  const { data: channels } = useQuery({
    queryKey: ['sync-channels'],
    queryFn: getChannels,
  });

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['sync-jobs', page, filterChannel, filterStatus],
    queryFn: () => listSyncJobs(page, size, filterChannel || undefined, filterStatus || undefined),
    refetchInterval: 5000,
  });

  const createMutation = useMutation({
    mutationFn: (payload: SyncJobCreate) => createSyncJob(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sync-jobs'] });
      setDialogOpen(false);
      setNewChannel('');
      setNewFilterStatus('');
      setNewFilterBrand('');
    },
  });

  const retryMutation = useMutation({
    mutationFn: (jobId: string) => retrySyncJob(jobId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['sync-jobs'] }),
  });

  const handleCreate = () => {
    if (!newChannel) return;
    const filters: Record<string, string> = {};
    if (newFilterStatus) filters.status = newFilterStatus;
    if (newFilterBrand) filters.brand = newFilterBrand;
    createMutation.mutate({ channel: newChannel, filters });
  };

  const items = data?.items ?? [];
  const totalPages = data?.pages ?? 1;

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
        <Typography variant="h4">Sincronizaciones</Typography>
        <Box display="flex" gap={1}>
          <IconButton onClick={() => refetch()}>
            <Refresh />
          </IconButton>
          <Button variant="contained" startIcon={<Add />} onClick={() => setDialogOpen(true)}>
            Nuevo Job
          </Button>
        </Box>
      </Box>

      <Box display="flex" gap={2} mb={2}>
        <FormControl size="small" sx={{ minWidth: 140 }}>
          <InputLabel>Canal</InputLabel>
          <Select
            value={filterChannel}
            label="Canal"
            onChange={(e) => { setFilterChannel(e.target.value); setPage(1); }}
          >
            <MenuItem value="">Todos</MenuItem>
            {(channels ?? []).map((ch) => (
              <MenuItem key={ch} value={ch}>{ch}</MenuItem>
            ))}
          </Select>
        </FormControl>
        <FormControl size="small" sx={{ minWidth: 140 }}>
          <InputLabel>Estado</InputLabel>
          <Select
            value={filterStatus}
            label="Estado"
            onChange={(e) => { setFilterStatus(e.target.value); setPage(1); }}
          >
            <MenuItem value="">Todos</MenuItem>
            <MenuItem value="queued">queued</MenuItem>
            <MenuItem value="running">running</MenuItem>
            <MenuItem value="done">done</MenuItem>
            <MenuItem value="failed">failed</MenuItem>
          </Select>
        </FormControl>
      </Box>

      {isLoading ? (
        <Box display="flex" justifyContent="center" mt={4}>
          <CircularProgress />
        </Box>
      ) : (
        <>
          <TableContainer component={Paper}>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell>Canal</TableCell>
                  <TableCell>Estado</TableCell>
                  <TableCell>Filtros</TableCell>
                  <TableCell>Metricas</TableCell>
                  <TableCell>Iniciado</TableCell>
                  <TableCell>Finalizado</TableCell>
                  <TableCell />
                </TableRow>
              </TableHead>
              <TableBody>
                {items.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={7} align="center">
                      <Typography variant="body2" color="text.secondary">
                        No hay sincronizaciones registradas
                      </Typography>
                    </TableCell>
                  </TableRow>
                )}
                {items.map((job) => (
                  <TableRow key={job.id} hover>
                    <TableCell>
                      <Chip label={job.channel} size="small" variant="outlined" />
                    </TableCell>
                    <TableCell>
                      <StatusChip status={job.status} />
                    </TableCell>
                    <TableCell>
                      <Typography variant="caption">
                        {Object.entries(job.filters || {})
                          .filter(([, v]) => v)
                          .map(([k, v]) => `${k}: ${v}`)
                          .join(', ') || '-'}
                      </Typography>
                    </TableCell>
                    <TableCell>
                      <MetricsSummary job={job} />
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">{formatDate(job.started_at)}</Typography>
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">{formatDate(job.finished_at)}</Typography>
                    </TableCell>
                    <TableCell>
                      {(job.status === 'failed' || job.status === 'done') && (
                        <Tooltip title="Reintentar">
                          <IconButton
                            size="small"
                            onClick={() => retryMutation.mutate(job.id)}
                            disabled={retryMutation.isPending}
                          >
                            <Replay fontSize="small" />
                          </IconButton>
                        </Tooltip>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>

          {items.length > 0 && items.some((j) => j.error_message) && (
            <Box mt={2}>
              {items
                .filter((j) => j.error_message)
                .map((j) => (
                  <Alert key={j.id} severity="error" sx={{ mb: 1 }}>
                    <strong>{j.channel}</strong>: {j.error_message}
                  </Alert>
                ))}
            </Box>
          )}

          <Box display="flex" justifyContent="flex-end" alignItems="center" gap={1} mt={2}>
            <Typography variant="body2">
              Pagina {page} de {totalPages} ({data?.total ?? 0} jobs)
            </Typography>
            <IconButton size="small" disabled={page <= 1} onClick={() => setPage((p) => p - 1)}>
              <ChevronLeft />
            </IconButton>
            <IconButton size="small" disabled={page >= totalPages} onClick={() => setPage((p) => p + 1)}>
              <ChevronRight />
            </IconButton>
          </Box>
        </>
      )}

      {/* Dialog para crear nuevo job */}
      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Nueva Sincronizacion</DialogTitle>
        <DialogContent>
          <Box display="flex" flexDirection="column" gap={2} mt={1}>
            <FormControl fullWidth>
              <InputLabel>Canal</InputLabel>
              <Select
                value={newChannel}
                label="Canal"
                onChange={(e) => setNewChannel(e.target.value)}
              >
                {(channels ?? []).map((ch) => (
                  <MenuItem key={ch} value={ch}>{ch}</MenuItem>
                ))}
              </Select>
            </FormControl>

            <Typography variant="subtitle2" color="text.secondary">
              Filtros de productos (opcional)
            </Typography>

            <FormControl fullWidth size="small">
              <InputLabel>Estado del producto</InputLabel>
              <Select
                value={newFilterStatus}
                label="Estado del producto"
                onChange={(e) => setNewFilterStatus(e.target.value)}
              >
                <MenuItem value="">Todos</MenuItem>
                <MenuItem value="draft">draft</MenuItem>
                <MenuItem value="ready">ready</MenuItem>
                <MenuItem value="retired">retired</MenuItem>
              </Select>
            </FormControl>

            <TextField
              label="Marca"
              size="small"
              value={newFilterBrand}
              onChange={(e) => setNewFilterBrand(e.target.value)}
              placeholder="Filtrar por marca (opcional)"
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>Cancelar</Button>
          <Button
            variant="contained"
            onClick={handleCreate}
            disabled={!newChannel || createMutation.isPending}
          >
            Lanzar
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
