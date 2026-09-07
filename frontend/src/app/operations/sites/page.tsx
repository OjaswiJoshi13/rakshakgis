"use client";

import React, { useState, useEffect, useCallback, Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { OperationsSectionShell } from "@/components/operations/OperationsSectionShell";
import {
  CandidateSiteDetailRead,
  CandidateSiteRead,
  SiteCapacityResult,
  SiteDetailTab,
  SiteSuitabilityResult,
} from "@/types/sites";
import {
  listCandidateSites,
  getCandidateSiteDetail,
  getCandidateSiteSuitability,
  getCandidateSiteCapacity,
  HIMALAYAN_PILOT_SAMPLE_SITES,
  HIMALAYAN_PILOT_SAMPLE_SITE_DETAILS,
  HIMALAYAN_PILOT_SAMPLE_SUITABILITY,
  HIMALAYAN_PILOT_SAMPLE_CAPACITY,
} from "@/lib/api/sites";
import {
  SiteSelectorCard,
  SiteHeaderCard,
  SiteInfrastructureTab,
  SiteSuitabilityTab,
  SiteCapacityTab,
} from "@/components/operations/sites";
import { Button } from "@/components/ui/Button";
import { RefreshCw, MapPin } from "lucide-react";

function SitesOperationsContent() {
  const searchParams = useSearchParams();
  const querySiteId = searchParams.get("siteId");

  const [sites, setSites] = useState<CandidateSiteRead[]>(HIMALAYAN_PILOT_SAMPLE_SITES);
  const [selectedSiteId, setSelectedSiteId] = useState<number | null>(() => {
    if (querySiteId) {
      const parsed = parseInt(querySiteId, 10);
      if (!isNaN(parsed)) return parsed;
    }
    return HIMALAYAN_PILOT_SAMPLE_SITES[0]?.id ?? 101;
  });

  const [siteDetail, setSiteDetail] = useState<CandidateSiteDetailRead | null>(() => {
    const initId = querySiteId ? parseInt(querySiteId, 10) : 101;
    return HIMALAYAN_PILOT_SAMPLE_SITE_DETAILS[initId] || HIMALAYAN_PILOT_SAMPLE_SITE_DETAILS[101];
  });

  const [suitability, setSuitability] = useState<SiteSuitabilityResult | null>(() => {
    const initId = querySiteId ? parseInt(querySiteId, 10) : 101;
    return HIMALAYAN_PILOT_SAMPLE_SUITABILITY[initId] || HIMALAYAN_PILOT_SAMPLE_SUITABILITY[101];
  });

  const [capacity, setCapacity] = useState<SiteCapacityResult | null>(() => {
    const initId = querySiteId ? parseInt(querySiteId, 10) : 101;
    return HIMALAYAN_PILOT_SAMPLE_CAPACITY[initId] || HIMALAYAN_PILOT_SAMPLE_CAPACITY[101];
  });

  const [activeTab, setActiveTab] = useState<SiteDetailTab>("infrastructure");
  const [isLoadingSites, setIsLoadingSites] = useState<boolean>(false);
  const [isLoadingDetail, setIsLoadingDetail] = useState<boolean>(false);

  // Load candidate sites list
  const fetchSitesList = useCallback(async () => {
    setIsLoadingSites(true);
    try {
      const resp = await listCandidateSites();
      if (resp && resp.data && resp.data.length > 0) {
        setSites(resp.data);
      } else {
        setSites(HIMALAYAN_PILOT_SAMPLE_SITES);
      }
    } catch {
      setSites(HIMALAYAN_PILOT_SAMPLE_SITES);
    } finally {
      setIsLoadingSites(false);
    }
  }, []);

  useEffect(() => {
    fetchSitesList();
  }, [fetchSitesList]);

  // Handle URL query parameter changes
  useEffect(() => {
    if (querySiteId) {
      const parsed = parseInt(querySiteId, 10);
      if (!isNaN(parsed) && parsed !== selectedSiteId) {
        setSelectedSiteId(parsed);
      }
    }
  }, [querySiteId, selectedSiteId]);

  // Load detail, suitability, and capacity for selected site
  const fetchSiteDetailData = useCallback(async (siteId: number) => {
    setIsLoadingDetail(true);
    try {
      const [detailResp, suitResp, capResp] = await Promise.allSettled([
        getCandidateSiteDetail(siteId),
        getCandidateSiteSuitability(siteId),
        getCandidateSiteCapacity(siteId),
      ]);

      if (detailResp.status === "fulfilled" && detailResp.value?.data) {
        setSiteDetail(detailResp.value.data);
      } else {
        setSiteDetail(
          HIMALAYAN_PILOT_SAMPLE_SITE_DETAILS[siteId] ||
            HIMALAYAN_PILOT_SAMPLE_SITE_DETAILS[101]
        );
      }

      if (suitResp.status === "fulfilled" && suitResp.value?.data) {
        setSuitability(suitResp.value.data);
      } else {
        setSuitability(
          HIMALAYAN_PILOT_SAMPLE_SUITABILITY[siteId] ||
            HIMALAYAN_PILOT_SAMPLE_SUITABILITY[101]
        );
      }

      if (capResp.status === "fulfilled" && capResp.value?.data) {
        setCapacity(capResp.value.data);
      } else {
        setCapacity(
          HIMALAYAN_PILOT_SAMPLE_CAPACITY[siteId] ||
            HIMALAYAN_PILOT_SAMPLE_CAPACITY[101]
        );
      }
    } catch {
      setSiteDetail(
        HIMALAYAN_PILOT_SAMPLE_SITE_DETAILS[siteId] ||
          HIMALAYAN_PILOT_SAMPLE_SITE_DETAILS[101]
      );
      setSuitability(
        HIMALAYAN_PILOT_SAMPLE_SUITABILITY[siteId] ||
          HIMALAYAN_PILOT_SAMPLE_SUITABILITY[101]
      );
      setCapacity(
        HIMALAYAN_PILOT_SAMPLE_CAPACITY[siteId] ||
          HIMALAYAN_PILOT_SAMPLE_CAPACITY[101]
      );
    } finally {
      setIsLoadingDetail(false);
    }
  }, []);

  useEffect(() => {
    if (selectedSiteId !== null) {
      fetchSiteDetailData(selectedSiteId);
    }
  }, [selectedSiteId, fetchSiteDetailData]);

  const handleSelectSite = (id: number) => {
    setSelectedSiteId(id);
  };

  return (
    <OperationsSectionShell
      title="Relocation Sites & Infrastructure"
      description="Candidate relocation site suitability assessment, 5-dimensional infrastructure sizing (housing, water, sanitation, healthcare, shelters), and physical hazard buffer validation."
      chunkId="M6-03"
      chunkTitle="Relocation Site Details & Infrastructure UI"
      prerequisiteChunk="Chunk M6-02 (Relocation Planner) & M4-01/M4-03 (Sites & Capacity Engines — COMMITTED)"
      actionToolbar={
        <Button
          type="button"
          variant="secondary"
          size="sm"
          onClick={() => {
            fetchSitesList();
            if (selectedSiteId) fetchSiteDetailData(selectedSiteId);
          }}
          isLoading={isLoadingSites || isLoadingDetail}
          leftIcon={<RefreshCw className="h-3.5 w-3.5" />}
        >
          <span>Refresh Site Data</span>
        </Button>
      }
    >
      <div className="grid grid-cols-1 gap-6 lg:grid-cols-12 items-start">
        {/* Left Column: Candidate Sites Selector */}
        <div className="lg:col-span-4">
          <SiteSelectorCard
            sites={sites}
            selectedSiteId={selectedSiteId}
            onSelectSite={handleSelectSite}
            isLoading={isLoadingSites}
          />
        </div>

        {/* Right Column: Site Detail, Topography, and Domain Tabs */}
        <div className="lg:col-span-8 space-y-6">
          {siteDetail ? (
            <>
              {/* Site Header & Domain Tab Switcher */}
              <SiteHeaderCard
                site={siteDetail}
                activeTab={activeTab}
                onTabChange={setActiveTab}
              />

              {/* Tab 1: Overview & Infrastructure Assets Inventory */}
              {activeTab === "infrastructure" && (
                <SiteInfrastructureTab site={siteDetail} />
              )}

              {/* Tab 2: Multi-Criteria Suitability (M4-02) */}
              {activeTab === "suitability" && (
                <SiteSuitabilityTab
                  suitability={suitability}
                  isLoading={isLoadingDetail}
                />
              )}

              {/* Tab 3: Carrying Capacity & Weakest-Link Sizing (M4-03) */}
              {activeTab === "capacity" && (
                <SiteCapacityTab
                  capacity={capacity}
                  isLoading={isLoadingDetail}
                />
              )}
            </>
          ) : (
            <div className="rounded-lg border border-dashed border-border-base p-12 text-center text-xs text-text-muted">
              <MapPin className="h-8 w-8 mx-auto text-text-muted mb-3" />
              <p>Select a candidate relocation site to inspect its details and infrastructure.</p>
            </div>
          )}
        </div>
      </div>
    </OperationsSectionShell>
  );
}

export default function SitesOperationsPage() {
  return (
    <Suspense
      fallback={
        <div className="py-16 text-center text-xs text-slate-400 font-mono">
          Loading relocation sites workspace...
        </div>
      }
    >
      <SitesOperationsContent />
    </Suspense>
  );
}
