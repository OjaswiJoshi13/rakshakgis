import React from "react";
import { cn } from "@/lib/utils";
import { OperationalStatus, OPERATIONAL_STATUS_CONFIG } from "@/design-system/tokens";

export interface StatusIndicatorProps
  extends React.HTMLAttributes<HTMLDivElement> {
  status?: OperationalStatus;
  label?: string;
  showPulse?: boolean;
}

export const StatusIndicator: React.FC<StatusIndicatorProps> = ({
  status = "normal",
  label,
  showPulse = false,
  className,
  ...props
}) => {
  const config = OPERATIONAL_STATUS_CONFIG[status];
  const displayLabel = label || config.label;

  return (
    <div
      className={cn("inline-flex items-center gap-2 text-xs font-mono", className)}
      {...props}
    >
      <span className="relative flex h-2 w-2">
        {showPulse && status === "critical" && (
          <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-red-400 opacity-75" />
        )}
        <span
          className={cn(
            "relative inline-flex rounded-full h-2 w-2",
            config.dotClass
          )}
        />
      </span>
      <span className="text-slate-300 font-medium tracking-wide uppercase">
        {displayLabel}
      </span>
    </div>
  );
};
