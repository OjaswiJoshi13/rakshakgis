import React, { forwardRef } from "react";
import { cn } from "@/lib/utils";

export interface ButtonProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "tertiary" | "outline" | "ghost" | "danger";
  size?: "sm" | "md" | "lg";
  isLoading?: boolean;
  leftIcon?: React.ReactNode;
  rightIcon?: React.ReactNode;
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  (
    {
      className,
      variant = "primary",
      size = "md",
      isLoading = false,
      leftIcon,
      rightIcon,
      disabled,
      children,
      ...props
    },
    ref
  ) => {
    const baseStyles =
      "inline-flex items-center justify-center font-medium rounded-md transition-all duration-150 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-offset-1 focus-visible:ring-offset-transparent disabled:opacity-50 disabled:pointer-events-none select-none whitespace-nowrap";

    const variantStyles = {
      // Primary: high-emphasis solid action — sky blue, always visible light+dark
      primary:
        "bg-sky-600 hover:bg-sky-700 active:bg-sky-800 text-white shadow-xs border border-sky-600/80 focus-visible:ring-sky-400 active:scale-[0.99]",
      // Secondary: supporting action — neutral surface, clearly readable both modes
      secondary:
        "bg-slate-100 hover:bg-slate-200 active:bg-slate-300 text-slate-800 border border-slate-300 dark:bg-slate-800 dark:hover:bg-slate-700 dark:active:bg-slate-600 dark:text-slate-100 dark:border-slate-600 focus-visible:ring-slate-400 active:scale-[0.99]",
      // Tertiary: low-emphasis, no border — for subtle contextual actions
      tertiary:
        "bg-transparent hover:bg-slate-100 active:bg-slate-200 text-slate-700 border border-transparent dark:hover:bg-slate-800 dark:active:bg-slate-700 dark:text-slate-300 focus-visible:ring-slate-400",
      // Outline: bordered transparent — readable in both modes
      outline:
        "bg-transparent hover:bg-slate-100 active:bg-slate-200 text-slate-700 border border-slate-300 dark:hover:bg-slate-800 dark:active:bg-slate-700 dark:text-slate-200 dark:border-slate-600 focus-visible:ring-slate-400 active:scale-[0.99]",
      // Ghost: frameless — for toolbars and compact secondary actions
      ghost:
        "bg-transparent hover:bg-slate-100 active:bg-slate-200 text-slate-600 hover:text-slate-900 dark:hover:bg-slate-800 dark:text-slate-400 dark:hover:text-slate-100 focus-visible:ring-slate-400",
      // Danger: destructive action — red, high visibility
      danger:
        "bg-red-600 hover:bg-red-700 active:bg-red-800 text-white shadow-xs border border-red-600 focus-visible:ring-red-400 active:scale-[0.99]",
    };

    const sizeStyles = {
      sm: "h-7 px-2.5 text-xs gap-1.5",
      md: "h-8 px-3 text-xs gap-1.5",
      lg: "h-9 px-3.5 text-sm gap-2",
    };

    return (
      <button
        ref={ref}
        disabled={disabled || isLoading}
        aria-busy={isLoading}
        className={cn(
          baseStyles,
          variantStyles[variant],
          sizeStyles[size],
          className
        )}
        {...props}
      >
        {isLoading && (
          <svg
            className="animate-spin shrink-0 h-3.5 w-3.5 text-current"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
            role="status"
            aria-label="Loading"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            />
          </svg>
        )}
        {!isLoading && leftIcon && (
          <span className="inline-flex shrink-0 items-center">{leftIcon}</span>
        )}
        {children}
        {!isLoading && rightIcon && (
          <span className="inline-flex shrink-0 items-center">{rightIcon}</span>
        )}
      </button>
    );
  }
);

Button.displayName = "Button";
