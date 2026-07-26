import axios from 'axios';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { errorMessage, getAccessToken, refreshAccessToken, setAccessToken } from './client';

describe('api client', () => {
  afterEach(() => {
    setAccessToken(null);
    vi.restoreAllMocks();
  });

  it('keeps the access token in memory only', () => {
    setAccessToken('token-123');

    expect(getAccessToken()).toBe('token-123');
    expect(window.localStorage.getItem('access_token')).toBeNull();
    expect(JSON.stringify(window.localStorage)).not.toContain('token-123');
  });

  it('stores the rotated token after a successful refresh', async () => {
    const post = vi.spyOn(axios, 'post').mockResolvedValue({
      data: { access_token: 'fresh', token_type: 'bearer', expires_in: 900, user: null },
    });

    await expect(refreshAccessToken()).resolves.toBe('fresh');
    expect(getAccessToken()).toBe('fresh');
    expect(post).toHaveBeenCalledTimes(1);
  });

  it('clears the token when the refresh cookie is rejected', async () => {
    setAccessToken('stale');
    vi.spyOn(axios, 'post').mockRejectedValue(new Error('401'));

    await expect(refreshAccessToken()).resolves.toBeNull();
    expect(getAccessToken()).toBeNull();
  });

  it('shares one in-flight refresh between concurrent callers', async () => {
    const post = vi.spyOn(axios, 'post').mockResolvedValue({
      data: { access_token: 'once', token_type: 'bearer', expires_in: 900, user: null },
    });

    await Promise.all([refreshAccessToken(), refreshAccessToken(), refreshAccessToken()]);

    expect(post).toHaveBeenCalledTimes(1);
  });

  it('surfaces the API detail message', () => {
    const apiError = Object.assign(new Error('Request failed'), {
      isAxiosError: true,
      response: { data: { detail: 'Category not found' } },
    });

    expect(errorMessage(apiError)).toBe('Category not found');
    expect(errorMessage(new Error(''), 'fallback')).toBe('fallback');
  });
});
