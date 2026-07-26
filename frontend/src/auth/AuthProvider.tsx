import { useCallback, useEffect, useMemo, useState, type ReactNode } from 'react';
import * as authApi from '../api/auth';
import { setAccessToken, setSessionExpiredHandler } from '../api/client';
import type { User } from '../api/types';
import { AuthContext, type AuthStatus } from './AuthContext';

interface AuthProviderProps {
  children: ReactNode;
}

/**
 * Holds the session for the whole app.
 *
 * On start-up it tries the refresh cookie once: a returning user is signed in
 * without ever persisting an access token outside memory.
 */
export const AuthProvider = ({ children }: AuthProviderProps) => {
  const [user, setUser] = useState<User | null>(null);
  const [status, setStatus] = useState<AuthStatus>('loading');

  useEffect(() => {
    let active = true;
    authApi
      .restoreSession()
      .then((restored) => {
        if (active) {
          setUser(restored);
          setStatus('authenticated');
        }
      })
      .catch(() => {
        if (active) {
          setUser(null);
          setStatus('anonymous');
        }
      });
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    setSessionExpiredHandler(() => {
      setAccessToken(null);
      setUser(null);
      setStatus('anonymous');
    });
    return () => setSessionExpiredHandler(null);
  }, []);

  const login = useCallback(async (email: string, password: string) => {
    setUser(await authApi.login(email, password));
    setStatus('authenticated');
  }, []);

  const register = useCallback(async (email: string, password: string, fullName: string | null) => {
    setUser(await authApi.register(email, password, fullName));
    setStatus('authenticated');
  }, []);

  const logout = useCallback(async () => {
    await authApi.logout();
    setUser(null);
    setStatus('anonymous');
  }, []);

  const value = useMemo(
    () => ({ user, status, login, register, logout }),
    [user, status, login, register, logout],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
};
