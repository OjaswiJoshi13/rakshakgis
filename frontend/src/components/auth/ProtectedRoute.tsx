"use client";

import React, { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { UserRole } from "@/types/auth";
import { Alert } from "@/components/ui/Alert";

export interface ProtectedRouteProps {
  children: React.ReactNode;
  /** Optional role restriction check */
  requiredRoles?: UserRole[];
  /** Optional redirect URL when unauthenticated (defaults to /login) */
  redirectTo?: string;
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({
  children,
  requiredRoles,
  redirectTo = "/login",
}) => {
  const router = useRouter();
  const { user, isAuthenticated, isLoading, hasRole } = useAuth();

  useEffect(() => {
    if (!isLoading && !isAuthenticated) {
      router.replace(redirectTo);
    }
  }, [isLoading, isAuthenticated, redirectTo, router]);

  // Accessible loading indicator while resolving authentication state
  if (isLoading) {
    return (
      <div
        role="status"
        aria-live="polite"
        className="flex min-h-[50vh] flex-col items-center justify-center space-y-4 p-8 text-center"
      >
        <div className="relative flex h-12 w-12 items-center justify-center">
          <div className="h-12 w-12 rounded-full border-2 border-border-strong border-t-sky-600 animate-spin" />
          <span className="sr-only">Verifying credentials</span>
        </div>
        <div className="space-y-1">
          <p className="text-sm font-semibold text-text-primary">
            Verifying Authority Session
          </p>
          <p className="text-xs text-text-muted font-mono">
            Validating disaster decision support credentials...
          </p>
        </div>
      </div>
    );
  }

  // If not authenticated, render placeholder while redirect completes
  if (!isAuthenticated) {
    return (
      <div
        role="status"
        aria-live="polite"
        className="flex min-h-[50vh] items-center justify-center p-8 text-center text-xs text-text-muted font-mono"
      >
        Redirecting to authority login...
      </div>
    );
  }

  // Check role authorization if specific roles were requested
  if (requiredRoles && requiredRoles.length > 0 && !hasRole(requiredRoles)) {
    return (
      <div className="mx-auto max-w-2xl p-6 sm:p-8">
        <Alert
          severity="danger"
          title="Access Restricted: Insufficient Role Permissions"
        >
          <div className="space-y-2 text-xs">
            <p>
              Your current account role (
              <span className="font-mono font-semibold text-red-950 dark:text-red-100">
                {user?.role || "unknown"}
              </span>
              ) does not have clearance to view this module.
            </p>
            <p>
              Required roles:{" "}
              <span className="font-mono font-semibold text-red-950 dark:text-red-100">
                {requiredRoles.join(", ")}
              </span>
            </p>
            <p className="text-text-muted">
              Please contact the State Disaster Management Administrator to request elevated permissions.
            </p>
          </div>
        </Alert>
      </div>
    );
  }

  return <>{children}</>;
};
