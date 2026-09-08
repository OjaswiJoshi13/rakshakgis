"use client";

import React, { useState, useEffect, useRef } from "react";
import { searchGis } from "@/lib/api/gis";

export interface GisSearchResult {
  entity_type: "village" | "candidate_site" | "red_zone" | "region" | string;
  id: number | string;
  name: string;
  code?: string;
  coordinates?: [number, number] | null;
  highlight?: string;
  elevation_m?: number;
  slope_deg?: number;
  status?: string;
  state?: string;
}

interface GisSearchBarProps {
  onSelectResult: (result: GisSearchResult) => void;
  className?: string;
}

export const GisSearchBar: React.FC<GisSearchBarProps> = ({
  onSelectResult,
  className = "",
}) => {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<GisSearchResult[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [isOpen, setIsOpen] = useState(false);
  const [selectedIndex, setSelectedIndex] = useState(-1);
  const dropdownRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  // Debounced search effect
  useEffect(() => {
    if (!query.trim() || query.trim().length < 2) {
      setResults([]);
      setIsOpen(false);
      return;
    }

    const abortController = new AbortController();
    const timeoutId = setTimeout(async () => {
      setIsLoading(true);
      try {
        const response = await searchGis(query.trim(), undefined, 15, abortController.signal);
        if (response?.data) {
          setResults(response.data);
          setIsOpen(true);
          setSelectedIndex(-1);
        }
      } catch (err: any) {
        if (err.name !== "AbortError") {
          console.error("GIS search error:", err);
        }
      } finally {
        setIsLoading(false);
      }
    }, 250);

    return () => {
      clearTimeout(timeoutId);
      abortController.abort();
    };
  }, [query]);

  // Click outside listener
  useEffect(() => {
    const handleClickOutside = (e: MouseEvent) => {
      if (dropdownRef.current && !dropdownRef.current.contains(e.target as Node)) {
        setIsOpen(false);
      }
    };
    document.addEventListener("mousedown", handleClickOutside);
    return () => document.removeEventListener("mousedown", handleClickOutside);
  }, []);

  const handleSelect = (item: GisSearchResult) => {
    onSelectResult(item);
    setIsOpen(false);
    setQuery(item.name);
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLInputElement>) => {
    if (!isOpen || results.length === 0) return;

    if (e.key === "ArrowDown") {
      e.preventDefault();
      setSelectedIndex((prev) => (prev < results.length - 1 ? prev + 1 : 0));
    } else if (e.key === "ArrowUp") {
      e.preventDefault();
      setSelectedIndex((prev) => (prev > 0 ? prev - 1 : results.length - 1));
    } else if (e.key === "Enter" && selectedIndex >= 0) {
      e.preventDefault();
      handleSelect(results[selectedIndex]);
    } else if (e.key === "Escape") {
      setIsOpen(false);
    }
  };

  const getEntityBadge = (type: string) => {
    switch (type) {
      case "village":
        return <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-emerald-50 text-emerald-800 border border-emerald-300 dark:bg-emerald-950 dark:text-emerald-400 dark:border-emerald-800">Village</span>;
      case "candidate_site":
        return <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-sky-50 text-sky-800 border border-sky-300 dark:bg-sky-950 dark:text-sky-400 dark:border-sky-800">Haven Site</span>;
      case "red_zone":
        return <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-rose-50 text-rose-800 border border-rose-300 dark:bg-rose-950 dark:text-rose-400 dark:border-rose-800">Red Zone</span>;
      case "region":
        return <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-purple-50 text-purple-800 border border-purple-300 dark:bg-purple-950 dark:text-purple-400 dark:border-purple-800">Region</span>;
      default:
        return <span className="text-[10px] uppercase font-mono px-1.5 py-0.5 rounded bg-surface-elevated text-text-secondary border border-border-subtle">Entity</span>;
    }
  };

  return (
    <div ref={dropdownRef} className={`relative w-full max-w-md ${className}`}>
      <div className="relative flex items-center">
        <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none text-text-muted">
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
        </div>
        <input
          ref={inputRef}
          type="text"
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          onKeyDown={handleKeyDown}
          onFocus={() => {
            if (results.length > 0) setIsOpen(true);
          }}
          placeholder="Search villages, sites, zones..."
          className="w-full pl-9 pr-8 py-1.5 bg-surface-panel hover:bg-surface-panel focus:bg-surface-panel backdrop-blur border border-border-strong focus:border-sky-500 rounded-lg text-sm text-text-primary placeholder:text-text-muted outline-none transition-colors shadow-sm font-sans"
        />
        {isLoading && (
          <div className="absolute inset-y-0 right-2 flex items-center">
            <svg className="animate-spin h-3.5 w-3.5 text-sky-600 dark:text-sky-400" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" fill="none" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
            </svg>
          </div>
        )}
        {query && !isLoading && (
          <button
            onClick={() => {
              setQuery("");
              setResults([]);
              setIsOpen(false);
            }}
            className="absolute inset-y-0 right-2 flex items-center text-text-muted hover:text-text-primary"
            title="Clear search"
          >
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        )}
      </div>

      {/* Dropdown Results */}
      {isOpen && (
        <div className="absolute left-0 right-0 top-full mt-1.5 max-h-72 overflow-y-auto bg-surface-panel/95 backdrop-blur border border-border-strong rounded-lg shadow-xl z-50 divide-y divide-border-subtle font-sans">
          {results.length === 0 ? (
            <div className="p-3 text-xs text-text-muted text-center font-mono">
              No matching geographic entities found for &ldquo;{query}&rdquo;
            </div>
          ) : (
            results.map((item, idx) => (
              <button
                key={`${item.entity_type}-${item.id}`}
                onClick={() => handleSelect(item)}
                className={`w-full text-left px-3 py-2 text-xs flex items-center justify-between transition-colors ${
                  idx === selectedIndex ? "bg-sky-50 text-sky-900 dark:bg-sky-950/80 dark:text-sky-100" : "hover:bg-surface-elevated text-text-primary"
                }`}
              >
                <div className="flex flex-col gap-0.5">
                  <div className="flex items-center gap-1.5">
                    <span className="font-semibold text-text-primary text-sm">{item.name}</span>
                    {item.code && <span className="text-[11px] font-mono text-text-muted">({item.code})</span>}
                  </div>
                  {item.highlight && (
                    <span className="text-[11px] text-text-muted font-mono">{item.highlight}</span>
                  )}
                </div>
                <div className="flex items-center gap-2 flex-shrink-0">
                  {item.coordinates && (
                    <span className="text-[10px] text-text-muted font-mono hidden sm:inline">
                      {item.coordinates[0].toFixed(3)}, {item.coordinates[1].toFixed(3)}
                    </span>
                  )}
                  {getEntityBadge(item.entity_type)}
                </div>
              </button>
            ))
          )}
        </div>
      )}
    </div>
  );
};
