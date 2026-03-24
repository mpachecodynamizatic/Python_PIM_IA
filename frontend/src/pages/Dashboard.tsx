import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Alert,
  Box,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Divider,
  LinearProgress,
  List,
  ListItem,
  ListItemText,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from '@mui/material';
import {
  Warning,
  CheckCircle,
  Error,
  TrendingUp,
  Image,
  Translate,
  ShoppingCart,
  Schedule,
  ChevronRight,
  Assessment,
  Comment,
  Sync,
} from '@mui/icons-material';
import { PieChart, Pie, Cell, BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer } from 'recharts';
import { getDashboardStats } from '../api/dashboard';
import type { DashboardStats } from '../types/dashboard';

const STATUS_LABELS: Record<string, string> = {
  draft: 'Borrador',
  in_review: 'En revisión',
  approved: 'Aprobado',
  ready: 'Publicado',
  retired: 'Retirado',
};

const STATUS_COLORS: Record<string, string> = {
  draft: '#ed6c02',
  in_review: '#0288d1',
  approved: '#9c27b0',
  ready: '#2e7d32',
  retired: '#d32f2f',
};

export default function Dashboard() {
  const navigate = useNavigate();
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    async function fetchStats() {
      try {
        const data = await getDashboardStats();
        setStats(data);
      } catch {
        setError('Error al cargar estadísticas del dashboard');
      } finally {
        setLoading(false);
      }
    }
    fetchStats();
  }, []);

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="60vh">
        <CircularProgress />
      </Box>
    );
  }

  if (error || !stats) {
    return (
      <Alert severity="error" sx={{ mt: 2 }}>
        {error || 'No se pudieron cargar las estadísticas'}
      </Alert>
    );
  }

  // Preparar datos para gráficos
  const statusChartData = Object.entries(stats.products.by_status).map(([key, value]) => ({
    name: STATUS_LABELS[key] || key,
    value,
    color: STATUS_COLORS[key] || '#999',
  }));

  const qualityChartData = [
    { name: 'Excelente (80-100)', value: Math.max(0, stats.products.total - stats.quality.below_threshold - stats.quality.critical_errors) },
    { name: 'Aceptable (60-79)', value: Math.max(0, stats.quality.below_threshold - stats.quality.critical_errors) },
    { name: 'Crítico (<60)', value: stats.quality.critical_errors },
  ];

  // Contar acciones pendientes
  const pendingActions = [
    stats.quality.critical_errors > 0 && { type: 'critical', count: stats.quality.critical_errors, label: 'productos con calidad crítica', icon: <Error color="error" />, action: () => navigate('/quality') },
    stats.activity.pending_mentions > 0 && { type: 'mentions', count: stats.activity.pending_mentions, label: 'menciones sin leer', icon: <Comment color="info" />, action: () => navigate('/products') },
    stats.sync.channels_error > 0 && { type: 'sync', count: stats.sync.channels_error, label: 'canales con error de sync', icon: <Sync color="error" />, action: () => navigate('/sync') },
    stats.workflow.in_review > 0 && { type: 'review', count: stats.workflow.in_review, label: 'productos en revisión', icon: <Schedule color="warning" />, action: () => navigate('/products?status=in_review') },
  ].filter(Boolean);

  const completenessPercentage = stats.products.total > 0
    ? Math.round(((stats.products.total - stats.products.without_media - stats.products.without_i18n - stats.products.without_channels) / stats.products.total) * 100)
    : 100;

  return (
    <Box>
      {/* Header */}
      <Box mb={3}>
        <Typography variant="h4" gutterBottom>
          Mi trabajo hoy
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Resumen completo de tu catálogo PIM
        </Typography>
      </Box>

      {/* Acciones pendientes */}
      {pendingActions.length > 0 && (
        <Alert severity="warning" icon={<Warning />} sx={{ mb: 3 }}>
          <Typography variant="subtitle2" fontWeight={600} gutterBottom>
            Acciones pendientes
          </Typography>
          <Box display="flex" flexDirection="column" gap={1}>
            {pendingActions.map((action: any, idx) => (
              <Box
                key={idx}
                display="flex"
                alignItems="center"
                gap={1}
                sx={{ cursor: 'pointer', '&:hover': { opacity: 0.7 } }}
                onClick={action.action}
              >
                {action.icon}
                <Typography variant="body2">
                  <strong>{action.count}</strong> {action.label}
                </Typography>
                <ChevronRight fontSize="small" />
              </Box>
            ))}
          </Box>
        </Alert>
      )}

      {/* KPIs principales */}
      <Box display="flex" gap={2} flexWrap="wrap" sx={{ mb: 3 }}>
        <Box sx={{ flex: { xs: '1 1 100%', sm: '1 1 calc(50% - 8px)', md: '1 1 calc(25% - 12px)' } }}>
          <Card sx={{ cursor: 'pointer', '&:hover': { boxShadow: 6 } }} onClick={() => navigate('/products')}>
            <CardContent>
              <Box display="flex" justifyContent="space-between" alignItems="center">
                <Box>
                  <Typography color="text.secondary" variant="caption" display="block">
                    Total Productos
                  </Typography>
                  <Typography variant="h3" sx={{ color: '#1976d2', mt: 1 }}>
                    {stats.products.total}
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    +{stats.coverage.growth_this_month} este mes
                  </Typography>
                </Box>
                <TrendingUp sx={{ fontSize: 48, color: '#1976d2', opacity: 0.3 }} />
              </Box>
            </CardContent>
          </Card>
        </Box>

        <Box sx={{ flex: { xs: '1 1 100%', sm: '1 1 calc(50% - 8px)', md: '1 1 calc(25% - 12px)' } }}>
          <Card sx={{ cursor: 'pointer', '&:hover': { boxShadow: 6 } }} onClick={() => navigate('/quality')}>
            <CardContent>
              <Box display="flex" justifyContent="space-between" alignItems="center">
                <Box>
                  <Typography color="text.secondary" variant="caption" display="block">
                    Score Promedio
                  </Typography>
                  <Typography variant="h3" sx={{ color: stats.quality.avg_score >= 70 ? '#2e7d32' : '#ed6c02', mt: 1 }}>
                    {stats.quality.avg_score}
                    <Typography component="span" variant="h6" color="text.secondary">
                      /100
                    </Typography>
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    Calidad del catálogo
                  </Typography>
                </Box>
                <Assessment sx={{ fontSize: 48, color: '#2e7d32', opacity: 0.3 }} />
              </Box>
            </CardContent>
          </Card>
        </Box>

        <Box sx={{ flex: { xs: '1 1 100%', sm: '1 1 calc(50% - 8px)', md: '1 1 calc(25% - 12px)' } }}>
          <Card sx={{ cursor: 'pointer', '&:hover': { boxShadow: 6 } }} onClick={() => navigate('/products?status=ready')}>
            <CardContent>
              <Box display="flex" justifyContent="space-between" alignItems="center">
                <Box>
                  <Typography color="text.secondary" variant="caption" display="block">
                    % Publicados
                  </Typography>
                  <Typography variant="h3" sx={{ color: '#2e7d32', mt: 1 }}>
                    {stats.products.total > 0 ? Math.round((stats.products.by_status.ready / stats.products.total) * 100) : 0}%
                  </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {stats.products.by_status.ready} de {stats.products.total}
                  </Typography>
                </Box>
                <CheckCircle sx={{ fontSize: 48, color: '#2e7d32', opacity: 0.3 }} />
              </Box>
            </CardContent>
          </Card>
        </Box>

        <Box sx={{ flex: { xs: '1 1 100%', sm: '1 1 calc(50% - 8px)', md: '1 1 calc(25% - 12px)' } }}>
          <Card>
            <CardContent>
              <Box display="flex" justifyContent="space-between" alignItems="center">
                <Box sx={{ width: '100%' }}>
                  <Typography color="text.secondary" variant="caption" display="block">
                    Completitud
                  </Typography>
                  <Typography variant="h3" sx={{ color: completenessPercentage >= 80 ? '#2e7d32' : '#ed6c02', mt: 1 }}>
                    {completenessPercentage}%
                  </Typography>
                  <LinearProgress
                    variant="determinate"
                    value={completenessPercentage}
                    sx={{ mt: 1, height: 6, borderRadius: 3 }}
                  />
                </Box>
              </Box>
            </CardContent>
          </Card>
        </Box>
      </Box>

      {/* Gráficos y estadísticas */}
      <Box display="flex" gap={2} flexWrap="wrap" sx={{ mb: 3 }}>
        {/* Estado del Workflow - Gráfico de Donut */}
        <Box sx={{ flex: { xs: '1 1 100%', md: '1 1 calc(50% - 8px)' } }}>
          <Paper sx={{ p: 2, height: '100%' }}>
            <Typography variant="h6" gutterBottom>
              Estado del Workflow
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={statusChartData}
                  cx="50%"
                  cy="50%"
                  innerRadius={60}
                  outerRadius={100}
                  dataKey="value"
                  label={({ name, value }) => `${name}: ${value}`}
                >
                  {statusChartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Pie>
                <RechartsTooltip />
              </PieChart>
            </ResponsiveContainer>
          </Paper>
        </Box>

        {/* Distribución de Calidad */}
        <Box sx={{ flex: { xs: '1 1 100%', md: '1 1 calc(50% - 8px)' } }}>
          <Paper sx={{ p: 2, height: '100%' }}>
            <Typography variant="h6" gutterBottom>
              Distribución de Calidad
            </Typography>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={qualityChartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" angle={-15} textAnchor="end" height={80} />
                <YAxis />
                <RechartsTooltip />
                <Bar dataKey="value" fill="#1976d2">
                  {qualityChartData.map((_, index) => (
                    <Cell
                      key={`cell-${index}`}
                      fill={index === 0 ? '#2e7d32' : index === 1 ? '#ed6c02' : '#d32f2f'}
                    />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </Paper>
        </Box>
      </Box>

      {/* Completitud de datos */}
      <Box display="flex" gap={2} flexWrap="wrap" sx={{ mb: 3 }}>
        <Box sx={{ flex: { xs: '1 1 100%', md: '1 1 calc(50% - 8px)' } }}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Completitud de Datos
            </Typography>
            <List dense>
              <ListItem
                sx={{ cursor: 'pointer', '&:hover': { bgcolor: 'action.hover' } }}
                onClick={() => navigate('/products')}
              >
                <Image sx={{ mr: 2, color: 'text.secondary' }} />
                <ListItemText
                  primary="Productos sin media"
                  secondary={`${stats.products.without_media} productos (${stats.products.total > 0 ? Math.round((stats.products.without_media / stats.products.total) * 100) : 0}%)`}
                />
                <Chip
                  label={stats.products.without_media}
                  size="small"
                  color={stats.products.without_media === 0 ? 'success' : 'warning'}
                />
              </ListItem>
              <Divider />
              <ListItem
                sx={{ cursor: 'pointer', '&:hover': { bgcolor: 'action.hover' } }}
                onClick={() => navigate('/i18n')}
              >
                <Translate sx={{ mr: 2, color: 'text.secondary' }} />
                <ListItemText
                  primary="Productos sin traducciones"
                  secondary={`${stats.products.without_i18n} productos (${stats.products.total > 0 ? Math.round((stats.products.without_i18n / stats.products.total) * 100) : 0}%)`}
                />
                <Chip
                  label={stats.products.without_i18n}
                  size="small"
                  color={stats.products.without_i18n === 0 ? 'success' : 'warning'}
                />
              </ListItem>
              <Divider />
              <ListItem
                sx={{ cursor: 'pointer', '&:hover': { bgcolor: 'action.hover' } }}
                onClick={() => navigate('/channels')}
              >
                <ShoppingCart sx={{ mr: 2, color: 'text.secondary' }} />
                <ListItemText
                  primary="Productos sin asignar a canal"
                  secondary={`${stats.products.without_channels} productos (${stats.products.total > 0 ? Math.round((stats.products.without_channels / stats.products.total) * 100) : 0}%)`}
                />
                <Chip
                  label={stats.products.without_channels}
                  size="small"
                  color={stats.products.without_channels === 0 ? 'success' : 'warning'}
                />
              </ListItem>
              <Divider />
              <ListItem>
                <Comment sx={{ mr: 2, color: 'text.secondary' }} />
                <ListItemText
                  primary="Comentarios sin resolver"
                  secondary={`${stats.activity.unresolved_comments} comentarios pendientes`}
                />
                <Chip
                  label={stats.activity.unresolved_comments}
                  size="small"
                  color={stats.activity.unresolved_comments === 0 ? 'success' : 'info'}
                />
              </ListItem>
            </List>
          </Paper>
        </Box>

        {/* Top Categorías */}
        <Box sx={{ flex: { xs: '1 1 100%', md: '1 1 calc(50% - 8px)' } }}>
          <Paper sx={{ p: 2 }}>
            <Typography variant="h6" gutterBottom>
              Top Categorías por Volumen
            </Typography>
            {stats.coverage.top_categories.length > 0 ? (
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Categoría</TableCell>
                      <TableCell align="right">Productos</TableCell>
                      <TableCell align="right">%</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {stats.coverage.top_categories.map((cat, idx) => (
                      <TableRow key={idx} hover sx={{ cursor: 'pointer' }} onClick={() => navigate('/categories')}>
                        <TableCell>{cat.name}</TableCell>
                        <TableCell align="right">{cat.count}</TableCell>
                        <TableCell align="right">
                          {stats.products.total > 0 ? Math.round((cat.count / stats.products.total) * 100) : 0}%
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            ) : (
              <Typography variant="body2" color="text.secondary" align="center" sx={{ py: 4 }}>
                No hay categorías con productos
              </Typography>
            )}

            {stats.coverage.empty_categories > 0 && (
              <Alert severity="info" sx={{ mt: 2 }}>
                <Typography variant="body2">
                  <strong>{stats.coverage.empty_categories}</strong> categorías sin productos
                </Typography>
              </Alert>
            )}
          </Paper>
        </Box>
      </Box>

      {/* Actividad Reciente */}
      <Paper sx={{ p: 2 }}>
        <Typography variant="h6" gutterBottom>
          Actividad Reciente
        </Typography>
        <Typography variant="caption" color="text.secondary" display="block" sx={{ mb: 2 }}>
          {stats.activity.edits_today} cambios hoy
        </Typography>
        {stats.activity.recent_activity.length > 0 ? (
          <List dense>
            {stats.activity.recent_activity.slice(0, 10).map((activity, idx) => {
              const timeAgo = activity.created_at
                ? getTimeAgo(new Date(activity.created_at))
                : 'hace un momento';

              const actionLabels: Record<string, string> = {
                create: 'creó',
                update: 'editó',
                delete: 'eliminó',
                transition: 'cambió estado de',
              };

              const resourceLabels: Record<string, string> = {
                product: 'producto',
                category: 'categoría',
                brand: 'marca',
                channel: 'canal',
              };

              return (
                <Box key={idx}>
                  <ListItem>
                    <ListItemText
                      primary={
                        <Typography variant="body2">
                          <Typography component="span" fontWeight={600}>
                            {activity.actor}
                          </Typography>
                          {' '}
                          {actionLabels[activity.action] || activity.action}
                          {' '}
                          <Typography component="span" fontFamily="monospace" color="primary">
                            {resourceLabels[activity.resource] || activity.resource} {activity.resource_id}
                          </Typography>
                        </Typography>
                      }
                      secondary={timeAgo}
                    />
                  </ListItem>
                  {idx < stats.activity.recent_activity.length - 1 && <Divider />}
                </Box>
              );
            })}
          </List>
        ) : (
          <Typography variant="body2" color="text.secondary" align="center" sx={{ py: 4 }}>
            No hay actividad reciente
          </Typography>
        )}
      </Paper>
    </Box>
  );
}

function getTimeAgo(date: Date): string {
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffMins = Math.floor(diffMs / 60000);
  const diffHours = Math.floor(diffMins / 60);
  const diffDays = Math.floor(diffHours / 24);

  if (diffMins < 1) return 'hace un momento';
  if (diffMins < 60) return `hace ${diffMins} min`;
  if (diffHours < 24) return `hace ${diffHours}h`;
  if (diffDays < 7) return `hace ${diffDays}d`;
  return date.toLocaleDateString();
}
