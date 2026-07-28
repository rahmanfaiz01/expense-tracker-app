import { Alert, Box, Button, Link, Paper, Stack, TextField, Typography } from '@mui/material';
import { useState, type FormEvent } from 'react';
import { Link as RouterLink, useLocation, useNavigate } from 'react-router-dom';
import { errorMessage } from '../api/client';
import { useAuth } from '../auth/useAuth';

interface LocationState {
  from?: string;
}

export const LoginPage = () => {
  const { login } = useAuth();
  const navigate = useNavigate();
  const location = useLocation();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      await login(email, password);
      const state = location.state as LocationState | null;
      navigate(state?.from ?? '/', { replace: true });
    } catch (cause) {
      setError(errorMessage(cause, 'Unable to sign in'));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Box display="flex" justifyContent="center" alignItems="center" minHeight="100vh" p={2}>
      <Paper sx={{ p: 4, width: '100%', maxWidth: 420 }} variant="outlined">
        <Typography variant="h5" component="h1" gutterBottom>
          Sign in
        </Typography>
        <Typography variant="body2" color="text.secondary" mb={3}>
          Track your income and expenses in one place.
        </Typography>

        <form onSubmit={(event) => void handleSubmit(event)} noValidate>
          <Stack spacing={2}>
            {error ? <Alert severity="error">{error}</Alert> : null}
            <TextField
              label="Email"
              type="email"
              value={email}
              onChange={(event) => setEmail(event.target.value)}
              autoComplete="email"
              required
              fullWidth
            />
            <TextField
              label="Password"
              type="password"
              value={password}
              onChange={(event) => setPassword(event.target.value)}
              autoComplete="current-password"
              required
              fullWidth
            />
            <Button type="submit" variant="contained" size="large" disabled={submitting}>
              {submitting ? 'Signing in…' : 'Sign in'}
            </Button>
            <Typography variant="body2" textAlign="center">
              No account?{' '}
              <Link component={RouterLink} to="/register">
                Create one
              </Link>
            </Typography>
          </Stack>
        </form>
      </Paper>
    </Box>
  );
};
