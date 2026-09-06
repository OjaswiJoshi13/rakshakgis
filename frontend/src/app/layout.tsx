import type { Metadata } from "next";
import { AuthProvider } from "@/context/AuthContext";
import { OperationalProvider } from "@/context/OperationalContext";
import "./globals.css";

export const metadata: Metadata = {
  title: "RakshakGIS — Multi-Hazard Disaster Decision Support System",
  description:
    "AI-powered GIS platform for multi-hazard risk assessment, dynamic Red Zone demarcation, village vulnerability profiling, and climate-resilient relocation planning (SIH 26191).",
  keywords: [
    "RakshakGIS",
    "GIS",
    "Disaster Management",
    "Multi-Hazard",
    "Relocation Planning",
    "Red Zones",
    "SIH 26191",
  ],
  authors: [{ name: "RakshakGIS Team" }],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark">
      <head>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.ico" sizes="any" />
      </head>
      <body className="bg-slate-950 text-slate-100 min-h-screen">
        <AuthProvider>
          <OperationalProvider>{children}</OperationalProvider>
        </AuthProvider>
      </body>
    </html>
  );
}
