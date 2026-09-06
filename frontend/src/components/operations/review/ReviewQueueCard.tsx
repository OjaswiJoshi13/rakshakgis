"use client";

import React, { useState } from "react";
import { Card, CardHeader, CardTitle, CardDescription, CardContent } from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { RecommendationDossier, ReviewStatus } from "@/types/review";
import {
  Inbox,
  Search,
  CheckCircle2,
  XCircle,
  RotateCcw,
  Clock,
  AlertTriangle,
  ArrowRight,
} from "lucide-react";
import { cn } from "@/lib/utils";

interface ReviewQueueCardProps {
  dossiers: RecommendationDossier[];
  selectedDossierId: string;
  onSelectDossier: (id: string) => void;
  isLoading?: boolean;
}

type FilterTab = "all" | "pending" | "decided";

export const ReviewQueueCard: React.FC<ReviewQueueCardProps> = ({
  dossiers,
  selectedDossierId,
  onSelectDossier,
  isLoading = false,
}) => {
  const [activeTab, setActiveTab] = useState<FilterTab>("all");
  const [searchQuery, setSearchQuery] = useState("");

  const pendingCount = dossiers.filter((d) => d.status === "pending_review").length;
  const decidedCount = dossiers.filter((d) => d.status !== "pending_review").length;

  const filteredDossiers = dossiers.filter((d) => {
    // Tab filter
    if (activeTab === "pending" && d.status !== "pending_review") return false;
    if (activeTab === "decided" && d.status === "pending_review") return false;

    // Search query
    if (searchQuery.trim()) {
      const q = searchQuery.toLowerCase().trim();
      const matchTitle = d.title.toLowerCase().includes(q);
      const matchId = d.id.toLowerCase().includes(q);
      const matchEngine = d.source_engine.toLowerCase().includes(q);
      const matchAction = d.proposed_action.toLowerCase().includes(q);
      return matchTitle || matchId || matchEngine || matchAction;
    }

    return true;
  });

  const getStatusBadge = (status: ReviewStatus) => {
    switch (status) {
      case "approved":
        return (
          <Badge variant="success" size="sm" className="font-mono flex items-center gap-1">
            <CheckCircle2 className="h-3 w-3" />
            <span>Approved</span>
          </Badge>
        );
      case "rejected":
        return (
          <Badge variant="danger" size="sm" className="font-mono flex items-center gap-1">
            <XCircle className="h-3 w-3" />
            <span>Rejected</span>
          </Badge>
        );
      case "revision_requested":
        return (
          <Badge variant="info" size="sm" className="font-mono flex items-center gap-1">
            <RotateCcw className="h-3 w-3" />
            <span>Revision</span>
          </Badge>
        );
      case "pending_review":
      default:
        return (
          <Badge variant="warning" size="sm" className="font-mono flex items-center gap-1">
            <Clock className="h-3 w-3" />
            <span>Pending</span>
          </Badge>
        );
    }
  };

  const getUrgencyBadge = (level: "critical" | "high" | "moderate") => {
    switch (level) {
      case "critical":
        return (
          <span className="inline-flex items-center gap-1 text-[11px] font-mono text-rose-400 font-semibold">
            <AlertTriangle className="h-3 w-3" />
            <span>Critical</span>
          </span>
        );
      case "high":
        return (
          <span className="inline-flex items-center gap-1 text-[11px] font-mono text-amber-400 font-medium">
            <AlertTriangle className="h-3 w-3" />
            <span>High</span>
          </span>
        );
      case "moderate":
      default:
        return (
          <span className="inline-flex items-center gap-1 text-[11px] font-mono text-slate-400">
            <span>Moderate</span>
          </span>
        );
    }
  };

  return (
    <Card data-testid="review-queue" className="border-slate-800 bg-slate-900/60 shadow-xl overflow-hidden">
      <CardHeader className="p-4 border-b border-slate-800/80 bg-slate-950/40">
        <div className="flex items-center justify-between gap-2">
          <div className="flex items-center gap-2">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg bg-sky-950/80 border border-sky-600/40 text-sky-400">
              <Inbox className="h-4 w-4" />
            </div>
            <div>
              <CardTitle className="text-sm font-semibold text-slate-100">
                Review Queue
              </CardTitle>
              <CardDescription className="text-xs text-slate-400">
                Statutory Sign-Off Dossiers
              </CardDescription>
            </div>
          </div>
          <Badge variant="outline" size="sm" className="font-mono text-slate-300">
            {dossiers.length} Total
          </Badge>
        </div>

        {/* Tab Filters */}
        <div className="mt-3 grid grid-cols-3 gap-1 rounded-md bg-slate-950 p-1 border border-slate-800 text-xs font-medium">
          <button
            type="button"
            data-testid="filter-tab-all"
            onClick={() => setActiveTab("all")}
            className={cn(
              "rounded px-2 py-1 text-center transition-colors flex items-center justify-center gap-1",
              activeTab === "all"
                ? "bg-slate-800 text-slate-100 font-semibold shadow-sm"
                : "text-slate-400 hover:text-slate-200"
            )}
          >
            <span>All</span>
            <span className="text-[10px] opacity-75 font-mono">({dossiers.length})</span>
          </button>
          <button
            type="button"
            data-testid="filter-tab-pending"
            onClick={() => setActiveTab("pending")}
            className={cn(
              "rounded px-2 py-1 text-center transition-colors flex items-center justify-center gap-1",
              activeTab === "pending"
                ? "bg-amber-950/80 text-amber-300 font-semibold border border-amber-600/50 shadow-sm"
                : "text-slate-400 hover:text-slate-200"
            )}
          >
            <span>Pending</span>
            <span className="text-[10px] opacity-75 font-mono">({pendingCount})</span>
          </button>
          <button
            type="button"
            data-testid="filter-tab-decided"
            onClick={() => setActiveTab("decided")}
            className={cn(
              "rounded px-2 py-1 text-center transition-colors flex items-center justify-center gap-1",
              activeTab === "decided"
                ? "bg-slate-800 text-slate-100 font-semibold shadow-sm"
                : "text-slate-400 hover:text-slate-200"
            )}
          >
            <span>Decided</span>
            <span className="text-[10px] opacity-75 font-mono">({decidedCount})</span>
          </button>
        </div>

        {/* Search input */}
        <div className="relative mt-2.5">
          <Search className="absolute left-2.5 top-2.5 h-3.5 w-3.5 text-slate-500" />
          <input
            type="text"
            placeholder="Search dossier by name, ID, or action..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full rounded-md border border-slate-800 bg-slate-950/80 pl-8 pr-3 py-1.5 text-xs text-slate-200 placeholder-slate-500 focus:border-sky-500 focus:outline-none focus:ring-1 focus:ring-sky-500"
          />
        </div>
      </CardHeader>

      <CardContent className="p-2 divide-y divide-slate-800/60 max-h-[580px] overflow-y-auto">
        {isLoading ? (
          <div className="py-8 text-center text-xs text-slate-400 font-mono">
            Loading recommendation dossiers...
          </div>
        ) : filteredDossiers.length === 0 ? (
          <div className="py-8 text-center text-xs text-slate-500">
            No recommendation dossiers found in this view.
          </div>
        ) : (
          filteredDossiers.map((dossier) => {
            const isSelected = dossier.id === selectedDossierId;
            return (
              <button
                key={dossier.id}
                type="button"
                onClick={() => onSelectDossier(dossier.id)}
                className={cn(
                  "w-full text-left p-3 transition-all rounded-lg my-1 block",
                  isSelected
                    ? "bg-sky-950/40 border border-sky-500/60 shadow-md shadow-sky-950/50"
                    : "hover:bg-slate-800/40 border border-transparent"
                )}
              >
                <div className="flex items-start justify-between gap-2">
                  <div className="flex items-center gap-1.5 flex-wrap">
                    <span className="text-[11px] font-mono text-slate-500">
                      {dossier.id}
                    </span>
                    <span className="text-slate-600">•</span>
                    <span className="text-[11px] font-mono text-sky-400 capitalize">
                      {dossier.type === "relocation_plan"
                        ? "Relocation Plan"
                        : "Scenario Evaluation"}
                    </span>
                  </div>
                  {getStatusBadge(dossier.status)}
                </div>

                <div className="font-semibold text-xs text-slate-200 mt-1 line-clamp-1">
                  {dossier.title}
                </div>

                <div className="text-[11px] text-slate-400 mt-1 line-clamp-2 leading-relaxed">
                  {dossier.proposed_action}
                </div>

                <div className="mt-2.5 pt-2 border-t border-slate-800/50 flex items-center justify-between text-[11px]">
                  {getUrgencyBadge(dossier.urgency_level)}
                  <div className="flex items-center gap-1 text-slate-400 group-hover:text-slate-200">
                    <span className="text-[10px] font-mono">Inspect</span>
                    <ArrowRight className="h-3 w-3 text-sky-400" />
                  </div>
                </div>
              </button>
            );
          })
        )}
      </CardContent>
    </Card>
  );
};
