# RakshakGIS Project State

## Project Information

- **Project Name:** RakshakGIS
- **Problem Statement:** SIH Problem Statement 26191 — AI-powered GIS platform for disaster risk assessment, Red Zone demarcation, village vulnerability analysis, and climate-resilient relocation planning.
- **Repository:** `https://github.com/OjaswiJoshi13/rakshakgis.git`
- **Primary Branch:** `main`
- **Audit Date:** 2026-09-03

---

## Source of Truth

The authoritative requirements document for this project is the **RakshakGIS AI Development & Implementation Specification**. All architecture, formulas, schemas, data dictionaries, algorithms, and workflows must conform strictly to that specification.

---

## Team Ownership

| Member | Role | Primary Ownership |
| --- | --- | --- |
| **M1** | Platform / DevOps / Integration | Docker, scripts, docs, deployment, CI/CD, foundation integration |
| **M2** | Backend Core / Database | Models, schemas, API core, database configuration, authentication |
| **M3** | Risk / GIS / Data | Data management, adapters, risk engine, vulnerability, Red Zones |
| **M4** | Relocation / Routing | Priority integration, site suitability, capacity, matching, routing |
| **M5** | Frontend Core / GIS | Frontend shell, dashboard, MapLibre GIS, village analysis UI |
| **M6** | Frontend Operations | Relocation UI, sites, scenarios, alerts, reports, officer workflow |

---

## Status Definitions

The project uses the following formal lifecycle statuses across all tasks and chunks:

- `PLANNED`: The chunk has not started.
- `IN_PROGRESS`: A member or agent is actively implementing it.
- `IMPLEMENTED`: Implementation has been completed by the coding agent, but independent verification has not yet passed.
- `AWAITING_REVIEW`: Implementation and tests have been completed and reported, pending independent review.
- `VERIFIED`: The implementation has been independently reviewed and accepted against the specification.
- `COMMITTED`: The verified implementation has been committed to the shared `main` branch.
- `BLOCKED`: The chunk cannot proceed because one or more prerequisite dependencies are not yet `COMMITTED`.
- `FAILED_REVIEW`: The implementation was reviewed and found incomplete or incorrect. Requires correction before commit.

> **CRITICAL RULE:** The coding assistant (Antigravity) must **NEVER** mark its own implementation as `VERIFIED`. It may only mark its work as `IMPLEMENTED` or `AWAITING_REVIEW`. Verification is performed exclusively by an independent review process.

---

## Global Development Rules

1. **Specification as Source of Truth:** The RakshakGIS specification governs all requirements, naming, formulas, and schemas.
2. **No Invented Status:** Do not claim a feature or chunk is completed without verified evidence.
3. **Strict Dependency Order:** Do not skip dependencies or work out of order.
4. **Preserve Teammate Work:** Do not overwrite, reset, or discard another team member's work.
5. **Mandatory State Update:** Every chunk must update `PROJECT_STATE.md`.
6. **Report Changed Files:** Every chunk must explicitly enumerate all files created, modified, or removed.
7. **Automated Testing:** Every applicable chunk must execute tests and report exact results.
8. **Label Demo / Synthetic Data:** All synthetic, simulated, or demo datasets must be explicitly labelled as such.
9. **Zero Secrets in Git:** Never commit API keys, passwords, database credentials, or secret tokens.
10. **Deterministic Simulation:** Simulations must rerun actual backend computational engines, not mock random numbers.
11. **Numerical Risk Engine Independence:** LLMs must never be used as the numerical risk calculation engine.
12. **Officer Review Required:** All AI recommendations (relocation, zoning, evacuation) must require explicit officer review and approval.
13. **No Dead Buttons / Placeholder Navigation:** Core MVP navigation and UI controls must be functional; placeholder/dead UI is prohibited.
14. **Region-Agnostic Core Logic:** Core mathematical, GIS, and risk logic must remain region-agnostic; regional parameters live in configuration profiles.
15. **Adapter Isolation:** All external data integrations (weather, terrain, satellite, telemetry) must be behind provider adapters.
16. **Evidence-Based Claims:** Do not claim official government accuracy, certification, or formal methodology without concrete evidence.
17. **Deterministic MVP:** Prefer deterministic, reproducible, and easily testable implementations for the MVP.
18. **Module Scope Discipline:** Do not modify unrelated modules outside the scope of the assigned chunk.
19. **Real GIS Over Static Assets:** Never use a static image/screenshot as a substitute for dynamic GIS mapping functionality.
20. **Transparent Uncertainty:** If a requirement or boundary condition is ambiguous, report it immediately instead of guessing.

---

## Git Workflow Rules

Every coding chunk strictly adheres to this sequence:

1. **Synchronize:**
   ```bash
   git status
   git fetch origin
   git pull --rebase origin main
   ```
2. **Review State:** Read `PROJECT_STATE.md` and check prerequisite dependencies.
3. **Execute:** Implement and run relevant automated tests.
4. **Document:** Update `PROJECT_STATE.md` and document changed files and test results.
5. **Pre-Push Check:**
   ```bash
   git pull --rebase origin main
   ```
6. **Conflict Resolution:** If conflicts arise:
   - Preserve all valid work.
   - Resolve only unambiguous conflicts.
   - Stop and report any semantically ambiguous conflicts.
   - Never use `git push --force` on `main`.
   - Stage specific files explicitly with `git add <file>` rather than blind `git add .`.

---

## Dependency Rules

The baseline dependency hierarchy across teams is structured as follows:

```text
M1-00 Repository Audit
        ↓
M1-01 Repository + Docker Foundation
        ↓
M2-01 FastAPI Foundation
        ↓
M2-02 PostgreSQL / PostGIS Setup
        ↓
M2-03 Database Models & Migrations
        ↓
┌──────────────┬──────────────┬──────────────┬──────────────┐
│              │              │              │              │
M2-04 / M2-05  M3 Risk / GIS  M4 Relocation  M5 Frontend    M6 Operations
(Auth / Core)  (Data & Risk)  (Sites & Route)(GIS UI)       (Workflow UI)
│              │              │              │              │
└──────────────┴───────┬──────┴──────────────┴──────────────┘
                       │
                       ▼
            INT-01 / INT-02 / INT-03
             (Integration & Tests)
                       │
                       ▼
            DEP-01 / DOC-01 (Deploy & Docs)
```

No chunk may transition to `IN_PROGRESS` until all its listed prerequisite dependencies are marked `COMMITTED` (or `VERIFIED` by review).

---

## Complete Chunk Registry

| Chunk ID | Module | Title | Assigned | Dependencies | Status |
| --- | --- | --- | --- | --- | --- |
| **M1-00** | Platform | Repository Audit & State Initialization | M1 | None | **COMMITTED** |
| **M1-01** | Platform | Repository & Docker Foundation | M1 | M1-00 | **COMMITTED** |
| **M2-01** | Backend | FastAPI Foundation & Core App Setup | M2 | M1-01 | **COMMITTED** |
| **M2-02** | Backend | PostgreSQL / PostGIS Engine Setup | M2 | M2-01 | **COMMITTED** |
| **M2-03** | Backend | Database Models & Alembic Migrations | M2 | M2-02 | **PLANNED** |
| **M2-04** | Backend | Common API & Error Infrastructure | M2 | M2-03 | **BLOCKED** |
| **M2-05** | Backend | Authentication Backend (JWT / RBAC) | M2 | M2-04 | **BLOCKED** |
| **M3-01** | Risk/GIS | Region Profiles Configuration | M3 | M2-03 | **BLOCKED** |
| **M3-02** | Risk/GIS | Demo & Synthetic Datasets | M3 | M3-01 | **BLOCKED** |
| **M3-03** | Risk/GIS | Provider Interfaces & Mock Adapters | M3 | M3-01 | **BLOCKED** |
| **M3-04** | Risk/GIS | Data Validation & Ingestion Pipelines | M3 | M3-02, M3-03 | **BLOCKED** |
| **M3-05** | Risk/GIS | Risk Normalization Engine | M3 | M3-04 | **BLOCKED** |
| **M3-06** | Risk/GIS | Multi-Hazard Risk Computation Engine | M3 | M3-05 | **BLOCKED** |
| **M3-07** | Risk/GIS | Risk Classification & Grading | M3 | M3-06 | **BLOCKED** |
| **M3-08** | Risk/GIS | Risk Explainability & Factor Contribution | M3 | M3-07 | **BLOCKED** |
| **M3-09** | Risk/GIS | Vulnerability & Exposure Scoring Engine | M3 | M3-06 | **BLOCKED** |
| **M3-10** | Risk/GIS | Permanent Red Zones Demarcation | M3 | M3-07 | **BLOCKED** |
| **M3-11** | Risk/GIS | Dynamic Red Zones & Threshold Triggers | M3 | M3-10 | **BLOCKED** |
| **M3-12** | Risk/GIS | Relocation Priority Scoring Backend | M3 | M3-08, M3-09 | **BLOCKED** |
| **M3-13** | Risk/GIS | Data Source Freshness & Telemetry Backend | M3 | M3-03 | **BLOCKED** |
| **M4-01** | Relocation | Candidate Relocation Sites Backend | M4 | M2-03 | **BLOCKED** |
| **M4-02** | Relocation | Multi-Criteria Site Suitability Engine | M4 | M4-01, M3-06 | **BLOCKED** |
| **M4-03** | Relocation | Carrying Capacity & Infrastructure Sizing | M4 | M4-02 | **BLOCKED** |
| **M4-04** | Relocation | Relocation Matching & Assignment Engine | M4 | M3-12, M4-03 | **BLOCKED** |
| **M4-05** | Relocation | Evacuation & Access Routing Engine | M4 | M4-04 | **BLOCKED** |
| **M4-06** | Relocation | Scenario Simulator Integration Backend | M4 | M4-04, M3-11 | **BLOCKED** |
| **M5-01** | Frontend | Frontend Foundation & Design System | M5 | M1-01 | **BLOCKED** |
| **M5-02** | Frontend | Authentication UI & Session Handling | M5 | M5-01, M2-05 | **BLOCKED** |
| **M5-03** | Frontend | API Client & State Management Setup | M5 | M5-01, M2-04 | **BLOCKED** |
| **M5-04** | Frontend | Executive Dashboard UI | M5 | M5-03 | **BLOCKED** |
| **M5-05** | Frontend | MapLibre GIS Interactive Map Canvas | M5 | M5-03 | **BLOCKED** |
| **M5-06** | Frontend | Village Vulnerability Analysis UI | M5 | M5-04, M5-05 | **BLOCKED** |
| **M5-07** | Frontend | GIS API Integration & GeoJSON Layers | M5 | M5-05, M3-10 | **BLOCKED** |
| **M6-01** | Operations | Operations UI Shell & Navigation | M6 | M5-01 | **BLOCKED** |
| **M6-02** | Operations | Relocation Planner Workflow UI | M6 | M6-01, M4-04 | **BLOCKED** |
| **M6-03** | Operations | Relocation Site Details & Infrastructure UI | M6 | M6-02 | **BLOCKED** |
| **M6-04** | Operations | Scenario Simulator UI | M6 | M6-01, M4-06 | **BLOCKED** |
| **M6-05** | Operations | Real-Time Alerts & Threshold Warnings UI | M6 | M6-01, M3-11 | **BLOCKED** |
| **M6-06** | Operations | Data Sources & Freshness Monitoring UI | M6 | M6-01, M3-13 | **BLOCKED** |
| **M6-07** | Operations | Report Generation & Export UI | M6 | M6-02, M6-03 | **BLOCKED** |
| **M6-08** | Operations | Officer Review & Action Sign-Off Workflow | M6 | M6-02, M6-04 | **BLOCKED** |
| **M6-09** | Operations | Audit Log & Traceability UI | M6 | M6-08 | **BLOCKED** |
| **INT-01** | Integration | End-to-End Backend / Frontend Integration | M1 | All M2-M6 | **BLOCKED** |
| **INT-02** | Integration | End-to-End SIH Demo Flow Validation | M1 | INT-01 | **BLOCKED** |
| **INT-03** | Integration | Full Automated Test Suite Execution | M1 | INT-02 | **BLOCKED** |
| **DEP-01** | DevOps | Production Deployment & Containerization | M1 | INT-03 | **BLOCKED** |
| **DOC-01** | Docs | Final Project Documentation & Demo Guide | M1 | INT-02 | **BLOCKED** |

---

## Current Work

- **Active Chunk:** None
- **Next Eligible Chunk:** M2-03 (Database Models & Alembic Migrations)
- **Status:** Ready to start M2-03 (prerequisite M2-02 committed)

---

## Blocked Work

Chunks M2-04 through DOC-01 remain in `BLOCKED` status awaiting completion, independent verification, and commit of their respective prerequisites. Chunk M2-03 is unblocked (`PLANNED`).

---

## Completed / Verified / Committed Work

- Initial repository structure scaffold commit: `4c0bcc8` (`.env.example`, `.gitignore`, `README.md`, `docker-compose.yml`).
- M1-00: Repository Audit & State Initialization — COMMITTED (Commit: `3816b09`).
- M1-01: Repository & Docker Foundation — COMMITTED (Commit: `bb79e25`).
- M2-01: FastAPI Foundation & Core App Setup — COMMITTED (Commit: `f115a76`).
- M2-02: PostgreSQL / PostGIS Engine Setup — COMMITTED (Commit: `feat(database): establish PostgreSQL and PostGIS connectivity`).

---

## Known Issues

1. **Untracked Host Virtual Environment:** `backend/venv/` exists locally on Windows host and is properly ignored by `.gitignore`. The Docker service isolates this via an anonymous volume (`/app/venv`).
2. **Empty Frontend Directory:** `frontend/` contains no scaffolding, package files, or build tool configuration (scheduled for Chunk M5-01).

---

## Integration Notes

- Docker Compose defines two core services: `db` (`postgis/postgis:16-3.4`) and `backend` (`python:3.11-slim-bookworm` with native GDAL 3.6.2, GEOS 3.11.1, PROJ 9.1.1, and libpq 15.19).
- Backend image successfully built with all 44 pinned Python dependencies from `requirements.txt` (GeoPandas, Rasterio, Shapely, GeoAlchemy2, FastAPI).
- Database service verified healthy and queryable with PostGIS 3.4.3 on port 5432 using named persistent volume `rakshakgis_pgdata`.
- Backend container mounts `./backend:/app` for real-time hot-reloading during development.
- Environment variables are defined via `.env.example` with documented defaults; zero secrets are tracked in Git.
- Chunk M2-01 established FastAPI application entrypoint with `/health`, `/`, and `/api/v1` routes and automated test suite.
- Chunk M2-02 established PostgreSQL & PostGIS engine connectivity, `SessionLocal`, `get_db()`, `/ready` endpoint, and spatial capability verification.
- Automated tests verified: 15 passed in container (Python 3.11) and host (Python 3.13).

---

## Last Updated

- **Timestamp:** 2026-09-04 15:45:00 IST
- **Updated By:** M2 (Antigravity Agent)
- **Status Summary:** Chunk M2-02 finalized as COMMITTED; Chunk M2-03 unblocked to PLANNED.
