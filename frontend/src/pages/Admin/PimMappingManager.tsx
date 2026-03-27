import { useState, useEffect } from 'react';
import {
  Alert,
  Autocomplete,
  Box,
  Button,
  Chip,
  CircularProgress,
  FormControl,
  FormControlLabel,
  IconButton,
  InputLabel,
  MenuItem,
  Paper,
  Select,
  Switch,
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableRow,
  TextField,
  Tooltip,
  Typography,
} from '@mui/material';
import {
  Add,
  ArrowForward,
  AutoFixHigh,
  CheckCircle,
  CloudDownload,
  Delete,
  Error as ErrorIcon,
  Refresh,
  Save,
  Storage,
} from '@mui/icons-material';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import {
  listAvailableResources,
  getMysqlStatus,
  listMysqlTables,
  getMysqlTableColumns,
  proposeMysqlMapping,
  getInternalFields,
  getMappingByResource,
  createMapping,
  updateMapping,
  importResource,
  type PimFieldMapping,
  type MySQLTableInfo,
  type MySQLColumnInfo,
  type ResourceFieldSchema,
} from '../../api/pimMapping';

export default function PimMappingManager() {
  // ── Estado ────────────────────────────────────────────────────────────────
  const [selectedResource, setSelectedResource] = useState<string>('products');
  const [selectedTable, setSelectedTable] = useState<string>('');
  const [externalFields, setExternalFields] = useState<MySQLColumnInfo[]>([]);
  const [internalFields, setInternalFields] = useState<ResourceFieldSchema[]>([]);
  const [fieldMappings, setFieldMappings] = useState<PimFieldMapping[]>([]);
  const [defaults, setDefaults] = useState<Record<string, any>>({});
  const [transformConfig, setTransformConfig] = useState<Record<string, any>>({});
  const [whereClause, setWhereClause] = useState('');
  const [isActive, setIsActive] = useState(true);
  const [notes, setNotes] = useState('');
  const [error, setError] = useState('');
  const [success, setSuccess] = useState('');

  const queryClient = useQueryClient();

  // ── Conexión MySQL ────────────────────────────────────────────────────────
  const { data: mysqlStatus, refetch: recheckStatus, isFetching: checkingStatus } = useQuery({
    queryKey: ['mysql-status'],
    queryFn: getMysqlStatus,
    staleTime: 30_000,
  });

  const { data: tables = [], isLoading: loadingTables } = useQuery({
    queryKey: ['mysql-tables'],
    queryFn: listMysqlTables,
    enabled: mysqlStatus?.success === true,
  });

  // ── Recursos ──────────────────────────────────────────────────────────────
  const { data: resources = [] } = useQuery({
    queryKey: ['pim-resources'],
    queryFn: listAvailableResources,
  });

  // ── Mapeo guardado ────────────────────────────────────────────────────────
  const { data: currentMapping, isLoading: loadingMapping } = useQuery({
    queryKey: ['pim-mapping', selectedResource],
    queryFn: () => getMappingByResource(selectedResource),
    enabled: !!selectedResource,
  });

  useEffect(() => {
    if (currentMapping) {
      setFieldMappings(currentMapping.mappings);
      setDefaults(currentMapping.defaults);
      const { __mysql_table, ...rest } = currentMapping.transform_config || {};
      setTransformConfig(rest);
      setWhereClause(currentMapping.where_clause || '');
      setIsActive(currentMapping.is_active);
      setNotes(currentMapping.notes || '');
      if (__mysql_table) setSelectedTable(__mysql_table);
    } else {
      setFieldMappings([]);
      setDefaults({});
      setTransformConfig({});
      setWhereClause('');
      setIsActive(true);
      setNotes('');
    }
  }, [currentMapping]);

  // ── Campos internos ───────────────────────────────────────────────────────
  useEffect(() => {
    if (selectedResource) {
      getInternalFields(selectedResource)
        .then(setInternalFields)
        .catch(() => setInternalFields([]));
    }
  }, [selectedResource]);

  // ── Cargar columnas de tabla MySQL ────────────────────────────────────────
  const loadTableColumns = async (tableName: string) => {
    if (!tableName) return;
    try {
      const cols = await getMysqlTableColumns(tableName);
      setExternalFields(cols);
    } catch (e: any) {
      setError(e?.response?.data?.detail || `Error al cargar columnas de '${tableName}'`);
    }
  };

  const handleTableChange = (tableName: string) => {
    setSelectedTable(tableName);
    loadTableColumns(tableName);
  };

  // ── Proponer mapeo ────────────────────────────────────────────────────────
  const proposeMutation = useMutation({
    mutationFn: () => proposeMysqlMapping(selectedTable, selectedResource),
    onSuccess: (proposed) => {
      setFieldMappings(proposed);
      setSuccess(`Se propusieron ${proposed.length} mapeos para la tabla '${selectedTable}'`);
      setTimeout(() => setSuccess(''), 5000);
    },
    onError: (e: any) => {
      setError(e?.response?.data?.detail || 'Error al proponer mapeo');
    },
  });

  // ── Guardar ───────────────────────────────────────────────────────────────
  const saveMutation = useMutation({
    mutationFn: () => {
      const finalTransform = selectedTable
        ? { ...transformConfig, __mysql_table: selectedTable }
        : transformConfig;
      const payload = {
        resource: selectedResource,
        is_active: isActive,
        mappings: fieldMappings,
        defaults,
        transform_config: finalTransform,
        where_clause: whereClause || undefined,
        notes,
      };
      return currentMapping ? updateMapping(selectedResource, payload) : createMapping(payload);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['pim-mapping', selectedResource] });
      setSuccess('Configuración guardada correctamente');
      setTimeout(() => setSuccess(''), 3000);
    },
    onError: (e: any) => {
      setError(e?.response?.data?.detail || 'Error al guardar configuración');
    },
  });

  // ── Importar ──────────────────────────────────────────────────────────────
  const importMutation = useMutation({
    mutationFn: () => importResource(selectedResource),
    onSuccess: (data) => {
      const s = data.stats;
      setSuccess(
        `Importación completada: ${s.created} creados, ${s.updated} actualizados, ` +
          `${s.skipped} omitidos, ${s.errors} errores`,
      );
      setTimeout(() => setSuccess(''), 10_000);
    },
    onError: (e: any) => {
      setError(e?.response?.data?.detail || 'Error al importar desde MySQL');
    },
  });

  // ── CRUD filas mapeo ──────────────────────────────────────────────────────
  const addFieldMapping = () =>
    setFieldMappings([...fieldMappings, { source_field: '', target_field: '', required: false }]);

  const removeFieldMapping = (idx: number) =>
    setFieldMappings(fieldMappings.filter((_, i) => i !== idx));

  const updateFieldMapping = (idx: number, field: string, value: any) => {
    const updated = [...fieldMappings];
    (updated[idx] as any)[field] = value;
    setFieldMappings(updated);
  };

  const canImport =
    !!currentMapping &&
    isActive &&
    !!(currentMapping.transform_config?.__mysql_table || selectedTable);

  return (
    <Box sx={{ p: 3 }}>
      {/* Cabecera */}
      <Box mb={3}>
        <Typography variant="h4" gutterBottom>
          Importación desde MySQL
        </Typography>
        <Typography variant="body2" color="text.secondary">
          Mapea columnas de la base de datos MySQL a los campos del modelo interno y ejecuta la importación
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

      {/* ── Estado MySQL ── */}
      <Paper sx={{ p: 2, mb: 2 }}>
        <Box display="flex" alignItems="center" gap={2} flexWrap="wrap">
          <Storage color="primary" />
          <Typography variant="subtitle1" fontWeight="bold">
            Conexión MySQL
          </Typography>
          {checkingStatus ? (
            <CircularProgress size={20} />
          ) : mysqlStatus?.success ? (
            <Chip
              icon={<CheckCircle />}
              label={`Conectado · ${mysqlStatus.database} @ ${mysqlStatus.host} · v${mysqlStatus.version}`}
              color="success"
              size="small"
            />
          ) : (
            <Chip
              icon={<ErrorIcon />}
              label={mysqlStatus?.error || 'Sin conexión'}
              color="error"
              size="small"
            />
          )}
          <Tooltip title="Volver a comprobar conexión">
            <IconButton size="small" onClick={() => recheckStatus()}>
              <Refresh fontSize="small" />
            </IconButton>
          </Tooltip>
          {!mysqlStatus?.success && (
            <Typography variant="caption" color="text.secondary">
              Configura MYSQL_HOST, MYSQL_PORT, MYSQL_USER, MYSQL_PASSWORD, MYSQL_DATABASE en el .env del servidor
            </Typography>
          )}
        </Box>
      </Paper>

      {/* ── Selección recurso + tabla ── */}
      <Paper sx={{ p: 2, mb: 2 }}>
        <Box display="flex" gap={2} flexWrap="wrap" alignItems="center">
          <FormControl sx={{ minWidth: 200 }}>
            <InputLabel>Recurso destino</InputLabel>
            <Select
              value={selectedResource}
              onChange={(e) => setSelectedResource(e.target.value)}
              label="Recurso destino"
            >
              {resources.map((r) => (
                <MenuItem key={r} value={r}>
                  {r}
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          <FormControl sx={{ minWidth: 260 }}>
            <InputLabel>Tabla MySQL de origen</InputLabel>
            <Select
              value={selectedTable}
              onChange={(e) => handleTableChange(e.target.value)}
              label="Tabla MySQL de origen"
              disabled={!mysqlStatus?.success || loadingTables}
            >
              {loadingTables && (
                <MenuItem disabled>
                  <CircularProgress size={16} sx={{ mr: 1 }} /> Cargando...
                </MenuItem>
              )}
              {(tables as MySQLTableInfo[]).map((t) => (
                <MenuItem key={t.table_name} value={t.table_name}>
                  <Box>
                    <Typography variant="body2">{t.table_name}</Typography>
                    {t.row_count > 0 && (
                      <Typography variant="caption" color="text.secondary">
                        ~{t.row_count.toLocaleString()} filas
                      </Typography>
                    )}
                  </Box>
                </MenuItem>
              ))}
            </Select>
          </FormControl>

          <Tooltip title="Recargar columnas de la tabla seleccionada">
            <span>
              <IconButton onClick={() => loadTableColumns(selectedTable)} disabled={!selectedTable}>
                <Refresh />
              </IconButton>
            </span>
          </Tooltip>

          <Button
            variant="outlined"
            color="secondary"
            startIcon={
              proposeMutation.isPending ? <CircularProgress size={18} /> : <AutoFixHigh />
            }
            onClick={() => proposeMutation.mutate()}
            disabled={!selectedTable || !mysqlStatus?.success || proposeMutation.isPending}
          >
            Proponer Mapeo Automático
          </Button>

          <FormControlLabel
            control={<Switch checked={isActive} onChange={(e) => setIsActive(e.target.checked)} />}
            label="Activo"
          />
        </Box>

        {selectedTable && externalFields.length > 0 && (
          <Box mt={1}>
            <Typography variant="caption" color="text.secondary">
              Tabla: <strong>{selectedTable}</strong> · {externalFields.length} columnas cargadas
            </Typography>
          </Box>
        )}
      </Paper>

      {/* ── Tabla de mapeo ── */}
      {loadingMapping ? (
        <Box display="flex" justifyContent="center" p={4}>
          <CircularProgress />
        </Box>
      ) : (
        <Paper sx={{ p: 3, mb: 2 }}>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={2} flexWrap="wrap" gap={1}>
            <Box>
              <Typography variant="h6">Mapeo de Campos</Typography>
              {(transformConfig.__mysql_table || selectedTable) && (
                <Typography variant="caption" color="text.secondary">
                  <Storage fontSize="inherit" sx={{ verticalAlign: 'middle', mr: 0.5 }} />
                  <strong>{transformConfig.__mysql_table || selectedTable}</strong>
                  <ArrowForward fontSize="inherit" sx={{ verticalAlign: 'middle', mx: 0.5 }} />
                  <strong>{selectedResource}</strong>
                </Typography>
              )}
            </Box>
            <Box display="flex" gap={1} flexWrap="wrap">
              <Button startIcon={<Add />} onClick={addFieldMapping} variant="outlined" size="small">
                Añadir Campo
              </Button>
              <Button
                variant="contained"
                size="small"
                startIcon={saveMutation.isPending ? <CircularProgress size={16} /> : <Save />}
                onClick={() => saveMutation.mutate()}
                disabled={saveMutation.isPending}
              >
                Guardar
              </Button>
              <Tooltip title={!canImport ? 'Guarda primero la configuración con una tabla MySQL seleccionada' : ''}>
                <span>
                  <Button
                    variant="contained"
                    color="success"
                    size="small"
                    startIcon={importMutation.isPending ? <CircularProgress size={16} /> : <CloudDownload />}
                    onClick={() => importMutation.mutate()}
                    disabled={importMutation.isPending || !canImport}
                  >
                    Importar desde MySQL
                  </Button>
                </span>
              </Tooltip>
            </Box>
          </Box>

          <Box sx={{ overflowX: 'auto' }}>
            <Table size="small">
              <TableHead>
                <TableRow>
                  <TableCell width="25%">Columna MySQL (origen)</TableCell>
                  <TableCell width="40px" align="center" />
                  <TableCell width="25%">Campo interno (destino)</TableCell>
                  <TableCell width="14%">Transformación</TableCell>
                  <TableCell width="8%" align="center">Req.</TableCell>
                  <TableCell width="14%">Valor defecto</TableCell>
                  <TableCell width="50px" />
                </TableRow>
              </TableHead>
              <TableBody>
                {fieldMappings.map((mapping, idx) => (
                  <TableRow key={idx} hover>
                    <TableCell>
                      <Autocomplete
                        freeSolo
                        size="small"
                        options={externalFields.map((f) => f.field_path)}
                        value={mapping.source_field}
                        onChange={(_, v) => updateFieldMapping(idx, 'source_field', v || '')}
                        renderOption={(props, option) => {
                          const col = externalFields.find((f) => f.field_path === option);
                          return (
                            <li {...props}>
                              <Box>
                                <Typography variant="body2">{option}</Typography>
                                {col?.sample_value && (
                                  <Typography variant="caption" color="text.secondary">
                                    {col.data_type} · ej: {col.sample_value}
                                  </Typography>
                                )}
                              </Box>
                            </li>
                          );
                        }}
                        renderInput={(params) => <TextField {...params} size="small" />}
                      />
                    </TableCell>
                    <TableCell align="center">
                      <ArrowForward color="primary" fontSize="small" />
                    </TableCell>
                    <TableCell>
                      <Autocomplete
                        freeSolo
                        size="small"
                        options={internalFields.map((f) => f.field_path)}
                        value={mapping.target_field}
                        onChange={(_, v) => updateFieldMapping(idx, 'target_field', v || '')}
                        renderOption={(props, option) => {
                          const f = internalFields.find((x) => x.field_path === option);
                          return (
                            <li {...props}>
                              <Box>
                                <Typography variant="body2">{option}</Typography>
                                {f && (
                                  <Typography variant="caption" color="text.secondary">
                                    {f.label} · {f.data_type}
                                    {f.is_required ? ' · req.' : ''}
                                  </Typography>
                                )}
                              </Box>
                            </li>
                          );
                        }}
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
                        <MenuItem value="status_map">Mapeo Estado</MenuItem>
                        <MenuItem value="brand_code_map">Mapeo Marca</MenuItem>
                        <MenuItem value="fk_resolve">Resolver FK</MenuItem>
                      </Select>
                    </TableCell>
                    <TableCell align="center">
                      <Switch
                        size="small"
                        checked={mapping.required}
                        onChange={(e) => updateFieldMapping(idx, 'required', e.target.checked)}
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
                        <Delete fontSize="small" />
                      </IconButton>
                    </TableCell>
                  </TableRow>
                ))}
                {fieldMappings.length === 0 && (
                  <TableRow>
                    <TableCell colSpan={7} align="center" sx={{ py: 4 }}>
                      <Typography variant="body2" color="text.secondary">
                        {selectedTable
                          ? 'Haz clic en "Proponer Mapeo Automático" o "Añadir Campo".'
                          : 'Selecciona una tabla MySQL y propón el mapeo automático.'}
                      </Typography>
                    </TableCell>
                  </TableRow>
                )}
              </TableBody>
            </Table>
          </Box>
        </Paper>
      )}

      {/* ── Transform Config ── */}
      <Paper sx={{ p: 3, mb: 2 }}>
        <Typography variant="h6" gutterBottom>
          Transform Config (JSON)
        </Typography>
        <Typography variant="caption" color="text.secondary" display="block" mb={1}>
          El campo <code>__mysql_table</code> se gestiona automáticamente al seleccionar la tabla.
          Añade <code>status_map</code>, <code>brand_code_map</code>, etc. según necesites.
        </Typography>
        <TextField
          fullWidth
          multiline
          rows={6}
          value={JSON.stringify(
            selectedTable ? { ...transformConfig, __mysql_table: selectedTable } : transformConfig,
            null,
            2,
          )}
          onChange={(e) => {
            try {
              const parsed = JSON.parse(e.target.value);
              const { __mysql_table, ...rest } = parsed;
              setTransformConfig(rest);
              if (__mysql_table) setSelectedTable(__mysql_table);
              setError('');
            } catch {
              setError('JSON inválido en Transform Config');
            }
          }}
          placeholder='{"status_map": {"ACTIVA": "approved", "FIN EXISTENCIAS": "retired"}}'
        />
      </Paper>

      {/* ── Filtro WHERE ── */}
      <Paper sx={{ p: 3, mb: 2 }}>
        <Typography variant="h6" gutterBottom>
          Filtro WHERE (opcional)
        </Typography>
        <Typography variant="caption" color="text.secondary" display="block" mb={1}>
          Condición SQL para filtrar los registros de la tabla MySQL origen.
          <br />
          <strong>Ejemplos:</strong> <code>estado_referencia = 'ACTIVO'</code>,{' '}
          <code>marca = 'Aspes' AND fecha_creacion &gt;= '2024-01-01'</code>
          <br />
          ⚠️ No incluyas la palabra "WHERE", solo la condición. Usa sintaxis MySQL.
        </Typography>
        <TextField
          fullWidth
          multiline
          rows={2}
          value={whereClause}
          onChange={(e) => setWhereClause(e.target.value)}
          placeholder="estado_referencia = 'ACTIVO' AND categoria IS NOT NULL"
          helperText={whereClause ? `SQL: SELECT * FROM ${selectedTable || 'tabla'} WHERE ${whereClause}` : ''}
        />
      </Paper>

      {/* ── Notas ── */}
      <Paper sx={{ p: 3 }}>
        <Typography variant="h6" gutterBottom>
          Notas
        </Typography>
        <TextField
          fullWidth
          multiline
          rows={3}
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
          placeholder="Descripción del mapeo, observaciones, etc."
        />
      </Paper>
    </Box>
  );
}
