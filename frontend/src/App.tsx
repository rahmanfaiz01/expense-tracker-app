import { Box, Container, Paper, Typography } from '@mui/material';
import { HealthCheck } from './features/health/HealthCheck';

const App = () => (
  <Container maxWidth="md" sx={{ py: 6 }}>
    <Box mb={4}>
      <Typography variant="h3" component="h1" gutterBottom>
        Expense Tracker
      </Typography>
      <Typography variant="subtitle1" color="text.secondary">
        Phase 0 — project scaffold. Features arrive in later phases.
      </Typography>
    </Box>
    <Paper variant="outlined" sx={{ p: 3 }}>
      <HealthCheck />
    </Paper>
  </Container>
);

export default App;
