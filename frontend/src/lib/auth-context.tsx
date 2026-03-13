"use client";

import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
} from "react";
import { useQueryClient } from "@tanstack/react-query";
import type { User, AuthTokens } from "@/types";
import api, {
  clearAuthToken,
  clearRefreshToken,
  getAuthToken,
  setAuthToken,
  setRefreshToken,
} from "@/lib/api";

// ─── Context shape ────────────────────────────────────────────────────────────

interface AuthContextValue {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (email: string, password: string, full_name: string) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextValue | undefined>(undefined);

// ─── Provider ─────────────────────────────────────────────────────────────────

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const queryClient = useQueryClient();

  const fetchCurrentUser = useCallback(async (): Promise<User | null> => {
    const token = getAuthToken();
    if (!token) return null;
    try {
      const res = await api.get<User>("/auth/me");
      return res.data;
    } catch {
      return null;
    }
  }, []);

  const refreshUser = useCallback(async () => {
    const currentUser = await fetchCurrentUser();
    setUser(currentUser);
  }, [fetchCurrentUser]);

  // Initialise from stored token on mount
  useEffect(() => {
    fetchCurrentUser()
      .then(setUser)
      .finally(() => setIsLoading(false));
  }, [fetchCurrentUser]);

  const login = useCallback(async (email: string, password: string) => {
    const res = await api.post<AuthTokens>("/auth/login", {
      email,
      password,
    });

    setAuthToken(res.data.access_token);
    setRefreshToken(res.data.refresh_token);

    const currentUser = await api.get<User>("/auth/me");
    setUser(currentUser.data);
    queryClient.clear();
  }, [queryClient]);

  const register = useCallback(
    async (email: string, password: string, full_name: string) => {
      await api.post("/auth/register", { email, password, full_name });
      await login(email, password);
    },
    [login],
  );

  const logout = useCallback(() => {
    clearAuthToken();
    clearRefreshToken();
    setUser(null);
    queryClient.clear();
    window.location.href = "/login";
  }, [queryClient]);

  return (
    <AuthContext.Provider
      value={{
        user,
        isLoading,
        isAuthenticated: !!user,
        login,
        register,
        logout,
        refreshUser,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

// ─── Hook ─────────────────────────────────────────────────────────────────────

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used within <AuthProvider>");
  return ctx;
}
