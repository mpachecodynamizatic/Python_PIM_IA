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
  const [newFilterStatus, setNewFilterStatus] = useState('');
  const [newFilterBrand, setNewFilterBrand] = useState('');
  const [newMaxRetries, setNewMaxRetries] = useState(3);
  const [newCron, setNewCron] = useState('');

  // Connection override
  const [overrideConn, setOverrideConn] = useState(false);
  const [newConnType, setNewConnType] = useState('');
  // FTP / SSH fields
  const [connHost, setConnHost] = useState('');
  const [connPort, setConnPort] = useState(21);
  const [connUser, setConnUser] = useState('');
  const [connPass, setConnPass] = useState('');
  const [connPath, setConnPath] = useState('/');
  const [connPassive, setConnPassive] = useState(true);
  const [connPrivateKey, setConnPrivateKey] = useState('');
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
      setOverrideConn(false);
      setNewConnType('');
      setConnHost(''); setConnPort(21); setConnUser(''); setConnPass('');
      setConnPath('/'); setConnPassive(true); setConnPrivateKey('');
      setConnUrl(''); setConnAuthType('none'); setConnToken('');
      setConnHttpUser(''); setConnHttpPass('');
      setNewFilterStatus('');
      setNewFilterBrand('');
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
    if (!newChannelId) return;
    const filters: Record<string, string> = {};
    if (newFilterStatus) filters.status = newFilterStatus;
    if (newFilterBrand) filters.brand = newFilterBrand;

    let connection_type: string | null | undefined;
    let connection_config: Record<string, unknown> | undefined;

    if (overrideConn && newConnType) {
      connection_type = newConnType;
      if (newConnType === 'ftp') {
        connection_config = {
          host: connHost, port: connPort, username: connUser, password: connPass,
          remote_path: connPath, passive: connPassive,
        };
      } else if (newConnType === 'ssh') {
        connection_config = {
          host: connHost, port: connPort, username: connUser, password: connPass,
          remote_path: connPath, private_key: connPrivateKey || null,
        };
      } else if (newConnType === 'http_post') {
        connection_config = {
          url: connUrl, auth_type: connAuthType,
          ...(connAuthType === 'bearer' ? { token: connToken } : {}),
          ...(connAuthType === 'basic' ? { username: connHttpUser, password: connHttpPass } : {}),
        };
      }
    }

    createMutation.mutate({
      channel_id: newChannelId,
      filters,
      max_retries: newMaxRetries,
      cron_expression: newCron || null,
      ...(overrideConn && newConnType ? { connection_type, connection_config } : {}),
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
                onChange={(e) => {
                  setNewChannelId(e.target.value);
                  setOverrideConn(false);
                  setNewConnType('');
                }}
              >
                {(channels ?? []).map((ch) => (
                  <MenuItem key={ch.id} value={ch.id}>{ch.name}</MenuItem>
                ))}
              </Select>
            </FormControl>

            {/* Show inherited connection info when a channel is selected */}
            {newChannelId && (() => {
              const sel = (channels ?? []).find((c) => c.id === newChannelId);
              return sel ? (
                <Box sx={{ bgcolor: 'grey.50', border: '1px solid', borderColor: 'divider', borderRadius: 1, p: 1.5 }}>
                  <Typography variant="caption" color="text.secondary">
                    Conexión heredada del canal:
                  </Typography>
                  <Box display="flex" alignItems="center" gap={1} mt={0.5}>
                    <Chip
                      size="small"
                      label={sel.connection_type ?? 'sin configurar'}
                      color={sel.connection_type ? 'primary' : 'default'}
                      variant="outlined"
                    />
                  </Box>
                </Box>
              ) : null;
            })()}

            <FormControlLabel
              control={
                <Switch
                  checked={overrideConn}
                  size="small"
                  onChange={(e) => {
                    setOverrideConn(e.target.checked);
                    if (!e.target.checked) setNewConnType('');
                  }}
                />
              }
              label="Personalizar conexión para este job"
            />

            {overrideConn && (
              <>
                <FormControl fullWidth size="small">
                  <InputLabel>Tipo de conexión</InputLabel>
                  <Select
                    value={newConnType}
                    label="Tipo de conexión"
                    onChange={(e) => setNewConnType(e.target.value)}
                  >
                    <MenuItem value="">-- Heredar del canal --</MenuItem>
                    <MenuItem value="ftp">FTP</MenuItem>
                    <MenuItem value="ssh">SSH / SFTP</MenuItem>
                    <MenuItem value="http_post">HTTP POST</MenuItem>
                  </Select>
                </FormControl>

                {(newConnType === 'ftp' || newConnType === 'ssh') && (
                  <>
                    <Box display="flex" gap={1}>
                      <TextField
                        label="Host"
                        size="small"
                        value={connHost}
                        onChange={(e) => setConnHost(e.target.value)}
                        sx={{ flex: 3 }}
                      />
                      <TextField
                        label="Puerto"
                        size="small"
                        type="number"
                        value={connPort}
                        onChange={(e) => setConnPort(Number(e.target.value))}
                        sx={{ flex: 1 }}
                      />
                    </Box>
                    <Box display="flex" gap={1}>
                      <TextField
                        label="Usuario"
                        size="small"
                        value={connUser}
                        onChange={(e) => setConnUser(e.target.value)}
                        sx={{ flex: 1 }}
                      />
                      <TextField
                        label="Contraseña"
                        size="small"
                        type="password"
                        value={connPass}
                        onChange={(e) => setConnPass(e.target.value)}
                        sx={{ flex: 1 }}
                      />
                    </Box>
                    <TextField
                      label="Ruta remota"
                      size="small"
                      value={connPath}
                      onChange={(e) => setConnPath(e.target.value)}
                      placeholder="/ruta/remota/"
                      fullWidth
                    />
                    {newConnType === 'ftp' && (
                      <FormControlLabel
                        control={<Switch size="small" checked={connPassive} onChange={(e) => setConnPassive(e.target.checked)} />}
                        label="Modo pasivo"
                      />
                    )}
                    {newConnType === 'ssh' && (
                      <TextField
                        label="Clave privada SSH (opcional)"
                        size="small"
                        multiline
                        rows={2}
                        value={connPrivateKey}
                        onChange={(e) => setConnPrivateKey(e.target.value)}
                        placeholder="-----BEGIN RSA PRIVATE KEY-----"
                        fullWidth
                      />
                    )}
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
              </>
            )}

            <Divider />

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

            <Typography variant="subtitle2" color="text.secondary" sx={{ mt: 1 }}>
              Reintentos y programacion
            </Typography>

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
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>Cancelar</Button>
          <Button
            variant="contained"
            onClick={handleCreate}
            disabled={!newChannelId || createMutation.isPending}
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
