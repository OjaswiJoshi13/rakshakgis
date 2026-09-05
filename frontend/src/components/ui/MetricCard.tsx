import React from "react";
import { cn } from "@/lib/utils";

export interface MetricCardProps extends React.HTMLAttributes<HTMLDivElement> {
  label: string;
  value: string | number;
  unit?: string;
  subtext?: string;
  trend?: "up" | "down" | "neutral";
  trendLabel?: string;
  status?: "normal" | "warning" | "critical" | "info";
  icon?: React.ReactNode;
}

export const MetricCard: React.FC<MetricCardProps> = ({
  label,
  value,
  unit,
  subtext,
  trend,
  trendLabel,
  status = "normal",
  icon,
  className,
  ...props
}) => {
  const statusBorderStyles = {
    normal: "border-slate-800 hover:border-slate-700",
    info: "border-sky-800/60 hover:border-sky-700",
    warning: "border-amber-800/60 hover:border-amber-700",
    critical: "border-red-800/80 hover:border-red-700",
  };

  const statusIndicatorStyles = {
    normal: "bg-emerald-500",
    info: "bg-sky-500",
    warning: "bg-amber-500",
    critical: "bg-red-500 animate-pulse",
  };

  return (
    <div
      className={cn(
        "rounded-lg bg-slate-900 border p-4 transition-all relative overflow-hidden flex flex-col justify-between",
        statusBorderStyles[status],
        className
      )}
      {...props}
    >
      <div className="flex items-start justify-between gap-2 mb-2">
        <div className="flex items-center gap-2">
          <span
            aria-hidden="true"
            className={cn(
              "w-2 h-2 rounded-full shrink-0",
              statusIndicatorStyles[status]
            )}
          />
          <span className="text-xs font-medium uppercase tracking-wider text-slate-400">
            {label}
          </span>
        </div>
        {icon && <span className="text-slate-400 shrink-0">{icon}</span>}
      </div>

      <div className="flex items-baseline gap-1.5 my-1">
        <span className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-100 tabular-nums font-mono">
          {value}
        </span>
        {unit && (
          <span className="text-xs font-semibold text-slate-400 uppercase">
            {unit}
          </span>
        )}
      </div>

      {(subtext || trendLabel) && (
        <div className="flex items-center justify-between text-xs text-slate-400 mt-2 pt-2 border-t border-slate-800/60">
          {subtext && <span>{subtext}</span>}
          {trendLabel && (
            <span
              className={cn(
                "font-mono text-xs font-medium",
                trend === "up" && "text-amber-400",
                trend === "down" && "text-emerald-400",
                trend === "neutral" && "text-slate-400"
              )}
            >
              {trend === "up" && "▲ "}
              {trend === "down" && "▼ "}
              {trendLabel}
            </span>
          )}
        </div>
      )}
    </div>
  );
};
