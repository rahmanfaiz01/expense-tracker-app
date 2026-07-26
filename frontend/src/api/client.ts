import axios, { AxiosError, type InternalAxiosRequestConfig } from 'axios';
import type { AuthResponse } from './types';

/** Base URL of the backend API, configurable via VITE_API_URL. */
export const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000/api/v1';

/**
 * The access token lives in memory only — never in localStorage, where any XSS
 * could read it. The long-lived refresh token stays in its HttpOnly cookie.
 */
let accessToken: string | null = null;

export const setAccessToken = (token: string | null): void => {
  accessToken = token;
};

export const getAccessToken = (): string | null => accessToken;

let onSessionExpired: (() => void) | null = null;

/** Register the callback used when a refresh attempt finally fails. */
export const setSessionExpiredHandler = (handler: (() => void) | null): void => {
  onSessionExpired = handler;
};

/** Shared axios instance; `withCredentials` sends the refresh cookie. */
export const apiClient = axios.create({
  baseURL: API_URL,
  withCredentials: true,
});

apiClient.interceptors.request.use((config) => {
  if (accessToken) {
    config.headers.Authorization = `Bearer ${accessToken}`;
  }
  return config;
});

let pendingRefresh: Promise<string | null> | null = null;

/**
 * Exchange the refresh cookie for a new access token.
 *
 * Concurrent callers share one in-flight request so a burst of 401s cannot
 * rotate the refresh token several times (which the backend treats as replay).
 */
export const refreshAccessToken = async (): Promise<string | null> => {
  pendingRefresh ??= axios
    .post<AuthResponse>(`${API_URL}/auth/refresh`, null, { withCredentials: true })
    .then(({ data }) => {
      setAccessToken(data.access_token);
      return data.access_token;
    })
    .catch(() => {
      setAccessToken(null);
      return null;
    })
    .finally(() => {
      pendingRefresh = null;
    });
  return pendingRefresh;
};

interface RetriableRequest extends InternalAxiosRequestConfig {
  _retried?: boolean;
}

apiClient.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const request = error.config as RetriableRequest | undefined;
    const isAuthCall = request?.url?.startsWith('/auth/') ?? false;

    if (error.response?.status !== 401 || !request || request._retried || isAuthCall) {
      throw error;
    }

    request._retried = true;
    const token = await refreshAccessToken();
    if (!token) {
      onSessionExpired?.();
      throw error;
    }
    return apiClient(request);
  },
);

/** Extract a human-readable message from an API error. */
export const errorMessage = (error: unknown, fallback = 'Something went wrong'): string => {
  if (axios.isAxiosError(error)) {
    const detail = (error.response?.data as { detail?: unknown } | undefined)?.detail;
    if (typeof detail === 'string') {
      return detail;
    }
    if (Array.isArray(detail)) {
      const first = detail[0] as { msg?: string } | undefined;
      if (first?.msg) {
        return first.msg;
      }
    }
    if (!error.response) {
      return 'Cannot reach the server. Is the backend running?';
    }
  }
  return error instanceof Error && error.message ? error.message : fallback;
};
