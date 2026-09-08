"use client";

import React from "react";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { CandidateSiteRead } from "@/types/dashboard";

export interface CandidateSitesTableProps {
  sites?: CandidateSiteRead[] | null;
  totalCount?: number;
  isLoading?: boolean;
  isError?: boolean;
  errorMessage?: string | null;
}

export const CandidateSitesTable: React.FC<CandidateSitesTableProps> = ({
  sites,
  totalCount,
  isLoading = false,
  isError = false,
  errorMessage,
}) => {
  const getStatusBadge = (status: string) => {
    switch (status.toLowerCase()) {
      case "active":
        return (
          <Badge variant="success" size="sm" className="capitalize">
            Active
          </Badge>
        );
      case "approved":
        return (
          <Badge variant="info" size="sm" className="capitalize">
            Approved
          </Badge>
        );
      case "proposed":
        return (
          <Badge variant="outline" size="sm" className="capitalize">
            Proposed
          </Badge>
        );
      case "rejected":
        return (
          <Badge variant="danger" size="sm" className="capitalize">
            Rejected
          </Badge>
        );
      default:
        return (
          <Badge variant="outline" size="sm" className="capitalize">
            {status}
          </Badge>
        );
    }
  };

  return (
    <Card variant="elevated" className="space-y-4">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle>Candidate Relocation Sites</CardTitle>
            <CardDescription>
              Verified safe havens catalog evaluated against slope, flood buffers, and carrying capacity constraints.
            </CardDescription>
          </div>
          {totalCount !== undefined && (
            <span className="text-xs font-mono font-medium text-text-secondary bg-surface-elevated border border-border-subtle px-2 py-1 rounded">
              {totalCount} Total Registered Sites
            </span>
          )}
        </div>
      </CardHeader>

      <CardContent>
        {isLoading ? (
          <div className="py-8 text-center text-text-muted font-mono text-sm animate-pulse">
            Loading candidate relocation safe havens...
          </div>
        ) : isError ? (
          <div className="rounded-lg border border-red-200 bg-red-50 dark:border-red-900/60 dark:bg-red-950/30 p-4 text-sm text-red-900 dark:text-red-200">
            <div className="font-semibold mb-1 text-red-950 dark:text-red-100">Failed to Load Candidate Sites</div>
            <p className="text-xs text-red-800 dark:text-red-300">
              {errorMessage || "Unable to retrieve relocation sites from backend."}
            </p>
          </div>
        ) : !sites || sites.length === 0 ? (
          <div className="py-8 text-center text-text-muted text-sm font-mono">
            No candidate relocation sites found for the active region.
          </div>
        ) : (
          <div className="overflow-x-auto rounded-lg border border-border-subtle">
            <table className="w-full text-left text-xs text-text-secondary">
              <thead className="bg-surface-elevated/80 text-[11px] font-mono text-text-muted uppercase tracking-wider border-b border-border-subtle">
                <tr>
                  <th className="px-3 py-2.5">Site ID</th>
                  <th className="px-3 py-2.5">Site Name</th>
                  <th className="px-3 py-2.5">Status</th>
                  <th className="px-3 py-2.5 text-right">Elevation</th>
                  <th className="px-3 py-2.5 text-right">Area</th>
                  <th className="px-3 py-2.5">Coordinates (Lon, Lat)</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border-subtle bg-surface-panel">
                {sites.map((site) => {
                  const [lon, lat] = site.location?.coordinates || [0, 0];
                  return (
                    <tr key={site.id} className="hover:bg-surface-elevated/60 transition-colors">
                      <td className="px-3 py-2 font-mono text-text-muted">#{site.id}</td>
                      <td className="px-3 py-2 font-medium text-text-primary">{site.name}</td>
                      <td className="px-3 py-2">{getStatusBadge(site.status)}</td>
                      <td className="px-3 py-2 text-right font-mono text-text-secondary">
                        {site.elevation_m !== null ? `${site.elevation_m}m` : "—"}
                      </td>
                      <td className="px-3 py-2 text-right font-mono text-text-secondary">
                        {site.area_sq_m !== null
                          ? `${Math.round(site.area_sq_m).toLocaleString()} m²`
                          : "—"}
                      </td>
                      <td className="px-3 py-2 font-mono text-[11px] text-text-muted">
                        {lon.toFixed(4)}, {lat.toFixed(4)}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </CardContent>
    </Card>
  );
};
