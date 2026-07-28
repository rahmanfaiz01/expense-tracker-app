import { apiClient } from './client';
import type { Category, CategoryInput, TransactionType } from './types';

export const listCategories = async (type?: TransactionType): Promise<Category[]> => {
  const { data } = await apiClient.get<Category[]>('/categories', {
    params: type ? { type } : undefined,
  });
  return data;
};

export const createCategory = async (input: CategoryInput): Promise<Category> => {
  const { data } = await apiClient.post<Category>('/categories', input);
  return data;
};

export const updateCategory = async (
  id: string,
  input: Partial<CategoryInput>,
): Promise<Category> => {
  const { data } = await apiClient.patch<Category>(`/categories/${id}`, input);
  return data;
};

export const deleteCategory = async (id: string): Promise<void> => {
  await apiClient.delete(`/categories/${id}`);
};
