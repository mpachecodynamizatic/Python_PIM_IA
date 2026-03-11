import { useRef, useState } from 'react';
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
  Paper,
  Step,
  StepLabel,
  Stepper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Typography,
} from '@mui/material';
import { CheckCircle, CloudUpload, FileDownload, Warning } from '@mui/icons-material';
import { validateImport, applyImport, downloadTemplate } from '../api/export';
import type { ImportValidationResult, ImportResult } from '../types/export';

interface Props {
  open: boolean;
  onClose: () => void;
  resource: string;
  resourceLabel: string;
  onSuccess?: () => void;
}

const STEPS = ['Seleccionar fichero', 'Validación', 'Resultado'];

export default function ImportDialog({
  open,
  onClose,
  resource,
  resourceLabel,
  onSuccess,
}: Props) {
  const [step, setStep] = useState(0);
  const [file, setFile] = useState<File | null>(null);
  const [validation, setValidation] = useState<ImportValidationResult | null>(null);
  const [result, setResult] = useState<ImportResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const fileInputRef = useRef<HTMLInputElement>(null);

  const reset = () => {
    setStep(0);
    setFile(null);
    setValidation(null);
    setResult(null);
    setError('');
  };

  const handleClose = () => {
    reset();
    onClose();
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const f = e.target.files?.[0] ?? null;
    setFile(f);
    setError('');
  };

  // Step 1 → Step 2: validate
  const handleValidate = async () => {
    if (!file) return;
    setLoading(true);
    setError('');
    try {
      const res = await validateImport(resource, file);
      setValidation(res);
      setStep(1);
    } catch {
      setError('Error al validar el fichero. Comprueba que es un .xlsx válido.');
    } finally {
      setLoading(false);
    }
  };

  // Step 2 → Step 3: apply
  const handleApply = async () => {
    if (!file) return;
    setLoading(true);
    setError('');
    try {
      const res = await applyImport(resource, file);
      setResult(res);
      setStep(2);
      onSuccess?.();
    } catch (err: unknown) {
      const msg = (err as { response?: { data?: { detail?: { message?: string } } } })
        ?.response?.data?.detail?.message;
      setError(msg || 'Error al importar. Revisa los errores de validación.');
    } finally {
      setLoading(false);
    }
  };

  const handleTemplate = () => downloadTemplate(resource);

  const warningCount = validation?.warnings.length ?? 0;
  const errorCount = validation?.errors.length ?? 0;

  return (
    <Dialog open={open} onClose={handleClose} maxWidth="md" fullWidth>
      <DialogTitle>Importar {resourceLabel}</DialogTitle>
      <DialogContent dividers>
        <Stepper activeStep={step} sx={{ mb: 3 }}>
          {STEPS.map((label) => (
            <Step key={label}>
              <StepLabel>{label}</StepLabel>
            </Step>
          ))}
        </Stepper>

        {/* ── Step 0: File selection ── */}
        {step === 0 && (
          <Box>
            <Alert severity="info" sx={{ mb: 2 }}>
              Sube un fichero <strong>.xlsx</strong> con las columnas del recurso{' '}
              <strong>{resourceLabel}</strong>.{' '}
              <Button
                size="small"
                startIcon={<FileDownload />}
                onClick={handleTemplate}
                sx={{ ml: 1 }}
              >
                Descargar plantilla
              </Button>
            </Alert>

            {/* Dropzone */}
            <Paper
              variant="outlined"
              sx={{
                p: 4,
                textAlign: 'center',
                cursor: 'pointer',
                borderStyle: 'dashed',
                borderColor: file ? 'primary.main' : 'divider',
                '&:hover': { borderColor: 'primary.main', bgcolor: 'action.hover' },
              }}
              onClick={() => fileInputRef.current?.click()}
            >
              <CloudUpload sx={{ fontSize: 48, color: 'text.secondary', mb: 1 }} />
              {file ? (
                <Typography variant="body1" color="primary">
                  {file.name} ({(file.size / 1024).toFixed(1)} KB)
                </Typography>
              ) : (
                <Typography variant="body1" color="text.secondary">
                  Haz clic o arrastra aquí tu fichero .xlsx
                </Typography>
              )}
              <input
                ref={fileInputRef}
                type="file"
                accept=".xlsx"
                hidden
                onChange={handleFileChange}
              />
            </Paper>

            {error && (
              <Alert severity="error" sx={{ mt: 2 }}>
                {error}
              </Alert>
            )}
          </Box>
        )}

        {/* ── Step 1: Validation report ── */}
        {step === 1 && validation && (
          <Box>
            {/* Summary chips */}
            <Box display="flex" gap={1} mb={2} flexWrap="wrap">
              <Chip label={`Total: ${validation.total}`} />
              <Chip label={`Válidos: ${validation.valid}`} color="success" />
              {errorCount > 0 && (
                <Chip
                  label={`${errorCount} error${errorCount > 1 ? 'es' : ''}`}
                  color="error"
                  icon={<Warning />}
                />
              )}
              {warningCount > 0 && (
                <Chip
                  label={`${warningCount} aviso${warningCount > 1 ? 's' : ''}`}
                  color="warning"
                />
              )}
            </Box>

            {validation.has_blocking_errors && (
              <Alert severity="error" sx={{ mb: 2 }}>
                El fichero contiene errores bloqueantes. Corrígelos y vuelve a validar.
              </Alert>
            )}

            {/* Error table */}
            {validation.errors.length > 0 && (
              <>
                <Typography variant="subtitle2" mb={1}>Errores y avisos</Typography>
                <TableContainer component={Paper} variant="outlined" sx={{ mb: 2, maxHeight: 240 }}>
                  <Table size="small" stickyHeader>
                    <TableHead>
                      <TableRow>
                        <TableCell>Fila</TableCell>
                        <TableCell>Campo</TableCell>
                        <TableCell>Código</TableCell>
                        <TableCell>Descripción</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {validation.errors.map((e, i) => (
                        <TableRow key={i} sx={{ bgcolor: e.code.startsWith('error_') ? 'error.50' : 'warning.50' }}>
                          <TableCell>{e.row}</TableCell>
                          <TableCell>{e.field_key}</TableCell>
                          <TableCell>
                            <Chip
                              label={e.code}
                              size="small"
                              color={e.code.startsWith('error_') ? 'error' : 'warning'}
                            />
                          </TableCell>
                          <TableCell>{e.message}</TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </>
            )}

            {/* Preview table */}
            {validation.preview.length > 0 && (
              <>
                <Typography variant="subtitle2" mb={1}>
                  Vista previa (primeras {validation.preview.length} filas)
                </Typography>
                <TableContainer component={Paper} variant="outlined" sx={{ maxHeight: 200 }}>
                  <Table size="small" stickyHeader>
                    <TableHead>
                      <TableRow>
                        <TableCell>Fila</TableCell>
                        <TableCell>Modo</TableCell>
                        <TableCell>Identificador</TableCell>
                      </TableRow>
                    </TableHead>
                    <TableBody>
                      {validation.preview.map((p) => (
                        <TableRow key={p.row}>
                          <TableCell>{p.row}</TableCell>
                          <TableCell>
                            <Chip
                              label={p.mode === 'create' ? 'CREAR' : 'ACTUALIZAR'}
                              size="small"
                              color={p.mode === 'create' ? 'success' : 'warning'}
                            />
                          </TableCell>
                          <TableCell>
                            <Typography variant="caption" fontFamily="monospace">
                              {Object.entries(p.data)
                                .map(([k, v]) => `${k}=${v}`)
                                .join('  ')}
                            </Typography>
                          </TableCell>
                        </TableRow>
                      ))}
                    </TableBody>
                  </Table>
                </TableContainer>
              </>
            )}

            {error && (
              <Alert severity="error" sx={{ mt: 2 }}>
                {error}
              </Alert>
            )}
          </Box>
        )}

        {/* ── Step 2: Result ── */}
        {step === 2 && result && (
          <Box textAlign="center" py={3}>
            <CheckCircle color="success" sx={{ fontSize: 64, mb: 2 }} />
            <Typography variant="h6" gutterBottom>
              Importación completada
            </Typography>
            <Box display="flex" justifyContent="center" gap={2} mt={2}>
              <Chip label={`Creados: ${result.created}`} color="success" />
              <Chip label={`Actualizados: ${result.updated}`} color="warning" />
              {result.skipped > 0 && (
                <Chip label={`Omitidos: ${result.skipped}`} />
              )}
            </Box>
          </Box>
        )}
      </DialogContent>

      <DialogActions>
        {step === 0 && (
          <>
            <Button onClick={handleClose}>Cancelar</Button>
            <Button
              variant="contained"
              onClick={handleValidate}
              disabled={!file || loading}
              startIcon={loading ? <CircularProgress size={16} /> : undefined}
            >
              Validar
            </Button>
          </>
        )}

        {step === 1 && (
          <>
            <Button onClick={() => { setStep(0); setError(''); }}>Atrás</Button>
            <Box flex={1} />
            <Button onClick={handleClose}>Cancelar</Button>
            <Button
              variant="contained"
              onClick={handleApply}
              disabled={validation?.has_blocking_errors || loading}
              color={warningCount > 0 ? 'warning' : 'primary'}
              startIcon={loading ? <CircularProgress size={16} /> : undefined}
            >
              {warningCount > 0
                ? `Importar con ${warningCount} aviso${warningCount > 1 ? 's' : ''}`
                : 'Importar'}
            </Button>
          </>
        )}

        {step === 2 && (
          <Button variant="contained" onClick={handleClose}>
            Cerrar
          </Button>
        )}
      </DialogActions>
    </Dialog>
  );
}
