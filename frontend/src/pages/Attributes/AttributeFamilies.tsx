import { useCallback, useEffect, useState } from 'react';
import {
  Alert,
  Box,
  Button,
  Chip,
  Collapse,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Divider,
  FormControlLabel,
  IconButton,
  MenuItem,
  Paper,
  Switch,
  TextField,
  Typography,
} from '@mui/material';
import { Add, ExpandMore, ExpandLess } from '@mui/icons-material';
import {
  listFamilies,
  createFamily,
  listDefinitions,
  addDefinition,
} from '../../api/attributes';
import type {
  AttributeFamily,
  AttributeDefinition,
  AttributeFamilyCreate,
  AttributeDefinitionCreate,
} from '../../api/attributes';
import { listCategories } from '../../api/categories';
import type { Category } from '../../types/category';

const ATTR_TYPES = [
  { value: 'string', label: 'Texto' },
  { value: 'number', label: 'Numero' },
  { value: 'boolean', label: 'Booleano' },
  { value: 'enum', label: 'Lista de opciones' },
];

export default function AttributeFamilies() {
  const [families, setFamilies] = useState<AttributeFamily[]>([]);
  const [categories, setCategories] = useState<Category[]>([]);
  const [expandedId, setExpandedId] = useState<string | null>(null);
  const [definitions, setDefinitions] = useState<Record<string, AttributeDefinition[]>>({});
  const [message, setMessage] = useState('');
  const [errMsg, setErrMsg] = useState('');

  // Dialog crear familia
  const [showCreateFamily, setShowCreateFamily] = useState(false);
  const [newFamily, setNewFamily] = useState<AttributeFamilyCreate>({ code: '', name: '' });

  // Dialog crear definicion
  const [showCreateDef, setShowCreateDef] = useState<string | null>(null);
  const [newDef, setNewDef] = useState<AttributeDefinitionCreate>({
    code: '', label: '', type: 'string', required: false,
  });
  const [newDefOptions, setNewDefOptions] = useState('');

  const refresh = useCallback(async () => {
    try {
      const [fams, cats] = await Promise.all([listFamilies(), listCategories().catch(() => [])]);
      setFamilies(fams);
      setCategories(cats);
    } catch {
      setErrMsg('Error al cargar familias');
    }
  }, []);

  useEffect(() => { refresh(); }, [refresh]);

  const handleToggleExpand = async (familyId: string) => {
    if (expandedId === familyId) {
      setExpandedId(null);
      return;
    }
    setExpandedId(familyId);
    if (!definitions[familyId]) {
      try {
        const defs = await listDefinitions(familyId);
        setDefinitions((prev) => ({ ...prev, [familyId]: defs }));
      } catch {
        setErrMsg('Error al cargar definiciones');
      }
    }
  };

  const handleCreateFamily = async () => {
    if (!newFamily.code.trim() || !newFamily.name.trim()) return;
    try {
      await createFamily(newFamily);
      setShowCreateFamily(false);
      setNewFamily({ code: '', name: '' });
      setMessage('Familia creada');
      await refresh();
    } catch {
      setErrMsg('Error al crear familia');
    }
  };

  const handleCreateDef = async () => {
    if (!showCreateDef || !newDef.code.trim() || !newDef.label.trim()) return;
    try {
      const data: AttributeDefinitionCreate = { ...newDef };
      if (newDef.type === 'enum' && newDefOptions.trim()) {
        const opts = newDefOptions.split(',').map((o) => o.trim()).filter(Boolean);
        data.options_json = JSON.stringify(opts);
      }
      await addDefinition(showCreateDef, data);
      const defs = await listDefinitions(showCreateDef);
      setDefinitions((prev) => ({ ...prev, [showCreateDef]: defs }));
      setShowCreateDef(null);
      setNewDef({ code: '', label: '', type: 'string', required: false });
      setNewDefOptions('');
      setMessage('Atributo añadido');
    } catch {
      setErrMsg('Error al crear atributo');
    }
  };

  const getCategoryName = (id: string | null) => {
    if (!id) return null;
    return categories.find((c) => c.id === id)?.name || id;
  };

  return (
    <Box>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h5">Familias de atributos</Typography>
        <Button variant="contained" startIcon={<Add />} onClick={() => setShowCreateFamily(true)}>
          Nueva familia
        </Button>
      </Box>

      {message && (
        <Alert severity="success" onClose={() => setMessage('')} sx={{ mb: 2 }}>{message}</Alert>
      )}
      {errMsg && (
        <Alert severity="error" onClose={() => setErrMsg('')} sx={{ mb: 2 }}>{errMsg}</Alert>
      )}

      {families.length === 0 ? (
        <Typography color="text.secondary">No hay familias definidas. Crea la primera.</Typography>
      ) : (
        families.map((fam) => {
          const isExpanded = expandedId === fam.id;
          const defs = definitions[fam.id] || [];

          return (
            <Paper key={fam.id} sx={{ mb: 2, overflow: 'hidden' }}>
              <Box
                display="flex"
                justifyContent="space-between"
                alignItems="center"
                sx={{ p: 2, cursor: 'pointer' }}
                onClick={() => handleToggleExpand(fam.id)}
              >
                <Box display="flex" alignItems="center" gap={1.5}>
                  <Typography variant="subtitle1" fontWeight="bold">{fam.name}</Typography>
                  <Chip label={fam.code} size="small" variant="outlined" />
                  {fam.category_id && (
                    <Chip label={getCategoryName(fam.category_id)} size="small" color="info" variant="outlined" />
                  )}
                </Box>
                <IconButton size="small">
                  {isExpanded ? <ExpandLess /> : <ExpandMore />}
                </IconButton>
              </Box>

              <Collapse in={isExpanded}>
                <Divider />
                <Box sx={{ p: 2 }}>
                  {fam.description && (
                    <Typography variant="body2" color="text.secondary" sx={{ mb: 2 }}>
                      {fam.description}
                    </Typography>
                  )}

                  {defs.length === 0 ? (
                    <Typography variant="body2" color="text.secondary">
                      Sin atributos definidos.
                    </Typography>
                  ) : (
                    <Box component="table" sx={{ width: '100%', borderCollapse: 'collapse', '& th, & td': { px: 1.5, py: 1, textAlign: 'left', borderBottom: '1px solid #eee' } }}>
                      <thead>
                        <tr>
                          <th><Typography variant="caption" fontWeight="bold">Codigo</Typography></th>
                          <th><Typography variant="caption" fontWeight="bold">Etiqueta</Typography></th>
                          <th><Typography variant="caption" fontWeight="bold">Tipo</Typography></th>
                          <th><Typography variant="caption" fontWeight="bold">Obligatorio</Typography></th>
                          <th><Typography variant="caption" fontWeight="bold">Opciones</Typography></th>
                        </tr>
                      </thead>
                      <tbody>
                        {defs.map((d) => {
                          let options: string[] = [];
                          if (d.options_json) {
                            try { options = JSON.parse(d.options_json); } catch { /* ignore */ }
                          }
                          return (
                            <tr key={d.id}>
                              <td><Typography variant="body2" fontFamily="monospace">{d.code}</Typography></td>
                              <td><Typography variant="body2">{d.label}</Typography></td>
                              <td><Chip label={ATTR_TYPES.find((t) => t.value === d.type)?.label || d.type} size="small" /></td>
                              <td>{d.required ? <Chip label="Si" size="small" color="error" /> : <Chip label="No" size="small" />}</td>
                              <td>
                                {options.length > 0
                                  ? options.map((o) => <Chip key={o} label={o} size="small" variant="outlined" sx={{ mr: 0.5, mb: 0.5 }} />)
                                  : <Typography variant="caption" color="text.secondary">-</Typography>
                                }
                              </td>
                            </tr>
                          );
                        })}
                      </tbody>
                    </Box>
                  )}

                  <Button
                    size="small"
                    startIcon={<Add />}
                    sx={{ mt: 2 }}
                    onClick={(e) => { e.stopPropagation(); setShowCreateDef(fam.id); }}
                  >
                    Añadir atributo
                  </Button>
                </Box>
              </Collapse>
            </Paper>
          );
        })
      )}

      {/* Dialog crear familia */}
      <Dialog open={showCreateFamily} onClose={() => setShowCreateFamily(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Nueva familia de atributos</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth label="Codigo" margin="normal" size="small"
            value={newFamily.code}
            onChange={(e) => setNewFamily({ ...newFamily, code: e.target.value.toLowerCase().replace(/\s+/g, '_') })}
            helperText="Identificador unico (ej: smartphones, moda)"
          />
          <TextField
            fullWidth label="Nombre" margin="normal" size="small"
            value={newFamily.name}
            onChange={(e) => setNewFamily({ ...newFamily, name: e.target.value })}
          />
          <TextField
            fullWidth label="Descripcion" margin="normal" size="small" multiline rows={2}
            value={newFamily.description || ''}
            onChange={(e) => setNewFamily({ ...newFamily, description: e.target.value || undefined })}
          />
          <TextField
            fullWidth label="Categoria asociada (opcional)" margin="normal" size="small" select
            value={newFamily.category_id || ''}
            onChange={(e) => setNewFamily({ ...newFamily, category_id: e.target.value || undefined })}
          >
            <MenuItem value="">Ninguna</MenuItem>
            {categories.map((c) => (
              <MenuItem key={c.id} value={c.id}>{c.name}</MenuItem>
            ))}
          </TextField>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowCreateFamily(false)}>Cancelar</Button>
          <Button variant="contained" onClick={handleCreateFamily} disabled={!newFamily.code.trim() || !newFamily.name.trim()}>
            Crear
          </Button>
        </DialogActions>
      </Dialog>

      {/* Dialog crear definicion */}
      <Dialog open={showCreateDef !== null} onClose={() => setShowCreateDef(null)} maxWidth="sm" fullWidth>
        <DialogTitle>Añadir atributo</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth label="Codigo" margin="normal" size="small"
            value={newDef.code}
            onChange={(e) => setNewDef({ ...newDef, code: e.target.value.toLowerCase().replace(/\s+/g, '_') })}
            helperText="Identificador (ej: color, peso_kg)"
          />
          <TextField
            fullWidth label="Etiqueta" margin="normal" size="small"
            value={newDef.label}
            onChange={(e) => setNewDef({ ...newDef, label: e.target.value })}
            helperText="Nombre visible (ej: Color, Peso en kg)"
          />
          <TextField
            fullWidth label="Tipo" margin="normal" size="small" select
            value={newDef.type}
            onChange={(e) => setNewDef({ ...newDef, type: e.target.value })}
          >
            {ATTR_TYPES.map((t) => (
              <MenuItem key={t.value} value={t.value}>{t.label}</MenuItem>
            ))}
          </TextField>
          {newDef.type === 'enum' && (
            <TextField
              fullWidth label="Opciones (separadas por coma)" margin="normal" size="small"
              value={newDefOptions}
              onChange={(e) => setNewDefOptions(e.target.value)}
              helperText="Ej: rojo, azul, verde, negro"
            />
          )}
          <FormControlLabel
            control={
              <Switch
                checked={newDef.required}
                onChange={(e) => setNewDef({ ...newDef, required: e.target.checked })}
              />
            }
            label="Obligatorio"
            sx={{ mt: 1 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setShowCreateDef(null)}>Cancelar</Button>
          <Button variant="contained" onClick={handleCreateDef} disabled={!newDef.code.trim() || !newDef.label.trim()}>
            Añadir
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
}
