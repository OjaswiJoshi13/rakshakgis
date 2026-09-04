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
| **M2-03** | Backend | Database Models & Alembic Migrations | M2 | M2-02 | **COMMITTED** |
| **M2-04** | Backend | Common API & Error Infrastructure | M2 | M2-03 | **COMMITTED** |
| **M2-05** | Backend | Authentication Backend (JWT / RBAC) | M2 | M2-04 | **COMMITTED** |
| **M3-01** | Risk/GIS | Region Profiles Configuration | M3 | M2-03 | **COMMITTED** |
| **M3-02** | Risk/GIS | Demo & Synthetic Datasets | M3 | M3-01 | **COMMITTED** |
| **M3-03** | Risk/GIS | Provider Interfaces & Mock Adapters | M3 | M3-01 | **COMMITTED** |
| **M3-04** | Risk/GIS | Data Validation & Ingestion Pipelines | M3 | M3-02, M3-03 | **COMMITTED** |
| **M3-05** | Risk/GIS | Risk Normalization Engine | M3 | M3-04 | **COMMITTED** |
| **M3-06** | Risk/GIS | Multi-Hazard Risk Computation Engine | M3 | M3-05 | **COMMITTED** |
| **M3-07** | Risk/GIS | Risk Classification & Grading | M3 | M3-06 | **COMMITTED** |
| **M3-08** | Risk/GIS | Risk Explainability & Factor Contribution | M3 | M3-07 | **BLOCKED** |
| **M3-09** | Risk/GIS | Vulnerability & Exposure Scoring Engine | M3 | M3-06 | **BLOCKED** |
| **M3-10** | Risk/GIS | Permanent Red Zones Demarcation | M3 | M3-07 | **BLOCKED** |
| **M3-11** | Risk/GIS | Dynamic Red Zones & Threshold Triggers | M3 | M3-10 | **BLOCKED** |
| **M3-12** | Risk/GIS | Relocation Priority Scoring Backend | M3 | M3-08, M3-09 | **BLOCKED** |
| **M3-13** | Risk/GIS | Data Source Freshness & Telemetry Backend | M3 | M3-03 | **BLOCKED** |
| **M4-01** | Relocation | Candidate Relocation Sites Backend | M4 | M2-03 | **COMMITTED** |
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
- **Next Eligible Chunks:** M3-08 (Risk Explainability & Factor Contribution), M3-09 (Vulnerability & Exposure Scoring Engine), M4-02 (Multi-Criteria Site Suitability Engine)
- **Status:** Chunk M4-01 independently reviewed and COMMITTED (Commit: `5c100603b77e45a47a8c6420f405819166e58609`); Chunk M4-02 is now ELIGIBLE because M4-01 is COMMITTED and M3-06 is already COMMITTED; Chunks M3-08 and M3-09 are also eligible independently.

---

## Blocked Work

Chunks M3-08 through DOC-01 (except unblocked M3-01, M3-02, M3-03, M3-04, M3-05, M3-06, M3-07, and M4-01) remain in `BLOCKED` status awaiting completion, independent verification, and commit of their respective prerequisites.

---

## Completed / Verified / Committed Work

- Initial repository structure scaffold commit: `4c0bcc8` (`.env.example`, `.gitignore`, `README.md`, `docker-compose.yml`).
- M1-00: Repository Audit & State Initialization — COMMITTED (Commit: `3816b09`).
- M1-01: Repository & Docker Foundation — COMMITTED (Commit: `bb79e25`).
- M2-01: FastAPI Foundation & Core App Setup — COMMITTED (Commit: `f115a76`).
- M2-02: PostgreSQL / PostGIS Engine Setup — COMMITTED (Commit: `e15149a`).
- M2-03: Database Models & Alembic Migrations — COMMITTED (Commit: `3448035`).
- M2-04: Common API & Error Infrastructure — COMMITTED (Commit: `d81bbeb`).
- M2-05: Backend Authentication Backend (JWT / RBAC) — COMMITTED (Commit: `feat(auth): implement JWT authentication and RBAC`).
- M3-01: Region Profiles Configuration — COMMITTED (Commit: `feat(m3): add regional configuration profiles`).
- M3-02: Demo & Synthetic Datasets — COMMITTED (Commit: `feat(m3): add demo synthetic datasets`).
- M3-03: Provider Interfaces & Mock Adapters — COMMITTED (Commit: `feat(m3): add provider interfaces and mock adapters`).
- M3-04: Data Validation & Ingestion Pipelines — COMMITTED (Commit: `feat(m3): add data validation and ingestion pipeline`).
- M3-05: Risk Normalization Engine — COMMITTED (Commit: `feat(m3): add risk normalization engine`).
- M3-06: Multi-Hazard Risk Computation Engine — COMMITTED (Commit: `feat(m3): add multi-hazard risk computation engine`).
- M3-07: Risk Classification & Grading — COMMITTED (Commit: `feat(m3): add risk classification and grading`).
- M4-01: Candidate Relocation Sites Backend — COMMITTED (Commit: `5c100603b77e45a47a8c6420f405819166e58609`).

---

## Chunk M2-03 Implementation Record

- **Status:** `COMMITTED`
- **Files Created:**
  - `backend/alembic.ini` (Alembic configuration)
  - `backend/alembic/env.py` (Alembic environment with dynamic DB URL & PostGIS system table filters)
  - `backend/alembic/script.py.mako` (Migration template)
  - `backend/alembic/versions/.gitkeep`
  - `backend/alembic/versions/20260904_7f762509fde4_initial_schema.py` (Initial deterministic migration for all 29 tables)
  - `backend/app/models/__init__.py` (Central registry exporting all 29 models and Base)
  - `backend/app/models/geographic.py` (Region, District, Block, Village)
  - `backend/app/models/hazards.py` (HazardLayer, HazardObservation, LandslideEvent, FloodEvent, RainfallRecord, DisasterEvent)
  - `backend/app/models/vulnerability.py` (PopulationProfile, VulnerabilityProfile)
  - `backend/app/models/risk.py` (RiskScore, RiskFactor, RedZone)
  - `backend/app/models/relocation.py` (CandidateSite, SiteCapacity, Infrastructure, RelocationPriority, RelocationAssignment, Route)
  - `backend/app/models/scenarios.py` (Scenario, ScenarioRun)
  - `backend/app/models/telemetry.py` (DataSource, DataIngestionRun, Alert)
  - `backend/app/models/governance.py` (User, OfficerDecision, AuditLog)
  - `backend/tests/test_models.py` (Automated tests for models, schema, spatial SRID, and migrations)
- **Files Modified:**
  - `requirements.txt` (Added `alembic==1.19.1` and `Mako==1.4.1`)
  - `PROJECT_STATE.md` (Updated status to `AWAITING_REVIEW` and documented implementation record)
- **Files Removed:**
  - None
- **Migration Revision:** `7f762509fde4`
- **Database Tables Created (29 Domain Tables):**
  - `regions`, `districts`, `blocks`, `villages`
  - `hazard_layers`, `hazard_observations`, `landslide_events`, `flood_events`, `rainfall_records`, `disaster_events`
  - `population_profiles`, `vulnerability_profiles`
  - `candidate_sites`, `site_capacities`, `infrastructure`
  - `risk_scores`, `risk_factors`, `red_zones`
  - `relocation_priorities`, `relocation_assignments`, `routes`
  - `scenarios`, `scenario_runs`
  - `alerts`, `data_sources`, `data_ingestion_runs`
  - `officer_decisions`, `audit_logs`, `users`
- **PostGIS Spatial Columns (17 columns, WGS 84 SRID 4326 with GiST indexes):**
  - `blocks.boundary` (MULTIPOLYGON, 4326)
  - `candidate_sites.boundary` (POLYGON, 4326)
  - `candidate_sites.location` (POINT, 4326)
  - `disaster_events.affected_area` (MULTIPOLYGON, 4326)
  - `disaster_events.epicenter_or_center` (POINT, 4326)
  - `districts.boundary` (MULTIPOLYGON, 4326)
  - `flood_events.inundation_polygon` (MULTIPOLYGON, 4326)
  - `hazard_observations.location` (POINT, 4326)
  - `infrastructure.location` (POINT, 4326)
  - `landslide_events.location` (POINT, 4326)
  - `landslide_events.scar_polygon` (POLYGON, 4326)
  - `rainfall_records.station_location` (POINT, 4326)
  - `red_zones.geometry` (MULTIPOLYGON, 4326)
  - `regions.boundary` (MULTIPOLYGON, 4326)
  - `routes.path` (LINESTRING, 4326)
  - `villages.boundary` (POLYGON, 4326)
  - `villages.location` (POINT, 4326)
- **Alembic Verification Commands Executed:**
  - `alembic upgrade head` -> Successfully applied revision `7f762509fde4`
  - `alembic current` -> `7f762509fde4 (head)`
  - `alembic downgrade base` -> Successfully reverted to clean database
  - `alembic upgrade head` -> Deterministically reapplied all 29 tables & spatial indexes
- **Automated Test Results:**
  - Ran `pytest tests -v` in `rakshakgis-backend`: **23 passed, 0 failed** in 1.92s
  - All existing M2-01 (health/core) and M2-02 (database engine/readiness) tests pass 100%
  - 8 new model & migration tests pass 100%
- **Endpoint Verification:**
  - `GET /health` -> HTTP 200 OK (remains database-independent)
  - `GET /ready` -> HTTP 200 OK (PostgreSQL 16.4 & PostGIS 3.4.3 connected)
- **Known Issues or Ambiguities:** None.

---

## Chunk M2-04 Implementation Record

- **Status:** `COMMITTED`
- **Scope:** Backend Common API & Error Infrastructure
- **Files Created:**
  - `backend/app/schemas/__init__.py` (Central schema registry exporting error and response models)
  - `backend/app/schemas/common.py` (Pydantic models: `ErrorDetail`, `ErrorResponse`, `ResponseEnvelope[T]`, `PaginationMetadata`, `PaginatedResponse[T]`)
  - `backend/app/core/exceptions.py` (Custom application exception hierarchy: `AppException`, `BadRequestError`, `ValidationError`, `UnauthorizedError`, `ForbiddenError`, `NotFoundError`, `ConflictError`, `UnprocessableEntityError`, `ServiceUnavailableError`, `InternalServerError`)
  - `backend/app/core/middleware.py` (Pure ASGI `RequestIDMiddleware` generating or propagating `X-Request-ID` correlation IDs, setting request state and contextvar `get_request_id()`)
  - `backend/app/core/error_handlers.py` (Centralized FastAPI exception handlers: `app_exception_handler`, `http_exception_handler`, `validation_exception_handler`, `unhandled_exception_handler`)
  - `backend/tests/test_error_handling.py` (14 automated tests covering error schemas, status codes, sanitization, correlation IDs, and existing routes)
- **Files Modified:**
  - `backend/app/core/logging.py` (Added `RequestIDFilter` injecting `request_id` into all log records)
  - `backend/app/main.py` (Integrated `RequestIDMiddleware`, `register_error_handlers(app)`, and documented common error responses on OpenAPI schema)
  - `PROJECT_STATE.md` (Updated M2-04 to `COMMITTED`, unblocked M2-05 to `PLANNED`, and documented implementation record)
- **Files Removed:** None.
- **Automated Test Results:**
  - Full suite command: `wsl -e docker exec rakshakgis-backend pytest tests -v`
  - Result: **37 passed, 0 failed, 3 warnings in 1.73s**
  - Breakdown:
    - 14 tests in `tests/test_error_handling.py` (error responses, HTTP mappings, correlation IDs, 422 validation formatting, 500 sanitization without leaks, OpenAPI schema models)
    - 7 tests in `tests/test_database.py` (PostgreSQL & PostGIS engine, SessionLocal, get_db, readiness)
    - 8 tests in `tests/test_health.py` (app bootstrap, settings, /health, /, /api/v1, /docs, CORS)
    - 8 tests in `tests/test_models.py` (Alembic head, 29 ORM models, 17 PostGIS spatial geometry columns)
- **Live Endpoint Verification:**
  - `GET /health` -> HTTP 200 with `x-request-id` header
  - `GET /ready` -> HTTP 200 with `x-request-id` header
  - `GET /` -> HTTP 200 with `x-request-id` header
  - `GET /api/v1` -> HTTP 200 with `x-request-id` header
  - `GET /openapi.json` -> HTTP 200 with `ErrorResponse` and `ErrorDetail` schemas
  - `GET /non-existent-route` -> HTTP 404 with structured `ErrorResponse` schema, `NOT_FOUND` code, and `x-request-id`
  - Client-supplied `X-Request-ID` header accepted, propagated to logs, and echoed in response headers
  - Unhandled 500 exceptions sanitized; passwords/SQL/tracebacks never leaked to client responses
- **Known Issues or Ambiguities:** None.

---

## Chunk M2-05 Implementation Record

- **Status:** `COMMITTED`
- **Scope:** Backend Authentication Backend (JWT / RBAC)
- **Files Created:**
  - `backend/app/core/security.py` (Password hashing/verification via `bcrypt`, JWT access token issuance/decoding via `pyjwt`)
  - `backend/app/schemas/auth.py` (Pydantic models: `LoginRequest`, `TokenResponse`, `UserRead`)
  - `backend/app/api/deps.py` (`UserRole` enum, `get_current_user` dependency, `require_roles` RBAC callable)
  - `backend/app/api/v1/__init__.py` (API v1 package marker)
  - `backend/app/api/v1/auth.py` (`POST /api/v1/auth/login`, `GET /api/v1/auth/me`)
  - `backend/tests/test_auth.py` (25 automated tests covering password hashing, JWT operations, production configuration validation, login, me, and RBAC authorization)
- **Files Modified:**
  - `requirements.txt` (Added `bcrypt==5.0.0` and `pyjwt==2.13.0`)
  - `backend/app/core/config.py` (Added `JWT_SECRET`, `JWT_ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES`, and production validation check)
  - `backend/app/schemas/__init__.py` (Exported auth schemas: `LoginRequest`, `TokenResponse`, `UserRead`)
  - `backend/app/api/routes.py` (Mounted `auth_router` under prefix `/auth`)
  - `PROJECT_STATE.md` (Updated M2-05 to `COMMITTED` and documented implementation record)
- **Files Removed:** None.
- **Automated Test Results:**
  - Full suite command: `wsl -e docker exec rakshakgis-backend pytest tests -v`
  - Result: **62 passed, 0 failed, 3 warnings in 4.34s**
  - Breakdown:
    - 25 tests in `tests/test_auth.py` (bcrypt hashing/uniqueness, JWT issuance/expiry/signatures, production fallback rejection, login by username/email, 401 invalid credentials, sanitized `/me` without password leak, RBAC admin/officer/responder roles and 403 forbidden checks, OpenAPI documentation)
    - 14 tests in `tests/test_error_handling.py` (M2-04 common API error contract and correlation ID)
    - 7 tests in `tests/test_database.py` (M2-02 PostgreSQL / PostGIS engine and readiness)
    - 8 tests in `tests/test_health.py` (M2-01 health, root, /api/v1, docs)
    - 8 tests in `tests/test_models.py` (M2-03 Alembic head and 29 ORM models)
- **Live Endpoint Verification:**
  - `GET /health` -> HTTP 200 with `x-request-id`
  - `GET /ready` -> HTTP 200 with `x-request-id`
  - `GET /` -> HTTP 200 with `x-request-id`
  - `GET /api/v1` -> HTTP 200 with `x-request-id`
  - `GET /openapi.json` -> HTTP 200 with `LoginRequest`, `TokenResponse`, `UserRead` schemas
  - `POST /api/v1/auth/login` -> HTTP 200 with `access_token`, `token_type: bearer`, and `expires_in`
  - `POST /api/v1/auth/login` (bad credentials) -> HTTP 401 `UNAUTHORIZED` with structured `ErrorResponse`
  - `GET /api/v1/auth/me` (with Bearer token) -> HTTP 200 with sanitized `UserRead` strictly excluding `hashed_password`
  - `GET /api/v1/auth/me` (without token) -> HTTP 401 `UNAUTHORIZED` with structured `ErrorResponse`
  - Protected role endpoints properly return HTTP 403 `FORBIDDEN` when role is insufficient
- **Known Issues or Ambiguities:** None.

---

## Chunk M4-01 Implementation Record

- **Status:** `COMMITTED`
- **Commit:** `5c100603b77e45a47a8c6420f405819166e58609`
- **Scope:** Candidate Relocation Sites Backend
- **Files Created:**
  - `backend/app/schemas/sites.py` (Pydantic schemas for `GeoJSONPoint`, `GeoJSONPolygon`, `CandidateSiteRead`, `CandidateSiteDetailRead`, `CandidateSiteCreate`, `CandidateSiteUpdate`, `SiteCapacityRead`, `InfrastructureRead`)
  - `backend/app/api/v1/sites.py` (API router for candidate relocation sites: `GET /sites`, `GET /sites/{id}`, `POST /sites`, `PATCH /sites/{id}`, `DELETE /sites/{id}`)
  - `backend/tests/test_sites.py` (Automated unit and API integration tests for M4-01)
- **Files Modified:**
  - `backend/app/api/routes.py` (Registered candidate relocation sites router under `/api/v1/sites`)
  - `PROJECT_STATE.md` (Documented M4-01 implementation record, updated chunk registry and metadata to COMMITTED)
- **Files Removed:** None
- **API Endpoints Implemented:**
  - `GET /api/v1/sites` — List paginated candidate sites with filters (`district_id`, `status`, `min_elevation_m`, `max_elevation_m`, `min_area_sq_m`, `max_area_sq_m`, `search`).
  - `GET /api/v1/sites/{id}` — Get detailed candidate site by ID including loaded `capacities` and `infrastructures`.
  - `POST /api/v1/sites` — Create new candidate site (Requires `ADMIN` or `DISTRICT_OFFICER` role). Returns `404` for non-existent `district_id`, `422` for invalid spatial geometries.
  - `PATCH /api/v1/sites/{id}` — Partially update candidate site (Requires `ADMIN` or `DISTRICT_OFFICER` role).
  - `DELETE /api/v1/sites/{id}` — Delete candidate site (Requires `ADMIN` or `DISTRICT_OFFICER` role).
- **Automated Test Results:**
  - Container Environment: Docker Compose `rakshakgis-backend` (Python 3.11.16) & `rakshakgis-db` (PostgreSQL 16.4 / PostGIS 3.4.3).
  - Complete backend test suite command: `docker exec rakshakgis-backend pytest tests -v`
  - Result: **74 passed, 4 warnings in 6.26s** (0 failed, 0 errors).
  - M4-01 Candidate Sites test suite command: `docker exec rakshakgis-backend pytest tests/test_sites.py -v`
  - Result: **12 passed, 3 warnings in 1.03s** (0 failed, 0 errors).
  - All 14 M2-04 error handling tests pass cleanly with `backend/tests/test_error_handling.py` unweakened and unmodified.
- **Known Issues or Ambiguities:** None.

---

## Chunk M3-01 Implementation Record

- **Status:** `COMMITTED`
- **Scope:** Region Profiles Configuration
- **Specification Alignment Corrections Applied:**
  - Replaced quintile cutoffs with exact specification Risk Score Bands: `SAFE` (0–25), `MODERATE` (25–50), `HIGH` (50–70), `VERY_HIGH` (70–85), `CRITICAL` (85–100).
  - Implemented exact specification 6-factor Multi-Hazard Composite Risk formula: `Risk = 0.30H + 0.20F + 0.15R + 0.15S + 0.10D + 0.10V` (`hazard_weight=0.30`, `flood_weight=0.20`, `rainfall_weight=0.15`, `seismic_weight=0.15`, `demographic_weight=0.10`, `vulnerability_weight=0.10`).
  - Implemented exact specification 5-factor Relocation Priority formula: `0.40 Risk + 0.25 Exposure + 0.20 Vulnerability + 0.10 Historical Impact + 0.05 Accessibility`.
  - Implemented exact specification 4 Relocation Priority Bands: `IMMEDIATE` (80–100), `SHORT_TERM` (60–79), `MEDIUM_TERM` (40–59), `MONITOR` (<40).
- **Files Created:**
  - `backend/app/core/profiles/__init__.py` (Central package exports: models, canonical profiles, validator, registry)
  - `backend/app/core/profiles/models.py` (Strongly typed, immutable Pydantic models: `RegionProfile`, `RegionProfileId`, `RegionType`, `CompositeRiskWeights`, `RiskScoreBands`, `HazardParameters`, `VulnerabilityParameters`, `RedZoneThresholds`, `RelocationPriorityParameters`, `RelocationPriorityWeights`, `RelocationPriorityCutoffs`, `SiteCapacityAssumptions`, `ScenarioBounds`, `UncertaintyNotes`)
  - `backend/app/core/profiles/validation.py` (Deterministic validation enforcing weight sums, threshold ordering, non-negativity, and metadata invariants)
  - `backend/app/core/profiles/himalayan.py` (Canonical Himalayan pilot profile with Uttarakhand hill parameters and explicit pilot disclaimer)
  - `backend/app/core/profiles/riverine.py` (Template Riverine floodplain profile for region-agnostic multi-region support)
  - `backend/app/core/profiles/coastal.py` (Template Coastal maritime profile for cyclone/storm surge scenarios)
  - `backend/app/core/profiles/registry.py` (`RegionProfileRegistry`, `UnknownRegionProfileError`, and thread-safe resolution/enumeration functions)
  - `backend/tests/test_profiles.py` (11 automated tests verifying loading, immutability, validation rejection, resolution, region-agnostic decoupling, and exact specification constants)
- **Files Modified:**
  - `PROJECT_STATE.md` (Updated M3-01 to `COMMITTED`, added implementation record, updated integration notes)
- **Files Removed:** None.
- **Configuration Profiles Implemented:**
  - `himalayan_pilot` (Pilot/Demonstration configuration: composite risk 0.30H+0.20F+0.15R+0.15S+0.10D+0.10V; relocation priority 0.40Risk+0.25Exp+0.20Vuln+0.10Hist+0.05Acc; warning slope 25°, critical slope 35°; IMD rainfall triggers 64.5/115.5 mm; safe relocation slope <= 15°; water supply 70 LPD)
  - `riverine_template` (Template configuration using specification default risk & relocation weights with floodplain threshold assumptions)
  - `coastal_template` (Template configuration using specification default risk & relocation weights with maritime threshold assumptions)
- **Automated Test Results:**
  - Profiles suite command: `docker exec rakshakgis-backend pytest tests/test_profiles.py -v`
  - Result: **11 passed, 0 failed, 2 warnings in 0.36s**
  - Full suite regression command: `docker exec rakshakgis-backend pytest tests -v`
  - Result: **85 passed, 0 failed, 4 warnings in 6.53s**
- **Known Issues or Ambiguities:** None.

---

## Chunk M3-02 Implementation Record

- **Status:** `COMMITTED`
- **Scope:** Demo & Synthetic Datasets for Himalayan Pilot (Chamoli District)
- **Deterministic Seed:** `26191` (Fixed pseudo-random seed from SIH Problem Statement 26191)
- **Pilot Region Profile ID:** `himalayan_pilot` (From Chunk M3-01 `RegionProfileRegistry`)
- **Dataset Scales & Entities Generated:**
  - **40 Villages (`villages.geojson`):** GeoJSON FeatureCollection spanning Joshimath (15), Dasholi (13), Karnaprayag (7), and Ghat (5) blocks. Contains WGS84 Point geometry, non-negative populations (190–920), households, demographic breakdowns (elderly, children, disabled, livestock), vulnerability indices, infrastructure indicators, road connectivity, and physical hazard indicators.
  - **12 Candidate Relocation Sites (`candidate_sites.geojson`):** GeoJSON FeatureCollection with closed-ring bounding polygons, area (9,500–85,000 m²), slope (5.8°–24.0°), hazard buffer distances (220–1,400 m), carrying capacities, road access, and water supply (35–90 LPD). Includes 7 suitable sites, 4 intentionally rejected sites (slope > 15°, buffer < 500m, water < 70 LPD), and 1 constrained site (capacity bottleneck of 18 households) for downstream M4 suitability engine verification.
  - **30 Hazard Events (`hazard_events.json`):** Incident observations covering all 4 required hazard categories (10 landslides, 8 extreme/heavy rainfall readings exceeding IMD 64.5/115.5 mm thresholds, 6 seismic events MMI 5.5–7.2, and 6 flash flood / cloudburst runoffs).
  - **Dataset Metadata Manifest (`himalayan_pilot_metadata.json`):** Dataset versioning, bounds, counts, and non-official synthetic disclaimers.
- **Files Created:**
  - `backend/app/data/__init__.py` (Data package initialization)
  - `backend/app/data/synthetic/__init__.py` (Public package exports)
  - `backend/app/data/synthetic/constants.py` (Deterministic seed, block specs, settlement and site registries)
  - `backend/app/data/synthetic/schemas.py` (Pydantic models and GeoJSON validators)
  - `backend/app/data/synthetic/generator.py` (Deterministic dataset generator and fixture serializer)
  - `backend/app/data/synthetic/loader.py` (In-memory loader and direct GeoJSON dictionary accessor helpers)
  - `backend/app/data/synthetic/README.md` (Dataset documentation, schema descriptions, and consumption guide)
  - `backend/app/data/synthetic/fixtures/himalayan_pilot_metadata.json`
  - `backend/app/data/synthetic/fixtures/villages.geojson`
  - `backend/app/data/synthetic/fixtures/candidate_sites.geojson`
  - `backend/app/data/synthetic/fixtures/hazard_events.json`
  - `backend/tests/test_synthetic_data.py` (12 automated tests covering counts, GeoJSON topology, demographic bounds, hazard references, intentional rejection cases, determinism, and zero PII)
- **Files Modified:**
  - `PROJECT_STATE.md` (Updated M3-02 to `COMMITTED`, added implementation record, updated integration notes)
- **Files Removed:** None.
- **Automated Test Results:**
  - Synthetic dataset suite command: `docker exec rakshakgis-backend pytest tests/test_synthetic_data.py -v`
  - Result: **12 passed, 0 failed, 2 warnings in 0.41s**
  - Full backend regression command: `docker exec rakshakgis-backend pytest tests -v`
  - Result: **97 passed, 0 failed, 4 warnings in 6.36s**
- **Known Issues or Ambiguities:** None.

---

## Chunk M3-03 Implementation Record

- **Status:** `VERIFIED`
- **Scope:** Provider Interfaces & Mock Adapters
- **Scope Discipline:** Adapter/interface contracts and deterministic mock providers only; zero risk scoring, red zones, relocation matching, routing, or live network calls implemented.
- **Independent Review:** Verified and approved by independent review:
  - Provider contracts: Genuinely abstract `BaseDataProvider`, typed enums (`SourceCategory`, `ProviderMode`, `ProviderHealth`), typed records, and explicit exception hierarchy.
  - Deterministic mock adapters: 5 offline adapters consuming M3-02 fixtures without fabrication or credentials.
  - Registry: Thread-safe `ProviderRegistry` with isolated instance support and category/region lookup.
  - Provenance: Synthetic flags and disclaimers preserved on envelope and record levels with zero PII.
  - Test quality: 15 comprehensive behavior-oriented tests passing in container.
  - Scope compliance: Strict adapter boundary maintained; zero premature calculations or live API calls.
- **Provider Contracts & Schemas Introduced (`app.data.providers.contracts`):**
  - Enums: `SourceCategory` (`RAINFALL`, `FLOOD`, `LANDSLIDE`, `HAZARD_OBSERVATION`, `POPULATION_EXPOSURE`), `ProviderMode` (`MOCK`, `LIVE`), `ProviderHealth` (`HEALTHY`, `DEGRADED`, `UNAVAILABLE`).
  - Exceptions: `ProviderError` base class, `ProviderUnavailableError`, `UnsupportedQueryError`, `ProviderPayloadError`.
  - Normalized Records: `NormalizedRainfallRecord`, `NormalizedFloodRecord`, `NormalizedLandslideRecord`, `NormalizedHazardObservationRecord`, `NormalizedPopulationRecord`.
  - Envelope: `ProviderResponse[T]` with `ProviderProvenance` and `ProviderQuery`.
  - Interface: `BaseDataProvider(ABC)` specifying `provider_id`, `provider_name`, `supported_categories`, `supported_regions`, `mode`, `check_health()`, and `fetch_data()`.
- **Mock Adapters Implemented (`app.data.providers.mock`):**
  - `MockRainfallProvider` (`mock_imd_rainfall`): Consumes rainfall events from M3-02 fixtures; emits `NormalizedRainfallRecord` with IMD heavy/very heavy rain flags (64.5/115.5 mm).
  - `MockFloodProvider` (`mock_cwc_flood`): Consumes flash flood events from M3-02 fixtures; emits `NormalizedFloodRecord` with water level above danger marks.
  - `MockLandslideProvider` (`mock_gsi_landslide`): Consumes landslide observations from M3-02 fixtures; emits `NormalizedLandslideRecord` with debris volume and road blockage indicators.
  - `MockHazardObservationProvider` (`mock_multi_hazard_telemetry`): Consumes all multi-hazard telemetry (landslide, rain, seismic, flood) from M3-02 fixtures; emits `NormalizedHazardObservationRecord`.
  - `MockPopulationExposureProvider` (`mock_census_demographics`): Consumes village demographics from M3-02 `villages.geojson`; emits `NormalizedPopulationRecord` with vulnerable demographic splits.
- **Provider Registry (`app.data.providers.registry`):**
  - Thread-safe `ProviderRegistry` for discovery and category-based resolution.
  - Module helpers: `get_provider()`, `get_provider_by_id()`, `register_provider()`, `list_providers()`, `list_provider_ids()`.
- **Files Created:**
  - `backend/app/data/providers/__init__.py` (Package exports)
  - `backend/app/data/providers/contracts.py` (Contracts, normalized models, exception hierarchy)
  - `backend/app/data/providers/mock.py` (Deterministic mock adapters)
  - `backend/app/data/providers/registry.py` (Provider registry and resolution helpers)
  - `backend/app/data/providers/README.md` (Architecture documentation and live provider implementation guide)
  - `backend/tests/test_providers.py` (15 automated tests covering contracts, determinism, filtering, error states, and zero PII)
- **Files Modified:**
  - `PROJECT_STATE.md` (Updated M3-03 to `VERIFIED`, added implementation record, updated integration notes)
- **Files Removed:** None.
- **Automated Test Results:**
  - Provider suite command: `docker exec rakshakgis-backend pytest tests/test_providers.py -v`
  - Result: **15 passed, 0 failed, 2 warnings in 0.49s**
  - Synthetic dataset suite command: `docker exec rakshakgis-backend pytest tests/test_synthetic_data.py -v`
  - Result: **12 passed, 0 failed, 2 warnings in 0.55s**
  - Full backend regression command: `docker exec rakshakgis-backend pytest tests -v`
  - Result: **112 passed, 0 failed, 4 warnings in 6.26s**
- **Known Issues or Ambiguities / Limitations:**
  - Mock adapters operate exclusively on offline deterministic M3-02 fixtures for the `himalayan_pilot` region.
  - Rainfall threshold flags (`64.5` and `115.5`) are descriptive provider metadata matching canonical Himalayan values; cumulative exceedance semantics apply.
  - Live API integration with external agency endpoints (IMD, CWC, NRSC, USGS) will be introduced in future live telemetry phases following the `BaseDataProvider` contract.

---

## Chunk M3-04 Implementation Record

- **Status:** `COMMITTED`
- **Scope:** Data Validation & Ingestion Pipelines
- **Scope Discipline:** Input/provider validation, geographic sanity checks, temporal parsing, intra-batch deduplication, canonicalization, and structured result envelope generation only; zero risk scoring, red zones, relocation matching, routing, or live network calls implemented.
- **Independent Review:** Verified and approved by independent review:
  - Provider & batch envelope validation: Typed categories, provider identity, provenance preservation.
  - Stage validators: Pure validation functions for identity, ISO-8601 timestamps, WGS84 coordinates, numerical domain bounds, and severities.
  - Duplicate policy: Deterministic intra-batch duplicate detection (first occurrence accepted, duplicates flagged).
  - Canonical records: Subclasses of M3-03 normalized models with `ingested_at`, `batch_id`, and `canonical_hash`.
  - Result envelope: Structured `IngestionResult[T]` with accepted/rejected records, validation diagnostics, and deterministic metadata.
  - Test coverage: 20 focused tests passing in container.
  - Scope compliance: Strict validation/canonicalization boundary maintained; zero risk calculations or live API calls.
- **Validation & Ingestion Modules (`app.data.ingestion`):**
  - Exception Hierarchy (`errors.py`): `IngestionError` base class, `BatchValidationError`, `UnsupportedCategoryError`, `RecordValidationError`.
  - Diagnostics & Result Schemas (`schemas.py`): `ValidationIssueCode`, `ValidationSeverity`, `ValidationIssue`, `RejectedRecord`, `IngestionBatchMetadata`, and `IngestionResult[T]`.
  - Canonical Ingested Records (`schemas.py`): Subclasses of M3-03 normalized models (`CanonicalRainfallRecord`, `CanonicalFloodRecord`, `CanonicalLandslideRecord`, `CanonicalHazardObservationRecord`, `CanonicalPopulationRecord`) with `ingested_at`, `batch_id`, and `canonical_hash`.
  - Stage Validators (`validators.py`): Pure functions for identity, ISO-8601 timestamps, WGS84 coordinates (bounds, no NaN/inf, no clamping), numerical non-negative domains, severities, and synthetic provenance preservation.
  - Pipeline Coordinator (`pipeline.py`): `IngestionPipeline` with `ingest_provider_response()`, `ingest_batch()`, partial-batch fault isolation, intra-batch duplicate detection (first occurrence accepted, duplicates flagged), and deterministic metadata derivation.
  - Architecture Documentation (`README.md`): Pipeline stages, validation vs normalization, duplicate policy, provenance handling, determinism, and no-risk-logic boundary.
- **Files Created:**
  - `backend/app/data/ingestion/__init__.py` (Package exports)
  - `backend/app/data/ingestion/errors.py` (Ingestion exception hierarchy)
  - `backend/app/data/ingestion/schemas.py` (Validation issues, canonical records, ingestion result envelopes)
  - `backend/app/data/ingestion/validators.py` (Granular stage-by-stage validators)
  - `backend/app/data/ingestion/pipeline.py` (Pipeline coordinator and batch processor)
  - `backend/app/data/ingestion/README.md` (Architecture and operational documentation)
  - `backend/tests/test_ingestion.py` (20 automated tests covering all categories, invalid inputs, error isolation, determinism, PII scans, and M3-02/M3-03 integration)
- **Files Modified:**
  - `PROJECT_STATE.md` (Updated M3-04 to `COMMITTED`, added implementation record, updated integration notes)
- **Files Removed:** None.
- **Automated Test Results:**
  - Ingestion suite command: `docker exec rakshakgis-backend pytest tests/test_ingestion.py -v`
  - Result: **20 passed, 0 failed, 2 warnings in 0.50s**
  - Synthetic dataset suite command: `docker exec rakshakgis-backend pytest tests/test_synthetic_data.py -v`
  - Result: **12 passed, 0 failed, 2 warnings in 0.42s**
  - Provider suite command: `docker exec rakshakgis-backend pytest tests/test_providers.py -v`
  - Result: **15 passed, 0 failed, 2 warnings in 0.42s**
  - Full backend regression command: `docker exec rakshakgis-backend pytest tests -v`
  - Result: **132 passed, 0 failed, 4 warnings in 6.11s**
- **Known Issues or Ambiguities / Limitations:**
  - Ingestion produces in-memory typed `IngestionResult` envelopes; database persistence into PostGIS tables will occur via downstream ingestion-to-db hooks or CLI commands.
  - Rainfall flags (`64.5 mm` and `115.5 mm`) are preserved as descriptive provider metadata; cumulative exceedance semantics apply without computing risk scores.

---

## Chunk M3-05 Implementation Record

- **Status:** `COMMITTED`
- **Scope:** Risk Normalization Engine
- **Scope Discipline:** Strictly limited to transforming validated heterogeneous hazard and exposure observations into comparable factor values on a standardized `0.0 — 100.0` scale. Zero composite risk computation ($Risk = 0.30H + 0.20F + ...$), zero multi-hazard aggregation, zero risk banding (SAFE, MODERATE, HIGH, CRITICAL), zero Red Zones, zero relocation priorities, zero live external API calls, and zero database migrations implemented. Demographic exposure and vulnerability scoring ($D$ and $V$) are explicitly deferred to Chunk M3-09.
- **Normalization Modules (`app.core.risk.normalization`):**
  - Exception Hierarchy (`errors.py`): `NormalizationError` base class, `NormalizationConfigError`, `InvalidInputError`, `UnsupportedFactorError`.
  - Typed Contracts (`contracts.py`): `FactorCategory` enum, `NormalizationMethod` enum, `NormalizationStatus` enum, `LinearRangeConfig` (with bounds validation), `PiecewiseThresholdConfig` (with monotonicity validation), `CategoricalSeverityPolicy` (with score validation), `NormalizationExplainability` metadata envelope, and `NormalizationResult` output envelope with strict invariants ($0.0 \le \text{normalized\_value} \le 100.0$; missing/unavailable records strictly mapped to `normalized_value=None`).
  - Mathematical Methods (`methods.py`): Pure deterministic functions: `linear_normalize()`, `piecewise_threshold_normalize()`, and `categorical_severity_normalize()` with explicit clamping tracking and NaN/Inf rejection.
  - Normalization Coordinator (`engine.py`): `RiskNormalizationEngine` integrating M3-01 `RegionProfile` thresholds (`rainfall_heavy_24h_mm = 64.5`, `rainfall_very_heavy_24h_mm = 115.5`, `seismic_critical_mmi = 7.0`), factor normalizers (`normalize_rainfall()`, `normalize_flood()`, `normalize_landslide()`, `normalize_hazard_observation()`, `normalize_categorical()`), and universal record normalizer `normalize_record()` handling canonical M3-04 records.
  - Public Package Exports (`__init__.py`): Re-exported under `app.core.risk` and `app.core.risk.normalization`.
  - Technical Documentation (`README.md`): Architecture, 0–100 scale contract, supported methods, configuration sourcing, clamping behavior, safety-critical missing/unknown handling, explainability metadata, and strict boundary definition.
- **Files Created:**
  - `backend/app/core/risk/__init__.py` (Top-level risk module exports)
  - `backend/app/core/risk/normalization/__init__.py` (Normalization package exports)
  - `backend/app/core/risk/normalization/contracts.py` (Typed schemas, policy models, and result envelopes)
  - `backend/app/core/risk/normalization/errors.py` (Normalization exception hierarchy)
  - `backend/app/core/risk/normalization/methods.py` (Pure mathematical scaling and interpolation methods)
  - `backend/app/core/risk/normalization/engine.py` (Normalization engine with profile integration)
  - `backend/app/core/risk/normalization/README.md` (Architecture and technical reference)
  - `backend/tests/test_risk_normalization.py` (22 comprehensive unit tests covering all required invariants)
- **Files Modified:**
  - `PROJECT_STATE.md` (Updated M3-05 to `AWAITING_REVIEW`, updated current/blocked work, added implementation record, updated integration notes)
- **Files Removed:** None.
- **Automated Test Results:**
  - M3-05 normalization suite: `docker exec rakshakgis-backend pytest tests/test_risk_normalization.py -v`
  - Result: **22 passed, 0 failed, 2 warnings in 0.57s**
  - Ingestion suite regression: `docker exec rakshakgis-backend pytest tests/test_ingestion.py -v`
  - Result: **20 passed, 0 failed, 2 warnings in 0.71s**
  - Provider suite regression: `docker exec rakshakgis-backend pytest tests/test_providers.py -v`
  - Result: **15 passed, 0 failed, 2 warnings in 0.36s**
  - Synthetic dataset regression: `docker exec rakshakgis-backend pytest tests/test_synthetic_data.py -v`
  - Result: **12 passed, 0 failed, 2 warnings in 0.43s**
  - Full backend regression: `docker exec rakshakgis-backend pytest tests -v`
  - Result: **154 passed, 0 failed, 4 warnings in 6.38s**
- **Known Issues or Ambiguities / Limitations:**
  - Demographic exposure ($D$) and vulnerability scoring ($V$) are explicitly deferred to M3-09; population records return `NormalizationStatus.DEFERRED` with `normalized_value=None`.
  - Composite multi-hazard risk scoring ($0.30H + 0.20F + 0.15R + 0.15S + 0.10D + 0.10V$) is implemented in Chunk M3-06.

---

## Chunk M3-06 Implementation Record

- **Status:** `COMMITTED`
- **Scope:** Multi-Hazard Risk Computation Engine
- **Scope Discipline:** Implements the authoritative multi-hazard composite risk formulation $\text{Risk} = 0.30H + 0.20F + 0.15R + 0.15S + 0.10D + 0.10V$ strictly bounded to $[0.0, 100.0]$. Directly consumes and reuses M3-01 `CompositeRiskWeights` profile configuration. Computes full factor breakdowns with individual weighted contributions and transparent explainability audit trails. Safety-critical missing factor policy: missing or unavailable factors strictly yield `status=INSUFFICIENT_FACTORS` with `score=None` and never default to $0.0$.
- **Independent Review:** Verified and approved with PASS by independent review. Exact formula verified; missing/unavailable safety invariants verified; M3-05 integration verified; scope discipline verified; 19 focused tests and 173 total regression tests passing.
- **Strictly Prohibited & Omitted:** Zero risk classification bands (`SAFE`, `MODERATE`, `HIGH`, `CRITICAL` - deferred to M3-07), zero Red Zones (M3-10/M3-11), zero relocation priority (M3-12), zero site suitability/routing (M4), zero live external APIs, zero database migrations, zero LLMs.
- **Risk Computation Modules (`app.core.risk.computation`):**
  - Exception Hierarchy (`errors.py`): `RiskComputationError` base class, `InsufficientFactorsError`, `InvalidFactorValueError`, `WeightConfigurationError`.
  - Typed Contracts (`contracts.py`): `RiskFactorType` enum (`HAZARD_SEVERITY`, `FLOOD_EXPOSURE`, `RAINFALL_INTENSITY`, `SLOPE_LANDSLIDE_SUSCEPTIBILITY`, `INFRASTRUCTURE_VULNERABILITY`, `SOCIAL_VULNERABILITY`), `RiskComputationStatus` enum (`COMPUTED`, `INSUFFICIENT_FACTORS`, `INVALID_INPUT`), `RiskWeightsConfig` (with `from_profile()` factory and sum-to-1.0 validation), `RiskFactorInput` (supporting raw floats or M3-05 `NormalizationResult` envelopes), `CompositeRiskExplainability` (formula string, contributions breakdown, weights dictionary, factor values dictionary, human-readable audit trail), and `CompositeRiskResult` envelope with strict invariants ($0.0 \le \text{score} \le 100.0$; score cannot be non-null if status is not `COMPUTED`).
  - Computation Coordinator (`engine.py`): `MultiHazardRiskEngine` executing formula, contribution breakdown, safety checks, and audit trails. Rejects NaN/Inf, validates input ranges $[0.0, 100.0]$, and produces structured `CompositeRiskResult`.
  - Public Package Exports (`__init__.py`): Re-exported under `app.core.risk` and `app.core.risk.computation`.
  - Technical Documentation (`README.md`): Architecture, exact formula and weights, explainability breakdown, safety-critical missing input handling, and clear chunk boundaries.
- **Files Created:**
  - `backend/app/core/risk/computation/__init__.py` (Package exports)
  - `backend/app/core/risk/computation/contracts.py` (Typed schemas, factor types, explainability models, result envelopes)
  - `backend/app/core/risk/computation/errors.py` (Computation exception hierarchy)
  - `backend/app/core/risk/computation/engine.py` (Multi-hazard risk engine implementation)
  - `backend/app/core/risk/computation/README.md` (Architecture, formula, and technical specification)
  - `backend/tests/test_risk_computation.py` (19 automated unit tests covering all mathematical boundaries, missing value safety, explainability breakdown, determinism, M3-05 integration, and scope boundary checks)
- **Files Modified:**
  - `backend/app/core/risk/__init__.py` (Re-exported M3-06 computation classes alongside M3-05)
  - `PROJECT_STATE.md` (Updated M3-06 status to `COMMITTED`, added implementation record, updated integration notes)
- **Files Removed:** None.
- **Automated Test Results:**
  - Computation suite command: `docker exec rakshakgis-backend pytest tests/test_risk_computation.py -v`
  - Result: **19 passed, 0 failed, 2 warnings in 0.54s**
  - Risk normalization suite regression: `docker exec rakshakgis-backend pytest tests/test_risk_normalization.py -v`
  - Result: **22 passed, 0 failed, 2 warnings in 0.58s**
  - Ingestion suite regression: `docker exec rakshakgis-backend pytest tests/test_ingestion.py -v`
  - Result: **20 passed, 0 failed, 2 warnings in 0.70s**
  - Provider suite regression: `docker exec rakshakgis-backend pytest tests/test_providers.py -v`
  - Result: **15 passed, 0 failed, 2 warnings in 0.44s**
  - Synthetic dataset regression: `docker exec rakshakgis-backend pytest tests/test_synthetic_data.py -v`
  - Result: **12 passed, 0 failed, 2 warnings in 0.42s**
  - Full backend regression: `docker exec rakshakgis-backend pytest tests -v`
  - Result: **173 passed, 0 failed, 4 warnings in 6.78s**
- **Known Issues or Ambiguities / Limitations:**
  - Categorical risk tier classification (e.g. `SAFE`, `MODERATE`, `HIGH`, `CRITICAL`) is implemented in Chunk M3-07.
  - Demographic exposure ($D$) and social vulnerability ($V$) scoring engine is deferred to Chunk M3-09; however, the engine accepts their normalized factor values whenever provided.

---

## Chunk M3-07 Implementation Record

- **Status:** `COMMITTED`
- **Scope:** Risk Classification & Grading Engine
- **Scope Discipline:** Strictly limited to classifying an already computed composite risk score ($0.0 \le \text{Risk} \le 100.0$) into its authoritative categorical risk band (`SAFE`, `MODERATE`, `HIGH`, `VERY_HIGH`, `CRITICAL`). Zero risk score recalculation (reusing M3-06 outputs), zero Red Zone demarcation (M3-10 / M3-11), zero relocation priority (M3-12), zero site suitability/routing (M4), zero live external APIs, zero database migrations, zero LLMs.
- **Independent Review:** Verified and approved with PASS by independent review. Exact cutoffs and boundaries verified; input safety and NaN/Inf rejection verified; original score preservation verified; 23 focused tests and 196 total regression tests passing.
- **Risk Classification Modules (`app.core.risk.classification`):**
  - Exception Hierarchy (`errors.py`): `RiskClassificationError` base class, `InvalidRiskScoreError`, `ClassificationBandConfigError`.
  - Typed Contracts (`contracts.py`): Re-exports `RiskBand` enum from `app.core.profiles.models`, `RiskScoreBandsConfig` (with monotonicity validation and `from_profile()` factory), `RiskClassificationExplainability` (selected band, score, interval notation, lower/upper bounds, inclusivity flags, audit trail), and `RiskClassificationResult` envelope with numerical invariants ($0.0 \le \text{score} \le 100.0$; preserves original continuous score and village ID).
  - Classification Engine (`engine.py`): `RiskClassificationEngine` executing authoritative interval logic:
    - $[0.0, 25.0) \implies \text{SAFE}$
    - $[25.0, 50.0) \implies \text{MODERATE}$
    - $[50.0, 70.0) \implies \text{HIGH}$
    - $[70.0, 85.0) \implies \text{VERY\_HIGH}$
    - $[85.0, 100.0] \implies \text{CRITICAL}$
  - Safety-Critical Input Validation: Rejects negative scores ($< 0.0$), scores $> 100.0$, `NaN`, $\pm\infty$, non-numeric/boolean types, and incomplete `CompositeRiskResult` objects (`status != COMPUTED`) with `InvalidRiskScoreError`. Strictly refuses to clamp invalid inputs.
  - Public Package Exports (`__init__.py`): Re-exported under `app.core.risk` and `app.core.risk.classification`.
  - Technical Documentation (`README.md`): Interval specifications, boundary behaviors, explainability metadata, and chunk boundaries.
- **Files Created:**
  - `backend/app/core/risk/classification/__init__.py` (Package exports)
  - `backend/app/core/risk/classification/contracts.py` (Typed schemas, result envelopes, explainability models)
  - `backend/app/core/risk/classification/errors.py` (Classification exception hierarchy)
  - `backend/app/core/risk/classification/engine.py` (Risk classification engine implementation)
  - `backend/app/core/risk/classification/README.md` (Architecture, cutoffs, and boundary specification)
  - `backend/tests/test_risk_classification.py` (23 automated unit tests covering all boundary values, interval ranges, invalid inputs, NaN/Inf rejection, determinism, M3-06 integration, and scope boundary checks)
- **Files Modified:**
  - `backend/app/core/risk/__init__.py` (Re-exported M3-07 classification classes alongside M3-05 and M3-06)
  - `PROJECT_STATE.md` (Updated M3-07 status to `COMMITTED`, added implementation record, updated integration notes)
- **Files Removed:** None.
- **Automated Test Results:**
  - Classification suite command: `docker exec rakshakgis-backend pytest tests/test_risk_classification.py -v`
  - Result: **23 passed, 0 failed, 2 warnings in 1.68s**
  - Computation suite regression: `docker exec rakshakgis-backend pytest tests/test_risk_computation.py -v`
  - Result: **19 passed, 0 failed, 2 warnings in 0.52s**
  - Risk normalization suite regression: `docker exec rakshakgis-backend pytest tests/test_risk_normalization.py -v`
  - Result: **22 passed, 0 failed, 2 warnings in 0.58s**
  - Ingestion suite regression: `docker exec rakshakgis-backend pytest tests/test_ingestion.py -v`
  - Result: **20 passed, 0 failed, 2 warnings in 0.70s**
  - Provider suite regression: `docker exec rakshakgis-backend pytest tests/test_providers.py -v`
  - Result: **15 passed, 0 failed, 2 warnings in 0.44s**
  - Synthetic dataset regression: `docker exec rakshakgis-backend pytest tests/test_synthetic_data.py -v`
  - Result: **12 passed, 0 failed, 2 warnings in 0.42s**
  - Full backend regression: `docker exec rakshakgis-backend pytest tests -v`
  - Result: **196 passed, 0 failed, 4 warnings in 6.89s**
- **Known Issues or Ambiguities / Limitations:**
  - Demographic exposure ($D$) and social vulnerability ($V$) scoring engine is deferred to Chunk M3-09.
  - Permanent and dynamic Red Zone demarcation is deferred to Chunks M3-10 and M3-11.

---

## Known Issues

1. **Untracked Host Virtual Environment:** `backend/venv/` exists locally on Windows host and is properly ignored by `.gitignore`. The Docker service isolates this via an anonymous volume (`/app/venv`).
2. **Empty Frontend Directory:** `frontend/` contains no scaffolding, package files, or build tool configuration (scheduled for Chunk M5-01).

---

## Integration Notes

- Docker Compose defines two core services: `db` (`postgis/postgis:16-3.4`) and `backend` (`python:3.11-slim-bookworm` with native GDAL 3.6.2, GEOS 3.11.1, PROJ 9.1.1, and libpq 15.19).
- Backend image contains all pinned Python dependencies from `requirements.txt` including `alembic==1.19.1`, `Mako==1.4.1`, `bcrypt==5.0.0`, and `pyjwt==2.13.0`.
- Database service verified healthy and queryable with PostGIS 3.4.3 on port 5432 using named persistent volume `rakshakgis_pgdata`.
- Backend container mounts `./backend:/app` for real-time hot-reloading during development.
- Environment variables are defined via `.env.example` with documented defaults; zero secrets are tracked in Git.
- Chunk M2-01 established FastAPI application entrypoint with `/health`, `/`, and `/api/v1` routes and automated test suite.
- Chunk M2-02 established PostgreSQL & PostGIS engine connectivity, `SessionLocal`, `get_db()`, `/ready` endpoint, and spatial capability verification.
- Chunk M2-03 established Alembic migration foundation and all 29 SQLAlchemy ORM models with PostGIS spatial types (SRID 4326).
- Chunk M2-04 established common API schemas, standardized error responses, exception hierarchy, correlation ID middleware (`X-Request-ID`), and centralized error handlers.
- Chunk M2-05 established password hashing with bcrypt, JWT token operations with pyjwt, current-user authentication dependency, RBAC authorization (`require_roles`), and auth API endpoints (`/login`, `/me`).
- Chunk M4-01 established candidate relocation sites backend API (`/api/v1/sites`), Pydantic GeoJSON Point/Polygon schemas with coordinate bounds and closed-ring validation, pagination and domain filters, RBAC mutation enforcement (`ADMIN`, `DISTRICT_OFFICER`), and relational detail loading.
- Chunk M3-01 established typed, immutable regional configuration system (`app.core.profiles`) with deterministic validation, registry resolver, Himalayan pilot profile, and future Riverine/Coastal templates.
- Chunk M3-02 established deterministic synthetic Himalayan pilot dataset (40 villages, 12 candidate relocation sites, 30 hazard events, seed 26191) with GeoJSON fixtures and Pydantic loader schemas.
- Chunk M3-03 established provider-adapter abstraction layer (`app.data.providers`) with typed contracts, exception hierarchy, registry, and deterministic mock adapters consuming M3-02 fixtures.
- Chunk M3-04 established data validation and ingestion pipeline (`app.data.ingestion`) with multi-stage validators, intra-batch deduplication, canonicalization, and deterministic `IngestionResult` envelopes.
- Chunk M3-05 established risk normalization engine (`app.core.risk.normalization`) transforming heterogeneous hazard observations to comparable 0.0 - 100.0 factors with M3-01 profile thresholds, clamping tracking, explainability metadata, and safety-critical missing/unknown handling.
- Chunk M3-06 established multi-hazard risk computation engine (`app.core.risk.computation`) implementing $Risk = 0.30H + 0.20F + 0.15R + 0.15S + 0.10D + 0.10V$, weighted explainability breakdown, strict $[0.0, 100.0]$ bounds, and safe missing-factor handling.
- Chunk M3-07 established risk classification and grading engine (`app.core.risk.classification`) evaluating authoritative risk bands (SAFE, MODERATE, HIGH, VERY_HIGH, CRITICAL) with explicit boundary transitions, explainability metadata, and strict rejection of invalid scores.
- Automated tests verified: 196 passed in container (Python 3.11).

---

## Last Updated

- **Timestamp:** 2026-09-05 02:22:00 IST
- **Updated By:** M4 (Bookkeeping Correction)
- **Status Summary:** Chunk M4-01 independently reviewed and COMMITTED (Commit: `5c100603b77e45a47a8c6420f405819166e58609`); Chunk M4-02 is now eligible; Chunks M3-08 and M3-09 are eligible independently.
