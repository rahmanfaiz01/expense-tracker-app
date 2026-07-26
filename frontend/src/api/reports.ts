import { apiClient } from './client';
import type { CategoryTotal, MonthlyPoint, Summary, TransactionType } from './types';

export const fetchSummary = async (dateFrom?: string, dateTo?: string): Promise<Summary> => {
  const { data } = await apiClient.get<Summary>('/reports/summary', {
    params: { date_from: dateFrom, date_to: dateTo },
  });
  return data;
};

export const fetchMonthly = async (months = 6): Promise<MonthlyPoint[]> => {
  const { data } = await apiClient.get<MonthlyPoint[]>('/reports/monthly', { params: { months } });
  return data;
};

export const fetchByCategory = async (
  type: TransactionType = 'expense',
): Promise<CategoryTotal[]> => {
  const { data } = await apiClient.get<CategoryTotal[]>('/reports/by-category', {
    params: { type },
  });
  return data;
};
