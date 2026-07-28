import { Box, CircularProgress, Typography } from '@mui/material';

interface FullPageLoaderProps {
  label?: string;
}

export const FullPageLoader = ({ label = 'Loading…' }: FullPageLoaderProps) => (
  <Box
    role="status"
    display="flex"
    flexDirection="column"
    alignItems="center"
    justifyContent="center"
    gap={2}
    minHeight="60vh"
  >
    <CircularProgress />
    <Typography color="text.secondary">{label}</Typography>
  </Box>
);
