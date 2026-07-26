import { useCallback, useEffect, useState } from 'react';
import { errorMessage } from '../api/client';

interface ApiData<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
  reload: () => void;
}

/**
 * Run an API call and expose loading/error/data state.
 *
 * `fetcher` must be stable (wrap it in `useCallback`); changing it refetches.
 */
export const useApiData = <T>(fetcher: () => Promise<T>): ApiData<T> => {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [reloadToken, setReloadToken] = useState(0);

  const reload = useCallback(() => setReloadToken((token) => token + 1), []);

  useEffect(() => {
    let active = true;
    setLoading(true);
    setError(null);
    fetcher()
      .then((result) => {
        if (active) {
          setData(result);
        }
      })
      .catch((cause: unknown) => {
        if (active) {
          setError(errorMessage(cause));
        }
      })
      .finally(() => {
        if (active) {
          setLoading(false);
        }
      });
    return () => {
      active = false;
    };
  }, [fetcher, reloadToken]);

  return { data, loading, error, reload };
};
