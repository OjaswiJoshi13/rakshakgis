"use client";

import React, { useState, useEffect } from "react";
import { DATA_MODE_CONFIG, DataMode } from "@/design-system/tokens";
import { StatusIndicator } from "@/components/ui/StatusIndicator";
import { Badge } from "@/components/ui/Badge";

export interface CommandHeaderProps {
  onToggleSidebar?: () => void;
  isSidebarOpen?: boolean;
}

export const CommandHeader: React.FC<CommandHeaderProps> = ({
  onToggleSidebar,
  isSidebarOpen = true,
}) => {
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

        {/* User / Session Placeholder (Auth Chunk M5-02 will wire this) */}
        <div className="flex items-center gap-2 border-l border-slate-800 pl-3">
          <div
            className="flex h-7 w-7 items-center justify-center rounded-full bg-slate-800 border border-slate-700 text-xs text-slate-300 font-mono"
            title="Disaster Management Officer (Guest/Dev)"
          >
            OP
          </div>
        </div>
      </div>
    </header>
  );
};
