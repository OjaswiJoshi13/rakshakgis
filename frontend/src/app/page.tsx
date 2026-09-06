import React from "react";
import Link from "next/link";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { AppLayout } from "@/components/layout/AppLayout";
import {
  Card,
  CardHeader,
  CardTitle,
  CardDescription,
  CardContent,
} from "@/components/ui/Card";
import { Button } from "@/components/ui/Button";
import { Badge, RiskBadge, RelocationBadge } from "@/components/ui/Badge";
import { MetricCard } from "@/components/ui/MetricCard";
import { Alert } from "@/components/ui/Alert";
import { StatusIndicator } from "@/components/ui/StatusIndicator";
import { RISK_BANDS, RELOCATION_PRIORITY_BANDS } from "@/design-system/tokens";

export default function HomePage() {
  return (
    <ProtectedRoute>
      <AppLayout>
      <div className="space-y-8">
        {/* Foundation Hero Banner */}
        <div className="border-b border-slate-800 pb-5">
          <div className="flex flex-wrap items-center justify-between gap-4">
            <div>
              <div className="flex items-center gap-2 mb-1">
                <Badge variant="outline" size="sm">
                  Chunk M5-01
                </Badge>
                <span className="text-xs font-mono text-emerald-400">
                  Foundation & Design System
                </span>
              </div>
              <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-slate-100">
                RakshakGIS Command Center Shell
              </h1>
              <p className="text-sm text-slate-400 mt-1 max-w-3xl">
                Authority-facing decision support system for multi-hazard risk assessment,
                dynamic red zone demarcation, and climate-resilient relocation planning.
              </p>
            </div>

            <div className="flex items-center gap-2">
              <Link href="/dashboard">
                <Button variant="primary" size="sm">
                  Executive Dashboard &rarr;
                </Button>
              </Link>
              <Button variant="secondary" size="sm">
                System Specification
              </Button>
            </div>
          </div>
        </div>

        {/* Operational Overview Metrics */}
        <section aria-labelledby="system-parameters-heading">
          <h2
            id="system-parameters-heading"
            className="text-xs font-mono font-semibold uppercase tracking-wider text-slate-400 mb-3"
          >
            System Baseline & Architecture Parameters
          </h2>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
            <MetricCard
              label="Region Profile"
              value="Himalayan"
              subtext="Chamoli District Pilot"
              status="normal"
            />
            <MetricCard
              label="Multi-Hazard Model"
              value="6"
              unit="Factors"
              subtext="0.30H+0.20F+0.15R+0.15S+0.10D+0.10V"
              status="info"
            />
            <MetricCard
              label="Relocation Priority"
              value="4"
              unit="Bands"
              subtext="Immediate, Short, Medium, Monitor"
              status="warning"
            />
            <MetricCard
              label="Coordinate System"
              value="EPSG:4326"
              subtext="WGS 84 Standard Lat/Long"
              status="normal"
            />
          </div>
        </section>

        {/* Operational Risk & Severity Specification Grid */}
        <section aria-labelledby="severity-tokens-heading">
          <h2
            id="severity-tokens-heading"
            className="text-xs font-mono font-semibold uppercase tracking-wider text-slate-400 mb-3"
          >
            Multi-Hazard Risk Bands (Authoritative Specification)
          </h2>

          <Card variant="elevated">
            <CardHeader>
              <CardTitle>Composite Risk Score Classifications</CardTitle>
              <CardDescription>
                Deterministic risk score bands matching Chunk M3-01 & M3-07 domain engine thresholds.
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-5 gap-3">
                {(
                  Object.keys(RISK_BANDS) as Array<keyof typeof RISK_BANDS>
                ).map((bandKey) => {
                  const band = RISK_BANDS[bandKey];
                  return (
                    <div
                      key={bandKey}
                      className="rounded border border-slate-800 bg-slate-950 p-3 flex flex-col justify-between space-y-2"
                    >
                      <div className="flex items-center justify-between">
                        <RiskBadge band={bandKey} showScore={false} />
                        <span className="text-xs font-mono text-slate-400">
                          {band.min}–{band.max}
                        </span>
                      </div>
                      <p className="text-[11px] text-slate-400 leading-snug">
                        {band.description}
                      </p>
                    </div>
                  );
                })}
              </div>
            </CardContent>
          </Card>
        </section>

        {/* Relocation Priority Bands */}
        <section aria-labelledby="relocation-tokens-heading">
          <h2
            id="relocation-tokens-heading"
            className="text-xs font-mono font-semibold uppercase tracking-wider text-slate-400 mb-3"
          >
            Relocation Urgency Bands (Authoritative Specification)
          </h2>

          <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3">
            {(
              Object.keys(RELOCATION_PRIORITY_BANDS) as Array<
                keyof typeof RELOCATION_PRIORITY_BANDS
              >
            ).map((bandKey) => {
              const band = RELOCATION_PRIORITY_BANDS[bandKey];
              return (
                <div
                  key={bandKey}
                  className="rounded border border-slate-800 bg-slate-900/60 p-3 space-y-2"
                >
                  <div className="flex items-center justify-between">
                    <RelocationBadge band={bandKey} />
                    <span className="text-xs font-mono text-slate-400">
                      Score: {band.min}–{band.max}
                    </span>
                  </div>
                  <p className="text-xs text-slate-400 font-sans">
                    Action horizon: {band.label}
                  </p>
                </div>
              );
            })}
          </div>
        </section>

        {/* Operational Alerts Showcase */}
        <section aria-labelledby="operational-alerts-heading">
          <h2
            id="operational-alerts-heading"
            className="text-xs font-mono font-semibold uppercase tracking-wider text-slate-400 mb-3"
          >
            Operational Alert & Warning Components
          </h2>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <Alert severity="danger" title="CRITICAL: Dynamic Red Zone Threshold Exceeded">
              Landslide slope telemetry in Joshimath Sector B exceeded warning trigger (35.2°).
              Immediate officer review required under SOP-RZ-01.
            </Alert>
            <Alert severity="warning" title="WEATHER WATCH: IMD Rainfall Warning">
              Heavy rainfall observation detected (72.4 mm/24h &gt; 64.5 mm threshold). Soil moisture
              saturation escalating in Dasholi block.
            </Alert>
            <Alert severity="info" title="SYSTEM INFO: Synthetic Dataset Mode Active">
              Demonstration mode enabled using seed 26191 fixtures (40 villages, 12 candidate sites).
              No external API credentials required for local verification.
            </Alert>
            <Alert severity="success" title="FOUNDATION READY: Chunk M5-01 Initialized">
              Design tokens, UI primitives, command header, sidebar navigation, and layout canvas
              established for downstream M5/M6 modules.
            </Alert>
          </div>
        </section>

        {/* UI Primitives Showcase */}
        <section aria-labelledby="ui-primitives-heading">
          <h2
            id="ui-primitives-heading"
            className="text-xs font-mono font-semibold uppercase tracking-wider text-slate-400 mb-3"
          >
            Reusable Foundational UI Primitives
          </h2>

          <Card variant="bordered">
            <CardHeader>
              <CardTitle>Interactive Elements & Focus States</CardTitle>
              <CardDescription>
                Accessible, keyboard-navigable components adhering to WCAG 2.1 AA standards.
              </CardDescription>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex flex-wrap items-center gap-3">
                <Button variant="primary">Primary Action</Button>
                <Button variant="secondary">Secondary Action</Button>
                <Button variant="outline">Outline</Button>
                <Button variant="ghost">Ghost</Button>
                <Button variant="danger">Emergency / Critical</Button>
                <Button variant="primary" isLoading>
                  Processing
                </Button>
              </div>

              <div className="flex flex-wrap items-center gap-3 pt-2">
                <StatusIndicator status="normal" />
                <StatusIndicator status="info" />
                <StatusIndicator status="warning" />
                <StatusIndicator status="critical" showPulse />
              </div>
            </CardContent>
          </Card>
        </section>
      </div>
    </AppLayout>
    </ProtectedRoute>
  );
}
