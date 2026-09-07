import type { Metadata } from "next";
import { AuthProvider } from "@/context/AuthContext";
import { OperationalProvider } from "@/context/OperationalContext";
import { ThemeProvider } from "@/context/ThemeContext";
import "./globals.css";

export const metadata: Metadata = {
  title: "RakshakGIS — Multi-Hazard Disaster Decision Support System",
  description:
    "Spatial decision support platform for multi-hazard risk assessment, dynamic Red Zone demarcation, habitation vulnerability profiling, and climate-resilient relocation planning.",
  keywords: [
    "RakshakGIS",
    "GIS",
    "Disaster Management",
    "Multi-Hazard",
    "Relocation Planning",
    "Red Zones",
    "Spatial Intelligence",
  ],
  authors: [{ name: "RakshakGIS Team" }],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" suppressHydrationWarning>
      <head>
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.ico" sizes="any" />
      </head>
      <body className="min-h-screen bg-surface-bg text-text-primary transition-colors duration-200">
        <ThemeProvider>
          <AuthProvider>
            <OperationalProvider>{children}</OperationalProvider>
          </AuthProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
