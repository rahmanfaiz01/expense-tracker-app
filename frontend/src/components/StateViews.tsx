import { Alert, Box, Button, CircularProgress, Typography } from '@mui/material';
import type { ReactNode } from 'react';

interface LoadingStateProps {
  label?: string;
}

export const LoadingState = ({ label = 'Loading…' }: LoadingStateProps) => (
  <Box role="status" display="flex" alignItems="center" gap={2} py={4} justifyContent="center">
    <CircularProgress size={24} />
    <Typography color="text.secondary">{label}</Typography>
  </Box>
);

interface ErrorStateProps {
  message: string;
  onRetry?: () => void;
}

export const ErrorState = ({ message, onRetry }: ErrorStateProps) => (
  <Alert
    severity="error"
    action={
      onRetry ? (
        <Button color="inherit" size="small" onClick={onRetry}>
          Retry
        </Button>
      ) : undefined
    }
  >
    {message}
  </Alert>
);

interface EmptyStateProps {
  title: string;
  description?: string;
  action?: ReactNode;
}

export const EmptyState = ({ title, description, action }: EmptyStateProps) => (
  <Box py={5} textAlign="center">
    <Typography variant="subtitle1" gutterBottom>
      {title}
    </Typography>
    {description ? (
      <Typography variant="body2" color="text.secondary" mb={2}>
        {description}
      </Typography>
    ) : null}
    {action}
  </Box>
);
