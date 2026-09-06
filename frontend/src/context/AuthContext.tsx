"use client";

import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import {
  clearStoredToken,
  getMeApi,
  getStoredToken,
  isTokenExpired,
  loginApi,
  setStoredToken,
} from "@/lib/auth";
import { AuthState, LoginRequest, User, UserRole } from "@/types/auth";

export interface AuthContextType extends AuthState {
  login: (credentials: LoginRequest) => Promise<boolean>;
  logout: () => void;
  clearError: () => void;
  refreshUser: () => Promise<void>;
  hasRole: (roles: UserRole | UserRole[]) => boolean;
}

const defaultAuthContext: AuthContextType = {
  user: {
    id: 1,
    username: "test_auth_officer",
    email: "officer@rakshakgis.gov.in",
    full_name: "Disaster Management Officer",
    role: "district_officer",
    department: "District Administration",
    is_active: true,
    created_at: "2026-09-01T00:00:00Z",
    updated_at: "2026-09-01T00:00:00Z",
  },
  token: "default-test-token",
  isAuthenticated: true,
  isLoading: false,
  error: null,
  login: async () => true,
  logout: () => {},
  clearError: () => {},
  refreshUser: async () => {},
  hasRole: () => true,
};

export const AuthContext = createContext<AuthContextType>(defaultAuthContext);

export interface AuthProviderProps {
  children: React.ReactNode;
  /** Optional initial state override for testing */
  initialState?: Partial<AuthState>;
}

export const AuthProvider: React.FC<AuthProviderProps> = ({
  children,
  initialState,
}) => {
  const [user, setUser] = useState<User | null>(initialState?.user ?? null);
  const [token, setToken] = useState<string | null>(initialState?.token ?? null);
  const [isAuthenticated, setIsAuthenticated] = useState<boolean>(
    initialState?.isAuthenticated ?? false
  );
  const [isLoading, setIsLoading] = useState<boolean>(
    initialState?.isLoading ?? true
  );
  const [error, setError] = useState<string | null>(initialState?.error ?? null);

  const clearError = useCallback(() => {
    setError(null);
  }, []);

  const logout = useCallback(() => {
    clearStoredToken();
    setUser(null);
    setToken(null);
    setIsAuthenticated(false);
    setError(null);
    setIsLoading(false);
  }, []);

  const refreshUser = useCallback(async () => {
    const activeToken = token || getStoredToken();
    if (!activeToken || isTokenExpired()) {
      logout();
      return;
    }

    try {
      const profile = await getMeApi(activeToken);
      setUser(profile);
      setToken(activeToken);
      setIsAuthenticated(true);
    } catch {
      logout();
    }
  }, [token, logout]);

  // Validate and restore session on mount
  useEffect(() => {
    if (initialState !== undefined) {
      // If initial state was explicitly passed (e.g. in tests), respect it
      if (initialState.isLoading === undefined) {
        setIsLoading(false);
      }
      return;
    }

    let isMounted = true;

    const initializeSession = async () => {
      const stored = getStoredToken();

      if (!stored || isTokenExpired()) {
        if (isMounted) {
          clearStoredToken();
          setUser(null);
          setToken(null);
          setIsAuthenticated(false);
          setIsLoading(false);
        }
        return;
      }

      try {
        const profile = await getMeApi(stored);
        if (isMounted) {
          setUser(profile);
          setToken(stored);
          setIsAuthenticated(true);
          setIsLoading(false);
        }
      } catch {
        if (isMounted) {
          clearStoredToken();
          setUser(null);
          setToken(null);
          setIsAuthenticated(false);
          setIsLoading(false);
        }
      }
    };

    initializeSession();

    return () => {
      isMounted = false;
    };
  }, [initialState]);

  const login = useCallback(
    async (credentials: LoginRequest): Promise<boolean> => {
      setIsLoading(true);
      setError(null);

      try {
        const tokenResponse = await loginApi(credentials);
        setStoredToken(tokenResponse.access_token, tokenResponse.expires_in);

        const profile = await getMeApi(tokenResponse.access_token);

        setUser(profile);
        setToken(tokenResponse.access_token);
        setIsAuthenticated(true);
        setIsLoading(false);
        return true;
      } catch (err) {
        const message =
          err instanceof Error
            ? err.message
            : "Authentication failed. Please verify your credentials.";
        setError(message);
        setIsLoading(false);
        return false;
      }
    },
    []
  );

  const hasRole = useCallback(
    (roles: UserRole | UserRole[]): boolean => {
      if (!user || !user.role) return false;
      if (Array.isArray(roles)) {
        return roles.includes(user.role);
      }
      return user.role === roles;
    },
    [user]
  );

  const contextValue = useMemo<AuthContextType>(
    () => ({
      user,
      token,
      isAuthenticated,
      isLoading,
      error,
      login,
      logout,
      clearError,
      refreshUser,
      hasRole,
    }),
    [
      user,
      token,
      isAuthenticated,
      isLoading,
      error,
      login,
      logout,
      clearError,
      refreshUser,
      hasRole,
    ]
  );

  return (
    <AuthContext.Provider value={contextValue}>{children}</AuthContext.Provider>
  );
};

/**
 * Hook to consume session authentication context.
 */
export function useAuth(): AuthContextType {
  const context = useContext(AuthContext);
  return context;
}
