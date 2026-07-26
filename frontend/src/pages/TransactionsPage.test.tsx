import { fireEvent, screen, waitFor, within } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import * as categoriesApi from '../api/categories';
import * as transactionsApi from '../api/transactions';
import type { Category, Transaction, TransactionPage } from '../api/types';
import { renderWithProviders } from '../test/renderWithProviders';
import { TransactionsPage } from './TransactionsPage';

vi.mock('../api/transactions');
vi.mock('../api/categories');

const category: Category = {
  id: 'cat-1',
  user_id: 'user-1',
  name: 'Groceries',
  type: 'expense',
  color: '#1A2B3C',
  created_at: '2026-01-01T00:00:00Z',
  updated_at: '2026-01-01T00:00:00Z',
};

const transaction: Transaction = {
  id: 'txn-1',
  user_id: 'user-1',
  category_id: category.id,
  category_name: category.name,
  type: 'expense',
  amount: '25.40',
  currency: 'USD',
  description: 'Coffee beans',
  occurred_on: '2026-03-15',
  created_at: '2026-03-15T00:00:00Z',
  updated_at: '2026-03-15T00:00:00Z',
};

const page = (items: Transaction[]): TransactionPage => ({
  items,
  total: items.length,
  page: 1,
  page_size: 10,
  pages: 1,
});

const renderPage = () => renderWithProviders(<TransactionsPage />, { withAuth: false });

describe('TransactionsPage', () => {
  beforeEach(() => {
    vi.resetAllMocks();
    vi.mocked(categoriesApi.listCategories).mockResolvedValue([category]);
  });

  it('renders the transactions returned by the API', async () => {
    vi.mocked(transactionsApi.listTransactions).mockResolvedValue(page([transaction]));

    renderPage();

    expect(screen.getByRole('status')).toBeInTheDocument();
    const row = await screen.findByText('Coffee beans');
    expect(row).toBeInTheDocument();
    expect(screen.getByText('Groceries')).toBeInTheDocument();
    expect(screen.getByText(/\$25\.40/)).toBeInTheDocument();
  });

  it('shows an empty state when nothing matches', async () => {
    vi.mocked(transactionsApi.listTransactions).mockResolvedValue(page([]));

    renderPage();

    expect(await screen.findByText('No transactions yet')).toBeInTheDocument();
  });

  it('shows an error state when the request fails', async () => {
    vi.mocked(transactionsApi.listTransactions).mockRejectedValue(new Error('boom'));

    renderPage();

    expect(await screen.findByRole('alert')).toHaveTextContent('boom');
  });

  it('sends the search term to the API', async () => {
    vi.mocked(transactionsApi.listTransactions).mockResolvedValue(page([transaction]));

    renderPage();
    await screen.findByText('Coffee beans');

    fireEvent.change(screen.getByLabelText(/search description/i), {
      target: { value: 'coffee' },
    });

    await waitFor(() =>
      expect(transactionsApi.listTransactions).toHaveBeenLastCalledWith(
        expect.objectContaining({ q: 'coffee', page: 1 }),
      ),
    );
  });

  it('exports the filtered transactions as CSV', async () => {
    vi.mocked(transactionsApi.listTransactions).mockResolvedValue(page([transaction]));
    vi.mocked(transactionsApi.exportTransactionsCsv).mockResolvedValue(undefined);

    renderPage();
    await screen.findByText('Coffee beans');

    fireEvent.click(screen.getByRole('button', { name: /export csv/i }));

    await waitFor(() => expect(transactionsApi.exportTransactionsCsv).toHaveBeenCalledTimes(1));
  });

  it('asks for confirmation before deleting', async () => {
    vi.mocked(transactionsApi.listTransactions).mockResolvedValue(page([transaction]));
    vi.mocked(transactionsApi.deleteTransaction).mockResolvedValue(undefined);

    renderPage();
    await screen.findByText('Coffee beans');

    fireEvent.click(screen.getByRole('button', { name: /delete coffee beans/i }));
    const dialog = await screen.findByRole('dialog');
    fireEvent.click(within(dialog).getByRole('button', { name: /delete/i }));

    await waitFor(() => expect(transactionsApi.deleteTransaction).toHaveBeenCalledWith('txn-1'));
  });
});
