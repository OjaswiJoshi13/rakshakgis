"use client";

import React from "react";
import { CandidateSiteDetailRead } from "@/types/sites";
import { MetricCard } from "@/components/ui/MetricCard";
import { Badge } from "@/components/ui/Badge";
import {
  Users,
  CheckCircle2,
  Droplets,
  Boxes,
  Home,
  Layers,
  MapPin,
  Clock,
  ShieldCheck,
  AlertCircle,
} from "lucide-react";

export interface SiteInfrastructureTabProps {
  site: CandidateSiteDetailRead;
}

export const SiteInfrastructureTab: React.FC<SiteInfrastructureTabProps> = ({
  site,
}) => {
  // Aggregate capacities across all capacity records for this site
  const totalMaxHH = site.capacities.reduce((acc, c) => acc + (c.max_households || 0), 0);
  const totalAllocatedHH = site.capacities.reduce((acc, c) => acc + (c.allocated_households || 0), 0);
  const totalAvailableHH = site.capacities.reduce((acc, c) => acc + (c.available_households || 0), 0);
  const totalWaterLpd = site.capacities.reduce((acc, c) => acc + (c.water_supply_lpd || 0), 0);
  const totalSanitationUnits = site.capacities.reduce((acc, c) => acc + (c.sanitation_units || 0), 0);

  const occupancyRate = totalMaxHH > 0 ? Math.round((totalAllocatedHH / totalMaxHH) * 100) : 0;

  return (
    <div className="space-y-6">
      {/* Carrying Capacity KPI Grid */}
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-4">
        <MetricCard
          label="Housing Capacity"
          value={totalMaxHH.toLocaleString()}
          unit="HH"
          subtext={`Allocated: ${totalAllocatedHH} (${occupancyRate}% full)`}
          status="info"
          icon={<Home className="h-4 w-4" />}
        />

        <MetricCard
          label="Available Capacity"
          value={totalAvailableHH.toLocaleString()}
          unit="HH"
          subtext={`Unreserved safe plots remaining`}
          status={totalAvailableHH > 0 ? "normal" : "critical"}
          icon={<CheckCircle2 className="h-4 w-4" />}
        />

        <MetricCard
          label="Water Supply"
          value={totalWaterLpd > 0 ? totalWaterLpd.toLocaleString() : "—"}
          unit={totalWaterLpd > 0 ? "LPD" : undefined}
          subtext={totalWaterLpd > 0 ? "Filtered municipal & spring intake" : "No water asset recorded"}
          status={totalWaterLpd > 0 ? "normal" : "warning"}
          icon={<Droplets className="h-4 w-4" />}
        />

        <MetricCard
          label="Sanitation Units"
          value={totalSanitationUnits > 0 ? totalSanitationUnits : "—"}
          unit={totalSanitationUnits > 0 ? "Units" : undefined}
          subtext={totalSanitationUnits > 0 ? "Community toilets & septic banks" : "No sanitation units recorded"}
          status={totalSanitationUnits > 0 ? "normal" : "warning"}
          icon={<Boxes className="h-4 w-4" />}
        />
      </div>

      {/* On-Site Infrastructure Assets Inventory */}
      <div className="space-y-3 rounded-lg border border-border-subtle bg-surface-panel p-4 shadow-xs">
        <div className="flex items-center justify-between border-b border-border-subtle pb-3">
          <div>
            <h3 className="text-sm font-bold text-text-primary flex items-center gap-2">
              <Layers className="h-4 w-4 text-primary-600 dark:text-primary-400" />
              <span>On-Site Infrastructure Assets ({site.infrastructures.length})</span>
            </h3>
            <p className="text-xs text-text-secondary mt-0.5">
              Verified physical infrastructure, lifelines, emergency services, and utilities.
            </p>
          </div>
        </div>

        {site.infrastructures.length === 0 ? (
          <div className="rounded-lg border border-dashed border-border-strong p-8 text-center text-xs text-text-muted">
            No on-site infrastructure assets recorded for this site yet.
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left border-collapse text-xs">
              <thead>
                <tr className="border-b border-border-subtle bg-surface-elevated font-mono text-text-muted uppercase tracking-wider">
                  <th className="py-2.5 px-3">Asset Name</th>
                  <th className="py-2.5 px-3">Infrastructure Type</th>
                  <th className="py-2.5 px-3">Operational Status</th>
                  <th className="py-2.5 px-3">Capacity / Specification</th>
                  <th className="py-2.5 px-3">Coordinates</th>
                  <th className="py-2.5 px-3 text-right">Added</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-border-subtle font-sans">
                {site.infrastructures.map((asset) => {
                  const isFunctional = asset.status.toLowerCase() === "functional";
                  const isDamaged = asset.status.toLowerCase() === "damaged";

                  return (
                    <tr
                      key={asset.id}
                      className="hover:bg-surface-subtle transition-colors"
                    >
                      <td className="py-3 px-3">
                        <span className="font-semibold text-text-primary">
                          {asset.name}
                        </span>
                        <span className="text-[11px] font-mono text-text-muted block">
                          Asset #{asset.id}
                        </span>
                      </td>

                      <td className="py-3 px-3 font-mono text-text-secondary capitalize">
                        {asset.infra_type.replace(/_/g, " ")}
                      </td>

                      <td className="py-3 px-3 font-mono">
                        <Badge
                          variant={
                            isFunctional
                              ? "success"
                              : isDamaged
                              ? "danger"
                              : "warning"
                          }
                          size="sm"
                          className="capitalize"
                        >
                          {asset.status}
                        </Badge>
                      </td>

                      <td className="py-3 px-3 text-text-secondary">
                        {asset.capacity_description || "Standard specification"}
                      </td>

                      <td className="py-3 px-3 font-mono text-text-muted text-[11px]">
                        {asset.location
                          ? `${asset.location.coordinates[0].toFixed(3)}°E, ${asset.location.coordinates[1].toFixed(3)}°N`
                          : "—"}
                      </td>

                      <td className="py-3 px-3 font-mono text-text-muted text-[11px] text-right">
                        {new Date(asset.created_at).toLocaleDateString()}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
};
