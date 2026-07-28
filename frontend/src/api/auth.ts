import { apiClient, setAccessToken } from './client';
import type { AuthResponse, User } from './types';

const storeSession = (auth: AuthResponse): User => {
  setAccessToken(auth.access_token);
  return auth.user;
};

export const register = async (
  email: string,
  password: string,
  fullName: string | null,
): Promise<User> => {
  const { data } = await apiClient.post<AuthResponse>('/auth/register', {
    email,
    password,
    full_name: fullName,
  });
  return storeSession(data);
};

export const login = async (email: string, password: string): Promise<User> => {
  const { data } = await apiClient.post<AuthResponse>('/auth/login', { email, password });
  return storeSession(data);
};

/** Restore a session from the refresh cookie (used on app start-up). */
export const restoreSession = async (): Promise<User> => {
  const { data } = await apiClient.post<AuthResponse>('/auth/refresh');
  return storeSession(data);
};

export const logout = async (): Promise<void> => {
  try {
    await apiClient.post('/auth/logout');
  } finally {
    setAccessToken(null);
  }
};

export const fetchCurrentUser = async (): Promise<User> => {
  const { data } = await apiClient.get<User>('/users/me');
  return data;
};
