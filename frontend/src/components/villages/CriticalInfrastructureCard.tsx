"use client";

import React from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";

export const CriticalInfrastructureCard: React.FC = () => {
  return (
    <Card className="h-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-base font-semibold text-text-primary flex items-center gap-2">
            <svg className="w-4 h-4 text-text-muted" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4"
              />
            </svg>
            Critical Infrastructure & Public Assets
          </CardTitle>
          <span className="text-xs font-mono text-text-muted">Asset Registry</span>
        </div>
      </CardHeader>

      <CardContent>
        <div className="p-4 bg-surface-elevated border border-border-subtle rounded-md text-center">
          <div className="inline-flex items-center justify-center w-8 h-8 rounded-full bg-surface-panel border border-border-subtle text-text-muted mb-2">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
          </div>
          <div className="text-sm font-medium text-text-secondary mb-1">
            Infrastructure Asset Inventory Unavailable
          </div>
          <p className="text-xs text-text-muted max-w-sm mx-auto leading-relaxed">
            Village infrastructure asset inventory (health centers, schools, lifeline roads) is not currently provided by the backend API. In compliance with RakshakGIS data integrity standards, no assets are fabricated.
          </p>
        </div>
      </CardContent>
    </Card>
  );
};
