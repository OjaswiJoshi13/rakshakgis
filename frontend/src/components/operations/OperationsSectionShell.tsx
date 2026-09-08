"use client";

import React from "react";
import Link from "next/link";
import { ChevronRight, Shield, Layers } from "lucide-react";
import { Badge } from "@/components/ui/Badge";
import { cn } from "@/lib/utils";

export interface OperationsSectionShellProps {
  title: string;
  description: string;
  chunkId: string;
  chunkTitle: string;
  prerequisiteChunk?: string;
  actionToolbar?: React.ReactNode;
  children: React.ReactNode;
  className?: string;
}

export const OperationsSectionShell: React.FC<OperationsSectionShellProps> = ({
  title,
  description,
  chunkId,
  chunkTitle,
  prerequisiteChunk,
  actionToolbar,
  children,
  className,
}) => {
  return (
    <div className={cn("space-y-6", className)}>
      {/* Breadcrumbs & Section Hierarchy */}
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-border-subtle pb-4 print:hidden">
        <div>
          <nav aria-label="Breadcrumb" className="flex items-center gap-1.5 text-xs text-text-muted font-mono mb-1.5">
            <Link
              href="/operations"
              className="text-text-secondary hover:text-text-primary transition-colors"
            >
              Operations
            </Link>
            <ChevronRight className="h-3 w-3 text-text-muted" />
            <span className="text-text-primary font-medium">{title}</span>
          </nav>

          <div className="flex flex-wrap items-center gap-2.5">
            <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-text-primary">
              {title}
            </h1>
            <span className="sr-only" data-testid="dev-chunk-id">{chunkId}</span>
            <span className="sr-only" data-testid="dev-chunk-title">{chunkTitle}</span>
          </div>

          <p className="text-xs sm:text-sm text-text-secondary mt-1 max-w-3xl">
            {description}
          </p>
        </div>

        {/* Action Toolbar slot for operational workflows */}
        {actionToolbar && (
          <div className="flex items-center gap-2 self-start sm:self-auto">
            {actionToolbar}
          </div>
        )}
      </div>

      {/* Operational Protocol Context Strip */}
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-md border border-border-subtle bg-surface-raised/60 px-3.5 py-2 text-xs text-text-secondary font-mono print:hidden">
        <div className="flex items-center gap-2">
          <Shield className="h-4 w-4 text-[#0969da] dark:text-[#2f81f7] shrink-0" />
          <span>
            Protocol: <strong className="text-text-primary font-semibold">Rule 12 Mandate</strong> — Officer Review &amp; Statutory Approval Required
          </span>
        </div>

        {prerequisiteChunk && (
          <span className="sr-only" data-testid="dev-engine-binding">
            Engine Binding: {prerequisiteChunk}
          </span>
        )}
      </div>

      {/* Main Operational Workspace Body */}
      <div className="w-full">
        {children}
      </div>
    </div>
  );
};
