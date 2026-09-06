"use client";

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
  type ReactNode,
} from "react";

import { api } from "@/lib/api";
import { clearSession, getStoredUser, getToken, isAdmin, setSession } from "@/lib/auth";
import type { AuthUser } from "@/lib/types";

type AuthContextValue = {
  user: AuthUser | null;
  loading: boolean;
  isAdmin: boolean;
  login: (email: string, password: string) => Promise<AuthUser>;
  register: (payload: {
    email: string;
    password: string;
    first_name: string;
    last_name: string;
  }) => Promise<AuthUser>;
  logout: () => void;
  refresh: () => Promise<void>;
};

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null);
  const [loading, setLoading] = useState(true);

  const refresh = useCallback(async () => {
    const token = getToken();
    if (!token) {
      setUser(null);
      setLoading(false);
      return;
    }
    try {
      const me = await api.get<AuthUser>("/api/v1/auth/me");
      setUser(me);
      setSession(token, me);
    } catch {
      clearSession();
      setUser(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    setUser(getStoredUser());
    void refresh();
  }, [refresh]);

  const login = useCallback(async (email: string, password: string) => {
    const data = await api.post<{ token: { access_token: string }; user: AuthUser }>(
      "/api/v1/auth/login",
      { email, password },
      false,
    );
    setSession(data.token.access_token, data.user);
    setUser(data.user);
    return data.user;
  }, []);

  const register = useCallback(
    async (payload: {
      email: string;
      password: string;
      first_name: string;
      last_name: string;
    }) => {
      const data = await api.post<{ token: { access_token: string }; user: AuthUser }>(
        "/api/v1/auth/register",
        payload,
        false,
      );
      setSession(data.token.access_token, data.user);
      setUser(data.user);
      return data.user;
    },
    [],
  );

  const logout = useCallback(() => {
    clearSession();
    setUser(null);
  }, []);

  const value = useMemo(
    () => ({
      user,
      loading,
      isAdmin: isAdmin(user),
      login,
      register,
      logout,
      refresh,
    }),
    [user, loading, login, register, logout, refresh],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within AuthProvider");
  return ctx;
}
