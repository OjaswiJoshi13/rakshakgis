"use client";

import React, { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { DATA_MODE_CONFIG, DataMode } from "@/design-system/tokens";
import { StatusIndicator } from "@/components/ui/StatusIndicator";
import { Badge } from "@/components/ui/Badge";
import { useAuth } from "@/context/AuthContext";
import { useTheme } from "@/context/ThemeContext";
import { Sun, Moon } from "lucide-react";

export interface CommandHeaderProps {
  onToggleSidebar?: () => void;
  isSidebarOpen?: boolean;
}

export const CommandHeader: React.FC<CommandHeaderProps> = ({
  onToggleSidebar,
  isSidebarOpen = true,
}) => {
  const router = useRouter();
  const { user, isAuthenticated, logout } = useAuth();
  const { resolvedTheme, toggleTheme } = useTheme();
  const [currentTime, setCurrentTime] = useState<string>("");

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      const timeStr = now.toLocaleTimeString("en-IN", {
        timeZone: "Asia/Kolkata",
        hour12: false,
        hour: "2-digit",
        minute: "2-digit",
        second: "2-digit",
      });
      setCurrentTime(`${timeStr} IST`);
    };

    updateTime();
    const interval = setInterval(updateTime, 1000);
    return () => clearInterval(interval);
  }, []);

  const dataMode: DataMode =
    (process.env.NEXT_PUBLIC_DATA_MODE as DataMode) || "demo";
  const modeConfig = DATA_MODE_CONFIG[dataMode] || DATA_MODE_CONFIG.demo;

  const roleLabels: Record<string, string> = {
    admin: "Admin",
    district_officer: "District Officer",
    field_responder: "Field Responder",
    viewer: "Viewer",
  };

  const getInitials = () => {
    if (!user) return "OP";
    if (user.full_name) {
      const parts = user.full_name.trim().split(/\s+/);
      if (parts.length >= 2) {
        return (parts[0][0] + parts[parts.length - 1][0]).toUpperCase();
      }
      return user.full_name.slice(0, 2).toUpperCase();
    }
    return user.username.slice(0, 2).toUpperCase();
  };

  const handleLogout = () => {
    logout();
    router.push("/login");
  };

  return (
    <header className="sticky top-0 z-40 flex h-14 w-full items-center justify-between border-b border-border-subtle bg-surface-panel/95 px-4 backdrop-blur transition-colors">
      <div className="flex items-center gap-3">
        {onToggleSidebar && (
          <button
            type="button"
            onClick={onToggleSidebar}
            aria-label={isSidebarOpen ? "Collapse navigation sidebar" : "Expand navigation sidebar"}
            className="rounded p-1.5 text-text-muted hover:bg-black/5 dark:hover:bg-white/10 hover:text-text-primary focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-500 lg:hidden"
          >
            <svg
              className="h-5 w-5"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M4 6h16M4 12h16M4 18h16"
              />
            </svg>
          </button>
        )}

        <Link
          href={isAuthenticated ? "/dashboard" : "/login"}
          className="flex items-center gap-2.5 group focus:outline-none focus-visible:ring-2 focus-visible:ring-sky-500 rounded"
          aria-label="RakshakGIS Home"
        >
          <div className="flex h-7 w-7 items-center justify-center rounded bg-slate-900 text-slate-100 dark:bg-slate-800 border border-border-strong font-bold font-mono text-xs tracking-wider shadow-xs group-hover:border-sky-500 transition-colors">
            RG
          </div>
          <div className="flex flex-col">
            <div className="flex items-center gap-1.5">
              <span className="font-semibold tracking-tight text-text-primary text-sm group-hover:text-sky-600 dark:group-hover:text-sky-400 transition-colors">
                RakshakGIS
              </span>
            </div>
            <span className="text-[10px] text-text-muted hidden md:block leading-none">
              Disaster Management Decision Support System
            </span>
          </div>
        </Link>
      </div>

      <div className="flex items-center gap-2 sm:gap-3">
        {/* Unified Sector, Mode & Clock Strip */}
        <div className="hidden lg:flex items-center divide-x divide-border-subtle bg-surface-elevated/70 border border-border-subtle rounded-md text-xs py-0.5">
          <div className="flex items-center gap-1.5 px-2.5">
            <span className="text-[11px] text-text-muted">Sector:</span>
            <span className="font-medium text-text-primary text-xs">Himalayan Pilot Sector</span>
          </div>
          <div className="px-2">
            <span className={`text-[11px] font-medium ${modeConfig.badgeClass}`}>
              {modeConfig.label}
              <span className="sr-only"> DEMO MODE</span>
            </span>
          </div>
          <div className="flex items-center gap-1.5 px-2.5 text-xs text-text-muted tabular-nums">
            <span className="w-1.5 h-1.5 rounded-full bg-emerald-600 dark:bg-emerald-400 inline-block" />
            <span>{currentTime || "00:00:00 IST"}</span>
          </div>
        </div>

        {/* System Health State */}
        <div className="hidden md:flex items-center">
          <StatusIndicator status="normal" label="Operational" />
        </div>

        {/* Theme Toggle Button */}
        <button
          type="button"
          onClick={toggleTheme}
          title={`Switch to ${resolvedTheme === "dark" ? "light" : "dark"} mode`}
          aria-label="Toggle visual theme"
          className="flex h-8 w-8 items-center justify-center rounded-md border border-border-strong bg-surface-elevated text-text-secondary hover:text-text-primary hover:bg-black/5 dark:hover:bg-white/10 transition-colors"
        >
          {resolvedTheme === "dark" ? (
            <Sun className="h-4 w-4 text-amber-400" />
          ) : (
            <Moon className="h-4 w-4 text-slate-700" />
          )}
        </button>

        {/* User / Session Information */}
        <div className="flex items-center gap-2 border-l border-border-subtle pl-2.5">
          {isAuthenticated && user ? (
            <div className="flex items-center gap-2">
              <div
                className="flex h-7 w-7 items-center justify-center rounded-full bg-slate-200 text-slate-800 dark:bg-slate-800 dark:text-slate-200 border border-border-strong text-xs font-semibold"
                title={`${user.full_name} (${user.email})${user.department ? ` • ${user.department}` : ""}`}
              >
                {getInitials()}
              </div>
              <div className="hidden xl:flex flex-col text-left">
                <span className="text-xs font-medium text-text-primary leading-tight truncate max-w-[140px]">
                  {user.full_name || user.username}
                </span>
                <span className="text-[11px] text-text-muted">
                  {roleLabels[user.role] || user.role}
                </span>
              </div>
              <button
                type="button"
                onClick={handleLogout}
                title="Sign out of command center"
                aria-label="Sign out"
                className="rounded px-2 py-1 text-xs text-text-muted hover:bg-surface-elevated hover:text-text-primary focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-sky-500 font-medium transition-colors"
              >
                Sign Out
              </button>
            </div>
          ) : (
            <button
              type="button"
              onClick={() => router.push("/login")}
              className="rounded bg-surface-elevated border border-border-strong px-2.5 py-1 text-xs font-medium text-text-primary hover:bg-surface-panel transition-colors"
            >
              Sign In
            </button>
          )}
        </div>
      </div>
    </header>
  );
};
