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
      : "Coordinates unavailable";

  const isRedZone = habitation.risk.is_red_zone_triggered;

  return (
    <div className="bg-slate-900 border border-slate-800 rounded-lg p-6 mb-6 shadow-sm">
      <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
        {/* Left: Settlement Identity */}
        <div>
          <div className="flex items-center gap-3 flex-wrap mb-2">
            <h1 className="text-2xl font-bold tracking-tight text-slate-100 font-mono">
              {habitation.name}
            </h1>
            <span className="text-xs font-mono px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-300">
              ID: {habitation.id}
            </span>
            {habitation.census_code && (
              <span className="text-xs font-mono px-2 py-0.5 rounded bg-slate-800 border border-slate-700 text-slate-400">
                Census: {habitation.census_code}
              </span>
            )}
            {/* Red Zone Status Pill */}
            {isRedZone ? (
              <Badge variant="danger" size="sm" aria-label="Red Zone Trigger Status: Active Trigger Proposal">
                RED ZONE TRIGGER ACTIVE
              </Badge>
            ) : (
              <Badge variant="outline" size="sm" aria-label="Red Zone Trigger Status: Standard Monitoring">
                STANDARD MONITORING
              </Badge>
            )}
          </div>

          {/* Context Metadata */}
          <div className="flex items-center gap-4 text-xs font-mono text-slate-400 flex-wrap">
            <span>
              <strong className="text-slate-500">Region:</strong> {habitation.region_profile_id || "—"}
            </span>
            <span aria-hidden="true" className="text-slate-700">•</span>
            <span>
              <strong className="text-slate-500">District:</strong> {habitation.district || "—"}
            </span>
            <span aria-hidden="true" className="text-slate-700">•</span>
            <span>
              <strong className="text-slate-500">Block:</strong> {habitation.block || "—"}
            </span>
            <span aria-hidden="true" className="text-slate-700">•</span>
            <span>
              <strong className="text-slate-500">Location:</strong> {coordsFormatted}
            </span>
            {habitation.elevation_m !== undefined && habitation.elevation_m !== null && (
              <>
                <span aria-hidden="true" className="text-slate-700">•</span>
                <span>
                  <strong className="text-slate-500">Elevation:</strong> {habitation.elevation_m} m
                </span>
              </>
            )}
          </div>
        </div>

        {/* Right: Map Quick-Link */}
        <div className="flex items-center gap-3 self-start lg:self-center">
          <Link
            href="/gis"
            className="inline-flex items-center gap-2 px-3 py-1.5 text-xs font-mono font-medium rounded border border-sky-700/60 bg-sky-950/40 text-sky-300 hover:bg-sky-900/60 transition-colors focus:outline-none focus:ring-1 focus:ring-sky-500"
            aria-label={`View ${habitation.name} on GIS Interactive Map`}
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
          className="mt-4 p-3 bg-red-950/40 border border-red-800/60 rounded-md flex items-start gap-2.5 text-xs text-red-200"
          role="alert"
        >
          <svg
            className="w-4 h-4 text-red-400 shrink-0 mt-0.5"
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
            <strong className="font-semibold text-red-300">Dynamic Red Zone Trigger Tripped:</strong>{" "}
            This settlement has exceeded dynamic event thresholds under regional profile criteria (M3-11 dynamic trigger engine). Official officer review required prior to executive evacuation declaration.
          </div>
        </div>
      )}
    </div>
  );
};
