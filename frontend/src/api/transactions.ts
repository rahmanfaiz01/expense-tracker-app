import { apiClient } from './client';
import type { Transaction, TransactionInput, TransactionPage, TransactionQuery } from './types';

/** Drop empty values so the backend receives only the active filters. */
const toParams = (query: TransactionQuery): Record<string, string | number> => {
  const params: Record<string, string | number> = {};
  Object.entries(query).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== '') {
      params[key] = value;
    }
  });
  return params;
};

export const listTransactions = async (query: TransactionQuery): Promise<TransactionPage> => {
  const { data } = await apiClient.get<TransactionPage>('/transactions', {
    params: toParams(query),
  });
  return data;
};

export const createTransaction = async (input: TransactionInput): Promise<Transaction> => {
  const { data } = await apiClient.post<Transaction>('/transactions', input);
  return data;
};

export const updateTransaction = async (
  id: string,
  input: Partial<TransactionInput>,
): Promise<Transaction> => {
  const { data } = await apiClient.patch<Transaction>(`/transactions/${id}`, input);
  return data;
};

export const deleteTransaction = async (id: string): Promise<void> => {
  await apiClient.delete(`/transactions/${id}`);
};

/** Download the filtered export through the API client so it stays authenticated. */
export const exportTransactionsCsv = async (query: TransactionQuery): Promise<void> => {
  const { page, page_size: pageSize, ...filters } = query;
  void page;
  void pageSize;
  const response = await apiClient.get<Blob>('/transactions/export.csv', {
    params: toParams(filters),
    responseType: 'blob',
  });

  const disposition = String(response.headers['content-disposition'] ?? '');
  const filename = /filename="?([^";]+)"?/.exec(disposition)?.[1] ?? 'transactions.csv';

  const url = URL.createObjectURL(response.data);
  const link = document.createElement('a');
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
};
