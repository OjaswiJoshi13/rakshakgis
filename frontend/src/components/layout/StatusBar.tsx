import React from "react";

export const StatusBar: React.FC = () => {
  const version = process.env.NEXT_PUBLIC_APP_VERSION || "0.1.0";

  return (
    <footer
      className="fixed bottom-0 left-0 right-0 z-40 flex h-8 w-full items-center justify-between border-t border-border-subtle bg-surface-panel px-4 text-[11px] font-mono text-text-muted select-none transition-colors"
      role="contentinfo"
      aria-label="Operational System Status"
    >
      <div className="flex items-center gap-4">
        <div className="flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
          <span className="text-text-primary">SYSTEM: NORMAL</span>
        </div>
        <div className="hidden sm:flex items-center gap-1">
          <span className="text-text-muted">CRS:</span>
          <span className="text-text-secondary">EPSG:4326 (WGS 84)</span>
        </div>
        <div className="hidden md:flex items-center gap-1">
          <span className="text-text-muted">PROFILE:</span>
          <span className="text-text-secondary">himalayan_pilot (Chamoli)</span>
        </div>
      </div>

      <div className="flex items-center gap-4">
        <div className="hidden sm:flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-emerald-500" />
          <span className="text-text-primary">TELEMETRY: CONNECTED</span>
        </div>
        <div className="flex items-center gap-1">
          <span className="text-text-muted">BUILD:</span>
          <span className="text-text-secondary">{version}</span>
        </div>
      </div>
    </footer>
  );
};
