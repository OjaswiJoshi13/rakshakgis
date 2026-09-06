/**
 * Authentication and Session Types
 * Conforms strictly to backend Chunk M2-05 authentication contracts (JWT / RBAC).
 */

export type UserRole =
  | "admin"
  | "district_officer"
  | "field_responder"
  | "viewer";

export interface User {
  id: number;
  username: string;
  email: string;
  full_name: string;
  role: UserRole;
  department?: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface LoginRequest {
  username: string;
  password: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
}

export interface AuthErrorResponse {
  success: false;
  error: {
    code: string;
    message: string;
    status_code: number;
    request_id?: string | null;
    details?: unknown;
    timestamp?: string;
  };
}

export interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
}
