"use client";

import React from "react";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from "@/components/ui/Card";
import { Alert } from "@/components/ui/Alert";
import { Badge } from "@/components/ui/Badge";

export const AlertsNoticeCard: React.FC = () => {
  return (
    <Card variant="bordered" className="space-y-3">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Operational Alerts & Threshold Triggers</CardTitle>
            <CardDescription>
              Early warning thresholds and dynamic red zone event triggers under regional SOPs.
            </CardDescription>
          </div>
          <span className="font-mono text-[11px] text-text-secondary bg-surface-elevated border border-border-subtle px-2 py-0.5 rounded">
            Early Warning Pipeline<span className="sr-only"> M6-05</span>
          </span>
        </div>
      </CardHeader>

      <CardContent className="space-y-3">
        <Alert severity="info" title="Dynamic Hazard Monitoring Protocol Active">
          Automated threshold triggers evaluate continuous precipitation, seismic intensity, and terrain
          slope against regional limits (e.g., IMD 64.5mm/24h heavy rainfall standard). Dynamic Red Zone
          proposals require statutory District Officer sign-off under SOP-RZ-01 prior to evacuation dispatch.
        </Alert>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-2.5 pt-1">
          <div className="bg-surface-elevated border border-border-subtle rounded-lg p-3 space-y-1 shadow-2xs">
            <span className="text-[10px] font-mono uppercase tracking-wider text-text-muted">
              Rainfall Alert Threshold
            </span>
            <div className="text-base font-bold font-mono text-text-primary">64.5 mm / 24h</div>
            <p className="text-[11px] text-text-secondary leading-tight">
              Standard IMD heavy precipitation boundary.
            </p>
          </div>

          <div className="bg-surface-elevated border border-border-subtle rounded-lg p-3 space-y-1 shadow-2xs">
            <span className="text-[10px] font-mono uppercase tracking-wider text-text-muted">
              Critical Slope Trigger
            </span>
            <div className="text-base font-bold font-mono text-text-primary">&ge; 25.0&deg;</div>
            <p className="text-[11px] text-text-secondary leading-tight">
              Compound danger trigger with historical slides.
            </p>
          </div>

          <div className="bg-surface-elevated border border-border-subtle rounded-lg p-3 space-y-1 shadow-2xs">
            <span className="text-[10px] font-mono uppercase tracking-wider text-text-muted">
              Geodesic Buffer
            </span>
            <div className="text-base font-bold font-mono text-text-primary">500 m Buffer</div>
            <p className="text-[11px] text-text-secondary leading-tight">
              Circular safety perimeter for point settlements.
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
};
