import React from "react";
import { cn } from "@/lib/utils";

export interface AlertProps extends React.HTMLAttributes<HTMLDivElement> {
  severity?: "info" | "warning" | "danger" | "success";
  title?: string;
  icon?: React.ReactNode;
  onClose?: () => void;
}

export const Alert: React.FC<AlertProps> = ({
  severity = "info",
  title,
  icon,
  onClose,
  children,
  className,
  ...props
}) => {
  const severityStyles = {
    info: "bg-sky-950/60 border-sky-800 text-sky-200",
    warning: "bg-amber-950/60 border-amber-800 text-amber-200",
    danger: "bg-red-950/80 border-red-700 text-red-200",
    success: "bg-emerald-950/60 border-emerald-800 text-emerald-200",
  };

  const defaultIcons = {
    info: (
      <svg
        className="w-4 h-4 text-sky-400 shrink-0"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
        aria-hidden="true"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
        />
      </svg>
    ),
    warning: (
      <svg
        className="w-4 h-4 text-amber-400 shrink-0"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
        aria-hidden="true"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
        />
      </svg>
    ),
    danger: (
      <svg
        className="w-4 h-4 text-red-400 shrink-0"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
        aria-hidden="true"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
        />
      </svg>
    ),
    success: (
      <svg
        className="w-4 h-4 text-emerald-400 shrink-0"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
        aria-hidden="true"
      >
        <path
          strokeLinecap="round"
          strokeLinejoin="round"
          strokeWidth={2}
          d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"
        />
      </svg>
    ),
  };

  return (
    <div
      role="alert"
      className={cn(
        "rounded-md border p-3.5 flex items-start gap-3 text-sm transition-all",
        severityStyles[severity],
        className
      )}
      {...props}
    >
      <div className="pt-0.5">{icon || defaultIcons[severity]}</div>
      <div className="flex-1 min-w-0">
        {title && (
          <h4 className="font-semibold leading-tight text-slate-100 text-sm mb-1">
            {title}
          </h4>
        )}
        <div className="text-xs text-slate-300 leading-relaxed">{children}</div>
      </div>
      {onClose && (
        <button
          type="button"
          onClick={onClose}
          aria-label="Dismiss alert"
          className="text-slate-400 hover:text-slate-100 p-1 -mr-1 -mt-1 rounded hover:bg-slate-800/60 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-slate-400"
        >
          <svg
            className="w-4 h-4"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M6 18L18 6M6 6l12 12"
            />
          </svg>
        </button>
      )}
    </div>
  );
};
