import axios from 'axios';

/** Base URL of the backend API, configurable via VITE_API_URL. */
export const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api/v1';

/**
 * Shared axios instance. `withCredentials` is enabled so the HttpOnly refresh
 * cookie (added in the auth phase) is sent automatically.
 */
export const apiClient = axios.create({
  baseURL: API_URL,
  withCredentials: true,
});

export interface HealthResponse {
  status: string;
  service: string;
  environment: string;
  version: string;
}

/** Fetch the backend health status. */
export const getHealth = async (): Promise<HealthResponse> => {
  const { data } = await apiClient.get<HealthResponse>('/health');
  return data;
};
