import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Alert,
  Box,
  Button,
  Checkbox,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  FormControlLabel,
  LinearProgress,
  Paper,
  Typography,
} from '@mui/material';
import { CloudDownload, DataObject, Delete, DeleteForever, Settings } from '@mui/icons-material';
import { useMutation } from '@tanstack/react-query';
import { importFromMysql, purgeAllData, purgeProductsData, seedSampleData } from '../../api/database';
import type { DatabaseOperationResult } from '../../types/database';

export default function DatabaseManager() {
  const navigate = useNavigate();
  const [purgeAllOpen, setPurgeAllOpen] = useState(false);
  const [purgeAllConfirm, setPurgeAllConfirm] = useState(false);
  const [purgeProductsOpen, setPurgeProductsOpen] = useState(false);
  const [result, setResult] = useState<DatabaseOperationResult | null>(null);
  const [error, setError] = useState('');

  const purgeAllMutation = useMutation({
    mutationFn: purgeAllData,
    onSuccess: (data) => {
      setResult(data);
      setPurgeAllOpen(false);
      setPurgeAllConfirm(false);
      setError('');
    },
    onError: (err: unknown) => {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(msg || 'Error al eliminar datos');
    },
  });

  const purgeProductsMutation = useMutation({
    mutationFn: purgeProductsData,
    onSuccess: (data) => {
      setResult(data);
      setPurgeProductsOpen(false);
      setError('');
    },
    onError: (err: unknown) => {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(msg || 'Error al eliminar productos');
    },
  });

  const seedMutation = useMutation({
    mutationFn: seedSampleData,
    onSuccess: (data) => {
      setResult(data);
      setError('');
    },
    onError: (err: unknown) => {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(msg || 'Error al generar datos');
    },
  });

  const importMysqlMutation = useMutation({
    mutationFn: importFromMysql,
    onSuccess: (data) => {
      setResult(data);
      setError('');
    },
    onError: (err: unknown) => {
      const msg = (err as { response?: { data?: { detail?: string } } })?.response?.data?.detail;
      setError(msg || 'Error al importar datos desde MySQL');
    },
  });

  const isPending = purgeAllMutation.isPending || purgeProductsMutation.isPending || seedMutation.isPending || importMysqlMutation.isPending;

  return (
    <Box>
      <Box mb={3}>
        <Typography variant="h4">Gestión de Base de Datos</Typography>
        <Typography variant="body2" color="text.secondary">
          Operaciones administrativas sobre los datos del sistema
        </Typography>
      </Box>

      {error && (
        <Alert severity="error" onClose={() => setError('')} sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {result && (
        <Alert severity="success" onClose={() => setResult(null)} sx={{ mb: 2 }}>
          <Typography variant="subtitle2" gutterBottom>
            Operación completada
          </Typography>
          <Box component="ul" sx={{ m: 0, pl: 2 }}>
            {Object.entries(result).map(([table, count]) => (
              <li key={table}>
                <Typography variant="body2">
                  {table}: {count} registros
                </Typography>
              </li>
            ))}
          </Box>
        </Alert>
      )}

      {isPending && <LinearProgress sx={{ mb: 2 }} />}

      <Box display="flex" flexDirection="column" gap={2}>
        {/* Card 1: Eliminar Todos los Datos */}
        <Paper sx={{ p: 3 }}>
          <Box display="flex" alignItems="flex-start" gap={2}>
            <DeleteForever color="error" sx={{ fontSize: 40, mt: 0.5 }} />
            <Box flex={1}>
              <Typography variant="h6" gutterBottom>
                Eliminar Todos los Datos
              </Typography>
              <Typography variant="body2" color="text.secondary" paragraph>
                Elimina todos los datos excepto usuarios y roles. Esta operación no se puede deshacer.
                Borra productos, categorías, marcas, canales, proveedores, trabajos de sincronización,
                reglas de calidad, auditorías, y todos los demás datos del sistema.
              </Typography>
              <Button
                variant="contained"
                color="error"
                onClick={() => setPurgeAllOpen(true)}
                disabled={isPending}
              >
                Eliminar Todo
              </Button>
            </Box>
          </Box>
        </Paper>

        {/* Card 2: Eliminar Solo Productos */}
        <Paper sx={{ p: 3 }}>
          <Box display="flex" alignItems="flex-start" gap={2}>
            <Delete color="warning" sx={{ fontSize: 40, mt: 0.5 }} />
            <Box flex={1}>
              <Typography variant="h6" gutterBottom>
                Eliminar Productos
              </Typography>
              <Typography variant="body2" color="text.secondary" paragraph>
                Elimina todos los productos y sus datos relacionados: media, traducciones, logística,
                cumplimiento, comentarios, historial de sincronización, y asignaciones de canales/proveedores.
              </Typography>
              <Button
                variant="contained"
                color="warning"
                onClick={() => setPurgeProductsOpen(true)}
                disabled={isPending}
              >
                Eliminar Productos
              </Button>
            </Box>
          </Box>
        </Paper>

        {/* Card 3: Generar Datos de Ejemplo */}
        <Paper sx={{ p: 3 }}>
          <Box display="flex" alignItems="flex-start" gap={2}>
            <DataObject color="success" sx={{ fontSize: 40, mt: 0.5 }} />
            <Box flex={1}>
              <Typography variant="h6" gutterBottom>
                Generar Datos de Ejemplo
              </Typography>
              <Typography variant="body2" color="text.secondary" paragraph>
                Crea datos de prueba para demos y testing: 16 marcas, 6 canales, 10 categorías,
                18 productos (con media, traducciones, SEO), 7 trabajos de sincronización,
                3 conjuntos de reglas de calidad, y taxonomías externas.
              </Typography>
              <Button
                variant="contained"
                color="success"
                onClick={() => seedMutation.mutate()}
                disabled={isPending}
              >
                Generar Datos
              </Button>
            </Box>
          </Box>
        </Paper>

        {/* Card 4: Importar desde MySQL */}
        <Paper sx={{ p: 3 }}>
          <Box display="flex" alignItems="flex-start" gap={2}>
            <CloudDownload color="info" sx={{ fontSize: 40, mt: 0.5 }} />
            <Box flex={1}>
              <Typography variant="h6" gutterBottom>
                Importar desde MySQL
              </Typography>
              <Typography variant="body2" color="text.secondary" paragraph>
                Importa productos desde la base de datos MySQL usando el mapeo de campos configurado.
                Requiere que exista un mapeo activo para 'products' con la tabla MySQL de origen.
                Configura el mapeo en <em>Configurar Mapeo de Campos→MySQL</em> antes de importar.
              </Typography>
              <Button
                variant="contained"
                color="info"
                onClick={() => importMysqlMutation.mutate()}
                disabled={isPending}
                startIcon={<CloudDownload />}
              >
                Importar desde MySQL
              </Button>
            </Box>
          </Box>
        </Paper>

        {/* Card 5: Configurar Mapeo de Campos MySQL */}
        <Paper sx={{ p: 3 }}>
          <Box display="flex" alignItems="flex-start" gap={2}>
            <Settings color="primary" sx={{ fontSize: 40, mt: 0.5 }} />
            <Box flex={1}>
              <Typography variant="h6" gutterBottom>
                Configurar Mapeo de Campos MySQL
              </Typography>
              <Typography variant="body2" color="text.secondary" paragraph>
                Configure cómo se mapean las columnas de la base de datos MySQL a los campos del modelo
                interno. Selecciona la tabla de origen, propone mapeos automáticamente o configúralos
                manualmente. Soporta transformaciones (strip, upper, status_map, fk_resolve, etc.) y
                valores por defecto para cada recurso.
              </Typography>
              <Button
                variant="contained"
                color="primary"
                onClick={() => navigate('/admin/pim-mapping')}
                startIcon={<Settings />}
              >
                Configurar Mapeo
              </Button>
            </Box>
          </Box>
        </Paper>
      </Box>

      {/* Dialog: Confirmar eliminación de todos los datos */}
      <Dialog
        open={purgeAllOpen}
        onClose={() => !purgeAllMutation.isPending && setPurgeAllOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Eliminar Todos los Datos</DialogTitle>
        <DialogContent>
          <Alert severity="warning" sx={{ mb: 2 }}>
            Esta operación eliminará TODOS los datos excepto usuarios y roles.
            <strong> No se puede deshacer.</strong>
          </Alert>
          <Typography paragraph>
            Se eliminarán:
          </Typography>
          <Box component="ul" sx={{ m: 0, pl: 2 }}>
            <li>Todos los productos y sus datos relacionados</li>
            <li>Categorías, marcas, canales, proveedores</li>
            <li>Trabajos de sincronización e historial</li>
            <li>Reglas de calidad y auditorías</li>
            <li>Vistas guardadas y trabajos de importación</li>
            <li>Familias de atributos y taxonomías</li>
          </Box>
          <FormControlLabel
            sx={{ mt: 2 }}
            control={
              <Checkbox
                checked={purgeAllConfirm}
                onChange={(e) => setPurgeAllConfirm(e.target.checked)}
              />
            }
            label="Entiendo que esto eliminará todos los datos"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setPurgeAllOpen(false)} disabled={purgeAllMutation.isPending}>
            Cancelar
          </Button>
          <Button
            variant="contained"
            color="error"
            disabled={!purgeAllConfirm || purgeAllMutation.isPending}
            onClick={() => purgeAllMutation.mutate()}
          >
            {purgeAllMutation.isPending ? 'Eliminando...' : 'Eliminar Todo'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Dialog: Confirmar eliminación de productos */}
      <Dialog
        open={purgeProductsOpen}
        onClose={() => !purgeProductsMutation.isPending && setPurgeProductsOpen(false)}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>Eliminar Productos</DialogTitle>
        <DialogContent>
          <Alert severity="warning" sx={{ mb: 2 }}>
            Esta operación eliminará todos los productos y sus datos relacionados.
            <strong> No se puede deshacer.</strong>
          </Alert>
          <Typography>
            ¿Estás seguro de que quieres eliminar todos los productos del sistema?
            Se eliminarán también todas las traducciones, media, logística, cumplimiento,
            y asignaciones asociadas.
          </Typography>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setPurgeProductsOpen(false)} disabled={purgeProductsMutation.isPending}>
            Cancelar
          </Button>
          <Button
            variant="contained"
            color="warning"
            disabled={purgeProductsMutation.isPending}
            onClick={() => purgeProductsMutation.mutate()}
          >
            {purgeProductsMutation.isPending ? 'Eliminando...' : 'Eliminar Productos'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
