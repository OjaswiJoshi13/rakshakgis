"use client";

import React, { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/context/AuthContext";
import { LoginForm } from "@/components/auth/LoginForm";
import { Badge } from "@/components/ui/Badge";

export default function LoginPage() {
  const router = useRouter();
  const { isAuthenticated, isLoading } = useAuth();

  useEffect(() => {
    if (!isLoading && isAuthenticated) {
      router.replace("/");
    }
  }, [isAuthenticated, isLoading, router]);

  return (
    <div className="flex min-h-screen flex-col justify-between bg-slate-950 text-slate-100 selection:bg-sky-500 selection:text-white">
      {/* Background ambient glow effect */}
      <div className="fixed inset-0 pointer-events-none overflow-hidden">
        <div className="absolute -top-40 left-1/2 -translate-x-1/2 w-[600px] h-[350px] bg-sky-600/10 blur-[120px] rounded-full" />
        <div className="absolute -bottom-40 left-1/3 w-[500px] h-[300px] bg-emerald-600/5 blur-[120px] rounded-full" />
      </div>

      {/* Top Banner Header */}
      <header className="relative z-10 flex h-14 w-full items-center justify-between border-b border-slate-800/80 bg-slate-950/80 px-6 backdrop-blur">
        <div className="flex items-center gap-2.5">
          <div className="flex h-7 w-7 items-center justify-center rounded bg-sky-950 border border-sky-600 text-sky-400 font-bold font-mono text-xs tracking-tighter">
            RG
          </div>
          <div className="flex items-center gap-2">
            <span className="font-bold tracking-tight text-slate-100 text-sm">
              RakshakGIS
            </span>
            <span className="rounded bg-slate-800 px-1.5 py-0.2 text-[10px] font-mono text-slate-400 uppercase tracking-widest border border-slate-700">
              SIH 26191
            </span>
          </div>
        </div>

        <div className="flex items-center gap-2">
          <Badge variant="outline" size="sm" className="font-mono text-[10px]">
            Himalayan Pilot (Chamoli)
          </Badge>
        </div>
      </header>

      {/* Main Login Canvas */}
      <main className="relative z-10 flex flex-1 items-center justify-center p-4 sm:p-6 lg:p-8">
        <div className="w-full max-w-md space-y-6">
          <div className="text-center space-y-2">
            <h1 className="text-2xl font-bold tracking-tight text-slate-100 sm:text-3xl">
              Authority Sign In
            </h1>
            <p className="text-xs sm:text-sm text-slate-400 max-w-sm mx-auto leading-relaxed">
              Multi-Hazard Risk Assessment, Red Zone Demarcation &amp; Relocation Decision Support System
            </p>
          </div>

          <div className="rounded-xl border border-slate-800 bg-slate-900/70 p-6 sm:p-8 shadow-2xl backdrop-blur">
            <LoginForm />
          </div>

          <div className="flex flex-col items-center justify-center gap-2 text-center text-xs text-slate-500 font-mono">
            <div className="flex items-center gap-3">
              <span>CRS: EPSG:4326</span>
              <span>•</span>
              <span>Chunk M5-02 Auth Layer</span>
              <span>•</span>
              <span>Role-Based Clearance</span>
            </div>
          </div>
        </div>
      </main>

      {/* Security & Governance Footer */}
      <footer className="relative z-10 border-t border-slate-800/80 bg-slate-950/80 py-3 px-6 text-center text-[11px] text-slate-500 backdrop-blur">
        Disaster Management Authority Decision Support Platform • SIH Problem Statement 26191 • Internal Authority Clearance Only
      </footer>
    </div>
  );
}
