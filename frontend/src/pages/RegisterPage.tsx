import { Alert, Box, Button, Link, Paper, Stack, TextField, Typography } from '@mui/material';
import { useState, type FormEvent } from 'react';
import { Link as RouterLink, useNavigate } from 'react-router-dom';
import { errorMessage } from '../api/client';
import { useAuth } from '../auth/useAuth';

const MIN_PASSWORD_LENGTH = 10;
const PASSWORD_HELPER = `At least ${MIN_PASSWORD_LENGTH} characters, including a letter and a digit`;

const passwordProblem = (password: string): string | null => {
  if (password.length < MIN_PASSWORD_LENGTH) {
    return PASSWORD_HELPER;
  }
  if (!/[A-Za-z]/.test(password) || !/\d/.test(password)) {
    return PASSWORD_HELPER;
  }
  return null;
};

export const RegisterPage = () => {
  const { register } = useAuth();
  const navigate = useNavigate();
  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const handleSubmit = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const problem = passwordProblem(password);
    if (problem) {
      setError(problem);
      return;
    }
    setError(null);
    setSubmitting(true);
    try {
      await register(email, password, fullName.trim() || null);
      navigate('/', { replace: true });
    } catch (cause) {
      setError(errorMessage(cause, 'Unable to create the account'));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <Box display="flex" justifyContent="center" alignItems="center" minHeight="100vh" p={2}>
      <Paper sx={{ p: 4, width: '100%', maxWidth: 420 }} variant="outlined">
        <Typography variant="h5" component="h1" gutterBottom>
          Create your account
        </Typography>

        <form onSubmit={(event) => void handleSubmit(event)} noValidate>
          <Stack spacing={2} mt={2}>
            {error ? <Alert severity="error">{error}</Alert> : null}
            <TextField
              label="Full name"
              value={fullName}
              onChange={(event) => setFullName(event.target.value)}
              autoComplete="name"
              fullWidth
            />
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
              autoComplete="new-password"
              helperText={PASSWORD_HELPER}
              required
              fullWidth
            />
            <Button type="submit" variant="contained" size="large" disabled={submitting}>
              {submitting ? 'Creating account…' : 'Create account'}
            </Button>
            <Typography variant="body2" textAlign="center">
              Already registered?{' '}
              <Link component={RouterLink} to="/login">
                Sign in
              </Link>
            </Typography>
          </Stack>
        </form>
      </Paper>
    </Box>
  );
};
