import { screen } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import * as reportsApi from '../api/reports';
import type { CategoryTotal, MonthlyPoint, Summary } from '../api/types';
import { renderWithProviders } from '../test/renderWithProviders';
import { DashboardPage } from './DashboardPage';

vi.mock('../api/reports');

const summary: Summary = {
  total_income: '2000.00',
  total_expenses: '750.50',
  balance: '1249.50',
  transaction_count: 2,
};

const monthly: MonthlyPoint[] = [
  { month: '2026-02', income: '0.00', expenses: '0.00', net: '0.00' },
  { month: '2026-03', income: '2000.00', expenses: '750.50', net: '1249.50' },
];

const byCategory: CategoryTotal[] = [
  {
    category_id: 'cat-1',
    category_name: 'Rent',
    color: '#112233',
    total: '750.50',
    type: 'expense',
  },
];

const renderPage = () => renderWithProviders(<DashboardPage />, { withAuth: false });

describe('DashboardPage', () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it('shows the summary cards with formatted totals', async () => {
    vi.mocked(reportsApi.fetchSummary).mockResolvedValue(summary);
    vi.mocked(reportsApi.fetchMonthly).mockResolvedValue(monthly);
    vi.mocked(reportsApi.fetchByCategory).mockResolvedValue(byCategory);

    renderPage();

    expect(await screen.findByText('$2,000.00')).toBeInTheDocument();
    expect(screen.getByText('$750.50')).toBeInTheDocument();
    expect(screen.getByText('$1,249.50')).toBeInTheDocument();
    expect(screen.getByText('Income vs expenses')).toBeInTheDocument();
  });

  it('invites the user to add a transaction when there is no data', async () => {
    vi.mocked(reportsApi.fetchSummary).mockResolvedValue({
      total_income: '0.00',
      total_expenses: '0.00',
      balance: '0.00',
      transaction_count: 0,
    });
    vi.mocked(reportsApi.fetchMonthly).mockResolvedValue([]);
    vi.mocked(reportsApi.fetchByCategory).mockResolvedValue([]);

    renderPage();

    expect(await screen.findByText('No transactions yet')).toBeInTheDocument();
  });

  it('reports a failure with a retry action', async () => {
    vi.mocked(reportsApi.fetchSummary).mockRejectedValue(new Error('offline'));
    vi.mocked(reportsApi.fetchMonthly).mockResolvedValue([]);
    vi.mocked(reportsApi.fetchByCategory).mockResolvedValue([]);

    renderPage();

    expect(await screen.findByRole('alert')).toHaveTextContent('offline');
    expect(screen.getByRole('button', { name: /retry/i })).toBeInTheDocument();
  });
});
