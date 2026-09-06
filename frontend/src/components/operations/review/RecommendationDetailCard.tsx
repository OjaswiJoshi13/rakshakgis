"use client";

import React from "react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { RecommendationDossier } from "@/types/review";
import {
  ShieldAlert,
  MapPin,
  Building2,
  Users,
  Compass,
  AlertCircle,
  FileCheck2,
  Cpu,
  Layers,
  CheckCircle2,
  XCircle,
  RotateCcw,
  Clock,
} from "lucide-react";

interface RecommendationDetailCardProps {
  dossier: RecommendationDossier;
}

export const RecommendationDetailCard: React.FC<RecommendationDetailCardProps> = ({
  dossier,
}) => {
  const getStatusBadge = (status: RecommendationDossier["status"]) => {
    switch (status) {
      case "approved":
        return (
          <Badge variant="success" size="sm" className="font-mono flex items-center gap-1">
            <CheckCircle2 className="h-3.5 w-3.5" />
            <span>Approved for Operations</span>
          </Badge>
        );
      case "rejected":
        return (
          <Badge variant="danger" size="sm" className="font-mono flex items-center gap-1">
            <XCircle className="h-3.5 w-3.5" />
            <span>Action Rejected</span>
          </Badge>
        );
      case "revision_requested":
        return (
          <Badge variant="info" size="sm" className="font-mono flex items-center gap-1">
            <RotateCcw className="h-3.5 w-3.5" />
            <span>Returned for Revision</span>
          </Badge>
        );
      case "pending_review":
      default:
        return (
          <Badge variant="warning" size="sm" className="font-mono flex items-center gap-1">
            <Clock className="h-3.5 w-3.5" />
            <span>Awaiting Officer Sign-Off</span>
          </Badge>
        );
    }
  };

  return (
    <Card className="border-slate-800 bg-slate-900/60 shadow-xl overflow-hidden">
      {/* Card Header & Provenance */}
      <CardHeader className="p-5 border-b border-slate-800/80 bg-slate-950/40">
        <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3">
          <div>
            <div className="flex items-center gap-2 flex-wrap mb-1.5">
              <Badge variant="outline" size="sm" className="font-mono text-slate-400">
                {dossier.id}
              </Badge>
              <Badge variant="outline" size="sm" className="font-mono text-sky-400 border-sky-600/50">
                {dossier.type === "relocation_plan" ? "Relocation Plan" : "Scenario Simulation"}
              </Badge>
              <span className="text-xs text-slate-500 font-mono">
                {new Date(dossier.created_at).toLocaleString("en-IN", {
                  dateStyle: "medium",
                  timeStyle: "short",
                })}
              </span>
            </div>
            <CardTitle className="text-lg font-bold text-slate-100">
              {dossier.title}
            </CardTitle>
            <CardDescription className="text-xs text-slate-400 mt-1 flex items-center gap-2 flex-wrap">
              <span className="inline-flex items-center gap-1">
                <Cpu className="h-3 w-3 text-emerald-400" />
                <strong className="text-slate-300">Engine:</strong> {dossier.source_engine}
              </span>
              <span className="text-slate-600">•</span>
              <span className="inline-flex items-center gap-1">
                <Layers className="h-3 w-3 text-sky-400" />
                <strong className="text-slate-300">Profile:</strong> {dossier.region_profile_id}
              </span>
            </CardDescription>
          </div>

          <div>{getStatusBadge(dossier.status)}</div>
        </div>

        {/* Rule 12 Statutory Mandate Banner */}
        <div className="mt-4 rounded-lg border border-amber-800/60 bg-amber-950/30 p-3 text-xs text-amber-200/90 leading-relaxed flex items-start gap-2.5">
          <ShieldAlert className="h-4 w-4 text-amber-400 shrink-0 mt-0.5" />
          <div>
            <div className="font-semibold text-amber-300 font-mono">
              Statutory Rule 12 Protocol — Mandatory Officer Authorization
            </div>
            <p className="mt-0.5 text-[11px] text-amber-200/80">
              {dossier.statutory_mandate} Algorithmic matching calculations are strictly advisory
              decision-support models and have zero legal effect until signed off by the reviewing officer.
            </p>
          </div>
        </div>
      </CardHeader>

      <CardContent className="p-5 space-y-6">
        {/* Proposed Operational Action Block */}
        <div className="rounded-lg border border-sky-900/60 bg-sky-950/20 p-4">
          <div className="flex items-center gap-2 text-xs font-semibold text-sky-300 mb-1.5">
            <FileCheck2 className="h-4 w-4 text-sky-400" />
            <span>PROPOSED OPERATIONAL DIRECTIVE</span>
          </div>
          <p className="text-xs sm:text-sm text-slate-200 leading-relaxed font-medium">
            {dossier.proposed_action}
          </p>
        </div>

        {/* Executive Narrative */}
        <div>
          <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider mb-2 font-mono">
            Analytical Executive Summary
          </h4>
          <p className="text-xs text-slate-400 leading-relaxed">
            {dossier.executive_summary}
          </p>
        </div>

        {/* Dynamic Metric Cards Grid */}
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
          {dossier.metrics.map((m, idx) => (
            <div
              key={idx}
              className="rounded-lg border border-slate-800 bg-slate-950/60 p-3 text-center"
            >
              <div className="text-[11px] text-slate-400 truncate">{m.label}</div>
              <div
                className={`text-lg font-bold mt-1 font-mono ${
                  m.variant === "danger"
                    ? "text-rose-400"
                    : m.variant === "warning"
                    ? "text-amber-400"
                    : m.variant === "success"
                    ? "text-emerald-400"
                    : "text-slate-100"
                }`}
              >
                {m.value}
              </div>
              {m.subtext && (
                <div className="text-[10px] text-slate-500 mt-0.5 truncate font-mono">
                  {m.subtext}
                </div>
              )}
            </div>
          ))}
        </div>

        {/* Payload Section: Relocation Matching Breakdown */}
        {dossier.type === "relocation_plan" && dossier.relocation_payload && (
          <div className="space-y-3">
            <div className="flex items-center justify-between">
              <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider font-mono flex items-center gap-2">
                <Building2 className="h-3.5 w-3.5 text-sky-400" />
                <span>Proposed Settlement Allocation Plan</span>
              </h4>
              <span className="text-[11px] font-mono text-slate-500">
                Matching ID: {dossier.relocation_payload.matching_id}
              </span>
            </div>

            <div className="overflow-x-auto rounded-lg border border-slate-800 bg-slate-950/40">
              <table className="w-full text-left text-xs">
                <thead className="border-b border-slate-800 bg-slate-900/60 text-slate-400 font-mono text-[11px]">
                  <tr>
                    <th className="py-2.5 px-3">Village Settlement</th>
                    <th className="py-2.5 px-3">Urgency Band</th>
                    <th className="py-2.5 px-3">Households</th>
                    <th className="py-2.5 px-3">Assigned Safe Site</th>
                    <th className="py-2.5 px-3">Distance</th>
                    <th className="py-2.5 px-3">Status</th>
                  </tr>
                </thead>
                <tbody className="divide-y divide-slate-800/60 text-slate-300">
                  {dossier.relocation_payload.assignments.map((assignment) => {
                    const isAssigned = assignment.status === "assigned";
                    return (
                      <tr key={String(assignment.village_id)} className="hover:bg-slate-900/30">
                        <td className="py-2.5 px-3 font-medium text-slate-200">
                          {assignment.village_name}
                        </td>
                        <td className="py-2.5 px-3 font-mono text-[11px]">
                          {assignment.priority_band || "P1_immediate"}
                        </td>
                        <td className="py-2.5 px-3 font-mono">
                          {assignment.incoming_households} HH
                        </td>
                        <td className="py-2.5 px-3">
                          {isAssigned ? (
                            <span className="text-sky-300 font-medium">
                              {assignment.assigned_site_name}
                            </span>
                          ) : (
                            <span className="text-rose-400 italic">None (Capacity Exhausted)</span>
                          )}
                        </td>
                        <td className="py-2.5 px-3 font-mono text-slate-400">
                          {isAssigned && assignment.distance_km != null
                            ? `${assignment.distance_km} km`
                            : "—"}
                        </td>
                        <td className="py-2.5 px-3">
                          {isAssigned ? (
                            <Badge variant="success" size="sm" className="text-[10px]">
                              Allocated
                            </Badge>
                          ) : (
                            <Badge variant="danger" size="sm" className="text-[10px]">
                              Deficit Unassigned
                            </Badge>
                          )}
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          </div>
        )}

        {/* Payload Section: Scenario What-If Evaluation Breakdown */}
        {dossier.type === "scenario_evaluation" && dossier.scenario_payload && (
          <div className="space-y-3">
            <h4 className="text-xs font-semibold text-slate-300 uppercase tracking-wider font-mono flex items-center gap-2">
              <Compass className="h-3.5 w-3.5 text-amber-400" />
              <span>Simulated Scenario Parameters & Threat Response</span>
            </h4>

            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
              <div className="rounded-lg border border-slate-800 bg-slate-950/40 p-3">
                <div className="text-[11px] text-slate-400 font-mono">Rainfall Surge Multiplier</div>
                <div className="text-base font-bold text-amber-300 font-mono mt-1">
                  {dossier.scenario_payload.parameters.rainfall_multiplier}x
                </div>
                <div className="text-[10px] text-slate-500 mt-0.5">Heavy precipitation baseline</div>
              </div>

              <div className="rounded-lg border border-slate-800 bg-slate-950/40 p-3">
                <div className="text-[11px] text-slate-400 font-mono">Transit Road Blockage</div>
                <div className="text-base font-bold text-rose-300 font-mono mt-1">
                  {dossier.scenario_payload.parameters.road_blockage_percentage}%
                </div>
                <div className="text-[10px] text-slate-500 mt-0.5">Highway route occlusion</div>
              </div>

              <div className="rounded-lg border border-slate-800 bg-slate-950/40 p-3">
                <div className="text-[11px] text-slate-400 font-mono">Flood Inundation Increase</div>
                <div className="text-base font-bold text-sky-300 font-mono mt-1">
                  +{dossier.scenario_payload.parameters.flood_hazard_increase}%
                </div>
                <div className="text-[10px] text-slate-500 mt-0.5">River valley hazard delta</div>
              </div>
            </div>

            <div className="rounded-lg border border-slate-800 bg-slate-950/40 p-3.5 text-xs">
              <div className="font-semibold text-slate-200 mb-1 flex items-center gap-1.5">
                <AlertCircle className="h-3.5 w-3.5 text-amber-400" />
                <span>Simulation Threat Assessment</span>
              </div>
              <p className="text-slate-400 text-[11px] leading-relaxed">
                {dossier.scenario_payload.summary_narrative}
              </p>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
};
