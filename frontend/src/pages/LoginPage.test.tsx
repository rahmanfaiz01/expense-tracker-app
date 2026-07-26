import { fireEvent, screen, waitFor } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import * as authApi from '../api/auth';
import type { User } from '../api/types';
import { renderWithProviders } from '../test/renderWithProviders';
import { LoginPage } from './LoginPage';

vi.mock('../api/auth');

const user: User = {
  id: 'user-1',
  email: 'ada@example.com',
  full_name: 'Ada',
  is_active: true,
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
};

const submitCredentials = () => {
  fireEvent.change(screen.getByLabelText(/email/i), { target: { value: 'ada@example.com' } });
  fireEvent.change(screen.getByLabelText(/password/i), { target: { value: 'correct-horse-9' } });
  fireEvent.click(screen.getByRole('button', { name: /sign in/i }));
};

describe('LoginPage', () => {
  beforeEach(() => {
    vi.resetAllMocks();
    vi.mocked(authApi.restoreSession).mockRejectedValue(new Error('401'));
  });

  it('signs the user in with the submitted credentials', async () => {
    vi.mocked(authApi.login).mockResolvedValue(user);

    renderWithProviders(<LoginPage />, { route: '/login' });
    submitCredentials();

    await waitFor(() =>
      expect(authApi.login).toHaveBeenCalledWith('ada@example.com', 'correct-horse-9'),
    );
  });

  it('shows the generic backend error when the credentials are wrong', async () => {
    vi.mocked(authApi.login).mockRejectedValue(
      Object.assign(new Error('Request failed'), {
        isAxiosError: true,
        response: { data: { detail: 'Invalid email or password' } },
      }),
    );

    renderWithProviders(<LoginPage />, { route: '/login' });
    submitCredentials();

    expect(await screen.findByText('Invalid email or password')).toBeInTheDocument();
  });
});
