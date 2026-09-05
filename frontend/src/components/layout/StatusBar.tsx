import React from "react";

export const StatusBar: React.FC = () => {
  const version = process.env.NEXT_PUBLIC_APP_VERSION || "0.1.0";
  const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL || "http://localhost:8000/api/v1";

  return (
    <footer
      className="fixed bottom-0 left-0 right-0 z-40 flex h-8 w-full items-center justify-between border-t border-slate-800 bg-slate-950 px-4 text-[11px] font-mono text-slate-400 select-none"
      role="contentinfo"
      aria-label="Operational System Status"
    >
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
          <span className="text-slate-300">SYSTEM: NORMAL</span>
        </div>
        <div className="hidden sm:flex items-center gap-1">
          <span className="text-slate-400">CRS:</span>
          <span className="text-slate-200">EPSG:4326 (WGS 84)</span>
        </div>
        <div className="hidden md:flex items-center gap-1">
          <span className="text-slate-400">PROFILE:</span>
          <span className="text-slate-200">himalayan_pilot (Chamoli)</span>
        </div>
      </div>

      <div className="flex items-center gap-4">
        <div className="hidden sm:flex items-center gap-1">
          <span className="text-slate-400">API:</span>
          <span className="text-slate-300 truncate max-w-[180px]" title={apiBase}>
            FastAPI (:8000)
          </span>
        </div>
        <div className="flex items-center gap-1">
          <span className="text-slate-400">VER:</span>
          <span className="text-slate-200">{version}</span>
        </div>
      </div>
    </footer>
  );
};
