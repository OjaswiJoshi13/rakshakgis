import React from "react";
import { ProtectedRoute } from "@/components/auth/ProtectedRoute";
import { AppLayout } from "@/components/layout/AppLayout";
import { OperationsShell } from "@/components/operations/OperationsShell";

export const metadata = {
  title: "Operations Console — RakshakGIS",
  description:
    "Officer operations console for disaster response, village-to-site relocation matching, scenario simulation, and statutory sign-off.",
};

export default function OperationsLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <ProtectedRoute>
      <AppLayout>
        <OperationsShell>{children}</OperationsShell>
      </AppLayout>
    </ProtectedRoute>
  );
}
