import { useState, useEffect } from 'react';
import {
  Box,
  Button,
  Paper,
  Typography,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  IconButton,
  TextField,
  Alert,
  Grid,
  Switch,
  FormControlLabel,
  Autocomplete,
  CircularProgress,
} from '@mui/material';
import { Add, Delete, Save, Refresh, ArrowForward } from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  listAvailableResources,
  introspectExternalFields,
  getInternalFields,
  getMappingByResource,
  createMapping,
  updateMapping,
  type PimFieldMapping,
} from '../../api/pimMapping';

export default function PimMappingManager() {
  const [selectedResource, setSelectedResource] = useState<string>('products');
  const [externalFields, setExternalFields] = useState<any[]>([]);
  const [internalFields, setInternalFields] = useState<any[]>([]);
  const [fieldMappings, setFieldMappings] = useState<PimFieldMapping[]>([]);
  const [defaults, setDefaults] = useState<Record<string, any>>({});
  const [transformConfig, setTransformConfig] = useState<Record<string, any>>({});
  const [isActive, setIsActive] = useState(true);
  const [notes, setNotes] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const queryClient = useQueryClient();

  // Load available resources
  const { data: resources } = useQuery({
    queryKey: ['pim-resources'],
    queryFn: listAvailableResources,
  });

  // Load current mapping config
  const { data: currentMapping, isLoading } = useQuery({
    queryKey: ['pim-mapping', selectedResource],
    queryFn: () => getMappingByResource(selectedResource),
    enabled: !!selectedResource,
  });

  useEffect(() => {
    if (currentMapping) {
      setFieldMappings(currentMapping.mappings);
      setDefaults(currentMapping.defaults);
      setTransformConfig(currentMapping.transform_config);
      setIsActive(currentMapping.is_active);
      setNotes(currentMapping.notes || '');
    } else {
      setFieldMappings([]);
      setDefaults({});
      setTransformConfig({});
      setIsActive(true);
      setNotes('');
    }
  }, [currentMapping]);

  // Introspect external PIM fields
  const introspectMutation = useMutation({
    mutationFn: () => introspectExternalFields(selectedResource),
    onSuccess: (data) => {
      setExternalFields(data);
      setSuccess('Campos externos descubiertos correctamente');
      setTimeout(() => setSuccess(''), 3000);
    },
    onError: (err: any) => {
      setError(err.response?.data?.detail || 'Error al descubrir campos externos');
    },
  });

  // Load internal model fields
  useEffect(() => {
    if (selectedResource) {
      getInternalFields(selectedResource)
        .then(setInternalFields)
        .catch((err) => {
          console.error('Error loading internal fields:', err);
          setInternalFields([]);
        });
    }
  }, [selectedResource]);

  // Save mapping
  const saveMutation = useMutation({
    mutationFn: () => {
      const payload = {
        resource: selectedResource,
        is_active: isActive,
        mappings: fieldMappings,
        defaults,
        transform_config: transformConfig,
        notes,
      };
      return currentMapping
        ? updateMapping(selectedResource, payload)
        : createMapping(payload);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pim-mapping', selectedResource] });
      setSuccess('Configuración guardada correctamente');
      setTimeout(() => setSuccess(''), 3000);
    },
    onError: (err: any) => {
      setError(err.response?.data?.detail || 'Error al guardar configuración');
    },
  });

  const addFieldMapping = () => {
    setFieldMappings([
      ...fieldMappings,
      {
        source_field: '',
        target_field: '',
        transform: undefined,
        required: false,
        default_value: undefined,
        fk_config: undefined,
      },
    ]);
  };

  const removeFieldMapping = (index: number) => {
    setFieldMappings(fieldMappings.filter((_, i) => i !== index));
  };

  const updateFieldMapping = (index: number, field: string, value: any) => {
    const updated = [...fieldMappings];
    (updated[index] as any)[field] = value;
    setFieldMappings(updated);
  };

  return (
    <Box sx={{ p: 3 }}>
      <Box mb={3}>
        <Typography variant="h4" gutterBottom>
          Configuración de Mapeo PIM Externo
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Configure el mapeo de campos entre el PIM externo y el sistema interno
        </Typography>
      </Box>

      {error && (
        <Alert severity="error" onClose={() => setError('')} sx={{ mb: 2 }}>
          {error}
        </Alert>
      )}

      {success && (
        <Alert severity="success" onClose={() => setSuccess('')} sx={{ mb: 2 }}>
          {success}
        </Alert>
      )}

      <Grid container spacing={2} mb={3}>
        <Grid item xs={12} md={4}>
          <FormControl fullWidth>
            <InputLabel>Recurso</InputLabel>
            <Select
              value={selectedResource}
              onChange={(e) => setSelectedResource(e.target.value)}
              label="Recurso"
            >
              {resources?.map((r) => (
                <MenuItem key={r} value={r}>
                  {r}
                </MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>

        <Grid item xs={12} md={4}>
          <Button
            variant="outlined"
            startIcon={
              introspectMutation.isPending ? (
                <CircularProgress size={20} />
              ) : (
                <Refresh />
              )
            }
            onClick={() => introspectMutation.mutate()}
            disabled={introspectMutation.isPending}
            fullWidth
            sx={{ height: '56px' }}
          >
            Descubrir Campos Externos
          </Button>
        </Grid>

        <Grid item xs={12} md={4}>
          <FormControlLabel
            control={
              <Switch checked={isActive} onChange={(e) => setIsActive(e.target.checked)} />
            }
            label="Configuración Activa"
            sx={{ height: '56px', display: 'flex', alignItems: 'center', ml: 1 }}
          />
        </Grid>
      </Grid>

      {isLoading ? (
        <Box display="flex" justifyContent="center" p={4}>
          <CircularProgress />
        </Box>
      ) : (
        <>
          <Paper sx={{ p: 3, mb: 3 }}>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="h6">Mapeo de Campos</Typography>
              <Box>
                <Button
                  startIcon={<Add />}
                  onClick={addFieldMapping}
                  sx={{ mr: 1 }}
                  variant="outlined"
                >
                  Añadir Campo
                </Button>
                <Button
                  variant="contained"
                  startIcon={
                    saveMutation.isPending ? <CircularProgress size={20} /> : <Save />
                  }
                  onClick={() => saveMutation.mutate()}
                  disabled={saveMutation.isPending}
                >
                  Guardar Configuración
                </Button>
              </Box>
            </Box>

            <Table>
              <TableHead>
                <TableRow>
                  <TableCell width="25%">Campo Externo</TableCell>
                  <TableCell width="50px" align="center">
                    <ArrowForward fontSize="small" />
                  </TableCell>
                  <TableCell width="25%">Campo Interno</TableCell>
                  <TableCell width="15%">Transformación</TableCell>
                  <TableCell width="10%">Requerido</TableCell>
                  <TableCell width="15%">Valor por Defecto</TableCell>
                  <TableCell width="70px">Acciones</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {fieldMappings.map((mapping, idx) => (
                  <TableRow key={idx}>
                    <TableCell>
                      <Autocomplete
                        freeSolo
                        options={externalFields.map((f) => f.field_path)}
                        value={mapping.source_field}
                        onChange={(_, value) =>
                          updateFieldMapping(idx, 'source_field', value || '')
                        }
                        renderInput={(params) => <TextField {...params} size="small" />}
                      />
                    </TableCell>
                    <TableCell align="center">
                      <ArrowForward color="primary" fontSize="small" />
                    </TableCell>
                    <TableCell>
                      <Autocomplete
                        freeSolo
                        options={internalFields.map((f) => f.field_path)}
                        value={mapping.target_field}
                        onChange={(_, value) =>
                          updateFieldMapping(idx, 'target_field', value || '')
                        }
                        renderInput={(params) => <TextField {...params} size="small" />}
                      />
                    </TableCell>
                    <TableCell>
                      <Select
                        size="small"
                        value={mapping.transform || ''}
                        onChange={(e) =>
                          updateFieldMapping(idx, 'transform', e.target.value || undefined)
                        }
                        displayEmpty
                        fullWidth
                      >
                        <MenuItem value="">Ninguna</MenuItem>
                        <MenuItem value="strip">Strip</MenuItem>
                        <MenuItem value="upper">Mayúsculas</MenuItem>
                        <MenuItem value="lower">Minúsculas</MenuItem>
                        <MenuItem value="int">Entero</MenuItem>
                        <MenuItem value="float">Decimal</MenuItem>
                        <MenuItem value="bool">Booleano</MenuItem>
                        <MenuItem value="status_map">Mapeo de Estado</MenuItem>
                        <MenuItem value="brand_code_map">Mapeo de Marca</MenuItem>
                        <MenuItem value="fk_resolve">Resolver FK</MenuItem>
                      </Select>
                    </TableCell>
                    <TableCell>
                      <Switch
                        checked={mapping.required}
                        onChange={(e) =>
                          updateFieldMapping(idx, 'required', e.target.checked)
                        }
                      />
                    </TableCell>
                    <TableCell>
                      <TextField
                        size="small"
                        value={mapping.default_value || ''}
                        onChange={(e) =>
                          updateFieldMapping(idx, 'default_value', e.target.value || undefined)
                        }
                        fullWidth
                      />
                    </TableCell>
                    <TableCell>
                      <IconButton
                        size="small"
                        onClick={() => removeFieldMapping(idx)}
                        color="error"
                      >
                        <Delete />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                ))}
                {fieldMappings.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={7} align="center">
                      <Typography variant="body2" color="text.secondary">
                        No hay mapeos configurados. Haz clic en "Añadir Campo" para comenzar.
                      </Typography>
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </Paper>

          <Paper sx={{ p: 3 }}>
            <Typography variant="h6" gutterBottom>
              Configuración de Transformaciones
            </Typography>
            <TextField
              fullWidth
              multiline
              rows={6}
              label="Transform Config (JSON)"
              value={JSON.stringify(transformConfig, null, 2)}
              onChange={(e) => {
                try {
                  setTransformConfig(JSON.parse(e.target.value));
                  setError('');
                } catch {
                  setError('JSON inválido en Transform Config');
                }
              }}
              helperText='Ejemplo: {"status_map": {"ACTIVA": "approved"}, "brand_code_map": {"Aspes": "AS"}}'
            />
          </Paper>
        </>
      )}
    </Box>
  );
}
