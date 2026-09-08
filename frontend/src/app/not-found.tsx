"use client";

import React from "react";
import Link from "next/link";
import { Compass, ArrowLeft } from "lucide-react";
import { Button } from "@/components/ui/Button";

export default function NotFound() {
  return (
    <div className="min-h-screen flex flex-col items-center justify-center p-6 bg-surface-bg text-text-primary">
      <div className="w-full max-w-md p-8 rounded-xl border border-border-subtle bg-surface-panel shadow-sm text-center space-y-4">
        <div className="mx-auto flex h-12 w-12 items-center justify-center rounded-full bg-surface-elevated border border-border-subtle text-text-muted">
          <Compass className="h-6 w-6 text-sky-600 dark:text-sky-400" />
        </div>
        <div>
          <span className="text-xs font-mono font-semibold uppercase tracking-wider text-text-muted">
            Status Code 404
          </span>
          <h1 className="text-xl font-bold text-text-primary mt-1">
            Sector / View Not Found
          </h1>
          <p className="text-xs text-text-muted mt-2 leading-relaxed">
            The requested spatial viewport, operational module, or record identifier does not exist or has been relocated within the command registry.
          </p>
        </div>
        <div className="pt-2">
          <Link href="/dashboard">
            <Button variant="primary" size="sm" className="gap-2">
              <ArrowLeft className="h-4 w-4" />
              <span>Return to Command Overview</span>
            </Button>
          </Link>
        </div>
      </div>
    </div>
  );
}
