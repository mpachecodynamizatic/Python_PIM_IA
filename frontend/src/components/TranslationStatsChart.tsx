import { Paper, Typography, Box } from '@mui/material';
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
} from 'recharts';
import { useNavigate } from 'react-router-dom';
import type { I18nStats } from '../api/i18n';

interface Props {
  stats: I18nStats;
}

export default function TranslationStatsChart({ stats }: Props) {
  const navigate = useNavigate();

  // Transformar datos para Recharts
  const chartData = stats.locales.map((locale) => {
    const data = stats.by_locale[locale];
    return {
      locale: locale.toUpperCase(),
      Completadas: data.translated,
      Pendientes: data.pending,
    };
  });

  const handleClick = (data: any) => {
    if (data && data.activeLabel) {
      const locale = data.activeLabel.toLowerCase();
      navigate(`/i18n?locale=${locale}`);
    }
  };

  // Si no hay traducciones configuradas
  if (!stats.locales || stats.locales.length === 0) {
    return (
      <Paper sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>
          Estado de Traducciones por Idioma
        </Typography>
        <Typography variant="body2" color="text.secondary" sx={{ textAlign: 'center', py: 4 }}>
          No hay traducciones configuradas en el sistema
        </Typography>
      </Paper>
    );
  }

  return (
    <Paper sx={{ p: 3 }}>
      <Typography variant="h6" gutterBottom>
        Estado de Traducciones por Idioma
      </Typography>
      <Typography variant="body2" color="text.secondary" gutterBottom>
        Click en una barra para ver traducciones pendientes de ese idioma
      </Typography>
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={chartData} onClick={handleClick}>
          <CartesianGrid strokeDasharray="3 3" />
          <XAxis dataKey="locale" />
          <YAxis />
          <Tooltip />
          <Legend />
          <Bar dataKey="Completadas" stackId="a" fill="#4caf50" cursor="pointer" />
          <Bar dataKey="Pendientes" stackId="a" fill="#ff9800" cursor="pointer" />
        </BarChart>
      </ResponsiveContainer>
      <Box mt={2}>
        <Typography variant="caption" color="text.secondary">
          Total de productos: {stats.total_products}
        </Typography>
      </Box>
    </Paper>
  );
}
