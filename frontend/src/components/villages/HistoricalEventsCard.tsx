"use client";

import React from "react";
import { Card, CardHeader, CardTitle, CardContent } from "@/components/ui/Card";

export const HistoricalEventsCard: React.FC = () => {
  return (
    <Card className="h-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="text-base font-medium text-slate-100 flex items-center gap-2">
            <svg className="w-4 h-4 text-slate-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
            Historical Disaster Events
          </CardTitle>
          <span className="text-xs font-mono text-slate-500">Registry</span>
        </div>
      </CardHeader>

      <CardContent>
        <div className="p-4 bg-slate-950/60 border border-slate-800 rounded-lg text-center">
          <div className="inline-flex items-center justify-center w-8 h-8 rounded-full bg-slate-800/80 text-slate-400 mb-2">
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
              />
            </svg>
          </div>
          <div className="text-sm font-medium text-slate-300 mb-1">
            Historical Event Registry Unavailable
          </div>
          <p className="text-xs text-slate-500 max-w-sm mx-auto leading-relaxed">
            Historical disaster event history endpoint is not yet exposed by the backend API. In compliance with RakshakGIS data integrity standards, no historical events are fabricated.
          </p>
        </div>
      </CardContent>
    </Card>
  );
};
