'use client';

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from 'react';

import { apiFetch, tokenStore } from '@/lib/api';
import type { AuthConfig, TokenPair, User } from '@/lib/types';

interface AuthState {
  user: User | null;
  config: AuthConfig | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, fullName: string) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
  applyTokens: (tokens: TokenPair) => Promise<void>;
}

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [config, setConfig] = useState<AuthConfig | null>(null);
  const [loading, setLoading] = useState(true);

  const loadUser = useCallback(async () => {
    if (!tokenStore.access) {
      setUser(null);
      return;
    }
    try {
      setUser(await apiFetch<User>('/auth/me'));
    } catch {
      tokenStore.clear();
      setUser(null);
    }
  }, []);

  useEffect(() => {
    let cancelled = false;

    (async () => {
      const [cfg] = await Promise.allSettled([
        apiFetch<AuthConfig>('/auth/config', { auth: false }),
        loadUser(),
      ]);
      if (cancelled) return;
      if (cfg.status === 'fulfilled') setConfig(cfg.value);
      setLoading(false);
    })();

    // Keeps tabs in sync and reacts to token changes from the OAuth callback.
    const onChange = () => void loadUser();
    window.addEventListener('cka:auth-changed', onChange);
    window.addEventListener('storage', onChange);

    return () => {
      cancelled = true;
      window.removeEventListener('cka:auth-changed', onChange);
      window.removeEventListener('storage', onChange);
    };
  }, [loadUser]);

  const applyTokens = useCallback(
    async (tokens: TokenPair) => {
      tokenStore.set(tokens.access_token, tokens.refresh_token);
      await loadUser();
    },
    [loadUser],
  );

  const login = useCallback(
    async (identifier: string, password: string) => {
      // Username or email - the API accepts either under this key.
      const tokens = await apiFetch<TokenPair>('/auth/login', {
        method: 'POST',
        auth: false,
        body: { identifier, password },
      });
      await applyTokens(tokens);
    },
    [applyTokens],
  );

  const register = useCallback(
    async (email: string, password: string, fullName: string) => {
      const tokens = await apiFetch<TokenPair>('/auth/register', {
        method: 'POST',
        auth: false,
        body: { email, password, full_name: fullName || null },
      });
      await applyTokens(tokens);
    },
    [applyTokens],
  );

  const logout = useCallback(() => {
    tokenStore.clear();
    setUser(null);
  }, []);

  const value = useMemo<AuthState>(
    () => ({
      user,
      config,
      loading,
      login,
      register,
      logout,
      refreshUser: loadUser,
      applyTokens,
    }),
    [user, config, loading, login, register, logout, loadUser, applyTokens],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used inside <AuthProvider>');
  return ctx;
}
