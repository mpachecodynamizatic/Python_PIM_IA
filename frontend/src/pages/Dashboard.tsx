import { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Box,
  Card,
  CardContent,
  Grid,
  Typography,
  CircularProgress,
} from '@mui/material';
import { listProducts } from '../api/products';
import { listCategories } from '../api/categories';

interface Stats {
  totalProducts: number;
  draftProducts: number;
  readyProducts: number;
  totalCategories: number;
}

export default function Dashboard() {
  const navigate = useNavigate();
  const [stats, setStats] = useState<Stats | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchStats() {
      try {
        const [allProducts, drafts, ready, categories] = await Promise.all([
          listProducts({ page: 1, size: 1 }),
          listProducts({ page: 1, size: 1, status: 'draft' }),
          listProducts({ page: 1, size: 1, status: 'ready' }),
          listCategories(),
        ]);
        setStats({
          totalProducts: allProducts.total,
          draftProducts: drafts.total,
          readyProducts: ready.total,
          totalCategories: categories.length,
        });
      } catch {
        // Stats will remain null
      } finally {
        setLoading(false);
      }
    }
    fetchStats();
  }, []);

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" mt={4}>
        <CircularProgress />
      </Box>
    );
  }

  const cards = [
    {
      title: 'Total Productos',
      value: stats?.totalProducts ?? 0,
      color: '#1976d2',
      onClick: () => navigate('/products'),
    },
    {
      title: 'Borradores',
      value: stats?.draftProducts ?? 0,
      color: '#ed6c02',
      onClick: () => navigate('/products?status=draft'),
    },
    {
      title: 'Publicados',
      value: stats?.readyProducts ?? 0,
      color: '#2e7d32',
      onClick: () => navigate('/products?status=ready'),
    },
    {
      title: 'Categorias',
      value: stats?.totalCategories ?? 0,
      color: '#9c27b0',
      onClick: () => navigate('/categories'),
    },
  ];

  return (
    <Box>
      <Typography variant="h4" gutterBottom>
        Mi trabajo hoy
      </Typography>
      <Grid container spacing={3}>
        {cards.map((card) => (
          <Grid size={{ xs: 12, sm: 6, md: 3 }} key={card.title}>
            <Card
              sx={{ cursor: 'pointer', '&:hover': { boxShadow: 6 } }}
              onClick={card.onClick}
            >
              <CardContent>
                <Typography color="text.secondary" gutterBottom>
                  {card.title}
                </Typography>
                <Typography variant="h3" sx={{ color: card.color }}>
                  {card.value}
                </Typography>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>
    </Box>
  );
}
