"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

export interface NavItem {
  name: string;
  href: string;
  chunkId: string;
  status: "active" | "planned";
  icon: React.ReactNode;
}

export interface SidebarProps {
  isOpen?: boolean;
  onClose?: () => void;
}

export const Sidebar: React.FC<SidebarProps> = ({ isOpen = true, onClose }) => {
  const pathname = usePathname();

  const platformItems: NavItem[] = [
    {
      name: "System Foundation",
      href: "/",
      chunkId: "M5-01",
      status: "active",
      icon: (
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2V6zM14 6a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V6zM4 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2H6a2 2 0 01-2-2v-2zM14 16a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
        </svg>
      ),
    },
    {
      name: "Executive Dashboard",
      href: "/dashboard",
      chunkId: "M5-04",
      status: "planned",
      icon: (
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>
      ),
    },
    {
      name: "MapLibre GIS Canvas",
      href: "/gis",
      chunkId: "M5-05",
      status: "planned",
      icon: (
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 20l-5.447-2.724A1 1 0 013 16.382V5.618a1 1 0 011.447-.894L9 7m0 13l6-3m-6 3V7m6 10l4.553 2.276A1 1 0 0021 18.382V7.618a1 1 0 00-.553-.894L15 4m0 13V4m0 0L9 7" />
        </svg>
      ),
    },
    {
      name: "Village Vulnerability",
      href: "/villages",
      chunkId: "M5-06",
      status: "planned",
      icon: (
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 21V5a2 2 0 00-2-2H7a2 2 0 00-2 2v16m14 0h2m-2 0h-5m-9 0H3m2 0h5M9 7h1m-1 4h1m4-4h1m-1 4h1m-5 10v-5a1 1 0 011-1h2a1 1 0 011 1v5m-4 0h4" />
        </svg>
      ),
    },
  ];

  const operationsItems: NavItem[] = [
    {
      name: "Operations Hub",
      href: "/operations",
      chunkId: "M6-01",
      status: "active",
      icon: (
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z" />
        </svg>
      ),
    },
    {
      name: "Relocation Planner",
      href: "/operations/relocation",
      chunkId: "M6-02",
      status: "active",
      icon: (
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 7h12m0 0l-4-4m4 4l-4 4m0 6H4m0 0l4 4m-4-4l4-4" />
        </svg>
      ),
    },
    {
      name: "Relocation Sites",
      href: "/operations/sites",
      chunkId: "M6-03",
      status: "active",
      icon: (
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M17.657 16.657L13.414 20.9a1.998 1.998 0 01-2.827 0l-4.244-4.243a8 8 0 1111.314 0z" />
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 11a3 3 0 11-6 0 3 3 0 016 0z" />
        </svg>
      ),
    },
    {
      name: "Scenario Simulator",
      href: "/operations/scenarios",
      chunkId: "M6-04",
      status: "active",
      icon: (
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
        </svg>
      ),
    },
    {
      name: "Threshold Warnings",
      href: "/operations/alerts",
      chunkId: "M6-05",
      status: "active",
      icon: (
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9" />
        </svg>
      ),
    },
    {
      name: "Reports & Export",
      href: "/operations/reports",
      chunkId: "M6-07",
      status: "active",
      icon: (
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
        </svg>
      ),
    },
    {
      name: "Officer Sign-Off",
      href: "/operations/review",
      chunkId: "M6-08",
      status: "active",
      icon: (
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m5.618-4.016A11.955 11.955 0 0112 2.944a11.955 11.955 0 01-8.618 3.04A12.02 12.02 0 003 9c0 5.591 3.824 10.29 9 11.622 5.176-1.332 9-6.03 9-11.622 0-1.042-.133-2.052-.382-3.016z" />
        </svg>
      ),
    },
    {
      name: "Audit & Traceability",
      href: "/operations/audit",
      chunkId: "M6-09",
      status: "active",
      icon: (
        <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
      ),
    },
  ];


  return (
    <>
      {/* Mobile backdrop */}
      {isOpen && (
        <div
          className="fixed inset-0 z-30 bg-black/60 backdrop-blur-sm lg:hidden"
          onClick={onClose}
          aria-hidden="true"
        />
      )}

      <aside
        className={cn(
          "fixed top-14 bottom-8 left-0 z-30 flex w-64 flex-col border-r border-slate-800 bg-slate-950 transition-transform duration-200 ease-in-out lg:static lg:translate-x-0",
          isOpen ? "translate-x-0" : "-translate-x-full"
        )}
        aria-label="Platform Modules Navigation"
      >
        <div className="p-3 border-b border-slate-800/80">
          <span className="text-[11px] font-mono font-semibold uppercase tracking-wider text-slate-400">
            Platform Modules
          </span>
        </div>

        <nav className="flex-1 space-y-3 p-2 overflow-y-auto">
          {/* Platform Core Modules */}
          <div className="space-y-1">
            <div className="px-2 pt-1 pb-0.5">
              <span className="text-[10px] font-mono font-semibold uppercase tracking-wider text-slate-400">
                Platform Core
              </span>
            </div>
            {platformItems.map((item) => {
              const isActive =
                item.href === "/"
                  ? pathname === "/"
                  : pathname === item.href || pathname?.startsWith(`${item.href}/`);
              return (
                <div key={item.chunkId}>
                  {item.status === "active" ? (
                    <Link
                      href={item.href}
                      onClick={onClose}
                      aria-current={isActive ? "page" : undefined}
                      className={cn(
                        "flex items-center justify-between rounded-md px-3 py-2 text-xs font-medium transition-colors group",
                        isActive
                          ? "bg-sky-950/80 text-sky-200 border border-sky-800/60 font-semibold"
                          : "text-slate-300 hover:bg-slate-900 hover:text-slate-100"
                      )}
                    >
                      <div className="flex items-center gap-2.5">
                        <span className={cn(isActive ? "text-sky-400" : "text-slate-400 group-hover:text-slate-200")}>
                          {item.icon}
                        </span>
                        <span>{item.name}</span>
                      </div>
                      <span className="rounded bg-sky-900/60 border border-sky-700/50 px-1 py-0.5 text-[10px] font-mono text-sky-300">
                        {item.chunkId}
                      </span>
                    </Link>
                  ) : (
                    <div
                      className="flex items-center justify-between rounded-md px-3 py-2 text-xs font-medium text-slate-500 hover:text-slate-400 transition-colors select-none cursor-not-allowed"
                      title={`Scheduled for Chunk ${item.chunkId}`}
                    >
                      <div className="flex items-center gap-2.5">
                        <span className="text-slate-600">{item.icon}</span>
                        <span>{item.name}</span>
                      </div>
                      <span className="rounded bg-slate-900 border border-slate-800 px-1 py-0.5 text-[9px] font-mono text-slate-500">
                        {item.chunkId}
                      </span>
                    </div>
                  )}
                </div>
              );
            })}
          </div>

          {/* Officer Operations Modules (M6) */}
          <div className="space-y-1 pt-1 border-t border-slate-800/80">
            <div className="px-2 pt-1 pb-0.5 flex items-center justify-between">
              <span className="text-[10px] font-mono font-semibold uppercase tracking-wider text-sky-400">
                Officer Operations
              </span>
              <span className="rounded bg-sky-950/80 border border-sky-700/50 px-1 py-0.2 text-[9px] font-mono text-sky-400">
                M6
              </span>
            </div>
            {operationsItems.map((item) => {
              const isActive =
                item.href === "/operations"
                  ? pathname === "/operations"
                  : pathname === item.href || pathname?.startsWith(`${item.href}/`);
              return (
                <div key={item.chunkId}>
                  <Link
                    href={item.href}
                    onClick={onClose}
                    aria-current={isActive ? "page" : undefined}
                    className={cn(
                      "flex items-center justify-between rounded-md px-3 py-2 text-xs font-medium transition-colors group",
                      isActive
                        ? "bg-sky-950/80 text-sky-200 border border-sky-800/60 font-semibold"
                        : "text-slate-300 hover:bg-slate-900 hover:text-slate-100"
                    )}
                  >
                    <div className="flex items-center gap-2.5">
                      <span className={cn(isActive ? "text-sky-400" : "text-slate-400 group-hover:text-slate-200")}>
                        {item.icon}
                      </span>
                      <span>{item.name}</span>
                    </div>
                    <span className="rounded bg-sky-900/60 border border-sky-700/50 px-1 py-0.5 text-[10px] font-mono text-sky-300">
                      {item.chunkId}
                    </span>
                  </Link>
                </div>
              );
            })}
          </div>
        </nav>

        {/* Status Footer within Sidebar */}
        <div className="border-t border-slate-800/80 p-3 bg-slate-950/50 text-[11px] font-mono text-slate-400 space-y-1.5">
          <div className="flex items-center justify-between">
            <span>Core Foundation</span>
            <span className="text-emerald-400">M5-01 READY</span>
          </div>
          <div className="flex items-center justify-between">
            <span>Operations Shell</span>
            <span className="text-sky-400">M6-01 READY</span>
          </div>
        </div>
      </aside>
    </>
  );
};
