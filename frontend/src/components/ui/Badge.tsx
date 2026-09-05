import React from "react";
import { cn } from "@/lib/utils";
import {
  RiskBand,
  RISK_BANDS,
  RelocationPriorityBand,
  RELOCATION_PRIORITY_BANDS,
  getRiskBandFromScore,
  getRelocationPriorityBand,
} from "@/design-system/tokens";

export interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: "default" | "outline" | "success" | "warning" | "danger" | "info";
  size?: "sm" | "md";
}

export const Badge: React.FC<BadgeProps> = ({
  className,
  variant = "default",
  size = "sm",
  children,
  ...props
}) => {
  const variantStyles = {
    default: "bg-slate-800 text-slate-200 border-slate-700",
    outline: "bg-transparent text-slate-300 border-slate-700",
    success: "bg-emerald-950/80 text-emerald-300 border-emerald-700/60",
    warning: "bg-amber-950/80 text-amber-300 border-amber-700/60",
    danger: "bg-red-950/80 text-red-200 border-red-700/60",
    info: "bg-sky-950/80 text-sky-300 border-sky-700/60",
  };

  const sizeStyles = {
    sm: "px-2 py-0.5 text-xs",
    md: "px-2.5 py-1 text-xs font-medium",
  };

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 font-medium rounded border tracking-wide uppercase font-mono",
        variantStyles[variant],
        sizeStyles[size],
        className
      )}
      {...props}
    >
      {children}
    </span>
  );
};

export interface RiskBadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  band?: RiskBand;
  score?: number;
  showScore?: boolean;
}

export const RiskBadge: React.FC<RiskBadgeProps> = ({
  band,
  score,
  showScore = true,
  className,
  ...props
}) => {
  const resolvedBand: RiskBand =
    band ?? (score !== undefined ? getRiskBandFromScore(score) : "safe");
  const config = RISK_BANDS[resolvedBand];

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 font-medium rounded border px-2 py-0.5 text-xs font-mono uppercase tracking-wider",
        config.badgeClass,
        className
      )}
      title={`Risk Band: ${config.label} (${config.min}–${config.max})`}
      {...props}
    >
      <span
        aria-hidden="true"
        className={cn("w-1.5 h-1.5 rounded-full shrink-0", config.dotColor)}
      />
      <span>{config.label}</span>
      {showScore && score !== undefined && (
        <span className="opacity-80 font-normal tabular-nums">
          [{score.toFixed(1)}]
        </span>
      )}
    </span>
  );
};

export interface RelocationBadgeProps
  extends React.HTMLAttributes<HTMLSpanElement> {
  band?: RelocationPriorityBand;
  score?: number;
}

export const RelocationBadge: React.FC<RelocationBadgeProps> = ({
  band,
  score,
  className,
  ...props
}) => {
  const resolvedBand: RelocationPriorityBand =
    band ??
    (score !== undefined ? getRelocationPriorityBand(score) : "monitor");
  const config = RELOCATION_PRIORITY_BANDS[resolvedBand];

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1 font-medium rounded border px-2 py-0.5 text-xs font-mono uppercase tracking-wider",
        config.badgeClass,
        className
      )}
      title={`Relocation Priority: ${config.label}`}
      {...props}
    >
      <span>{config.label}</span>
      {score !== undefined && (
        <span className="opacity-80 font-normal tabular-nums">
          ({score.toFixed(1)})
        </span>
      )}
    </span>
  );
};
