import { useEffect, useState } from 'react';
import { Alert, Box, Chip, CircularProgress, Stack, Typography } from '@mui/material';
import { getHealth, type HealthResponse } from '../../api/client';

type Status = 'loading' | 'ok' | 'error';

/**
 * Confirms the frontend can reach the backend `/api/v1/health` endpoint.
 * This is a Phase 0 connectivity check and will be replaced by the real
 * dashboard in a later phase.
 */
export const HealthCheck = () => {
  const [status, setStatus] = useState<Status>('loading');
  const [data, setData] = useState<HealthResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    getHealth()
      .then((res) => {
        if (!active) return;
        setData(res);
        setStatus('ok');
      })
      .catch((err: unknown) => {
        if (!active) return;
        setError(err instanceof Error ? err.message : 'Unknown error');
        setStatus('error');
      });
    return () => {
      active = false;
    };
  }, []);

  return (
    <Box sx={{ maxWidth: 480 }}>
      <Typography variant="h6" gutterBottom>
        Backend connectivity
      </Typography>

      {status === 'loading' && (
        <Stack direction="row" spacing={1} alignItems="center">
          <CircularProgress size={20} />
          <Typography>Checking backend…</Typography>
        </Stack>
      )}

      {status === 'ok' && data && (
        <Alert severity="success">
          <Stack spacing={1}>
            <Typography>Connected to the backend successfully.</Typography>
            <Stack direction="row" spacing={1} flexWrap="wrap" useFlexGap>
              <Chip label={`status: ${data.status}`} color="success" size="small" />
              <Chip label={`service: ${data.service}`} size="small" />
              <Chip label={`env: ${data.environment}`} size="small" />
              <Chip label={`v${data.version}`} size="small" />
            </Stack>
          </Stack>
        </Alert>
      )}

      {status === 'error' && (
        <Alert severity="error">Could not reach the backend health endpoint: {error}</Alert>
      )}
    </Box>
  );
};
