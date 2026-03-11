import { useState } from 'react';
import {
  Accordion,
  AccordionActions,
  AccordionDetails,
  AccordionSummary,
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
  Select,
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
  ArrowDownward,
  ArrowUpward,
  CheckCircle,
  Delete,
  ExpandMore,
  PlayArrow,
  PowerSettingsNew,
} from '@mui/icons-material';
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query';
import {
  activateRuleSet,
  addRule,
  createRuleSet,
  deactivateAllRuleSets,
  deleteRule,
  deleteRuleSet,
  listRuleSets,
  simulateRuleSet,
} from '../../api/quality';
import type { QualityRuleCreate, QualityRuleSetCreate, SimulationResult } from '../../types/quality';

const DIMENSIONS = ['brand', 'category', 'seo', 'attributes', 'media', 'i18n'];
const DIMENSION_LABELS: Record<string, string> = {
  brand: 'Marca',
  category: 'Categoria',
  seo: 'SEO',
  attributes: 'Atributos',
  media: 'Media',
  i18n: 'Idiomas',
};

export default function QualityRulesAdmin() {
  const queryClient = useQueryClient();
  const [createDialogOpen, setCreateDialogOpen] = useState(false);
  const [addRuleDialogOpen, setAddRuleDialogOpen] = useState(false);
  const [targetSetId, setTargetSetId] = useState('');
  // New rule set form
  const [newName, setNewName] = useState('');
  const [newDesc, setNewDesc] = useState('');
  // New rule form
  const [ruleDimension, setRuleDimension] = useState('brand');
  const [ruleWeight, setRuleWeight] = useState('1.0');
  const [ruleMinScore, setRuleMinScore] = useState('0.0');
  const [ruleStatus, setRuleStatus] = useState('');
  // Simulation
  const [simDialogOpen, setSimDialogOpen] = useState(false);
  const [simResult, setSimResult] = useState<SimulationResult | null>(null);
  const [simLoading, setSimLoading] = useState(false);

  const { data: ruleSets, isLoading } = useQuery({
    queryKey: ['quality-rule-sets'],
    queryFn: listRuleSets,
  });

  const invalidate = () => queryClient.invalidateQueries({ queryKey: ['quality-rule-sets'] });

  const createMutation = useMutation({
    mutationFn: (data: QualityRuleSetCreate) => createRuleSet(data),
    onSuccess: () => {
      invalidate();
      setCreateDialogOpen(false);
      setNewName('');
      setNewDesc('');
    },
  });

  const deleteMutation = useMutation({
    mutationFn: (id: string) => deleteRuleSet(id),
    onSuccess: invalidate,
  });

  const activateMutation = useMutation({
    mutationFn: (id: string) => activateRuleSet(id),
    onSuccess: invalidate,
  });

  const deactivateMutation = useMutation({
    mutationFn: () => deactivateAllRuleSets(),
    onSuccess: invalidate,
  });

  const addRuleMutation = useMutation({
    mutationFn: ({ setId, data }: { setId: string; data: QualityRuleCreate }) => addRule(setId, data),
    onSuccess: () => {
      invalidate();
      setAddRuleDialogOpen(false);
      setRuleDimension('brand');
      setRuleWeight('1.0');
      setRuleMinScore('0.0');
      setRuleStatus('');
    },
  });

  const deleteRuleMutation = useMutation({
    mutationFn: (id: string) => deleteRule(id),
    onSuccess: invalidate,
  });

  const handleCreateSet = () => {
    if (!newName.trim()) return;
    createMutation.mutate({ name: newName.trim(), description: newDesc.trim() || null });
  };

  const handleAddRule = () => {
    addRuleMutation.mutate({
      setId: targetSetId,
      data: {
        dimension: ruleDimension,
        weight: parseFloat(ruleWeight) || 1.0,
        min_score: parseFloat(ruleMinScore) || 0.0,
        required_status: ruleStatus || null,
      },
    });
  };

  const handleSimulate = async (ruleSetId: string) => {
    setSimLoading(true);
    setSimDialogOpen(true);
    try {
      const result = await simulateRuleSet(ruleSetId);
      setSimResult(result);
    } finally {
      setSimLoading(false);
    }
  };

  if (isLoading) {
    return (
      <Box display="flex" justifyContent="center" mt={4}>
        <CircularProgress />
      </Box>
    );
  }

  const activeSet = ruleSets?.find((rs) => rs.active);

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
        <Box>
          <Typography variant="h4">Reglas de Calidad</Typography>
          <Typography variant="body2" color="text.secondary">
            Configura conjuntos de reglas con pesos y umbrales por dimension
          </Typography>
        </Box>
        <Button variant="contained" startIcon={<Add />} onClick={() => setCreateDialogOpen(true)}>
          Nuevo Conjunto
        </Button>
      </Box>

      {activeSet ? (
        <Alert severity="info" sx={{ mb: 2 }}>
          Conjunto activo: <strong>{activeSet.name}</strong> ({activeSet.rules.length} reglas)
        </Alert>
      ) : (
        <Alert severity="warning" sx={{ mb: 2 }}>
          Sin conjunto activo — se usa calculo por defecto (media aritmetica sin pesos)
        </Alert>
      )}

      {(!ruleSets || ruleSets.length === 0) && (
        <Typography color="text.secondary" mt={4} textAlign="center">
          No hay conjuntos de reglas. Crea uno para personalizar el calculo de calidad.
        </Typography>
      )}

      {ruleSets?.map((rs) => (
        <Accordion key={rs.id} defaultExpanded={rs.active}>
          <AccordionSummary expandIcon={<ExpandMore />}>
            <Box display="flex" alignItems="center" gap={1} flexGrow={1}>
              <Typography fontWeight={500}>{rs.name}</Typography>
              {rs.active && <Chip label="Activo" size="small" color="success" icon={<CheckCircle />} />}
              <Typography variant="body2" color="text.secondary" sx={{ ml: 1 }}>
                {rs.rules.length} regla(s)
              </Typography>
            </Box>
          </AccordionSummary>
          <AccordionDetails>
            {rs.description && (
              <Typography variant="body2" color="text.secondary" mb={2}>
                {rs.description}
              </Typography>
            )}
            {rs.rules.length > 0 ? (
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>Dimension</TableCell>
                    <TableCell>Peso</TableCell>
                    <TableCell>Score minimo</TableCell>
                    <TableCell>Solo estado</TableCell>
                    <TableCell />
                  </TableRow>
                </TableHead>
                <TableBody>
                  {rs.rules.map((rule) => (
                    <TableRow key={rule.id}>
                      <TableCell>
                        <Chip label={DIMENSION_LABELS[rule.dimension] ?? rule.dimension} size="small" />
                      </TableCell>
                      <TableCell>{rule.weight}</TableCell>
                      <TableCell>{rule.min_score > 0 ? `>= ${rule.min_score}` : '-'}</TableCell>
                      <TableCell>
                        {rule.required_status ? (
                          <Chip label={rule.required_status} size="small" variant="outlined" />
                        ) : (
                          '-'
                        )}
                      </TableCell>
                      <TableCell>
                        <Tooltip title="Eliminar regla">
                          <IconButton
                            size="small"
                            onClick={() => deleteRuleMutation.mutate(rule.id)}
                            disabled={deleteRuleMutation.isPending}
                          >
                            <Delete fontSize="small" />
                          </IconButton>
                        </Tooltip>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            ) : (
              <Typography variant="body2" color="text.secondary">
                Sin reglas definidas. Agrega reglas por dimension.
              </Typography>
            )}
          </AccordionDetails>
          <AccordionActions>
            <Button
              size="small"
              startIcon={<PlayArrow />}
              onClick={() => handleSimulate(rs.id)}
              disabled={rs.rules.length === 0}
            >
              Simular
            </Button>
            <Button
              size="small"
              startIcon={<Add />}
              onClick={() => {
                setTargetSetId(rs.id);
                setAddRuleDialogOpen(true);
              }}
            >
              Agregar Regla
            </Button>
            {!rs.active ? (
              <Button
                size="small"
                color="success"
                startIcon={<PowerSettingsNew />}
                onClick={() => activateMutation.mutate(rs.id)}
                disabled={activateMutation.isPending}
              >
                Activar
              </Button>
            ) : (
              <Button
                size="small"
                color="warning"
                onClick={() => deactivateMutation.mutate()}
                disabled={deactivateMutation.isPending}
              >
                Desactivar
              </Button>
            )}
            <Button
              size="small"
              color="error"
              startIcon={<Delete />}
              onClick={() => deleteMutation.mutate(rs.id)}
              disabled={deleteMutation.isPending}
            >
              Eliminar
            </Button>
          </AccordionActions>
        </Accordion>
      ))}

      {/* Dialog: crear conjunto */}
      <Dialog open={createDialogOpen} onClose={() => setCreateDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Nuevo Conjunto de Reglas</DialogTitle>
        <DialogContent>
          <Box display="flex" flexDirection="column" gap={2} mt={1}>
            <TextField
              label="Nombre"
              value={newName}
              onChange={(e) => setNewName(e.target.value)}
              autoFocus
            />
            <TextField
              label="Descripcion (opcional)"
              value={newDesc}
              onChange={(e) => setNewDesc(e.target.value)}
              multiline
              rows={2}
            />
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setCreateDialogOpen(false)}>Cancelar</Button>
          <Button
            variant="contained"
            onClick={handleCreateSet}
            disabled={!newName.trim() || createMutation.isPending}
          >
            Crear
          </Button>
        </DialogActions>
      </Dialog>

      {/* Dialog: simulacion what-if */}
      <Dialog
        open={simDialogOpen}
        onClose={() => { setSimDialogOpen(false); setSimResult(null); }}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          Simulacion What-If
          {simResult && (
            <Typography variant="body2" color="text.secondary">
              Conjunto: <strong>{simResult.rule_set.name}</strong>
              {simResult.compared_to
                ? ` vs. ${simResult.compared_to.name} (activo)`
                : ' vs. calculo por defecto'}
            </Typography>
          )}
        </DialogTitle>
        <DialogContent>
          {simLoading ? (
            <Box display="flex" justifyContent="center" py={4}>
              <CircularProgress />
            </Box>
          ) : simResult ? (
            <>
              <Alert severity="info" sx={{ mb: 2 }}>
                {simResult.total} productos analizados.
                Media de cambio:{' '}
                {(() => {
                  const avg = simResult.items.length > 0
                    ? simResult.items.reduce((s, i) => s + i.diff, 0) / simResult.items.length
                    : 0;
                  return `${avg >= 0 ? '+' : ''}${avg.toFixed(1)}%`;
                })()}
              </Alert>
              <Table size="small">
                <TableHead>
                  <TableRow>
                    <TableCell>SKU</TableCell>
                    <TableCell>Estado</TableCell>
                    <TableCell>Score Actual</TableCell>
                    <TableCell>Score Simulado</TableCell>
                    <TableCell>Diferencia</TableCell>
                    <TableCell>Violaciones</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {simResult.items.map((item) => (
                    <TableRow key={item.sku}>
                      <TableCell>
                        <Typography variant="body2" fontWeight={500}>{item.sku}</Typography>
                      </TableCell>
                      <TableCell>
                        <Chip label={item.status} size="small" />
                      </TableCell>
                      <TableCell>{item.current_overall}%</TableCell>
                      <TableCell>{item.simulated_overall}%</TableCell>
                      <TableCell>
                        <Box display="flex" alignItems="center" gap={0.5}>
                          {item.diff > 0 && <ArrowUpward fontSize="small" color="success" />}
                          {item.diff < 0 && <ArrowDownward fontSize="small" color="error" />}
                          <Typography
                            variant="body2"
                            color={item.diff > 0 ? 'success.main' : item.diff < 0 ? 'error.main' : 'text.secondary'}
                            fontWeight={500}
                          >
                            {item.diff > 0 ? '+' : ''}{item.diff}%
                          </Typography>
                        </Box>
                      </TableCell>
                      <TableCell>
                        {item.simulated_violations.length > 0
                          ? item.simulated_violations.map((v) => (
                              <Chip
                                key={v}
                                label={DIMENSION_LABELS[v] ?? v}
                                size="small"
                                color="error"
                                variant="outlined"
                                sx={{ mr: 0.5 }}
                              />
                            ))
                          : '-'}
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </>
          ) : null}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => { setSimDialogOpen(false); setSimResult(null); }}>Cerrar</Button>
        </DialogActions>
      </Dialog>

      {/* Dialog: agregar regla */}
      <Dialog open={addRuleDialogOpen} onClose={() => setAddRuleDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Agregar Regla</DialogTitle>
        <DialogContent>
          <Box display="flex" flexDirection="column" gap={2} mt={1}>
            <FormControl fullWidth>
              <InputLabel>Dimension</InputLabel>
              <Select value={ruleDimension} label="Dimension" onChange={(e) => setRuleDimension(e.target.value)}>
                {DIMENSIONS.map((d) => (
                  <MenuItem key={d} value={d}>{DIMENSION_LABELS[d]}</MenuItem>
                ))}
              </Select>
            </FormControl>
            <TextField
              label="Peso"
              type="number"
              value={ruleWeight}
              onChange={(e) => setRuleWeight(e.target.value)}
              inputProps={{ step: 0.5, min: 0.1, max: 10 }}
              helperText="Peso relativo de esta dimension en el overall (defecto: 1.0)"
            />
            <TextField
              label="Score minimo"
              type="number"
              value={ruleMinScore}
              onChange={(e) => setRuleMinScore(e.target.value)}
              inputProps={{ step: 0.1, min: 0, max: 1 }}
              helperText="Si el score base < minimo, la dimension cuenta como 0 (defecto: 0.0)"
            />
            <FormControl fullWidth size="small">
              <InputLabel>Aplica solo a estado (opcional)</InputLabel>
              <Select
                value={ruleStatus}
                label="Aplica solo a estado (opcional)"
                onChange={(e) => setRuleStatus(e.target.value)}
              >
                <MenuItem value="">Todos los estados</MenuItem>
                <MenuItem value="draft">draft</MenuItem>
                <MenuItem value="ready">ready</MenuItem>
                <MenuItem value="retired">retired</MenuItem>
              </Select>
            </FormControl>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setAddRuleDialogOpen(false)}>Cancelar</Button>
          <Button variant="contained" onClick={handleAddRule} disabled={addRuleMutation.isPending}>
            Agregar
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
