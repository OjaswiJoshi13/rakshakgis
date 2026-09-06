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
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-slate-800 pb-4">
        <div>
          <nav aria-label="Breadcrumb" className="flex items-center gap-1.5 text-xs text-slate-400 font-mono mb-1.5">
            <Link
              href="/operations"
              className="hover:text-slate-200 transition-colors"
            >
              Operations
            </Link>
            <ChevronRight className="h-3 w-3 text-slate-400" />
            <span className="text-sky-400 font-semibold">{title}</span>
          </nav>

          <div className="flex flex-wrap items-center gap-2.5">
            <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-slate-100">
              {title}
            </h1>
            <Badge variant="outline" size="sm" className="font-mono text-sky-300 border-sky-600/50">
              {chunkId}
            </Badge>
            <span className="text-xs font-mono text-slate-400 hidden sm:inline-block">
              {chunkTitle}
            </span>
          </div>

          <p className="text-xs sm:text-sm text-slate-400 mt-1 max-w-3xl">
            {description}
          </p>
        </div>

        {/* Action Toolbar slot for future chunk workflows */}
        {actionToolbar && (
          <div className="flex items-center gap-2 self-start sm:self-auto">
            {actionToolbar}
          </div>
        )}
      </div>

      {/* Operational Protocol & Dependency Context Strip */}
      <div className="flex flex-wrap items-center justify-between gap-3 rounded-lg border border-slate-800/80 bg-slate-900/40 px-3.5 py-2.5 text-xs text-slate-300 font-mono">
        <div className="flex items-center gap-2">
          <Shield className="h-4 w-4 text-sky-400 shrink-0" />
          <span>
            Protocol: <strong className="text-slate-200">Rule 12 Mandate</strong> — Officer Review & Statutory Approval Required
          </span>
        </div>

        {prerequisiteChunk && (
          <div className="flex items-center gap-2 text-slate-400">
            <Layers className="h-3.5 w-3.5 text-slate-400 shrink-0" />
            <span>
              Engine Binding: <span className="text-emerald-400">{prerequisiteChunk}</span>
            </span>
          </div>
        )}
      </div>

      {/* Main Operational Workspace Body */}
      <div className="w-full">
        {children}
      </div>
    </div>
  );
};
