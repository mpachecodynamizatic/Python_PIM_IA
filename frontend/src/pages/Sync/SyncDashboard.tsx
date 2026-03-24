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
  Divider,
  FormControl,
  FormControlLabel,
  IconButton,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  Switch,
  Tab,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Tabs,
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
  Schedule,
} from '@mui/icons-material';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  createSyncJob,
  getChannels,
  getChannelSyncHistory,
  listSyncJobs,
  retrySyncJob,
  updateJobSchedule,
} from '../../api/sync';
import type { SyncJob, SyncJobCreate, SyncScheduleUpdate } from '../../types/sync';
import type { Channel } from '../../types/product';

const STATUS_COLORS: Record<string, 'default' | 'info' | 'warning' | 'success' | 'error'> = {
  queued: 'default',
  running: 'info',
  done: 'success',
  failed: 'error',
  retry_pending: 'warning',
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
  const [tabIndex, setTabIndex] = useState(0);
  const [page, setPage] = useState(1);
  const [filterChannel, setFilterChannel] = useState('');
  const [filterStatus, setFilterStatus] = useState('');
  const [dialogOpen, setDialogOpen] = useState(false);
  const [scheduleDialogOpen, setScheduleDialogOpen] = useState(false);
  const [scheduleJobId, setScheduleJobId] = useState('');
  const [cronExpression, setCronExpression] = useState('');

  // ── Create dialog state ──────────────────────────────────────────────────
  const [newChannelId, setNewChannelId] = useState('');
  const [newMaxRetries, setNewMaxRetries] = useState(3);
  const [newCron, setNewCron] = useState('');

  // Connection (always required)
  const [newConnType, setNewConnType] = useState<'script' | 'http_post'>('script');

  // Script fields
  const [scriptPath, setScriptPath] = useState('');
  const [scriptArgs, setScriptArgs] = useState('');
  const [scriptTimeout, setScriptTimeout] = useState(300);

  // HTTP POST fields
  const [connUrl, setConnUrl] = useState('');
  const [connAuthType, setConnAuthType] = useState<'none' | 'basic' | 'bearer'>('none');
  const [connToken, setConnToken] = useState('');
  const [connHttpUser, setConnHttpUser] = useState('');
  const [connHttpPass, setConnHttpPass] = useState('');

  // ── History tab state ────────────────────────────────────────────────────
  const [historyChannelCode, setHistoryChannelCode] = useState('');
  const [historyPage, setHistoryPage] = useState(1);
  const size = 20;

  const { data: channels } = useQuery<Channel[]>({
    queryKey: ['sync-channels'],
    queryFn: getChannels,
  });

  const { data, isLoading, refetch } = useQuery({
    queryKey: ['sync-jobs', page, filterChannel, filterStatus],
    queryFn: () => listSyncJobs(page, size, filterChannel || undefined, filterStatus || undefined),
    refetchInterval: 5000,
  });

  const { data: historyData, isLoading: historyLoading } = useQuery({
    queryKey: ['sync-channel-history', historyChannelCode, historyPage],
    queryFn: () => getChannelSyncHistory(historyChannelCode, historyPage, size),
    enabled: tabIndex === 1 && !!historyChannelCode,
  });

  const createMutation = useMutation({
    mutationFn: (payload: SyncJobCreate) => createSyncJob(payload),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sync-jobs'] });
      setDialogOpen(false);
      setNewChannelId('');
      setNewConnType('script');
      // Reset script fields
      setScriptPath('');
      setScriptArgs('');
      setScriptTimeout(300);
      // Reset HTTP fields
      setConnUrl('');
      setConnAuthType('none');
      setConnToken('');
      setConnHttpUser('');
      setConnHttpPass('');
      setNewMaxRetries(3);
      setNewCron('');
    },
  });

  const retryMutation = useMutation({
    mutationFn: (jobId: string) => retrySyncJob(jobId),
    onSuccess: () => queryClient.invalidateQueries({ queryKey: ['sync-jobs'] }),
  });

  const scheduleMutation = useMutation({
    mutationFn: ({ jobId, data }: { jobId: string; data: SyncScheduleUpdate }) =>
      updateJobSchedule(jobId, data),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['sync-jobs'] });
      setScheduleDialogOpen(false);
    },
  });

  const handleCreate = () => {
    if (!newChannelId || !newConnType) return;

    let connection_config: Record<string, unknown> = {};

    if (newConnType === 'script') {
      connection_config = {
        script_path: scriptPath,
        args: scriptArgs || '',
        timeout: scriptTimeout,
      };
    } else if (newConnType === 'http_post') {
      connection_config = {
        url: connUrl,
        auth_type: connAuthType,
        timeout: 30,
        ...(connAuthType === 'bearer' ? { token: connToken } : {}),
        ...(connAuthType === 'basic' ? { username: connHttpUser, password: connHttpPass } : {}),
      };
    }

    createMutation.mutate({
      channel_id: newChannelId,
      connection_type: newConnType,
      connection_config,
      filters: {},
      max_retries: newMaxRetries,
      cron_expression: newCron || null,
    });
  };

  const openScheduleDialog = (job: SyncJob) => {
    setScheduleJobId(job.id);
    setCronExpression(job.cron_expression ?? '');
    setScheduleDialogOpen(true);
  };

  const items = data?.items ?? [];
  const totalPages = data?.pages ?? 1;
  const historyItems = historyData?.items ?? [];
  const historyTotalPages = historyData?.pages ?? 1;

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

      <Tabs value={tabIndex} onChange={(_, v) => setTabIndex(v)} sx={{ mb: 2 }}>
        <Tab label="Jobs" />
        <Tab label="Historial por canal" />
      </Tabs>

      {/* ==================== TAB 0: Jobs ==================== */}
      {tabIndex === 0 && (
        <>
          <Box display="flex" gap={2} mb={2}>
            <FormControl size="small" sx={{ minWidth: 160 }}>
              <InputLabel>Canal</InputLabel>
              <Select
                value={filterChannel}
                label="Canal"
                onChange={(e) => { setFilterChannel(e.target.value); setPage(1); }}
              >
                <MenuItem value="">Todos</MenuItem>
                {(channels ?? []).map((ch) => (
                  <MenuItem key={ch.id} value={ch.id}>{ch.name}</MenuItem>
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
                <MenuItem value="retry_pending">retry_pending</MenuItem>
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
                      <TableCell>Reintentos</TableCell>
                      <TableCell>Programacion</TableCell>
                      <TableCell>Iniciado</TableCell>
                      <TableCell>Finalizado</TableCell>
                      <TableCell />
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {items.length === 0 && (
                      <TableRow>
                        <TableCell colSpan={9} align="center">
                          <Typography variant="body2" color="text.secondary">
                            No hay sincronizaciones registradas
                          </Typography>
                        </TableCell>
                      </TableRow>
                    )}
                    {items.map((job) => (
                      <TableRow key={job.id} hover>
                        <TableCell>
                          <Chip label={job.channel_name} size="small" variant="outlined" />
                          {job.connection_type && (
                            <Typography variant="caption" color="text.secondary" display="block">
                              {job.connection_type}
                            </Typography>
                          )}
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
                          <Typography variant="body2">
                            {job.retry_count}/{job.max_retries}
                          </Typography>
                          {job.next_retry_at && (
                            <Typography variant="caption" color="warning.main">
                              Reintento: {formatDate(job.next_retry_at)}
                            </Typography>
                          )}
                        </TableCell>
                        <TableCell>
                          {job.scheduled ? (
                            <Box>
                              <Chip label={job.cron_expression ?? 'cron'} size="small" color="primary" variant="outlined" />
                              {job.next_run_at && (
                                <Typography variant="caption" display="block">
                                  Prox: {formatDate(job.next_run_at)}
                                </Typography>
                              )}
                            </Box>
                          ) : (
                            <Typography variant="body2" color="text.secondary">-</Typography>
                          )}
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">{formatDate(job.started_at)}</Typography>
                        </TableCell>
                        <TableCell>
                          <Typography variant="body2">{formatDate(job.finished_at)}</Typography>
                        </TableCell>
                        <TableCell>
                          <Box display="flex" gap={0.5}>
                            {(job.status === 'failed' || job.status === 'done' || job.status === 'retry_pending') && (
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
                            <Tooltip title="Programar">
                              <IconButton
                                size="small"
                                onClick={() => openScheduleDialog(job)}
                              >
                                <Schedule fontSize="small" />
                              </IconButton>
                            </Tooltip>
                          </Box>
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
                        <strong>{j.channel_name}</strong>: {j.error_message}
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
        </>
      )}

      {/* ==================== TAB 1: Historial por canal ==================== */}
      {tabIndex === 1 && (
        <>
          <Box display="flex" gap={2} mb={2}>
            <FormControl size="small" sx={{ minWidth: 180 }}>
              <InputLabel>Canal</InputLabel>
              <Select
                value={historyChannelCode}
                label="Canal"
                onChange={(e) => { setHistoryChannelCode(e.target.value); setHistoryPage(1); }}
              >
                <MenuItem value="">Seleccionar canal</MenuItem>
                {(channels ?? []).map((ch) => (
                  <MenuItem key={ch.code} value={ch.code}>{ch.name}</MenuItem>
                ))}
              </Select>
            </FormControl>
          </Box>

          {!historyChannelCode ? (
            <Typography color="text.secondary">Selecciona un canal para ver el historial de publicaciones.</Typography>
          ) : historyLoading ? (
            <Box display="flex" justifyContent="center" mt={4}><CircularProgress /></Box>
          ) : (
            <>
              <TableContainer component={Paper}>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>SKU</TableCell>
                      <TableCell>Canal</TableCell>
                      <TableCell>Estado</TableCell>
                      <TableCell>Error</TableCell>
                      <TableCell>Fecha sync</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {historyItems.length === 0 && (
                      <TableRow>
                        <TableCell colSpan={5} align="center">
                          <Typography variant="body2" color="text.secondary">Sin registros</Typography>
                        </TableCell>
                      </TableRow>
                    )}
                    {historyItems.map((h) => (
                      <TableRow key={h.id} hover>
                        <TableCell>{h.sku}</TableCell>
                        <TableCell><Chip label={h.channel} size="small" variant="outlined" /></TableCell>
                        <TableCell><StatusChip status={h.status} /></TableCell>
                        <TableCell>
                          <Typography variant="caption" color="error">
                            {h.error_message ?? '-'}
                          </Typography>
                        </TableCell>
                        <TableCell>{formatDate(h.synced_at)}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>

              <Box display="flex" justifyContent="flex-end" alignItems="center" gap={1} mt={2}>
                <Typography variant="body2">
                  Pagina {historyPage} de {historyTotalPages} ({historyData?.total ?? 0} registros)
                </Typography>
                <IconButton size="small" disabled={historyPage <= 1} onClick={() => setHistoryPage((p) => p - 1)}>
                  <ChevronLeft />
                </IconButton>
                <IconButton size="small" disabled={historyPage >= historyTotalPages} onClick={() => setHistoryPage((p) => p + 1)}>
                  <ChevronRight />
                </IconButton>
              </Box>
            </>
          )}
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
                value={newChannelId}
                label="Canal"
                onChange={(e) => setNewChannelId(e.target.value)}
              >
                {(channels ?? []).map((ch) => (
                  <MenuItem key={ch.id} value={ch.id}>{ch.name}</MenuItem>
                ))}
              </Select>
            </FormControl>

            <Divider sx={{ my: 2 }} />

            <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1.5 }}>
              Configuración de conexión
            </Typography>

            <Box display="flex" flexDirection="column" gap={2}>
              <FormControl fullWidth size="small">
                <InputLabel>Tipo de conexión</InputLabel>
                <Select
                  value={newConnType}
                  label="Tipo de conexión"
                  onChange={(e) => setNewConnType(e.target.value as 'script' | 'http_post')}
                >
                  <MenuItem value="script">Script Personalizado</MenuItem>
                  <MenuItem value="http_post">HTTP POST</MenuItem>
                </Select>
              </FormControl>

              {newConnType === 'script' && (
                <>
                  <TextField
                    label="Ruta del script"
                    size="small"
                    value={scriptPath}
                    onChange={(e) => setScriptPath(e.target.value)}
                    placeholder="/ruta/al/script.py o C:\scripts\sync.bat"
                    helperText="Ruta absoluta al script que se ejecutará"
                    fullWidth
                    required
                  />
                  <TextField
                    label="Argumentos adicionales (opcional)"
                    size="small"
                    value={scriptArgs}
                    onChange={(e) => setScriptArgs(e.target.value)}
                    placeholder="--mode sync --verbose"
                    helperText="Argumentos que se pasarán al script"
                    fullWidth
                  />
                  <TextField
                    label="Timeout (segundos)"
                    size="small"
                    type="number"
                    value={scriptTimeout}
                    onChange={(e) => setScriptTimeout(Number(e.target.value))}
                    helperText="Tiempo máximo de ejecución (por defecto 300s)"
                    sx={{ width: 200 }}
                  />
                </>
              )}

              {newConnType === 'http_post' && (
                  <>
                    <TextField
                      label="URL del endpoint"
                      size="small"
                      value={connUrl}
                      onChange={(e) => setConnUrl(e.target.value)}
                      placeholder="https://api.example.com/products"
                      fullWidth
                    />
                    <FormControl fullWidth size="small">
                      <InputLabel>Autenticación</InputLabel>
                      <Select
                        value={connAuthType}
                        label="Autenticación"
                        onChange={(e) => setConnAuthType(e.target.value as 'none' | 'basic' | 'bearer')}
                      >
                        <MenuItem value="none">Sin autenticación</MenuItem>
                        <MenuItem value="basic">Basic (usuario/contraseña)</MenuItem>
                        <MenuItem value="bearer">Bearer token</MenuItem>
                      </Select>
                    </FormControl>
                    {connAuthType === 'bearer' && (
                      <TextField
                        label="Token"
                        size="small"
                        value={connToken}
                        onChange={(e) => setConnToken(e.target.value)}
                        fullWidth
                      />
                    )}
                    {connAuthType === 'basic' && (
                      <Box display="flex" gap={1}>
                        <TextField
                          label="Usuario"
                          size="small"
                          value={connHttpUser}
                          onChange={(e) => setConnHttpUser(e.target.value)}
                          sx={{ flex: 1 }}
                        />
                        <TextField
                          label="Contraseña"
                          size="small"
                          type="password"
                          value={connHttpPass}
                          onChange={(e) => setConnHttpPass(e.target.value)}
                          sx={{ flex: 1 }}
                        />
                      </Box>
                    )}
                  </>
                )}
            </Box>

            <Divider sx={{ my: 2 }} />

            <Typography variant="subtitle2" color="text.secondary" sx={{ mb: 1.5 }}>
              Reintentos y programacion
            </Typography>

            <Box display="flex" flexDirection="column" gap={2}>
              <TextField
                label="Max reintentos"
                size="small"
                type="number"
                value={newMaxRetries}
                onChange={(e) => setNewMaxRetries(Number(e.target.value))}
                inputProps={{ min: 0, max: 10 }}
              />

              <TextField
                label="Expresion cron (opcional)"
                size="small"
                value={newCron}
                onChange={(e) => setNewCron(e.target.value)}
                placeholder="0 */6 * * * (cada 6 horas)"
                helperText="Dejar vacio para ejecucion unica"
              />
            </Box>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>Cancelar</Button>
          <Button
            variant="contained"
            onClick={handleCreate}
            disabled={
              !newChannelId ||
              (newConnType === 'script' && !scriptPath.trim()) ||
              (newConnType === 'http_post' && !connUrl.trim()) ||
              createMutation.isPending
            }
          >
            Lanzar
          </Button>
        </DialogActions>
      </Dialog>

      {/* Dialog para programar job existente */}
      <Dialog open={scheduleDialogOpen} onClose={() => setScheduleDialogOpen(false)} maxWidth="xs" fullWidth>
        <DialogTitle>Programar sincronizacion</DialogTitle>
        <DialogContent>
          <Box display="flex" flexDirection="column" gap={2} mt={1}>
            <TextField
              label="Expresion cron"
              size="small"
              value={cronExpression}
              onChange={(e) => setCronExpression(e.target.value)}
              placeholder="0 */6 * * *"
              helperText="Ej: 0 */6 * * * (cada 6h), 0 0 * * * (diario a medianoche)"
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button
            color="error"
            onClick={() => scheduleMutation.mutate({
              jobId: scheduleJobId,
              data: { cron_expression: null, enabled: false },
            })}
            disabled={scheduleMutation.isPending}
          >
            Desactivar
          </Button>
          <Button onClick={() => setScheduleDialogOpen(false)}>Cancelar</Button>
          <Button
            variant="contained"
            onClick={() => scheduleMutation.mutate({
              jobId: scheduleJobId,
              data: { cron_expression: cronExpression || null, enabled: !!cronExpression },
            })}
            disabled={!cronExpression || scheduleMutation.isPending}
          >
            Guardar
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
