/** Shared API payload types (mirrors the FastAPI schemas). */

export type TransactionType = 'income' | 'expense';

export interface User {
  id: string;
  email: string;
  full_name: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface Category {
  id: string;
  user_id: string;
  name: string;
  type: TransactionType;
  color: string | null;
  created_at: string;
  updated_at: string;
}

export interface CategoryInput {
  name: string;
  type: TransactionType;
  color: string | null;
}

export interface Transaction {
  id: string;
  user_id: string;
  category_id: string | null;
  category_name: string | null;
  type: TransactionType;
  /** Serialized Decimal, e.g. "12.34" — never parsed into a float for display. */
  amount: string;
  currency: string;
  description: string | null;
  occurred_on: string;
  created_at: string;
  updated_at: string;
}

export interface TransactionInput {
  type: TransactionType;
  amount: string;
  currency: string;
  description: string | null;
  occurred_on: string;
  category_id: string | null;
}

export type TransactionSort = 'occurred_on' | 'amount' | 'created_at' | 'description';
export type SortOrder = 'asc' | 'desc';

export interface TransactionQuery {
  q?: string;
  type?: TransactionType | '';
  category_id?: string;
  date_from?: string;
  date_to?: string;
  sort?: TransactionSort;
  order?: SortOrder;
  page?: number;
  page_size?: number;
}

export interface TransactionPage {
  items: Transaction[];
  total: number;
  page: number;
  page_size: number;
  pages: number;
}

export interface Summary {
  total_income: string;
  total_expenses: string;
  balance: string;
  transaction_count: number;
}

export interface MonthlyPoint {
  month: string;
  income: string;
  expenses: string;
  net: string;
}

export interface CategoryTotal {
  category_id: string | null;
  category_name: string;
  color: string | null;
  total: string;
  type: TransactionType;
}
