import { render, screen, waitFor } from '@testing-library/react';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { HealthCheck } from './HealthCheck';
import * as api from '../../api/client';

describe('HealthCheck', () => {
  afterEach(() => {
    vi.restoreAllMocks();
  });

  it('renders a success state when the backend is reachable', async () => {
    vi.spyOn(api, 'getHealth').mockResolvedValue({
      status: 'ok',
      service: 'Expense Tracker API',
      environment: 'test',
      version: '0.1.0',
    });

    render(<HealthCheck />);

    await waitFor(() =>
      expect(screen.getByText(/Connected to the backend successfully/i)).toBeInTheDocument(),
    );
    expect(screen.getByText('status: ok')).toBeInTheDocument();
  });

  it('renders an error state when the backend is unreachable', async () => {
    vi.spyOn(api, 'getHealth').mockRejectedValue(new Error('Network Error'));

    render(<HealthCheck />);

    await waitFor(() =>
      expect(screen.getByText(/Could not reach the backend health endpoint/i)).toBeInTheDocument(),
    );
  });
});
