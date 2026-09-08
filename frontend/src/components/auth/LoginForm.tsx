"use client";

import React, { useState } from "react";
import { useRouter } from "next/navigation";
import { Eye, EyeOff } from "lucide-react";
import { useAuth } from "@/context/AuthContext";
import { Button } from "@/components/ui/Button";
import { Alert } from "@/components/ui/Alert";

export interface LoginFormProps {
  onSuccess?: () => void;
  className?: string;
}

export const LoginForm: React.FC<LoginFormProps> = ({ onSuccess, className = "" }) => {
  const router = useRouter();
  const { login, loginDemo, isLoading, error: serverError, clearError } = useAuth();

  const [username, setUsername] = useState<string>("");
  const [password, setPassword] = useState<string>("");
  const [showPassword, setShowPassword] = useState<boolean>(false);
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
        router.push("/dashboard");
      }
    }
  };

  const handleDemoLogin = async () => {
    setClientError(null);
    clearError();

    const success = await loginDemo();
    if (success) {
      if (onSuccess) {
        onSuccess();
      } else {
        router.push("/dashboard");
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
          className="block text-xs font-mono font-medium text-text-secondary uppercase tracking-wider"
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
          className="w-full rounded-md border border-border-strong bg-surface-elevated px-3 py-2 text-sm text-text-primary placeholder-text-muted transition-colors focus:border-sky-500 focus:outline-none focus:ring-2 focus:ring-sky-500/30 disabled:opacity-50"
        />
      </div>

      <div className="space-y-1.5">
        <div className="flex items-center justify-between">
          <label
            htmlFor="auth-password"
            className="block text-xs font-mono font-medium text-text-secondary uppercase tracking-wider"
          >
            Password
          </label>
        </div>
        <div className="relative">
          <input
            id="auth-password"
            name="password"
            type={showPassword ? "text" : "password"}
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
            className="w-full rounded-md border border-border-strong bg-surface-elevated pl-3 pr-10 py-2 text-sm text-text-primary placeholder-text-muted transition-colors focus:border-sky-500 focus:outline-none focus:ring-2 focus:ring-sky-500/30 disabled:opacity-50"
          />
          <button
            type="button"
            onClick={() => setShowPassword((prev) => !prev)}
            aria-label={showPassword ? "Hide password" : "Show password"}
            disabled={isLoading}
            className="absolute right-2.5 top-1/2 -translate-y-1/2 rounded p-1 text-text-muted hover:text-text-primary focus:outline-none focus-visible:ring-2 focus-visible:ring-sky-500 disabled:opacity-50 transition-colors"
          >
            {showPassword ? (
              <EyeOff className="h-4 w-4" aria-hidden="true" />
            ) : (
              <Eye className="h-4 w-4" aria-hidden="true" />
            )}
          </button>
        </div>
      </div>

      <div className="pt-2">
        <Button
          type="submit"
          variant="primary"
          size="md"
          isLoading={isLoading}
          disabled={isLoading}
          className="w-full font-semibold shadow-sm"
        >
          {isLoading ? "Authenticating Credentials..." : "Sign In to Command Center"}
        </Button>
      </div>

      <div className="relative my-4">
        <div className="absolute inset-0 flex items-center">
          <div className="w-full border-t border-border-subtle" />
        </div>
        <div className="relative flex justify-center text-xs uppercase">
          <span className="bg-surface-panel px-2 font-mono text-[10px] text-text-muted tracking-wider">
            Evaluation &amp; Offline Access
          </span>
        </div>
      </div>

      <div>
        <Button
          type="button"
          variant="outline"
          size="md"
          disabled={isLoading}
          onClick={handleDemoLogin}
          className="w-full border-emerald-600/40 bg-emerald-50 text-emerald-800 dark:bg-emerald-950/30 dark:text-emerald-300 dark:border-emerald-600/50 hover:bg-emerald-100 dark:hover:bg-emerald-900/50 font-medium shadow-sm transition-all duration-150"
        >
          <span>⚡ Quick Sign-In (District Officer)</span>
          <span className="sr-only">Sign In as Demo District Officer</span>
        </Button>
        <p className="mt-1.5 text-center text-[10px] font-mono text-text-muted">
          One-click evaluation access • District Collector (Chamoli)
        </p>
      </div>

      <div className="border-t border-border-subtle pt-3 text-center">
        <p className="text-[11px] text-text-muted">
          Authorized personnel only. Access monitored for disaster emergency operations.
        </p>
      </div>
    </form>
  );
};
