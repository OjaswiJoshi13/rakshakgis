"use client";

import React, { useState } from "react";
import { CompiledDossier } from "@/types/reports";
import { Card, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import {
  FileText,
  ShieldCheck,
  Layers,
  Building2,
  Users,
  MapPin,
  ChevronDown,
  ChevronUp,
  AlertTriangle,
  CheckCircle2,
  XCircle,
  Sliders,
  Calendar,
  Compass,
} from "lucide-react";

interface DossierViewerProps {
  dossier: CompiledDossier;
  includeAudits: boolean;
  includeDeficits: boolean;
}

export const DossierViewer: React.FC<DossierViewerProps> = ({
  dossier,
  includeAudits,
  includeDeficits,
}) => {
  const [expandedAudits, setExpandedAudits] = useState<Record<string, boolean>>({});

  const toggleAudit = (villageId: string | number) => {
    setExpandedAudits((prev) => ({
      ...prev,
      [villageId]: !prev[villageId],
    }));
  };

  const assignments = dossier.filteredAssignments || [];
  const sites = dossier.sites || [];
  const siteDetail = dossier.selectedSiteDetail;
  const suitability = dossier.suitability;
  const capacity = dossier.capacity;

  return (
    <div
      id="operational-dossier-print-root"
      className="space-y-6 bg-slate-950 p-6 sm:p-8 rounded-xl border border-slate-800 shadow-2xl print:bg-white print:text-black print:p-0 print:border-0 print:shadow-none"
    >
      {/* 1. Official Dossier Document Header */}
      <div className="border-b border-slate-800 pb-6 print:border-slate-300">
        <div className="flex flex-col sm:flex-row sm:items-start sm:justify-between gap-4">
          <div className="flex items-start gap-3.5">
            <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-sky-950 border border-sky-600/50 text-sky-400 shrink-0 print:border-black print:text-black print:bg-slate-100">
              <FileText className="h-6 w-6" />
            </div>
            <div>
              <div className="flex items-center gap-2 flex-wrap mb-1">
                <Badge
                  variant="outline"
                  size="sm"
                  className="font-mono text-[10px] tracking-wider uppercase border-sky-500/40 text-sky-300 bg-sky-950/40 print:border-black print:text-black"
                >
                  {dossier.classification}
                </Badge>
                <span className="text-[11px] font-mono text-slate-500 print:text-slate-700">
                  ID: {dossier.id}
                </span>
              </div>
              <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-slate-100 print:text-black">
                {dossier.title}
              </h2>
              <div className="flex items-center gap-4 text-xs text-slate-400 mt-1 flex-wrap print:text-slate-600">
                <span className="flex items-center gap-1">
                  <Calendar className="h-3.5 w-3.5 text-slate-500" />
                  Generated: {new Date(dossier.generatedAt).toLocaleString()}
                </span>
                <span className="flex items-center gap-1 font-mono">
                  <Compass className="h-3.5 w-3.5 text-slate-500" />
                  Region: {dossier.regionProfileId}
                </span>
              </div>
            </div>
          </div>

          <div className="text-right font-mono text-[11px] text-slate-500 shrink-0 print:text-slate-600">
            <div>CONFIDENTIAL & OPERATIONAL</div>
            <div>SIH-26191 / RAKSHAKGIS</div>
          </div>
        </div>
      </div>

      {/* 2. Statutory Invariants Callout Banners */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Rule 12 Legal Mandate Notice */}
        <div className="rounded-lg border border-sky-900/60 bg-sky-950/30 p-4 text-xs text-sky-200/90 space-y-1.5 print:border-slate-400 print:bg-slate-50 print:text-black">
          <div className="flex items-center gap-2 font-semibold text-sky-300 print:text-black">
            <ShieldCheck className="h-4 w-4 text-sky-400 shrink-0 print:text-black" />
            <span>Rule 12 Statutory Decision-Support Mandate</span>
          </div>
          <p className="text-[11px] text-sky-300/80 leading-relaxed print:text-slate-700">
            {dossier.governanceNotice}
          </p>
        </div>

        {/* Rule 8 Provenance Notice */}
        <div className="rounded-lg border border-slate-800 bg-slate-900/50 p-4 text-xs text-slate-300 space-y-1.5 print:border-slate-400 print:bg-slate-50 print:text-black">
          <div className="flex items-center gap-2 font-semibold text-slate-200 print:text-black">
            <Layers className="h-4 w-4 text-emerald-400 shrink-0 print:text-black" />
            <span>Rule 8 Analytical Provenance & Audit Trail</span>
          </div>
          <p className="text-[11px] text-slate-400 leading-relaxed print:text-slate-700">
            All numerical metrics and relocation recommendations are computed
            deterministically from verified spatial profile models (M4-01 through M4-04).
            Zero random numbers or generative LLM outputs are utilized in this compilation.
          </p>
        </div>
      </div>

      {/* 3. Executive Summary Narrative Block */}
      <div className="rounded-lg border border-slate-800/80 bg-slate-900/30 p-4 sm:p-5 print:border-slate-300 print:bg-white">
        <h3 className="text-xs font-semibold uppercase tracking-wider text-slate-400 mb-2 print:text-black">
          Executive Operational Narrative
        </h3>
        <p className="text-xs sm:text-sm text-slate-300 leading-relaxed italic print:text-black print:not-italic">
          &ldquo;{dossier.summaryNarrative}&rdquo;
        </p>
      </div>

      {/* 4. Section: Village-to-Site Relocation Ledger */}
      {assignments.length > 0 && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wide flex items-center gap-2 print:text-black">
              <Users className="h-4 w-4 text-sky-400 print:text-black" />
              <span>Village Relocation Allocation Ledger ({assignments.length})</span>
            </h3>
            <span className="text-xs font-mono text-slate-500 print:text-slate-700">
              Filtered: {dossier.filteredAssignments?.length ?? 0} Habitations
            </span>
          </div>

          <div className="overflow-x-auto rounded-lg border border-slate-800 bg-slate-900/40 print:border-slate-300">
            <table className="w-full text-left text-xs text-slate-300 print:text-black">
              <thead className="bg-slate-900/80 font-mono text-[11px] text-slate-400 uppercase border-b border-slate-800 print:bg-slate-100 print:text-black print:border-slate-300">
                <tr>
                  <th className="py-2.5 px-3">Habitation</th>
                  <th className="py-2.5 px-3">Demand (HH)</th>
                  <th className="py-2.5 px-3">Priority</th>
                  <th className="py-2.5 px-3">Status</th>
                  <th className="py-2.5 px-3">Assigned Safe Site</th>
                  <th className="py-2.5 px-3 text-right">Distance</th>
                  <th className="py-2.5 px-3 text-right">Suitability</th>
                  {includeAudits && <th className="py-2.5 px-3 text-center">Audit</th>}
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono text-xs print:divide-slate-200">
                {assignments.map((row) => {
                  const isAssigned = row.status === "assigned";
                  const isExpanded = Boolean(expandedAudits[row.village_id]);

                  return (
                    <React.Fragment key={row.village_id}>
                      <tr className="hover:bg-slate-800/30 transition-colors">
                        <td className="py-2.5 px-3 font-medium text-slate-100 print:text-black">
                          <div>{row.village_name}</div>
                          <span className="text-[10px] text-slate-500 font-normal">
                            ID: {row.village_id}
                          </span>
                        </td>
                        <td className="py-2.5 px-3 text-slate-200 print:text-black">
                          {row.incoming_households} HH
                        </td>
                        <td className="py-2.5 px-3">
                          <span className="font-semibold text-slate-200 print:text-black">
                            {row.priority_score.toFixed(1)}
                          </span>
                          {row.priority_band && (
                            <span className="ml-1 text-[10px] text-slate-400">
                              ({row.priority_band})
                            </span>
                          )}
                        </td>
                        <td className="py-2.5 px-3">
                          <Badge
                            variant={isAssigned ? "success" : "warning"}
                            size="sm"
                            className="capitalize text-[10px]"
                          >
                            {row.status}
                          </Badge>
                        </td>
                        <td className="py-2.5 px-3">
                          {isAssigned ? (
                            <div className="flex items-center gap-1.5 text-sky-300 font-sans print:text-black">
                              <Building2 className="h-3.5 w-3.5 text-sky-400 shrink-0 print:text-black" />
                              <span>{row.assigned_site_name}</span>
                            </div>
                          ) : (
                            <span className="text-amber-400/90 italic font-sans text-[11px] print:text-amber-800">
                              {row.unassigned_reason || "No safe site matched"}
                            </span>
                          )}
                        </td>
                        <td className="py-2.5 px-3 text-right text-slate-300 print:text-black">
                          {row.distance_km ? `${row.distance_km.toFixed(1)} km` : "—"}
                        </td>
                        <td className="py-2.5 px-3 text-right text-slate-300 print:text-black">
                          {row.suitability_score
                            ? `${row.suitability_score.toFixed(1)}%`
                            : "—"}
                        </td>
                        {includeAudits && (
                          <td className="py-2.5 px-3 text-center">
                            {row.evaluated_candidates &&
                            row.evaluated_candidates.length > 0 ? (
                              <button
                                type="button"
                                data-testid={`audit-toggle-btn-${row.village_id}`}
                                aria-label={`Toggle candidate audits for ${row.village_name}`}
                                onClick={() => toggleAudit(row.village_id)}
                                className="inline-flex items-center gap-1 text-[11px] text-sky-400 hover:text-sky-300 underline font-sans print:hidden"
                              >
                                <span>{row.evaluated_candidates.length} Sites</span>
                                {isExpanded ? (
                                  <ChevronUp className="h-3 w-3" />
                                ) : (
                                  <ChevronDown className="h-3 w-3" />
                                )}
                              </button>
                            ) : (
                              <span className="text-slate-600">—</span>
                            )}
                          </td>
                        )}
                      </tr>

                      {/* Expandable Rejection / Audit Breakdown */}
                      {includeAudits && isExpanded && row.evaluated_candidates && (
                        <tr className="bg-slate-950/80 border-t border-slate-800 print:bg-slate-50">
                          <td
                            colSpan={8}
                            className="p-3 pl-8 text-[11px] font-sans text-slate-300 space-y-2"
                          >
                            <div className="font-semibold text-slate-200 flex items-center gap-1.5 print:text-black">
                              <Sliders className="h-3.5 w-3.5 text-sky-400" />
                              <span>
                                Candidate Sites Evaluation Audit for {row.village_name}:
                              </span>
                            </div>
                            <div className="grid grid-cols-1 sm:grid-cols-2 gap-2">
                              {row.evaluated_candidates.map((cand) => (
                                <div
                                  key={cand.site_id}
                                  className="p-2 rounded bg-slate-900/60 border border-slate-800 print:bg-white print:border-slate-200"
                                >
                                  <div className="flex items-center justify-between text-xs font-medium">
                                    <span className="text-slate-200 print:text-black">
                                      {cand.site_name}
                                    </span>
                                    {cand.is_feasible ? (
                                      <Badge
                                        variant="success"
                                        size="sm"
                                        className="text-[9px]"
                                      >
                                        Feasible
                                      </Badge>
                                    ) : (
                                      <Badge
                                        variant="outline"
                                        size="sm"
                                        className="text-[9px] text-rose-400 border-rose-600/50"
                                      >
                                        Rejected
                                      </Badge>
                                    )}
                                  </div>
                                  <div className="text-[10px] text-slate-400 mt-1 flex gap-3">
                                    <span>Dist: {cand.distance_km?.toFixed(1) ?? "—"} km</span>
                                    <span>Score: {cand.suitability_score?.toFixed(1) ?? "—"}%</span>
                                  </div>
                                  {cand.rejection_reasons?.length > 0 && (
                                    <div className="text-[10px] text-amber-400/90 mt-1 font-mono">
                                      Rejection: {cand.rejection_reasons.join("; ")}
                                    </div>
                                  )}
                                </div>
                              ))}
                            </div>
                          </td>
                        </tr>
                      )}
                    </React.Fragment>
                  );
                })}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* 5. Section: Candidate Relocation Sites Inventory */}
      {sites.length > 0 && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wide flex items-center gap-2 print:text-black">
              <Building2 className="h-4 w-4 text-emerald-400 print:text-black" />
              <span>Candidate Relocation Sites Inventory ({sites.length})</span>
            </h3>
          </div>

          <div className="overflow-x-auto rounded-lg border border-slate-800 bg-slate-900/40 print:border-slate-300">
            <table className="w-full text-left text-xs text-slate-300 print:text-black">
              <thead className="bg-slate-900/80 font-mono text-[11px] text-slate-400 uppercase border-b border-slate-800 print:bg-slate-100 print:text-black print:border-slate-300">
                <tr>
                  <th className="py-2.5 px-3">Site ID</th>
                  <th className="py-2.5 px-3">Site Name</th>
                  <th className="py-2.5 px-3">District</th>
                  <th className="py-2.5 px-3 text-right">Elevation (m)</th>
                  <th className="py-2.5 px-3 text-right">Slope (deg)</th>
                  <th className="py-2.5 px-3 text-right">Area (sq m)</th>
                  <th className="py-2.5 px-3">Status</th>
                  <th className="py-2.5 px-3">Coordinates</th>
                </tr>
              </thead>
              <tbody className="divide-y divide-slate-800/60 font-mono text-xs print:divide-slate-200">
                {sites.map((site) => (
                  <tr key={site.id} className="hover:bg-slate-800/30 transition-colors">
                    <td className="py-2 px-3 font-semibold text-sky-300 print:text-black">
                      #{site.id}
                    </td>
                    <td className="py-2 px-3 font-sans font-medium text-slate-100 print:text-black">
                      {site.name}
                    </td>
                    <td className="py-2 px-3 text-slate-400 print:text-slate-700">
                      District {site.district_id}
                    </td>
                    <td className="py-2 px-3 text-right text-slate-200 print:text-black">
                      {site.elevation_m ? `${site.elevation_m}m` : "—"}
                    </td>
                    <td className="py-2 px-3 text-right text-slate-200 print:text-black">
                      {site.terrain_slope_deg ? `${site.terrain_slope_deg}°` : "—"}
                    </td>
                    <td className="py-2 px-3 text-right text-slate-200 print:text-black">
                      {site.area_sq_m ? site.area_sq_m.toLocaleString() : "—"}
                    </td>
                    <td className="py-2 px-3">
                      <Badge
                        variant={site.status === "approved" ? "success" : "info"}
                        size="sm"
                        className="capitalize text-[10px]"
                      >
                        {site.status}
                      </Badge>
                    </td>
                    <td className="py-2 px-3 text-slate-400 font-mono text-[11px] print:text-slate-700">
                      {site.location?.coordinates
                        ? `${site.location.coordinates[0].toFixed(3)}, ${site.location.coordinates[1].toFixed(3)}`
                        : "—"}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* 6. Section: Selected Site Infrastructure Asset Inventory */}
      {siteDetail && siteDetail.infrastructures && siteDetail.infrastructures.length > 0 && (
        <div className="space-y-3">
          <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wide flex items-center gap-2 print:text-black">
            <Building2 className="h-4 w-4 text-sky-400 print:text-black" />
            <span>Infrastructure Assets Profile: {siteDetail.name}</span>
          </h3>

          <div className="grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
            {siteDetail.infrastructures.map((infra) => (
              <div
                key={infra.id}
                className="p-3 rounded-lg border border-slate-800 bg-slate-900/50 space-y-1 print:border-slate-300 print:bg-white"
              >
                <div className="flex items-center justify-between text-xs font-semibold text-slate-200 print:text-black">
                  <span>{infra.name}</span>
                  <Badge variant="outline" size="sm" className="text-[10px] uppercase">
                    {infra.status}
                  </Badge>
                </div>
                <div className="text-[11px] text-sky-400 font-mono">
                  Type: {infra.infra_type}
                </div>
                <div className="text-[11px] text-slate-400 print:text-slate-700">
                  {infra.capacity_description || "Operational utility asset"}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 7. Section: Suitability Criteria & Carrying Capacity Dimensions */}
      {(suitability || capacity) && (
        <div className="space-y-4">
          <div className="flex items-center justify-between">
            <h3 className="text-sm font-bold text-slate-200 uppercase tracking-wide flex items-center gap-2 print:text-black">
              <Sliders className="h-4 w-4 text-sky-400 print:text-black" />
              <span>Multi-Criteria Suitability & Carrying Capacity Audit</span>
            </h3>
            {suitability && (
              <Badge
                variant={suitability.decision === "suitable" ? "success" : "warning"}
                size="sm"
                className="font-mono text-xs uppercase"
              >
                Decision: {suitability.decision} ({suitability.overall_score.toFixed(1)}/100)
              </Badge>
            )}
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* 9 Suitability Criteria */}
            {suitability && suitability.criteria_scores && (
              <div className="rounded-lg border border-slate-800 bg-slate-900/40 p-4 space-y-2.5 print:border-slate-300 print:bg-white">
                <div className="text-xs font-semibold text-slate-300 uppercase tracking-wider print:text-black">
                  9 Authoritative Suitability Criteria
                </div>
                <div className="space-y-1.5 divide-y divide-slate-800/60 print:divide-slate-200">
                  {Object.values(suitability.criteria_scores).map((c) => (
                    <div
                      key={c.criterion}
                      className="pt-1.5 flex items-center justify-between text-xs"
                    >
                      <div className="space-y-0.5">
                        <span className="font-medium text-slate-200 print:text-black">
                          {c.criterion_name}
                        </span>
                        <div className="text-[10px] text-slate-500 print:text-slate-600">
                          Weight: {(c.weight * 100).toFixed(0)}%
                        </div>
                      </div>
                      <div className="text-right font-mono">
                        <span className="text-slate-100 font-semibold print:text-black">
                          {c.raw_score.toFixed(1)}/100
                        </span>
                        <div className="text-[10px] text-sky-400">
                          +{c.weighted_contribution.toFixed(1)} pts
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Carrying Capacity 5 Critical Dimensions */}
            {capacity && (
              <div className="rounded-lg border border-slate-800 bg-slate-900/40 p-4 space-y-3 print:border-slate-300 print:bg-white">
                <div className="flex items-center justify-between">
                  <span className="text-xs font-semibold text-slate-300 uppercase tracking-wider print:text-black">
                    5 Critical Infrastructure Dimensions
                  </span>
                  <span className="text-xs font-mono font-bold text-emerald-400 print:text-black">
                    Effective: {capacity.effective_capacity_households} HH
                  </span>
                </div>

                {/* Limiting Factors Highlight */}
                {includeDeficits && capacity.limiting_factors && (
                  <div className="rounded border border-amber-900/60 bg-amber-950/30 p-2.5 text-xs text-amber-300 flex items-start gap-2 print:border-amber-400 print:bg-amber-50 print:text-black">
                    <AlertTriangle className="h-4 w-4 shrink-0 text-amber-400 mt-0.5" />
                    <div>
                      <span className="font-semibold">Limiting Factor Bottleneck:</span>{" "}
                      {capacity.limiting_factors.join(", ")} restricts overall expansion.
                    </div>
                  </div>
                )}

                {/* Sizing Dimensions List */}
                {capacity.infrastructure_results && (
                  <div className="space-y-2 text-xs">
                    {Object.values(capacity.infrastructure_results).map((dim) => (
                      <div
                        key={dim.dimension}
                        className="p-2 rounded bg-slate-900/80 border border-slate-800 flex items-center justify-between print:bg-white print:border-slate-200"
                      >
                        <div>
                          <div className="font-medium text-slate-200 print:text-black">
                            {dim.dimension_name}
                          </div>
                          {dim.deficit > 0 && (
                            <div className="text-[10px] text-amber-400 font-mono">
                              Deficit: {dim.deficit} {dim.unit}
                            </div>
                          )}
                        </div>
                        <div className="text-right font-mono">
                          <span className="font-bold text-slate-100 print:text-black">
                            {dim.current_capacity ?? "—"} {dim.unit}
                          </span>
                          <div className="text-[10px] text-slate-500">
                            Required: {dim.required_capacity} {dim.unit}
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </div>
            )}
          </div>
        </div>
      )}

      {/* 8. Dossier Document Footer */}
      <div className="border-t border-slate-800 pt-4 text-center text-[10px] font-mono text-slate-500 print:text-slate-600 print:border-slate-300">
        <div>
          RakshakGIS AI Disaster Mitigation Platform • Official Decision Support
          Dossier
        </div>
        <div>
          Conforms strictly to Himalayan Pilot SOP-RZ-01 Specifications & NDMA
          Guidelines
        </div>
      </div>
    </div>
  );
};
