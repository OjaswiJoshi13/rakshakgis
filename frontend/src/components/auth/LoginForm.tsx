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
  const { login, loginDemo, error: serverError, clearError, isLoading } = useAuth();

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

  const handleDemoLogin = async () => {
    setClientError(null);
    clearError();

    const success = await loginDemo();
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

      <div className="relative my-4">
        <div className="absolute inset-0 flex items-center">
          <div className="w-full border-t border-slate-800" />
        </div>
        <div className="relative flex justify-center text-xs uppercase">
          <span className="bg-slate-900 px-2 font-mono text-[10px] text-slate-500 tracking-wider">
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
          className="w-full border-emerald-600/50 bg-emerald-950/30 text-emerald-300 hover:bg-emerald-900/50 hover:text-emerald-100 font-medium shadow transition-all duration-150"
        >
          ⚡ Sign In as Demo District Officer
        </Button>
        <p className="mt-1.5 text-center text-[10px] font-mono text-slate-400">
          One-click evaluation access • District Collector (Chamoli)
        </p>
      </div>

      <div className="border-t border-slate-800/80 pt-3 text-center">
        <p className="text-[11px] text-slate-500">
          Authorized personnel only. Access monitored for disaster emergency operations.
        </p>
      </div>
    </form>
  );
};
