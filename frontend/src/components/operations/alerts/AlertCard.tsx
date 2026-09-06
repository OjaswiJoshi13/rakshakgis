"use client";

import React from "react";
import { OperationalAlertItem } from "@/types/alerts";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import {
  CloudRain,
  Activity,
  Waves,
  Mountain,
  AlertTriangle,
  CheckCircle2,
  Clock,
  MapPin,
  FileText,
  ShieldCheck,
} from "lucide-react";

export interface AlertCardProps {
  alert: OperationalAlertItem;
  onAcknowledge?: (alertId: string) => void;
  onInspect?: (alert: OperationalAlertItem) => void;
  isAcknowledging?: boolean;
}

export const AlertCard: React.FC<AlertCardProps> = ({
  alert,
  onAcknowledge,
  onInspect,
  isAcknowledging = false,
}) => {
  // Indicator Icon mapping
  const getIndicatorIcon = () => {
    switch (alert.indicator) {
      case "rainfall_24h":
        return <CloudRain className="h-4 w-4 text-sky-400" />;
      case "seismic_mmi":
        return <Activity className="h-4 w-4 text-amber-400" />;
      case "water_level_above_danger":
        return <Waves className="h-4 w-4 text-cyan-400" />;
      case "landslide_debris_volume":
      case "slope_deg":
        return <Mountain className="h-4 w-4 text-emerald-400" />;
      default:
        return <AlertTriangle className="h-4 w-4 text-amber-400" />;
    }
  };

  // Severity styling
  const getSeverityBadge = () => {
    switch (alert.severity) {
      case "extreme":
        return (
          <Badge variant="danger" size="sm" className="bg-red-950/90 text-red-200 border-red-500">
            <span className="animate-ping inline-block h-1.5 w-1.5 rounded-full bg-red-400 mr-1" />
            EXTREME
          </Badge>
        );
      case "severe":
        return (
          <Badge variant="danger" size="sm">
            SEVERE
          </Badge>
        );
      case "warning":
        return (
          <Badge variant="warning" size="sm">
            WARNING
          </Badge>
        );
      case "info":
      default:
        return (
          <Badge variant="info" size="sm">
            INFORMATIONAL
          </Badge>
        );
    }
  };

  // Status badge styling
  const getStatusBadge = () => {
    switch (alert.status) {
      case "triggered":
        return (
          <Badge variant="danger" size="sm" className="font-mono">
            TRIGGERED (CANDIDATE)
          </Badge>
        );
      case "insufficient_data":
        return (
          <Badge variant="warning" size="sm" className="font-mono">
            INSUFFICIENT DATA (GAP)
          </Badge>
        );
      case "no_trigger":
      default:
        return (
          <Badge variant="success" size="sm" className="font-mono">
            NO TRIGGER (NORMAL)
          </Badge>
        );
    }
  };

  return (
    <div
      className={`rounded-lg border bg-slate-900/90 p-4 transition-all ${
        alert.severity === "extreme"
          ? "border-red-600/70 shadow-sm shadow-red-950/40"
          : alert.severity === "severe"
          ? "border-amber-600/60"
          : alert.status === "insufficient_data"
          ? "border-amber-700/40"
          : "border-slate-800"
      }`}
    >
      {/* Header Row */}
      <div className="flex flex-wrap items-center justify-between gap-2 pb-3 border-b border-slate-800/80">
        <div className="flex flex-wrap items-center gap-2">
          {getSeverityBadge()}
          {getStatusBadge()}
          <span className="inline-flex items-center gap-1 text-xs font-mono text-slate-400 bg-slate-950 px-2 py-0.5 rounded border border-slate-800">
            {getIndicatorIcon()}
            <span className="uppercase">{alert.indicator}</span>
          </span>
          {alert.candidate_id && (
            <span className="text-[11px] font-mono text-slate-500">
              ID: {alert.candidate_id}
            </span>
          )}
        </div>

        {/* Timestamp */}
        <div className="flex items-center gap-1.5 text-xs text-slate-400 font-mono">
          <Clock className="h-3.5 w-3.5 text-slate-500" />
          <span>{new Date(alert.issued_at).toLocaleString()}</span>
        </div>
      </div>

      {/* Main Content */}
      <div className="py-3 space-y-2">
        <h4 className="text-sm sm:text-base font-semibold text-slate-100 flex items-center gap-2">
          {alert.headline}
        </h4>
        <p className="text-xs sm:text-sm text-slate-300 leading-relaxed">
          {alert.message}
        </p>

        {/* Threshold Comparison Banner */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-2 pt-2">
          {/* Observed vs Threshold */}
          <div className="bg-slate-950 rounded border border-slate-800 p-2 text-xs">
            <span className="text-[10px] font-mono uppercase text-slate-400 block mb-0.5">
              Telemetry vs Threshold
            </span>
            {alert.status === "insufficient_data" ? (
              <span className="font-mono text-amber-400 font-medium">
                Telemetry null/offline &mdash; safe gap halt
              </span>
            ) : alert.observed_value !== null && alert.configured_threshold !== null ? (
              <div className="font-mono flex items-center gap-1.5 text-slate-200">
                <span className="font-bold text-slate-100">
                  {alert.observed_value} {alert.unit}
                </span>
                <span className="text-slate-500">{alert.operator}</span>
                <span className="text-slate-400">
                  {alert.configured_threshold} {alert.unit}
                </span>
                {alert.status === "triggered" && (
                  <span className="text-[10px] text-red-400 font-semibold uppercase ml-1">
                    (Exceeded)
                  </span>
                )}
              </div>
            ) : (
              <span className="font-mono text-slate-400">Nominal baseline</span>
            )}
          </div>

          {/* Location & Buffer */}
          <div className="bg-slate-950 rounded border border-slate-800 p-2 text-xs">
            <span className="text-[10px] font-mono uppercase text-slate-400 block mb-0.5">
              Settlement & Buffer
            </span>
            <div className="flex items-center gap-1 text-slate-300">
              <MapPin className="h-3.5 w-3.5 text-rose-400 shrink-0" />
              <span className="truncate">
                {alert.village_name || "Regional Zone"} ({alert.district_name || "Pilot"})
              </span>
            </div>
            {alert.buffer_m && (
              <span className="text-[10px] text-slate-500 font-mono block">
                {alert.buffer_m}m Geodesic Perimeter
              </span>
            )}
          </div>

          {/* Provenance / Feed */}
          <div className="bg-slate-950 rounded border border-slate-800 p-2 text-xs">
            <span className="text-[10px] font-mono uppercase text-slate-400 block mb-0.5">
              Source & Protocol
            </span>
            <div className="font-mono text-slate-300 truncate">
              {alert.source_id || "Telemetry Station"}
            </div>
            <span className="text-[10px] text-sky-400 font-mono block">
              M3-11 Regional Profile Protocol
            </span>
          </div>
        </div>
      </div>

      {/* Footer / Actions */}
      <div className="flex flex-wrap items-center justify-between gap-3 pt-3 border-t border-slate-800/80">
        {/* Acknowledgment State */}
        <div className="flex items-center gap-2">
          {alert.is_acknowledged ? (
            <div className="flex items-center gap-1.5 text-xs text-emerald-400 font-mono">
              <ShieldCheck className="h-4 w-4" />
              <span>
                Acknowledged by {alert.acknowledged_by || "Duty Officer"}{" "}
                {alert.acknowledged_at && (
                  <span className="text-slate-500">
                    ({new Date(alert.acknowledged_at).toLocaleTimeString()})
                  </span>
                )}
              </span>
            </div>
          ) : (
            <div className="flex items-center gap-1.5 text-xs text-amber-400 font-mono">
              <AlertTriangle className="h-4 w-4" />
              <span>Pending Duty Officer Acknowledgment</span>
            </div>
          )}
        </div>

        {/* Action Buttons */}
        <div className="flex items-center gap-2">
          {!alert.is_acknowledged && onAcknowledge && (
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => onAcknowledge(alert.id)}
              disabled={isAcknowledging}
              className="text-xs h-7 text-emerald-400 hover:text-emerald-300 hover:border-emerald-600 border-slate-700"
            >
              <CheckCircle2 className="h-3.5 w-3.5 mr-1" />
              <span>Acknowledge</span>
            </Button>
          )}

          {onInspect && (
            <Button
              type="button"
              variant="secondary"
              size="sm"
              onClick={() => onInspect(alert)}
              className="text-xs h-7"
            >
              <FileText className="h-3.5 w-3.5 mr-1 text-sky-400" />
              <span>Audit Trail</span>
            </Button>
          )}
        </div>
      </div>
    </div>
  );
};
