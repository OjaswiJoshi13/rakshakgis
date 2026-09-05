import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/design-system/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        // Operational Command Center Surface Palette
        surface: {
          0: "var(--surface-0)",
          1: "var(--surface-1)",
          2: "var(--surface-2)",
          3: "var(--surface-3)",
          border: "var(--surface-border)",
          "border-subtle": "var(--surface-border-subtle)",
        },
        brand: {
          50: "#f0f9ff",
          100: "#e0f2fe",
          500: "#0ea5e9",
          600: "#0284c7",
          700: "#0369a1",
          800: "#075985",
          900: "#0c4a6e",
          950: "#082f49",
        },
        // Authoritative 5 Risk Bands (Spec: Safe, Moderate, High, Very High, Critical)
        risk: {
          safe: {
            DEFAULT: "#10b981", // 0-25
            light: "#ecfdf5",
            dark: "#064e3b",
            border: "#34d399",
          },
          moderate: {
            DEFAULT: "#f59e0b", // 25-50
            light: "#fffbeb",
            dark: "#78350f",
            border: "#fbbf24",
          },
          high: {
            DEFAULT: "#f97316", // 50-70
            light: "#fff7ed",
            dark: "#7c2d12",
            border: "#fb923c",
          },
          "very-high": {
            DEFAULT: "#f43f5e", // 70-85
            light: "#fff1f2",
            dark: "#881337",
            border: "#fb7185",
          },
          critical: {
            DEFAULT: "#ef4444", // 85-100
            light: "#fef2f2",
            dark: "#7f1d1d",
            border: "#f87171",
          },
        },
        // Authoritative 4 Relocation Priority Bands (Spec: Immediate, Short Term, Medium Term, Monitor)
        relocation: {
          immediate: "#dc2626", // 80-100
          "short-term": "#ea580c", // 60-79
          "medium-term": "#d97706", // 40-59
          monitor: "#2563eb", // <40
        },
        // Operational Status
        status: {
          normal: "#10b981",
          info: "#0284c7",
          warning: "#f59e0b",
          critical: "#ef4444",
        },
      },
      fontFamily: {
        sans: [
          "Inter",
          "-apple-system",
          "BlinkMacSystemFont",
          "Segoe UI",
          "Roboto",
          "sans-serif",
        ],
        mono: [
          "JetBrains Mono",
          "Fira Code",
          "Consolas",
          "ui-monospace",
          "monospace",
        ],
      },
    },
  },
  plugins: [],
};

export default config;
