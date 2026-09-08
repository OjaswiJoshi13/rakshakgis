import React from "react";
import { cn } from "@/lib/utils";

export interface MetricCardProps extends React.HTMLAttributes<HTMLDivElement> {
  label: React.ReactNode;
  value: string | number;
  unit?: string;
  subtext?: React.ReactNode;
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
    normal: "border-border-subtle",
    info: "border-border-subtle",
    warning: "border-amber-400/60 dark:border-amber-700/60",
    critical: "border-red-800/80 hover:border-red-700",
  };

  const statusIndicatorStyles = {
    normal: "bg-emerald-600 dark:bg-emerald-400",
    info: "bg-slate-400",
    warning: "bg-amber-500",
    critical: "bg-red-500",
  };

  return (
    <div
      className={cn(
        "rounded-lg bg-surface-panel border p-4 transition-all relative overflow-hidden flex flex-col justify-between",
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
          <span className="text-xs font-semibold text-text-muted">
            {label}
          </span>
        </div>
        {icon && <span className="text-text-muted shrink-0">{icon}</span>}
      </div>

      <div className="flex items-baseline gap-1.5 my-1">
        <span className="text-2xl sm:text-3xl font-bold tracking-tight text-text-primary tabular-nums">
          {value}
        </span>
        {unit && (
          <span className="text-xs font-semibold text-text-muted">
            {unit}
          </span>
        )}
      </div>

      {(subtext || trendLabel) && (
        <div className="flex items-center justify-between text-xs text-text-muted mt-2 pt-2 border-t border-border-subtle">
          {subtext && <span>{subtext}</span>}
          {trendLabel && (
            <span
              className={cn(
                "font-mono text-xs font-medium",
                trend === "up" && "text-amber-600 dark:text-amber-400",
                trend === "down" && "text-emerald-600 dark:text-emerald-400",
                trend === "neutral" && "text-text-muted"
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
