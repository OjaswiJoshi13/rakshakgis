/**
 * Strongly typed domain models and contracts for Report Generation & Export UI (Chunk M6-07).
 * Strictly composes existing backend and frontend contracts from M6-02 (Relocation Matching)
 * and M6-03 (Candidate Relocation Sites & Infrastructure).
 */

import {
  RelocationMatchingResult,
  VillageAssignmentResult,
} from "./relocation";
import {
  CandidateSiteRead,
  CandidateSiteDetailRead,
  SiteSuitabilityResult,
  SiteCapacityResult,
} from "./sites";

export type ReportTemplateId =
  | "relocation_allocation"
  | "site_infrastructure"
  | "suitability_capacity"
  | "comprehensive_dossier";

export type ReportStatusFilter = "all" | "assigned" | "unassigned";

export type ReportExportFormat = "json" | "csv";

export interface ReportTemplateMeta {
  id: ReportTemplateId;
  title: string;
  shortDescription: string;
  backendBinding: string;
  applicableFilters: {
    statusFilter: boolean;
    siteSelector: boolean;
    includeAudits: boolean;
    includeDeficits: boolean;
  };
}

export interface ReportConfig {
  templateId: ReportTemplateId;
  statusFilter: ReportStatusFilter;
  selectedSiteId: number | "all";
  includeAudits: boolean;
  includeDeficits: boolean;
  regionProfileId: string;
}

export interface ReportMetric {
  label: string;
  value: string | number;
  subtext?: string;
}

export interface CompiledDossier {
  id: string;
  title: string;
  templateId: ReportTemplateId;
  generatedAt: string;
  regionProfileId: string;
  classification: string;
  summaryNarrative: string;
  governanceNotice: string;
  metrics: ReportMetric[];
  matchingResult?: RelocationMatchingResult | null;
  filteredAssignments?: VillageAssignmentResult[];
  sites?: CandidateSiteRead[];
  selectedSiteDetail?: CandidateSiteDetailRead | null;
  suitability?: SiteSuitabilityResult | null;
  capacity?: SiteCapacityResult | null;
}
