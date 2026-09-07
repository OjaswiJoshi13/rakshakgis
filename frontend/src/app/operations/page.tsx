"use client";

import React from "react";
import Link from "next/link";
import {
  ArrowRightLeft,
  MapPin,
  Sliders,
  ShieldAlert,
  FileText,
  ShieldCheck,
  History,
  ArrowRight,
  Shield,
  Layers,
  Database,
} from "lucide-react";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
  CardFooter,
} from "@/components/ui/Card";
import { Badge } from "@/components/ui/Badge";
import { Button } from "@/components/ui/Button";
import { MetricCard } from "@/components/ui/MetricCard";
import { Alert } from "@/components/ui/Alert";

interface OperationsModuleCard {
  id: string;
  title: string;
  chunkId: string;
  chunkTitle: string;
  description: string;
  href: string;
  icon: React.ComponentType<{ className?: string }>;
  backendBinding: string;
  ruleMandate?: string;
}

const OPERATIONS_MODULES: OperationsModuleCard[] = [
  {
    id: "relocation",
    title: "Relocation Planner",
    chunkId: "M6-02",
    chunkTitle: "Relocation Planner Workflow UI",
    description:
      "Interactive village-to-site relocation matching workflow with capacity constraints and multi-village assignment visualization.",
    href: "/operations/relocation",
    icon: ArrowRightLeft,
    backendBinding: "M4-04 Relocation Matching Engine",
  },
  {
    id: "sites",
    title: "Relocation Sites & Infrastructure",
    chunkId: "M6-03",
    chunkTitle: "Relocation Site Details & Infrastructure UI",
    description:
      "Candidate site suitability inspection, 5-dimension infrastructure sizing, and community capacity bottlenecks.",
    href: "/operations/sites",
    icon: MapPin,
    backendBinding: "M4-01 Sites & M4-03 Carrying Capacity",
  },
  {
    id: "scenarios",
    title: "Scenario Simulator",
    chunkId: "M6-04",
    chunkTitle: "Scenario Simulator UI",
    description:
      "Deterministic hazard perturbation testing: simulate rainfall intensity spikes, slope destabilization, and cascading infrastructure impact.",
    href: "/operations/scenarios",
    icon: Sliders,
    backendBinding: "M4-06 Scenario Simulator Backend",
  },
  {
    id: "alerts",
    title: "Real-Time Alerts & Warnings",
    chunkId: "M6-05",
    chunkTitle: "Real-Time Alerts & Threshold Warnings UI",
    description:
      "Dynamic Red Zone threshold breach alerts, sensor telemetry monitoring, and multi-tier hazard warning notifications.",
    href: "/operations/alerts",
    icon: ShieldAlert,
    backendBinding: "M3-11 Red Zone Threshold Engine",
  },
  {
    id: "sources",
    title: "Data Sources & Freshness",
    chunkId: "M6-06",
    chunkTitle: "Data Sources & Freshness Monitoring UI",
    description:
      "Provider adapter health monitoring, deterministic 5-state temporal freshness evaluation, and ingestion run telemetry.",
    href: "/operations/sources",
    icon: Database,
    backendBinding: "M3-13 Freshness & Telemetry Backend",
  },
  {
    id: "reports",
    title: "Reports & Statutory Dossiers",
    chunkId: "M6-07",
    chunkTitle: "Report Generation & Export UI",
    description:
      "Statutory relocation reports, executive risk summaries, and machine-readable data export for district administration.",
    href: "/operations/reports",
    icon: FileText,
    backendBinding: "Relocation & Risk Core Engines",
  },
  {
    id: "review",
    title: "Officer Review & Sign-Off",
    chunkId: "M6-08",
    chunkTitle: "Officer Review & Action Sign-Off Workflow",
    description:
      "Statutory Rule 12 verification gateway: review AI recommendations, record legal declarations, and execute multi-officer digital sign-offs.",
    href: "/operations/review",
    icon: ShieldCheck,
    backendBinding: "M4 Relocation & M3 Risk Engines",
    ruleMandate: "Rule 12 Mandatory Approval",
  },
  {
    id: "audit",
    title: "Audit Log & Traceability",
    chunkId: "M6-09",
    chunkTitle: "Audit Log & Traceability UI",
    description:
      "Immutable decision audit trail, cryptographic hash verification, and timestamped action history for statutory transparency.",
    href: "/operations/audit",
    icon: History,
    backendBinding: "Decision Audit Trail Store",
  },
];

export default function OperationsHubPage() {
  return (
    <div className="space-y-8">
      {/* Officer Operational Posture Banner */}
      <div className="rounded-lg border border-border-subtle bg-surface-panel p-5 shadow-sm">
        <div className="flex flex-col lg:flex-row lg:items-center justify-between gap-4">
          <div className="space-y-1">
            <div className="flex items-center gap-2">
              <span className="sr-only">Chunk M6-01</span>
              <span className="text-xs font-mono text-[#1a7f37] dark:text-[#3fb950] font-medium">
                Decision Support Workflows Active
              </span>
            </div>
            <h1 className="text-xl sm:text-2xl font-bold tracking-tight text-text-primary">
              Operations Management & Decision Support Console
            </h1>
            <p className="text-xs sm:text-sm text-text-secondary max-w-3xl">
              Officer command center providing specialized interfaces for disaster response, 
              climate-resilient relocation planning, scenario exploration, statutory sign-off, 
              and immutable decision traceability.
            </p>
          </div>

          <div className="flex items-center gap-2">
            <Link href="/operations/review">
              <Button variant="primary" size="sm" className="gap-2">
                <ShieldCheck className="h-4 w-4" />
                <span>Officer Review Queue</span>
              </Button>
            </Link>
          </div>
        </div>
      </div>

      {/* Operational Readiness Parameters */}
      <section aria-labelledby="operational-readiness-heading">
        <h2
          id="operational-readiness-heading"
          className="text-xs font-mono font-semibold uppercase tracking-wider text-text-muted mb-3"
        >
          Operational Readiness & Governance Posture
        </h2>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          <MetricCard
            label="Protocol Standard"
            value="Rule 12"
            subtext="Officer Approval Required"
            status="warning"
          />
          <MetricCard
            label="Active Operation Areas"
            value="7"
            unit="Workflows"
            subtext={<>Decision Instruments<span className="sr-only"> M6-02 through M6-09</span></>}
            status="info"
          />
          <MetricCard
            label="Spatial Coordinate System"
            value="EPSG:4326"
            subtext="WGS 84 Authoritative Projection"
            status="normal"
          />
          <MetricCard
            label="Decision Traceability"
            value="Enabled"
            subtext="Immutable Action Logging"
            status="normal"
          />
        </div>
      </section>

      {/* Statutory Mandate Alert */}
      <Alert severity="info" title="Statutory Decision Governance — Rule 12 Compliance">
        All AI-generated recommendations (village relocation assignments, dynamic Red Zone demarcations,
        and simulated hazard impacts) must be explicitly reviewed, validated, and signed off by authorized
        district officers prior to field execution or administrative notification.
      </Alert>

      {/* Operations Area Directory */}
      <section aria-labelledby="operations-directory-heading">
        <div className="flex items-center justify-between mb-4">
          <div>
            <h2
              id="operations-directory-heading"
              className="text-xs font-mono font-semibold uppercase tracking-wider text-text-muted"
            >
              Officer Operational Domains
            </h2>
            <p className="text-xs text-text-secondary mt-0.5">
              Select an operations domain to navigate to its specialized workflow container.
            </p>
          </div>
          <span className="text-xs font-mono text-text-muted hidden sm:inline-block">
            7 Specialized Instruments
          </span>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
          {OPERATIONS_MODULES.map((module) => {
            const Icon = module.icon;
            return (
              <Card
                key={module.id}
                className="flex flex-col justify-between border-border-base bg-surface-raised hover:border-border-strong hover:shadow-2xs transition-all"
              >
                <CardHeader className="pb-3">
                  <div className="flex items-center justify-between gap-2 mb-2">
                    <div className="flex h-8 w-8 items-center justify-center rounded border border-border-base bg-surface-base text-text-secondary">
                      <Icon className="h-4 w-4" />
                    </div>
                    <div className="flex items-center gap-1.5">
                      {module.ruleMandate && (
                        <span className="rounded bg-amber-500/10 border border-amber-600/30 px-1.5 py-0.5 text-[9px] font-mono text-amber-700 dark:text-amber-300 font-medium">
                          {module.ruleMandate}
                        </span>
                      )}
                      <span className="sr-only">{module.chunkId}</span>
                    </div>
                  </div>

                  <CardTitle className="text-sm sm:text-base font-semibold text-text-primary">
                    {module.title}
                  </CardTitle>
                  <CardDescription className="text-xs text-text-secondary line-clamp-3 mt-1">
                    {module.description}
                  </CardDescription>
                </CardHeader>

                <CardContent className="py-0 pb-3">
                  <div className="flex items-center gap-1.5 text-[11px] font-mono text-text-muted bg-surface-base rounded px-2 py-1 border border-border-subtle">
                    <Layers className="h-3 w-3 text-text-muted shrink-0" />
                    <span className="truncate">{module.backendBinding.replace(/M\d+-\d+\s*/g, "")}</span>
                  </div>
                </CardContent>

                <CardFooter className="pt-2 border-t border-border-subtle flex items-center justify-between">
                  <span className="sr-only">{module.chunkTitle}</span>
                  <span className="text-[11px] font-mono text-text-muted">
                    Operational Workflow
                  </span>
                  <Link href={module.href}>
                    <Button variant="ghost" size="sm" className="gap-1 text-xs text-text-secondary hover:text-text-primary p-1">
                      <span>Open</span>
                      <ArrowRight className="h-3.5 w-3.5" />
                    </Button>
                  </Link>
                </CardFooter>
              </Card>
            );
          })}
        </div>
      </section>
    </div>
  );
}
