"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  Activity,
  ArrowRightLeft,
  MapPin,
  Sliders,
  ShieldAlert,
  FileText,
  ShieldCheck,
  History,
  Database,
} from "lucide-react";
import { cn } from "@/lib/utils";

export interface OperationsNavItem {
  id: string;
  label: string;
  href: string;
  chunkId: string;
  description: string;
  icon: React.ComponentType<{ className?: string }>;
}

export const OPERATIONS_NAV_ITEMS: OperationsNavItem[] = [
  {
    id: "overview",
    label: "Operations Hub",
    href: "/operations",
    chunkId: "M6-01",
    description: "Operations command center summary & readiness posture",
    icon: Activity,
  },
  {
    id: "relocation",
    label: "Relocation",
    href: "/operations/relocation",
    chunkId: "M6-02",
    description: "Village-to-site relocation matching & assignment",
    icon: ArrowRightLeft,
  },
  {
    id: "sites",
    label: "Sites",
    href: "/operations/sites",
    chunkId: "M6-03",
    description: "Candidate relocation site details & infrastructure sizing",
    icon: MapPin,
  },
  {
    id: "scenarios",
    label: "Scenarios",
    href: "/operations/scenarios",
    chunkId: "M6-04",
    description: "Multi-hazard scenario simulation & parameter perturbation",
    icon: Sliders,
  },
  {
    id: "alerts",
    label: "Alerts",
    href: "/operations/alerts",
    chunkId: "M6-05",
    description: "Real-time hazard telemetry & dynamic red zone threshold warnings",
    icon: ShieldAlert,
  },
  {
    id: "sources",
    label: "Data Sources",
    href: "/operations/sources",
    chunkId: "M6-06",
    description: "Real-time provider adapter health & freshness diagnostics",
    icon: Database,
  },
  {
    id: "reports",
    label: "Reports",
    href: "/operations/reports",
    chunkId: "M6-07",
    description: "Authoritative relocation dossiers & statutory export",
    icon: FileText,
  },
  {
    id: "review",
    label: "Officer Review",
    href: "/operations/review",
    chunkId: "M6-08",
    description: "Statutory Rule 12 officer review & action sign-off workflow",
    icon: ShieldCheck,
  },
  {
    id: "audit",
    label: "Audit Log",
    href: "/operations/audit",
    chunkId: "M6-09",
    description: "Immutable decision traceability & action change logs",
    icon: History,
  },
];

export interface OperationsNavProps {
  className?: string;
}

export const OperationsNav: React.FC<OperationsNavProps> = ({ className }) => {
  const pathname = usePathname();

  return (
    <nav
      aria-label="Operations Navigation"
      className={cn(
        "flex w-full items-center gap-1 overflow-x-auto border-b border-border-subtle pb-2 scrollbar-none",
        className
      )}
    >
      {OPERATIONS_NAV_ITEMS.map((item) => {
        const Icon = item.icon;
        const isActive =
          item.href === "/operations"
            ? pathname === "/operations"
            : pathname === item.href || pathname?.startsWith(`${item.href}/`);

        return (
          <Link
            key={item.id}
            href={item.href}
            aria-current={isActive ? "page" : undefined}
            title={`${item.label} (${item.chunkId}) — ${item.description}`}
            className={cn(
              "group flex shrink-0 items-center gap-2 rounded-md px-3 py-1.5 text-xs font-medium transition-all focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-focus-ring",
              isActive
                ? "bg-surface-elevated text-text-primary font-semibold border border-border-strong"
                : "text-text-secondary hover:text-text-primary hover:bg-surface-elevated/60 border border-transparent"
            )}
          >
            <Icon
              className={cn(
                "h-3.5 w-3.5 shrink-0 transition-colors",
                isActive ? "text-text-primary" : "text-text-muted group-hover:text-text-secondary"
              )}
            />
            <span className="whitespace-nowrap">{item.label}</span>
            <span className="sr-only" data-testid="nav-chunk-id">{item.chunkId}</span>
          </Link>
        );
      })}
    </nav>
  );
};
