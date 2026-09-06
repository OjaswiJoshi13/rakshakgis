"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { Button } from "@/components/ui/Button";
import { Alert } from "@/components/ui/Alert";

export interface LoginFormProps {
  onSuccess?: () => void;
  className?: string;
}

export const LoginForm: React.FC<LoginFormProps> = ({
  onSuccess,
  className = "",
}) => {
  const router = useRouter();
  const { login, error: serverError, clearError, isLoading } = useAuth();

  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [clientError, setClientError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent<HTMLFormElement>) => {
    e.preventDefault();
    setClientError(null);
    clearError();

    const trimmedUsername = username.trim();
    if (!trimmedUsername) {
      setClientError("Username or registered email address is required.");
      return;
    }

    if (!password) {
      setClientError("Account password is required.");
      return;
    }

    const success = await login({
      username: trimmedUsername,
      password,
    });

    if (success) {
      if (onSuccess) {
        onSuccess();
      } else {
        router.push("/");
      }
    }
  };

  const displayedError = clientError || serverError;

  return (
    <form
      onSubmit={handleSubmit}
      noValidate
      className={`space-y-4 ${className}`}
      aria-label="Disaster Management Authority Authentication"
    >
      {displayedError && (
        <Alert
          severity="danger"
          title="Authentication Failed"
          onClose={() => {
            setClientError(null);
            clearError();
          }}
        >
          {displayedError}
        </Alert>
      )}

      <div className="space-y-1.5">
        <label
          htmlFor="auth-identifier"
          className="block text-xs font-mono font-medium text-slate-300 uppercase tracking-wider"
        >
          Username or Official Email
        </label>
        <input
          id="auth-identifier"
          name="username"
          type="text"
          autoComplete="username"
          value={username}
          disabled={isLoading}
          onChange={(e) => {
            setUsername(e.target.value);
            if (clientError) setClientError(null);
            if (serverError) clearError();
          }}
          placeholder="e.g. officer@rakshakgis.gov.in"
          required
          aria-required="true"
          aria-invalid={displayedError ? "true" : "false"}
          className="w-full rounded-md border border-slate-700 bg-slate-900/90 px-3 py-2 text-sm text-slate-100 placeholder-slate-500 shadow-inner transition-colors focus:border-sky-500 focus:outline-none focus:ring-2 focus:ring-sky-500/40 disabled:opacity-50"
        />
      </div>

      <div className="space-y-1.5">
        <div className="flex items-center justify-between">
          <label
            htmlFor="auth-password"
            className="block text-xs font-mono font-medium text-slate-300 uppercase tracking-wider"
          >
            Password
          </label>
        </div>
        <input
          id="auth-password"
          name="password"
          type="password"
          autoComplete="current-password"
          value={password}
          disabled={isLoading}
          onChange={(e) => {
            setPassword(e.target.value);
            if (clientError) setClientError(null);
            if (serverError) clearError();
          }}
          placeholder="••••••••••••"
          required
          aria-required="true"
          aria-invalid={displayedError ? "true" : "false"}
          className="w-full rounded-md border border-slate-700 bg-slate-900/90 px-3 py-2 text-sm text-slate-100 placeholder-slate-500 shadow-inner transition-colors focus:border-sky-500 focus:outline-none focus:ring-2 focus:ring-sky-500/40 disabled:opacity-50"
        />
      </div>

      <div className="pt-2">
        <Button
          type="submit"
          variant="primary"
          size="md"
          isLoading={isLoading}
          disabled={isLoading}
          className="w-full font-semibold shadow-md"
        >
          {isLoading ? "Authenticating Credentials..." : "Sign In to Command Center"}
        </Button>
      </div>

      <div className="border-t border-slate-800/80 pt-3 text-center">
        <p className="text-[11px] text-slate-500">
          Authorized personnel only. Access monitored for disaster emergency operations.
        </p>
      </div>
    </form>
  );
};
