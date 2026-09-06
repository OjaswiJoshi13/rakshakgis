"use client";

import React, { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { DATA_MODE_CONFIG, DataMode } from "@/design-system/tokens";
import { StatusIndicator } from "@/components/ui/StatusIndicator";
import { Badge } from "@/components/ui/Badge";
import { useAuth } from "@/context/AuthContext";

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
  const [currentTime, setCurrentTime] = useState<string>("");

  useEffect(() => {
    const updateTime = () => {
      const now = new Date();
      // Format in IST / UTC standard for disaster operations
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
    <header className="sticky top-0 z-40 flex h-14 w-full items-center justify-between border-b border-slate-800 bg-slate-950/90 px-4 backdrop-blur transition-all">
      <div className="flex items-center gap-3">
        {onToggleSidebar && (
          <button
            type="button"
            onClick={onToggleSidebar}
            aria-label={isSidebarOpen ? "Collapse navigation sidebar" : "Expand navigation sidebar"}
            className="rounded p-1.5 text-slate-400 hover:bg-slate-800 hover:text-slate-100 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-500 lg:hidden"
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
                d={isSidebarOpen ? "M4 6h16M4 12h16M4 18h16" : "M4 6h16M4 12h16M4 18h16"}
              />
            </svg>
          </button>
        )}

        <div className="flex items-center gap-2.5">
          <div className="flex h-8 w-8 items-center justify-center rounded bg-sky-950 border border-sky-600 text-sky-400 font-bold font-mono text-sm tracking-tighter">
            RG
          </div>
          <div className="flex flex-col">
            <div className="flex items-center gap-2">
              <span className="font-bold tracking-tight text-slate-100 text-sm sm:text-base">
                RakshakGIS
              </span>
              <span className="hidden sm:inline-flex rounded bg-slate-800 px-1.5 py-0.2 text-[10px] font-mono text-slate-400 uppercase tracking-widest border border-slate-700">
                SIH 26191
              </span>
            </div>
            <span className="text-[10px] text-slate-400 hidden md:block">
              Multi-Hazard Risk & Relocation Decision Support
            </span>
          </div>
        </div>
      </div>

      <div className="flex items-center gap-2 sm:gap-4">
        {/* Active Region & Mode Badge */}
        <div className="hidden lg:flex items-center gap-2">
          <span className="text-xs text-slate-400 font-mono">Region:</span>
          <Badge variant="outline" size="sm" className="normal-case font-sans">
            Himalayan Pilot (Chamoli)
          </Badge>
        </div>

        <span
          className={`inline-flex items-center rounded border px-2 py-0.5 text-xs font-mono font-semibold tracking-wider uppercase ${modeConfig.badgeClass}`}
        >
          {modeConfig.label}
        </span>

        {/* Operational Clock */}
        <div className="hidden sm:flex items-center gap-1.5 font-mono text-xs text-slate-300 bg-slate-900 border border-slate-800 rounded px-2.5 py-1 tabular-nums">
          <span className="w-1.5 h-1.5 rounded-full bg-sky-400" />
          <span>{currentTime || "00:00:00 IST"}</span>
        </div>

        {/* System Health State */}
        <div className="hidden md:flex items-center border-l border-slate-800 pl-3">
          <StatusIndicator status="normal" label="Operational" />
        </div>

        {/* User / Session Information */}
        <div className="flex items-center gap-2.5 border-l border-slate-800 pl-3">
          {isAuthenticated && user ? (
            <div className="flex items-center gap-2">
              <div
                className="flex h-7 w-7 items-center justify-center rounded-full bg-sky-950 border border-sky-600 text-xs font-mono font-bold text-sky-300"
                title={`${user.full_name} (${user.email})${user.department ? ` • ${user.department}` : ""}`}
              >
                {getInitials()}
              </div>
              <div className="hidden xl:flex flex-col text-left">
                <span className="text-xs font-semibold text-slate-200 leading-tight truncate max-w-[140px]">
                  {user.full_name || user.username}
                </span>
                <span className="text-[10px] text-slate-400 font-mono">
                  {roleLabels[user.role] || user.role}
                </span>
              </div>
              <button
                type="button"
                onClick={handleLogout}
                title="Sign out of command center"
                aria-label="Sign out"
                className="rounded px-2 py-1 text-xs text-slate-400 hover:bg-slate-800 hover:text-slate-100 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-sky-500 font-mono transition-colors"
              >
                Sign Out
              </button>
            </div>
          ) : (
            <button
              type="button"
              onClick={() => router.push("/login")}
              className="rounded bg-sky-600/20 border border-sky-500/40 px-2.5 py-1 text-xs font-medium text-sky-300 hover:bg-sky-600/30 hover:text-white focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-sky-400 transition-colors"
            >
              Sign In
            </button>
          )}
        </div>
      </div>
    </header>
  );
};
