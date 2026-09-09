"use client";

import React from "react";
import Link from "next/link";
import { Badge } from "@/components/ui/Badge";
import { HabitationDetail } from "@/types/villages";

export interface VillageIdentityHeaderProps {
  habitation: HabitationDetail;
}

export const VillageIdentityHeader: React.FC<VillageIdentityHeaderProps> = ({
  habitation,
}) => {
  const coordsFormatted =
    habitation.coordinates && habitation.coordinates.length === 2
      ? `${habitation.coordinates[1].toFixed(4)}° N, ${habitation.coordinates[0].toFixed(4)}° E`
      : "Not available in source";

  const isRedZone = habitation.risk.is_red_zone_triggered;

  return (
    <div className="bg-surface-panel border border-border-subtle rounded-lg p-5 mb-5">
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        {/* Left: Settlement Identity */}
        <div>
          <div className="flex items-center gap-3 flex-wrap mb-2">
            <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-text-primary">
              {habitation.name}
            </h1>
            <span className="text-xs px-2 py-0.5 rounded bg-surface-elevated border border-border-subtle text-text-secondary">
              ID: {habitation.id}
            </span>
            {habitation.census_code && (
              <span className="text-xs px-2 py-0.5 rounded bg-surface-elevated border border-border-subtle text-text-muted">
                Census: {habitation.census_code}
              </span>
            )}
            {/* Red Zone Status Pill */}
            {isRedZone ? (
              <Badge variant="danger" size="sm" aria-label="Red Zone Trigger Status: Active Trigger Proposal">
                Red Zone Trigger Active
              </Badge>
            ) : (
              <Badge variant="outline" size="sm" aria-label="Red Zone Trigger Status: Standard Monitoring">
                Standard Monitoring
              </Badge>
            )}
          </div>

          {/* Context Metadata */}
          <div className="flex items-center gap-4 text-xs text-text-muted flex-wrap">
            <span>
              <strong className="text-text-secondary font-medium">Region:</strong> {habitation.region_profile_id || "Not available in source"}
            </span>
            <span aria-hidden="true" className="text-border-strong">•</span>
            <span>
              <strong className="text-text-secondary font-medium">District:</strong> {habitation.district || "Not available in source"}
            </span>
            <span aria-hidden="true" className="text-border-strong">•</span>
            <span>
              <strong className="text-text-secondary font-medium">Block:</strong> {habitation.block || "Not available in source"}
            </span>
            <span aria-hidden="true" className="text-border-strong">•</span>
            <span>
              <strong className="text-text-secondary font-medium">Location:</strong> {coordsFormatted}
            </span>
            {habitation.elevation_m !== undefined && habitation.elevation_m !== null && (
              <>
                <span aria-hidden="true" className="text-border-strong">•</span>
                <span>
                  <strong className="text-text-secondary font-medium">Elevation:</strong> {habitation.elevation_m} m
                </span>
              </>
            )}
          </div>
        </div>

        {/* Right: Map Quick-Link */}
        <div className="flex items-center gap-3 self-start lg:self-center">
          <Link
            href="/gis"
            className="inline-flex items-center gap-2 px-3 py-1.5 text-xs font-medium rounded-md border border-border-strong bg-surface-elevated text-text-primary hover:bg-surface-elevated/80 transition-colors focus:outline-none focus:ring-1 focus:ring-focus-ring"
            aria-label="View on GIS Canvas"
          >
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7"
              />
            </svg>
            View on GIS Canvas
          </Link>
        </div>
      </div>

      {/* Red Zone Warning Alert if triggered */}
      {isRedZone && (
        <div
          className="mt-4 p-3 bg-red-50 dark:bg-red-950/40 border border-red-200 dark:border-red-800/60 rounded-md flex items-start gap-2.5 text-xs text-red-900 dark:text-red-200 shadow-xs"
          role="alert"
        >
          <svg
            className="w-4 h-4 text-red-600 dark:text-red-400 shrink-0 mt-0.5"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              strokeWidth={2}
              d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z"
            />
          </svg>
          <div>
            <strong className="font-semibold text-red-950 dark:text-red-300">Dynamic Red Zone Trigger Tripped:</strong>{" "}
            This settlement has exceeded dynamic event thresholds under regional profile criteria. <span className="sr-only">(M3-11 dynamic trigger engine)</span> Official officer review required prior to executive evacuation declaration.
          </div>
        </div>
      )}
    </div>
  );
};
