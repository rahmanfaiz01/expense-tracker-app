import { screen, waitFor } from '@testing-library/react';
import { Route, Routes } from 'react-router-dom';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import * as authApi from '../api/auth';
import type { User } from '../api/types';
import { renderWithProviders } from '../test/renderWithProviders';
import { ProtectedRoute } from './ProtectedRoute';

vi.mock('../api/auth');

const user: User = {
  id: 'user-1',
  email: 'ada@example.com',
  full_name: 'Ada',
  is_active: true,
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
};

const renderRoutes = (route: string) =>
  renderWithProviders(
    <Routes>
      <Route element={<ProtectedRoute />}>
        <Route path="/" element={<p>Secret dashboard</p>} />
      </Route>
      <Route path="/login" element={<p>Login page</p>} />
    </Routes>,
    { route },
  );

describe('ProtectedRoute', () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it('shows a loader while the session is being restored', () => {
    vi.mocked(authApi.restoreSession).mockReturnValue(new Promise(() => {}));

    renderRoutes('/');

    expect(screen.getByText(/restoring your session/i)).toBeInTheDocument();
  });

  it('renders the page once the refresh cookie restores a session', async () => {
    vi.mocked(authApi.restoreSession).mockResolvedValue(user);

    renderRoutes('/');

    expect(await screen.findByText('Secret dashboard')).toBeInTheDocument();
  });

  it('redirects to the login page when there is no session', async () => {
    vi.mocked(authApi.restoreSession).mockRejectedValue(new Error('401'));

    renderRoutes('/');

    await waitFor(() => expect(screen.getByText('Login page')).toBeInTheDocument());
  });
});
