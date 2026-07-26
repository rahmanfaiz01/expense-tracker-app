import type { TransactionQuery, TransactionType } from '../../api/types';

/** Form state of the transaction filter bar (empty string means "not set"). */
export interface FilterState {
  q: string;
  type: TransactionType | '';
  categoryId: string;
  dateFrom: string;
  dateTo: string;
}

export const EMPTY_FILTERS: FilterState = {
  q: '',
  type: '',
  categoryId: '',
  dateFrom: '',
  dateTo: '',
};

export const isFiltered = (filters: FilterState): boolean =>
  JSON.stringify(filters) !== JSON.stringify(EMPTY_FILTERS);

/** Convert the form state into API query parameters. */
export const toQuery = (filters: FilterState): TransactionQuery => ({
  q: filters.q.trim() || undefined,
  type: filters.type || undefined,
  category_id: filters.categoryId || undefined,
  date_from: filters.dateFrom || undefined,
  date_to: filters.dateTo || undefined,
});
