import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Button,
  Chip,
  CircularProgress,
  LinearProgress,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Tooltip,
  Typography,
  IconButton,
} from '@mui/material';
import { ChevronLeft, ChevronRight, OpenInNew, Settings } from '@mui/icons-material';
import { useQuery } from '@tanstack/react-query';
import { getQualityReport } from '../../api/quality';
import type { QualityScore } from '../../types/quality';

const DIMENSION_LABELS: Record<string, string> = {
  brand: 'Marca',
  category: 'Categoría',
  seo: 'SEO',
  attributes: 'Atributos',
  media: 'Media',
  i18n: 'Idiomas',
};

function QualityBar({ value }: { value: number }) {
  const color = value >= 80 ? 'success' : value >= 50 ? 'warning' : 'error';
  return (
    <Box display="flex" alignItems="center" gap={1} minWidth={140}>
      <LinearProgress
        variant="determinate"
        value={value}
        color={color}
        sx={{ flexGrow: 1, height: 8, borderRadius: 4 }}
      />
      <Typography variant="body2" sx={{ minWidth: 36, textAlign: 'right' }}>
        {value}%
      </Typography>
    </Box>
  );
}

function DimensionChips({ item }: { item: QualityScore }) {
  return (
    <Box display="flex" flexWrap="wrap" gap={0.5}>
      {Object.entries(item.dimensions).map(([key, val]) => (
        <Tooltip key={key} title={`${DIMENSION_LABELS[key] ?? key}: ${Math.round(val * 100)}%`}>
          <Chip
            label={DIMENSION_LABELS[key] ?? key}
            size="small"
            color={val === 1 ? 'success' : val > 0 ? 'warning' : 'default'}
            variant={val === 0 ? 'outlined' : 'filled'}
          />
        </Tooltip>
      ))}
    </Box>
  );
}

const STATUS_COLORS: Record<string, 'warning' | 'success' | 'error' | 'default'> = {
  draft: 'warning',
  ready: 'success',
  retired: 'error',
};

export default function QualityDashboard() {
  const navigate = useNavigate();
  const [page, setPage] = useState(1);
  const size = 20;

  const { data, isLoading } = useQuery({
    queryKey: ['quality-report', page],
    queryFn: () => getQualityReport(page, size),
  });

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" mt={4}>
        <CircularProgress />
      </Box>
    );
  }

  const items = data?.items ?? [];
  const totalPages = data?.pages ?? 1;

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={1}>
        <Typography variant="h4">Calidad de Datos</Typography>
        <Button
          variant="outlined"
          size="small"
          startIcon={<Settings />}
          onClick={() => navigate('/quality/rules')}
        >
          Reglas
        </Button>
      </Box>
      <Typography variant="body2" color="text.secondary" gutterBottom>
        {data?.total ?? 0} productos
        {data?.active_rule_set
          ? ` · Conjunto activo: ${data.active_rule_set.name}`
          : ' · Score por defecto (media aritmetica)'}
      </Typography>

      <TableContainer component={Paper} sx={{ mt: 2 }}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>SKU</TableCell>
              <TableCell>Estado</TableCell>
              <TableCell>Score</TableCell>
              <TableCell>Dimensiones</TableCell>
              <TableCell />
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
                <TableCell>
                  <Chip
                    label={item.status}
                    size="small"
                    color={STATUS_COLORS[item.status] ?? 'default'}
                  />
                </TableCell>
                <TableCell>
                  <QualityBar value={item.overall} />
                </TableCell>
                <TableCell>
                  <DimensionChips item={item} />
                </TableCell>
                <TableCell>
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
    </Box>
  );
}
