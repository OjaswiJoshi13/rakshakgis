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
| **M4-01** | Relocation | Candidate Relocation Sites Backend | M4 | M2-03 | **AWAITING_REVIEW** |
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

- **Active Chunk:** None (Chunk M4-01 implemented and awaiting review)
- **Next Eligible Chunks:** M3-02 (Demo & Synthetic Datasets), M3-03 (Provider Interfaces & Mock Adapters)
- **Status:** Chunk M3-01 independently verified and COMMITTED; Chunk M4-01 (Candidate Relocation Sites Backend) implemented and awaiting independent review.

---

## Blocked Work

Chunks M3-02 through DOC-01 (except unblocked M3-01 and M4-01) remain in `BLOCKED` status awaiting completion, independent verification, and commit of their respective prerequisites.

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

- **Status:** `AWAITING_REVIEW`
- **Scope:** Candidate Relocation Sites Backend
- **Files Created:**
  - `backend/app/schemas/sites.py` (Pydantic schemas for `GeoJSONPoint`, `GeoJSONPolygon`, `CandidateSiteRead`, `CandidateSiteDetailRead`, `CandidateSiteCreate`, `CandidateSiteUpdate`, `SiteCapacityRead`, `InfrastructureRead`)
  - `backend/app/api/v1/sites.py` (API router for candidate relocation sites: `GET /sites`, `GET /sites/{id}`, `POST /sites`, `PATCH /sites/{id}`, `DELETE /sites/{id}`)
  - `backend/tests/test_sites.py` (Automated unit and API integration tests for M4-01)
- **Files Modified:**
  - `backend/app/api/routes.py` (Registered candidate relocation sites router under `/api/v1/sites`)
  - `PROJECT_STATE.md` (Documented M4-01 implementation record, updated chunk registry and metadata to AWAITING_REVIEW)
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
- Automated tests verified: 85 passed in container (Python 3.11).

---

## Last Updated

- **Timestamp:** 2026-09-05 00:03:00 IST
- **Updated By:** M3 (Antigravity Agent)
- **Status Summary:** Chunk M3-01 independently verified and COMMITTED; all 85 automated tests verified against live PostGIS database container.
