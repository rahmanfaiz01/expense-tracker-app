import { fireEvent, screen, waitFor, within } from '@testing-library/react';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import * as categoriesApi from '../api/categories';
import type { Category } from '../api/types';
import { renderWithProviders } from '../test/renderWithProviders';
import { CategoriesPage } from './CategoriesPage';

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

const renderPage = () => renderWithProviders(<CategoriesPage />, { withAuth: false });

describe('CategoriesPage', () => {
  beforeEach(() => {
    vi.resetAllMocks();
  });

  it('lists the categories', async () => {
    vi.mocked(categoriesApi.listCategories).mockResolvedValue([category]);

    renderPage();

    expect(await screen.findByText('Groceries')).toBeInTheDocument();
    expect(screen.getByText('#1A2B3C')).toBeInTheDocument();
  });

  it('shows an empty state with a create action', async () => {
    vi.mocked(categoriesApi.listCategories).mockResolvedValue([]);

    renderPage();

    expect(await screen.findByText('No categories yet')).toBeInTheDocument();
  });

  it('creates a category from the dialog', async () => {
    vi.mocked(categoriesApi.listCategories).mockResolvedValue([]);
    vi.mocked(categoriesApi.createCategory).mockResolvedValue(category);

    renderPage();
    await screen.findByText('No categories yet');

    fireEvent.click(screen.getByRole('button', { name: 'Add' }));
    const dialog = await screen.findByRole('dialog');
    fireEvent.change(within(dialog).getByLabelText(/name/i), { target: { value: 'Rent' } });
    fireEvent.click(within(dialog).getByRole('button', { name: /save/i }));

    await waitFor(() =>
      expect(categoriesApi.createCategory).toHaveBeenCalledWith(
        expect.objectContaining({ name: 'Rent', type: 'expense' }),
      ),
    );
  });

  it('surfaces a duplicate-name conflict from the API', async () => {
    vi.mocked(categoriesApi.listCategories).mockResolvedValue([category]);
    vi.mocked(categoriesApi.createCategory).mockRejectedValue(
      Object.assign(new Error('Request failed'), {
        isAxiosError: true,
        response: { data: { detail: 'A category with this name and type already exists' } },
      }),
    );

    renderPage();
    await screen.findByText('Groceries');

    fireEvent.click(screen.getByRole('button', { name: 'Add' }));
    const dialog = await screen.findByRole('dialog');
    fireEvent.change(within(dialog).getByLabelText(/name/i), { target: { value: 'Groceries' } });
    fireEvent.click(within(dialog).getByRole('button', { name: /save/i }));

    expect(
      await screen.findByText('A category with this name and type already exists'),
    ).toBeInTheDocument();
  });
});
