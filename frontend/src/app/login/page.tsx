"use client";

import React, { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { useTheme } from "@/context/ThemeContext";
import { LoginForm } from "@/components/auth/LoginForm";
import { Badge } from "@/components/ui/Badge";
import { Sun, Moon } from "lucide-react";

export default function LoginPage() {
  const router = useRouter();
  const { isAuthenticated, isLoading } = useAuth();
  const { resolvedTheme, toggleTheme } = useTheme();

  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      router.replace("/dashboard");
    }
  }, [isAuthenticated, isLoading, router]);

  if (isLoading) {
    return (
      <div
        role="status"
        aria-live="polite"
        className="flex min-h-screen flex-col items-center justify-center space-y-4 p-8 text-center bg-surface-bg text-text-primary"
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

  if (isAuthenticated) {
    return null;
  }

  return (
    <div className="flex min-h-screen flex-col justify-between bg-surface-bg text-text-primary transition-colors">
      {/* Top Banner Header */}
      <header className="relative z-10 flex h-14 w-full items-center justify-between border-b border-border-subtle bg-surface-panel/95 px-6 backdrop-blur">
        <div className="flex items-center gap-2.5">
          <div className="flex h-7 w-7 items-center justify-center rounded bg-slate-900 text-sky-400 dark:bg-slate-800 border border-border-strong font-bold font-mono text-xs tracking-tighter shadow-sm">
            RG
          </div>
          <div className="flex items-center gap-2">
            <span className="font-bold tracking-tight text-text-primary text-sm">
              RakshakGIS
            </span>
            <span className="rounded bg-surface-elevated px-1.5 py-0.5 text-[10px] font-mono text-text-muted uppercase tracking-widest border border-border-subtle">
              Authority Access
            </span>
          </div>
        </div>

        <div className="flex items-center gap-3">
          <Badge variant="outline" size="sm" className="font-mono text-[10px] text-text-secondary border-border-strong">
            Himalayan Pilot Sector
          </Badge>

          <button
            type="button"
            onClick={toggleTheme}
            title={`Switch to ${resolvedTheme === "dark" ? "light" : "dark"} mode`}
            aria-label="Toggle visual theme"
            className="flex h-7 w-7 items-center justify-center rounded-md border border-border-strong bg-surface-elevated text-text-secondary hover:text-text-primary transition-colors"
          >
            {resolvedTheme === "dark" ? (
              <Sun className="h-3.5 w-3.5 text-amber-400" />
            ) : (
              <Moon className="h-3.5 w-3.5 text-slate-700" />
            )}
          </button>
        </div>
      </header>

      {/* Main Login Canvas */}
      <main className="relative z-10 flex flex-1 items-center justify-center p-4 sm:p-6 lg:p-8">
        <div className="w-full max-w-md space-y-6">
          <div className="text-center space-y-2">
            <h1 className="text-2xl font-bold tracking-tight text-text-primary sm:text-3xl">
              Authority Sign In
            </h1>
            <p className="text-xs sm:text-sm text-text-muted max-w-sm mx-auto leading-relaxed">
              Multi-Hazard Risk Assessment, Red Zone Demarcation &amp; Relocation Decision Support System
            </p>
          </div>

          <div className="rounded-xl border border-border-subtle bg-surface-panel p-6 sm:p-8 shadow-sm">
            <LoginForm />
          </div>

          <div className="flex flex-col items-center justify-center gap-2 text-center text-xs text-text-muted font-mono">
            <div className="flex items-center gap-3">
              <span>CRS: EPSG:4326</span>
              <span>•</span>
              <span>Encrypted Session</span>
              <span>•</span>
              <span>Role-Based Clearance</span>
            </div>
          </div>
        </div>
      </main>

      {/* Security & Governance Footer */}
      <footer className="relative z-10 border-t border-border-subtle bg-surface-panel py-3 px-6 text-center text-[11px] text-text-muted">
        Disaster Management Authority Decision Support Platform • Internal Authority Clearance Only
      </footer>
    </div>
  );
}
