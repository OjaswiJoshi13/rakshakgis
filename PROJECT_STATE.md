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
| **M3-08** | Risk/GIS | Risk Explainability & Factor Contribution | M3 | M3-07 | **COMMITTED** |
| **M3-09** | Risk/GIS | Vulnerability & Exposure Scoring Engine | M3 | M3-06 | **COMMITTED** |
| **M3-10** | Risk/GIS | Permanent Red Zones Demarcation | M3 | M3-07 | **COMMITTED** |
| **M3-11** | Risk/GIS | Dynamic Red Zones & Threshold Triggers | M3 | M3-10 | **COMMITTED** |
| **M3-12** | Risk/GIS | Relocation Priority Scoring Backend | M3 | M3-08, M3-09 | **COMMITTED** |
| **M3-13** | Risk/GIS | Data Source Freshness & Telemetry Backend | M3 | M3-03 | **COMMITTED** |
| **M4-01** | Relocation | Candidate Relocation Sites Backend | M4 | M2-03 | **COMMITTED** |
| **M4-02** | Relocation | Multi-Criteria Site Suitability Engine | M4 | M4-01, M3-06 | **COMMITTED** |
| **M4-03** | Relocation | Carrying Capacity & Infrastructure Sizing | M4 | M4-02 | **COMMITTED** |
| **M4-04** | Relocation | Relocation Matching & Assignment Engine | M4 | M3-12, M4-03 | **COMMITTED** |
| **M4-05** | Relocation | Evacuation & Access Routing Engine | M4 | M4-04 | **COMMITTED** |
| **M4-06** | Relocation | Scenario Simulator Integration Backend | M4 | M4-04, M3-11 | **COMMITTED** |
| **M5-01** | Frontend | Frontend Foundation & Design System | M5 | M1-01 | **COMMITTED** |
| **M5-02** | Frontend | Authentication UI & Session Handling | M5 | M5-01, M2-05 | **COMMITTED** |
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

- **Active Chunk:** None (Chunk M5-02 committed; Milestone 5 progressing)
- **Next Eligible Chunks:** Chunk M5-03: API Client & State Management Setup (depends on M5-01 and M2-04 [both COMMITTED]); Chunk M6-01: Operations UI Shell & Navigation (depends on M5-01 [COMMITTED]); Chunk M6-04: Scenario Simulator UI (once M6-01 committed)
- **Status:** Chunk M5-02 COMMITTED (Commit: `c538c55`); Chunk M5-01 COMMITTED (Commit: `fda544e`); Chunk M4-06 COMMITTED; Chunk M2-05 COMMITTED. 58 frontend tests passed (100% clean), 0 lint errors, tsc clean, production build passed.

---

## Blocked Work

Chunks M5-03 through DOC-01 (except committed M3-01 through M3-13, M4-01 through M4-06, and M5-01 and M5-02 which are COMMITTED) remain in `BLOCKED` status awaiting completion, independent verification, and commit of their respective prerequisites.

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
- M3-08: Risk Explainability & Factor Contribution — COMMITTED (Commit: `80a34d4`).
- M3-09: Vulnerability & Exposure Scoring Engine — COMMITTED (Commit: `feat(risk): formalize demographic and social vulnerability scoring`).
- M3-10: Permanent Red Zones Demarcation — COMMITTED (Commit: `feat(risk): implement permanent red zone demarcation`).
- M3-11: Dynamic Red Zones & Threshold Triggers — COMMITTED (Commit: `feat(risk): implement dynamic red zone threshold triggers`).
- M3-12: Relocation Priority Scoring Backend — COMMITTED (Commit: `feat(risk): implement relocation priority scoring`).
- M3-13: Data Source Freshness & Telemetry Backend — COMMITTED (Commit: `a14d46b` — `feat(telemetry): implement data source freshness telemetry`).
- M4-01: Candidate Relocation Sites Backend — COMMITTED (Commit: `5c100603b77e45a47a8c6420f405819166e58609`).
- M4-02: Multi-Criteria Site Suitability Engine — COMMITTED (Commit: `feat(m4): add site suitability engine`).
- M4-03: Carrying Capacity & Infrastructure Sizing — COMMITTED (Commit: `3c0d37a7b8e19cbfcf16f0bcf82c813587b1c3e3`).
- M4-04: Relocation Matching & Assignment Engine — COMMITTED (Commit: `b4e984ebc6a567e149881079d36c2580525ab72f`).
- M4-05: Evacuation & Access Routing Engine — COMMITTED (Commit: `93e62e6392e0903aefc034a9cd13d4ad18e0c1ec` — `feat(m4): implement evacuation and access routing`).
- M4-06: Scenario Simulator Integration Backend — COMMITTED (Commit: `feat(m4): integrate scenario simulator pipeline`).

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

## Chunk M3-08 Implementation Record

- **Status:** `COMMITTED`
- **Commit:** `80a34d4` (`feat(risk): add deterministic risk explainability`)
- **Scope:** Risk Explainability & Factor Contribution
- **Scope Discipline:** Strictly limited to auditable decomposition and transparent explanation of an already-computed multi-hazard composite risk result ($0.30H + 0.20F + 0.15R + 0.15S + 0.10D + 0.10V$) and its integrated M3-07 risk classification. Zero risk formula alterations, zero secondary weight configurations, zero Red Zone demarcation (M3-10 / M3-11), zero relocation priority scoring (M3-12), zero demographic vulnerability scoring (M3-09), zero site suitability/routing (M4), zero live external APIs, zero database migrations, zero LLMs for risk computation or narrative generation.
- **Factor Decomposition & Semantics:**
  - **Six Authoritative Factors:** Hazard Severity ($H$, 0.30), Flood Exposure ($F$, 0.20), Rainfall Intensity ($R$, 0.15), Slope / Landslide Susceptibility ($S$, 0.15), Infrastructure Vulnerability ($D$, 0.10), Social Vulnerability ($V$, 0.10).
  - **Individual Contributions:** $c_i = w_i \times v_i$ where $v_i \in [0.0, 100.0]$. Sum of contributions matches composite score within numerical tolerance ($10^{-4}$).
  - **Contribution Percentage:** Proportional share $p_i = (c_i / \text{Risk}) \times 100\%$ for non-zero scores, summing to 100.0%.
  - **Ranked Contributions & Dominant Driver:** Deterministic descending contribution ranking with canonical tie-breaking ($H \to F \to R \to S \to D \to V$). Identifies primary hazard/vulnerability driver.
- **Safety-Critical Missing Data Policy:**
  - `INSUFFICIENT_FACTORS` status from M3-06 strictly yields `is_computable=False`, `score=None`, `ranked_contributions=[]`, `dominant_factor=None`, and `classification=None`.
  - Missing factors are explicitly enumerated in `missing_factors`.
  - Narrative explanation highlights disaster safety protocol: unmonitored or unavailable factors are **never** coerced to zero risk.
  - `INVALID_INPUT` (NaN, Inf, out of bounds) strictly yields `is_computable=False`, `score=None`, with explicit rejection audit trail.
- **M3-07 Risk Classification Integration:**
  - Accepts pre-computed `RiskClassificationResult` envelopes, validating mathematical consistency ($|\text{classification.score} - \text{composite.score}| < 10^{-4}$) and village ID alignment.
  - Automatically runs `RiskClassificationEngine` when unclassified `CompositeRiskResult` is passed and classification is requested.
  - Supports unclassified explanation (`classification=None`) when classification is omitted.
  - Never recalculates risk bands or duplicates cutoff thresholds.
- **Deterministic Narrative & Provenance:**
  - Generates template-driven human-readable explanations synthesizing overall risk score, risk band, primary driver, full factor breakdown, and applied formula.
  - Preserves regional configuration provenance (`RegionProfileRegistry`, `himalayan_pilot`).
- **Explainability Modules (`app.core.risk.explainability`):**
  - Exception Hierarchy (`errors.py`): `RiskExplainabilityError`, `UncomputableExplanationError`, `IncompatibleClassificationError`.
  - Typed Contracts (`contracts.py`): `FACTOR_METADATA`, `FactorContributionDetail`, `FactorRanking`, `RiskClassificationSummary`, `CompositeRiskExplanation`.
  - Explainability Engine (`engine.py`): `RiskExplainabilityEngine` coordinating decomposition, ranking, classification integration, narrative synthesis, and convenience `explain_computation()` pipeline.
  - Package Exports (`__init__.py`): Re-exported under `app.core.risk` and `app.core.risk.explainability`.
  - Technical Documentation (`README.md`): Architecture, formulas, factor semantics, missing data policy, classification integration, and boundary definitions.
- **Files Created:**
  - `backend/app/core/risk/explainability/__init__.py`
  - `backend/app/core/risk/explainability/contracts.py`
  - `backend/app/core/risk/explainability/engine.py`
  - `backend/app/core/risk/explainability/errors.py`
  - `backend/app/core/risk/explainability/README.md`
  - `backend/tests/test_risk_explainability.py` (28 automated unit tests covering all mathematical boundaries, missing value safety, ranking, classification integration, determinism, provenance, and scope boundaries)
- **Files Modified:**
  - `backend/app/core/risk/__init__.py` (Re-exported M3-08 explainability classes)
  - `PROJECT_STATE.md` (Updated M3-08 status to `AWAITING_REVIEW`, added implementation record, updated integration notes)
- **Files Removed:** None.
- **Automated Test Results:**
  - Explainability suite command: `wsl -e docker exec rakshakgis-backend pytest tests/test_risk_explainability.py -v`
  - Result: **28 passed, 0 failed, 2 warnings in 1.19s**
  - Computation & Classification regression: `wsl -e docker exec rakshakgis-backend pytest tests/test_risk_computation.py tests/test_risk_classification.py -v`
  - Result: **42 passed, 0 failed, 2 warnings in 1.37s**
  - Full backend regression command: `wsl -e docker exec rakshakgis-backend pytest tests -v`
  - Result: **262 passed, 0 failed, 4 warnings in 8.08s**
- **Known Issues or Ambiguities / Limitations:**
  - Demographic exposure and social vulnerability scoring engine is deferred to Chunk M3-09.
  - Permanent and dynamic Red Zone demarcation is deferred to Chunks M3-10 and M3-11.
  - Relocation priority scoring backend is deferred to Chunk M3-12 (requires M3-08 and M3-09).

---

## Chunk M4-02 Implementation Record

- **Status:** `COMMITTED`
- **Scope:** Multi-Criteria Site Suitability Engine
- **Scope Discipline:** Implements deterministic multi-criteria suitability evaluation across 9 authoritative criteria preceded by strict hard safety and capacity constraint gates. Zero relocation matching or assignment (M4-04), zero evacuation routing (M4-05), zero scenario simulator (M4-06), zero officer approval sign-off workflow (M6-08), zero LLMs for numerical scoring.
- **Criteria & Authoritative Weights (Strictly Sum to 1.00 / 100%):**
  1. Hazard Safety: 30% (`0.30`)
  2. Capacity: 20% (`0.20`)
  3. Road Access: 10% (`0.10`)
  4. Water Availability: 10% (`0.10`)
  5. Healthcare Access: 10% (`0.10`)
  6. School Access: 5% (`0.05`)
  7. Emergency Services: 5% (`0.05`)
  8. Livelihood Access: 5% (`0.05`)
  9. Expansion Potential: 5% (`0.05`)
- **Hard Constraints & Safety Invariants:**
  - **Slope Safety:** Evaluates `terrain_slope_deg <= max_safe_slope_deg` (15.0° default from Himalayan profile). Missing slope strictly fails.
  - **Hazard Buffer Distance:** Evaluates `hazard_buffer_distance_m >= min_hazard_buffer_m` (500.0m mandatory exclusion buffer).
  - **Known Usable Capacity:** Evaluates `available_households > 0` and `max_households > 0`. Missing, unknown, or zero capacity strictly fails (never treated as unlimited).
  - **Water Availability Criterion:** Water supply is strictly evaluated under the 10% weighted criterion (normalized against humanitarian baseline of 70 LPD/capita) rather than as an unconfigured hard disqualification gate.
  - **Strict Pre-Scoring Override Invariant:** Hard constraints are evaluated *before* weighted scoring. Any failure strictly marks `is_eligible=False` and `decision=INELIGIBLE`. Weighted scores are calculated for explainability and audit trail only, and can **never** override a hard constraint failure.
- **Categorical Decisions & Classification Rules:**
  - `SUITABLE`: Passes all hard constraints, overall score $\ge 65.0$, and capacity $\ge 20$ households.
  - `CONSTRAINED`: Passes hard constraints, but either score is in $[40.0, 65.0)$ or capacity $< 20$ households (community transfer bottleneck).
  - `UNSUITABLE`: Passes hard constraints, but overall score $< 40.0$.
  - `INELIGIBLE`: Failed one or more mandatory hard constraints.
- **Configuration Approach:**
  - `SuitabilityWeightsConfig`: Pydantic model with `@model_validator` enforcing strict sum-to-1.0 invariant within tolerance ($10^{-5}$).
  - `SuitabilityThresholdsConfig`: Configurable domain thresholds with `from_profile(profile: RegionProfile)` factory to source regional defaults (e.g. `HIMALAYAN_PILOT_PROFILE`).
- **Suitability Modules (`app.core.relocation.suitability`):**
  - Exception Hierarchy (`errors.py`): `SiteSuitabilityError`, `InvalidSiteDataError`, `MissingCriticalAttributeError`, `SuitabilityConfigError`, `HardConstraintError`.
  - Typed Contracts (`contracts.py`): `CriterionType`, `SuitabilityDecision`, `HardConstraintType`, `ConstraintEvaluation`, `CriterionScoreResult`, `SuitabilityWeightsConfig`, `SuitabilityThresholdsConfig`, `SiteSuitabilityInput` (with `from_candidate_site_model` and `from_synthetic_feature` factories), and `SiteSuitabilityResult` explainability envelope.
  - Hard Constraints Evaluator (`constraints.py`): `HardConstraintEvaluator` implementing pre-scoring safety and capacity checks.
  - Deterministic Scorer (`scoring.py`): Normalized 0.0–100.0 scoring functions for each of the 9 criteria with input validation against NaN/Inf.
  - Suitability Coordinator (`engine.py`): `SiteSuitabilityEngine` coordinating hard constraint gates, multi-criteria scoring, weighted aggregation, decision grading, and human-readable audit reasons.
  - Public Package Exports (`__init__.py`): Cleanly exported under `app.core.relocation.suitability`.
  - Architectural Documentation (`README.md`): Architectural specifications, weights, formulas, and explainability breakdown.
- **API Endpoints Added (`/api/v1/sites`):**
  - `POST /api/v1/sites/evaluate`: Direct candidate site payload evaluation.
  - `POST /api/v1/sites/{id}/evaluate`: Evaluate database candidate site by ID, with optional `persist_score` update.
  - `GET /api/v1/sites/{id}/suitability`: Retrieve suitability evaluation for database site by ID.
- **Files Created:**
  - `backend/app/core/relocation/__init__.py`
  - `backend/app/core/relocation/suitability/__init__.py`
  - `backend/app/core/relocation/suitability/contracts.py`
  - `backend/app/core/relocation/suitability/errors.py`
  - `backend/app/core/relocation/suitability/constraints.py`
  - `backend/app/core/relocation/suitability/scoring.py`
  - `backend/app/core/relocation/suitability/engine.py`
  - `backend/app/core/relocation/suitability/README.md`
  - `backend/tests/test_site_suitability.py`
- **Files Modified:**
  - `backend/app/schemas/sites.py` (Added `SiteEvaluationRequest`, re-exported contracts)
  - `backend/app/api/v1/sites.py` (Added suitability evaluation endpoints)
  - `PROJECT_STATE.md` (Updated status to `AWAITING_REVIEW` and added implementation record)
- **Files Removed:** None.
- **Automated Test Results:**
  - M4-02 suitability suite command: `docker exec rakshakgis-backend pytest tests/test_site_suitability.py -v`
  - Result: **20 passed, 0 failed, 2 warnings in 2.98s**
  - M4-01 sites suite regression command: `docker exec rakshakgis-backend pytest tests/test_sites.py -v`
  - Result: **12 passed, 0 failed, 3 warnings in 2.35s**
  - Full backend regression command: `docker exec rakshakgis-backend pytest tests -v`
  - Result: **216 passed, 0 failed, 4 warnings in 19.86s**
- **M4-02 Implementation Review Corrections:**
  - **Correction 1 (Silent Region-Profile Fallback Removed):** Removed broad `except Exception:` fallback in `/api/v1/sites` suitability endpoints (`/evaluate`, `/{id}/evaluate`, `/{id}/suitability`) that previously substituted the default `SiteSuitabilityEngine()`. Requesting an invalid or nonexistent `region_profile_id` now raises `UnknownRegionProfileError`, returning a standard HTTP 404 response with structured error code `"UNKNOWN_REGION_PROFILE"` and correlation ID.
  - **Correction 2 (Water Hard Constraint Removed):** Inspected existing `RegionProfile` and site rules. Water availability is an engineering baseline (`water_supply_lpd_per_capita = 70.0`) used for infrastructure capacity sizing in M4-03, not an authoritative hard exclusion gate in the M4-02 suitability specification. Removed `WATER_MINIMUM` from the mandatory hard-constraint gate (`Slope Safety`, `Hazard Buffer`, and `Usable Capacity` remain the hard exclusion gates). Kept Water Availability strictly as the 10% weighted criterion, ensuring low water supply proportionately penalizes the raw water score without bypassing authoritative safety gates or artificially disqualifying viable sites.
- **Explicitly Documented MVP Assumptions:**
  - Regional threshold defaults are sourced from Himalayan Pilot Profile (`SiteCapacityAssumptions`): max safe slope 15.0°, hazard exclusion buffer 500.0m, water supply standard 70.0 LPD/capita.
  - Minimum viable community relocation capacity is assumed at 20 households; sites passing scoring with < 20 households are classified as `CONSTRAINED`.
  - Non-perennial water sources and seasonal road access apply deterministic discount multipliers (0.75 and 0.70).
- **Known Limitations:**
  - Relocation carrying capacity sizing and infrastructure deficit calculations are deferred to Chunk M4-03.
  - Multi-village to candidate site matching and assignment optimization are deferred to Chunk M4-04.
  - Evacuation and access network routing engine are deferred to Chunk M4-05.
  - Dynamic scenario simulation is deferred to Chunk M4-06.

---

## Chunk M4-03 Implementation Record

- **Status:** `COMMITTED`
- **Commit:** `3c0d37a7b8e19cbfcf16f0bcf82c813587b1c3e3`
- **Scope:** Carrying Capacity & Infrastructure Sizing
- **Scope Discipline:** Implements deterministic, explainable carrying capacity calculations and infrastructure sizing across 5 critical dimensions. Zero relocation matching or assignment (deferred to M4-04), zero evacuation routing (deferred to M4-05), zero scenario simulation (deferred to M4-06), zero officer approval workflow (deferred to M6-08), zero frontend code, zero LLMs for capacity computations.
- **Authoritative Effective Capacity Rule:**
  $$\text{effective\_capacity} = \min(\text{housing\_capacity}, \text{water\_capacity}, \text{sanitation\_capacity}, \text{healthcare\_capacity}, \text{shelter\_capacity})$$
  - Enforces weakest-link bottleneck principle in households.
  - Strict rejection of averaging, summing, or allowing strong dimensions to compensate for deficit dimensions.
- **Incoming and Available Capacity Formulations:**
  $$\text{available\_capacity} = \text{effective\_capacity} - \text{current\_occupancy}$$
  $$\text{capacity\_margin} = \text{available\_capacity} - \text{incoming\_households}$$
  - **Negative Margin Preservation:** Deficits are strictly preserved as negative numbers (e.g. $-25$ households; never clamped to 0) to support explainability and downstream optimization (M4-04).
  - **Feasibility:** Feasible if and only if $\text{effective\_capacity} > 0$, $\text{available\_capacity} > 0$, and $\text{capacity\_margin} \ge 0$, with no critical deficits.
- **Deterministic Limiting Factor Identification:**
  - Identifies which critical dimension(s) constrain effective capacity.
  - In case of ties, all tied dimensions are reported deterministically (sorted alphabetically).
- **Unknown Data Safety Invariant:**
  - Missing, `None`, or unavailable critical capacity dimensions are **never** treated as unlimited.
  - Any unknown critical dimension produces an indeterminate/infeasible result (`feasible=False`, `effective_capacity=None`, `limiting_factors=[]`, `unknown_dimensions=[...]`) with clear human-readable explanation.
- **Infrastructure Sizing Across Critical Dimensions:**
  - **Housing / Habitation:** Existing household capacity vs. incoming household demand; physical land area ($\text{sq.m}$) sized against `land_area_sq_m_per_household`.
  - **Water Availability:** Existing household water capacity vs. incoming household demand; physical water sized against `water_supply_lpd_per_capita` (70.0 LPD/person baseline).
  - **Sanitation Facilities:** Existing household sanitation vs. incoming household demand; toilet units sized against `households_per_sanitation_unit` (4.0 hh/unit).
  - **Healthcare Access:** Existing healthcare coverage capacity vs. incoming household demand.
  - **Emergency Shelter:** Existing emergency shelter capacity vs. incoming household demand.
- **Validation Invariants:**
  - Rejects negative capacity, negative occupancy, negative incoming households, NaN, and $\pm\infty$ with `InvalidCapacityDataError` (HTTP 422).
- **Regional Configuration:**
  - Region-agnostic design; default planning parameters sourced dynamically from `RegionProfile` (`SiteCapacityAssumptions`).
  - Requesting an invalid `region_profile_id` raises `UnknownRegionProfileError` (HTTP 404 with error code `"UNKNOWN_REGION_PROFILE"`), with zero silent fallback.
- **API Endpoints Added (`/api/v1/sites`):**
  - `POST /api/v1/sites/capacity/evaluate`: Direct payload carrying capacity evaluation.
  - `POST /api/v1/sites/{id}/capacity/evaluate`: Evaluate carrying capacity for database candidate site by ID with optional demand and overrides.
  - `GET /api/v1/sites/{id}/capacity`: Retrieve carrying capacity evaluation for database site by ID.
- **Files Created:**
  - `backend/app/core/relocation/capacity/__init__.py`
  - `backend/app/core/relocation/capacity/contracts.py`
  - `backend/app/core/relocation/capacity/errors.py`
  - `backend/app/core/relocation/capacity/sizing.py`
  - `backend/app/core/relocation/capacity/engine.py`
  - `backend/app/core/relocation/capacity/README.md`
  - `backend/tests/test_m4_03_capacity.py`
- **Files Modified:**
  - `backend/app/schemas/sites.py` (Added `SiteCapacityEvaluationRequest`, re-exported contracts)
  - `backend/app/api/v1/sites.py` (Added capacity endpoints and `_resolve_capacity_engine`)
  - `PROJECT_STATE.md` (Updated status to `AWAITING_REVIEW` and added implementation record)
- **Files Removed:** None.
- **Automated Test Results:**
  - M4-03 focused capacity suite command: `docker exec rakshakgis-backend pytest tests/test_m4_03_capacity.py -v`
  - Result: **18 passed, 0 failed, 2 warnings in 1.78s**
  - M4-02 suitability suite regression command: `docker exec rakshakgis-backend pytest tests/test_site_suitability.py -v`
  - Result: **20 passed, 0 failed, 2 warnings in 2.66s**
  - M4-01 sites suite regression command: `docker exec rakshakgis-backend pytest tests/test_sites.py -v`
  - Result: **12 passed, 0 failed, 3 warnings in 1.50s**
  - Full backend regression command: `docker exec rakshakgis-backend pytest tests -v`
  - Result: **234 passed, 0 failed, 4 warnings in 17.88s**
- **Explicitly Documented MVP Assumptions:**
  - Regional planning assumptions are derived from Himalayan Pilot Profile: water requirement 70.0 LPD/capita, land area 120.0 sq.m/household.
  - Default demographic conversion assumes 4.17 persons per household (derived from synthetic dataset ratio).
  - Standard community sanitation assumes 4.0 households per toilet unit (matching SPHERE / synthetic dataset 4:1 ratio).
  - Healthcare and emergency shelter capacities are required inputs for safe effective capacity determination; if unmeasured in initial site surveys, they are safely reported as unknown rather than assumed infinite.
- **Known Limitations:**
  - Relocation matching and multi-village to site assignment optimization are deferred to Chunk M4-04.
  - Evacuation and access network routing engine are deferred to Chunk M4-05.
  - Dynamic scenario simulation is deferred to Chunk M4-06.

---

## Chunk M5-01 Implementation Record

- **Status:** `COMMITTED`
- **Commit:** `fda544e`
- **Chunk:** M5-01
- **Module:** Frontend Core / GIS
- **Title:** Frontend Foundation & Design System
- **Owner:** M5
- **Dependencies Consumed:** M1-01 (Repository & Docker Foundation — COMMITTED)
- **Independent Review Verification:**
  - Independent review PASSED.
  - Dependency: M1-01 confirmed `COMMITTED` (Commit `bb79e25`).
  - Frontend type-check: PASS (0 errors).
  - Frontend lint: PASS (0 warnings, 0 errors).
  - Frontend tests: PASS (7/7 suites, 29/29 tests passed).
  - Next.js production build: PASS (Route `/`: 18.3 kB / 105 kB; Route `/_not-found`: 873 B / 88.1 kB).
  - Backend regression: PASS (262 passed, 4 warnings, 0 failures in 8.79s).
  - Scope check: PASS (Strictly within M5-01 scope; zero downstream M5/M6 functionality or backend modifications).
- **Next Eligible M5 Chunks:**
  - M5-02: Authentication UI & Session Handling (once M5-01 verified/committed; depends on M5-01 and M2-05 [COMMITTED])
  - M5-03: API Client & State Management Setup (once M5-01 verified/committed; depends on M5-01 and M2-04 [COMMITTED])
- **Scope Discipline:**
  - Establishes clean Next.js 14 App Router application foundation with React 18, TypeScript, and Tailwind CSS.
  - Implements authoritative design system tokens strictly conforming to domain specification:
    - 5 Multi-Hazard Risk Bands: `SAFE` (0–25), `MODERATE` (25–50), `HIGH` (50–70), `VERY_HIGH` (70–85), `CRITICAL` (85–100).
    - 4 Relocation Urgency Bands: `IMMEDIATE` (80–100), `SHORT_TERM` (60–79), `MEDIUM_TERM` (40–59), `MONITOR` (<40).
    - Operational status indicators (`NORMAL`, `INFO`, `WARNING`, `CRITICAL`) and data modes (`DEMO`, `LIVE`, `SIMULATION`).
  - Implements reusable, WCAG 2.1 AA accessible UI primitives: `Button`, `Badge`, `RiskBadge`, `RelocationBadge`, `Card`, `MetricCard`, `Alert`, `StatusIndicator`.
  - Establishes command center layout shell: `CommandHeader` (with live clock and mode badges), `Sidebar` (with modular navigation and chunk indicators), `StatusBar` (with CRS EPSG:4326, profile, and version), `AppLayout` (with skip-to-content accessible link).
  - Implements foundational landing overview (`page.tsx`) showcasing design tokens, operational alerts, and parameter metrics.
  - Zero authentication functionality implemented (deferred to M5-02).
  - Zero API client or fake backend endpoints implemented (deferred to M5-03).
  - Zero MapLibre GIS canvas implemented (deferred to M5-05).
  - Zero modifications to backend business logic, schemas, or models.
- **Files Created (35 files):**
  - `frontend/.env.example`
  - `frontend/.eslintrc.json`
  - `frontend/next-env.d.ts`
  - `frontend/next.config.mjs`
  - `frontend/package.json`
  - `frontend/package-lock.json`
  - `frontend/postcss.config.mjs`
  - `frontend/tailwind.config.ts`
  - `frontend/tsconfig.json`
  - `frontend/vitest.config.ts`
  - `frontend/src/app/globals.css`
  - `frontend/src/app/layout.tsx`
  - `frontend/src/app/page.tsx`
  - `frontend/src/components/layout/AppLayout.tsx`
  - `frontend/src/components/layout/CommandHeader.tsx`
  - `frontend/src/components/layout/Sidebar.tsx`
  - `frontend/src/components/layout/StatusBar.tsx`
  - `frontend/src/components/layout/index.ts`
  - `frontend/src/components/ui/Alert.tsx`
  - `frontend/src/components/ui/Badge.tsx`
  - `frontend/src/components/ui/Button.tsx`
  - `frontend/src/components/ui/Card.tsx`
  - `frontend/src/components/ui/MetricCard.tsx`
  - `frontend/src/components/ui/StatusIndicator.tsx`
  - `frontend/src/components/ui/index.ts`
  - `frontend/src/design-system/tokens.ts`
  - `frontend/src/lib/utils.ts`
  - `frontend/src/__tests__/setup.ts`
  - `frontend/src/__tests__/Button.test.tsx`
  - `frontend/src/__tests__/Badge.test.tsx`
  - `frontend/src/__tests__/Card.test.tsx`
  - `frontend/src/__tests__/MetricCard.test.tsx`
  - `frontend/src/__tests__/Alert.test.tsx`
  - `frontend/src/__tests__/Layout.test.tsx`
  - `frontend/src/__tests__/Page.test.tsx`
- **Files Modified:**
  - `.gitignore` (Added `*.tsbuildinfo` under Frontend Dependencies and Builds)
  - `PROJECT_STATE.md` (Updated M5-01 status to `AWAITING_REVIEW` and added implementation record)
- **Files Removed:** None
- **Commands Executed & Results:**
  - `npm install` -> 523 packages added, audited with 0 compilation errors
  - `npm run type-check` (`tsc --noEmit`) -> Exited 0, zero type errors
  - `npm run lint` (`next lint`) -> Exited 0, "No ESLint warnings or errors"
  - `npm run test` (`vitest run`) -> Exited 0, 7 test files, 29 tests passed (100%)
  - `npm run build` (`next build`) -> Exited 0, static generation of `/` (18.3 kB / 105 kB first load JS) and `/_not-found` (873 B / 88.1 kB first load JS) completed successfully
  - `docker exec rakshakgis-backend pytest tests -q` -> Exited 0, 262 passed, 4 warnings in 8.79s (full backend test suite verified with zero regression)
- **Known Limitations:**
  - Live data fetching and auth session integration are scheduled for chunks M5-02 and M5-03.

---

## Chunk M5-02 Implementation Record

- **Status:** `COMMITTED`
- **Commit:** `c538c55`
- **Chunk:** M5-02
- **Module:** Frontend Core / GIS
- **Title:** Authentication UI & Session Handling
- **Owner:** M5
- **Dependencies Consumed:**
  - M5-01 (Frontend Foundation & Design System — COMMITTED, Commit `fda544e`)
  - M2-05 (Authentication / Session Backend — COMMITTED)
- **Independent Review Verification:**
  - Independent review PASSED (`PASS — READY FOR VERIFIED STATUS`).
  - Prerequisite dependencies verified: M5-01 (`fda544e`) COMMITTED, M2-05 COMMITTED, M2-04 COMMITTED.
  - Authentication contract verification: `POST /api/v1/auth/login`, `GET /api/v1/auth/me`, `UserRead`, `UserRole`, `TokenResponse`, and M2-04 `ErrorResponse` match backend contracts exactly.
  - Token & session lifecycle: verified client-safe JWT Bearer storage in `localStorage`, proactive expiry check with 5s clock-skew buffer, automatic token validation and profile hydration on mount, clean unauthenticated redirect without content flash, and full cleanup on logout.
  - Security review: verified tokens are never leaked into the DOM, passwords are never persisted or logged, zero hard-coded credentials or production secrets, and backend errors sanitized.
  - UI & Route protection: verified `LoginForm`, accessible labels, loading spinner states, `ProtectedRoute` blocking unauthenticated access without content flash, and `CommandHeader` integration with role badges and sign-out.
  - Frontend checks:
    - `npm run type-check` (`tsc --noEmit`): PASS (0 errors)
    - `npm run lint` (`next lint`): PASS (0 warnings, 0 errors)
    - `npm run test` (`vitest run`): PASS (12/12 test suites, 58/58 tests passed, 100% clean)
    - `npm run build` (`next build`): PASS (production build verified; static pages: `/`, `/_not-found`, `/login`)
  - Scope check: PASS (zero M5-03/M5-04/M5-05/M6 functionality implemented, zero backend modifications).
  - Backend regression note: Docker daemon was unavailable in the local Windows CLI environment; existing recorded backend regression from prior verified M5-01 review remains: 262 passed, 4 warnings, 0 failures in 8.79s.
- **Authentication Contract Consumed from M2-05:**
  - `POST /api/v1/auth/login`: Accepts `LoginRequest` (`username` [or registered email], `password`), returns `TokenResponse` (`access_token`, `token_type: "bearer"`, `expires_in`). Returns HTTP 401 with standard M2-04 `ErrorResponse` on invalid credentials or inactive accounts.
  - `GET /api/v1/auth/me`: Accepts `Authorization: Bearer <token>` header, returns `UserRead` (`id`, `username`, `email`, `full_name`, `role`, `department`, `is_active`, `created_at`, `updated_at`) strictly excluding sensitive password hashes. Returns HTTP 401 on missing or expired tokens.
  - Roles consumed: `admin`, `district_officer`, `field_responder`, `viewer`.
  - Session lifecycle: JWT Bearer storage via `localStorage` with expiration checking (`expires_in` in seconds mapped to epoch timestamp); automatic profile hydration via `GET /me`; automatic token expiration detection; graceful client logout clearing storage and state.
- **Implementation Summary:**
  - Implemented TypeScript authentication types (`User`, `UserRole`, `LoginRequest`, `TokenResponse`, `AuthState`, `AuthErrorResponse`) in `types/auth.ts` matching M2-05 backend schemas.
  - Created authentication and token storage service (`lib/auth.ts`) with client-safe token persistence, expiry tracking, M2-04 error response parsing, and API methods for `POST /auth/login` and `GET /auth/me`.
  - Built reactive session management context and hook (`AuthContext.tsx`, `useAuth()`) managing user profile, bearer token, authentication status, loading state, transient error messages, login, logout, profile refresh, and role authorization helpers (`hasRole`).
  - Implemented accessible authority login form (`LoginForm.tsx`) with username/email and password fields, client-side input validation, loading indicator with animated spinner, and danger alert displaying server/validation errors.
  - Implemented client route guard (`ProtectedRoute.tsx`) preventing unauthorized access, blocking unauthenticated users with redirect to `/login`, eliminating layout flash with accessible loading status, and verifying role permissions.
  - Created dedicated authority login page (`app/login/page.tsx`) styled with RakshakGIS disaster decision support branding, SIH 26191 tagging, and automatic redirect to `/` when already authenticated.
  - Integrated `AuthProvider` into root layout (`app/layout.tsx`).
  - Wired `CommandHeader` to display authenticated user's initials, name, department, role badge, and interactive "Sign Out" button (or "Sign In" button when unauthenticated).
  - Enforced route protection on command center shell (`app/page.tsx`) using `<ProtectedRoute>`.
  - Added comprehensive Vitest test suite with 29 new tests across 5 test files (58 tests total across 12 suites), verifying all auth services, context lifecycles, UI components, guards, and pages.
  - Strictly maintained scope: zero M5-03 API client or downstream dashboard/GIS/relocation features implemented; zero backend modifications.
- **Files Created (11 files):**
  - `frontend/src/types/auth.ts`
  - `frontend/src/lib/auth.ts`
  - `frontend/src/context/AuthContext.tsx`
  - `frontend/src/components/auth/LoginForm.tsx`
  - `frontend/src/components/auth/ProtectedRoute.tsx`
  - `frontend/src/app/login/page.tsx`
  - `frontend/src/__tests__/AuthService.test.ts`
  - `frontend/src/__tests__/AuthContext.test.tsx`
  - `frontend/src/__tests__/LoginForm.test.tsx`
  - `frontend/src/__tests__/ProtectedRoute.test.tsx`
  - `frontend/src/__tests__/LoginPage.test.tsx`
- **Files Modified (4 files):**
  - `frontend/src/__tests__/setup.ts` (Added `next/navigation` mocks for test runner)
  - `frontend/src/app/layout.tsx` (Wrapped root layout with `AuthProvider`)
  - `frontend/src/app/page.tsx` (Protected command center shell with `ProtectedRoute`)
  - `frontend/src/components/layout/CommandHeader.tsx` (Connected `useAuth` user profile, role badge, and logout action)
- **Files Removed:** None
- **Commands Executed & Exact Results:**
  - `npm run type-check` (`tsc --noEmit`) -> Exited 0, zero type errors
  - `npm run lint` (`next lint`) -> Exited 0, "No ESLint warnings or errors"
  - `npm run test` (`vitest run`) -> Exited 0, 12 test files passed, 58 tests passed (100% clean)
  - `npm run build` (`next build`) -> Exited 0, compiled successfully, static pages generated for `/`, `/_not-found`, and `/login`
- **Known Issues or Limitations:**
  - Live API client and state management architecture for operational data deferred to M5-03 as planned.
- **Next Eligible M5 Chunk:**
  - M5-03: API Client & State Management Setup (depends on M5-01 and M2-04 [both COMMITTED])

---

## Chunk M3-09 Implementation Record

- **Status:** `COMMITTED`
- **Commit:** `feat(risk): formalize demographic and social vulnerability scoring`
- **Scope:** Vulnerability & Exposure Scoring Engine
- **Lifecycle:** IMPLEMENTED -> VERIFIED -> COMMITTED
- **Summary:**
  - Implemented and formalized the Vulnerability & Exposure Scoring Engine for Member 3 (Risk / GIS / Data) per project lead approval (**Option 1 — Accept with Formalization**).
  - Produces normalized $[0.0, 100.0]$ factor scores for Factor $D$ (Demographic Exposure, mapped to `RiskFactorType.INFRASTRUCTURE_VULNERABILITY`, symbol `"D"`, weight 0.10) and Factor $V$ (Social Vulnerability, `RiskFactorType.SOCIAL_VULNERABILITY`, symbol `"V"`, weight 0.10).
  - **Factor $D$ — Demographic Exposure Formalized:**
    ```text
    P_eff = P + (m_E - 1)E + (m_C - 1)C + (m_Dis - 1)D_is

    Score_D = min(100.0, ((P_eff - P_min) / (P_benchmark - P_min)) * 100.0)
    ```
    - $P_{\min} = 0.0$
    - Himalayan profile multipliers: elderly $m_E = 1.25$, children $m_C = 1.20$, disabled $m_{\text{Dis}} = 1.50$, loaded dynamically from `RegionProfile.vulnerability_parameters.demographic_factors`.
    - Population benchmark parameter $P_{\text{benchmark}}$ is a configurable parameter via `DemographicExposureConfig(benchmark_population=...)`, with default $P_{\text{benchmark}} = 1000.0$ for the Himalayan pilot.
    - Zero-population safety rule: zero population strictly produces $D = 0.0$ (`Score_D = 0.0`) without division-by-zero.
    - Output is strictly bounded to $[0.0, 100.0]$ with explicit clamping metadata.
    - Contract Naming: Factor D retains `RiskFactorType.INFRASTRUCTURE_VULNERABILITY` (symbol `"D"`, weight 0.10) per explicit project lead decision to preserve full backwards compatibility with committed M3-06 MultiHazardRiskEngine and M3-08 Explainability contracts.
  - **Factor $V$ — Social Vulnerability Formalized:**
    ```text
    Score_V = (w_soc * I_soc + w_econ * I_econ + w_struct * I_struct + w_road * (1 - C_road)) * 100
    ```
    - Uses four committed indices from `VulnerabilityProfile`: social vulnerability ($I_{\text{soc}}$), economic vulnerability ($I_{\text{econ}}$), structural fragility ($I_{\text{struct}}$), and road connectivity ($C_{\text{road}}$).
    - Road vulnerability is formally defined as access isolation: $1.0 - C_{\text{road}}$.
    - Component weights loaded from active regional profile, with Himalayan pilot default $0.25$ each ($w_{\text{soc}}=0.25, w_{\text{econ}}=0.25, w_{\text{struct}}=0.25, w_{\text{road}}=0.25$), summing strictly to 1.0 within numerical tolerance ($10^{-4}$).
    - Output is strictly bounded to $[0.0, 100.0]$.
    - Indicator scope: strictly uses committed indicators; no BPL, literacy, marginal-worker, or agricultural-dependence indicators are used.
  - **Safety-Critical Missing Data & Determinism Policy:**
    - Missing/unavailable required demographic or vulnerability data strictly remains unavailable (`ScoringStatus.UNAVAILABLE` or `ScoringStatus.INSUFFICIENT_DATA` with `normalized_value=None`, `is_available=False`); never defaults or coerced to zero risk.
    - Deterministic execution guaranteed; identical inputs yield identical floating-point scores.
- **Files Created:**
  - `backend/app/core/risk/vulnerability/__init__.py` (Package exports)
  - `backend/app/core/risk/vulnerability/contracts.py` (Domain models, configs, inputs, results, invariants)
  - `backend/app/core/risk/vulnerability/errors.py` (Domain exception hierarchy)
  - `backend/app/core/risk/vulnerability/engine.py` (Core scoring coordinator and algorithms)
  - `backend/app/core/risk/vulnerability/README.md` (Technical documentation, math formulas, invariants)
  - `backend/tests/test_vulnerability_scoring.py` (22 automated unit & integration tests)
- **Files Modified:**
  - `backend/app/core/risk/__init__.py` (Re-exported vulnerability engine symbols)
  - `PROJECT_STATE.md` (Recorded Option 1 formalization, updated test counts and current work)
- **Files Removed:** None
- **Commands Executed & Results:**
  - `wsl -e docker exec rakshakgis-backend pytest tests/test_vulnerability_scoring.py -v` -> Exited 0, 22 passed, 2 warnings in 1.07s (100%)
  - `wsl -e docker exec rakshakgis-backend pytest tests/test_risk_normalization.py tests/test_risk_computation.py tests/test_risk_classification.py tests/test_risk_explainability.py tests/test_vulnerability_scoring.py -v` -> Exited 0, 95 passed, 2 warnings in 2.12s (100%)
  - `wsl -e docker exec rakshakgis-backend pytest tests -v` -> Exited 0, 284 passed, 4 warnings in 8.08s (100% full backend regression pass)
- **Test Coverage Mapping:**
  - D calculation: `test_demographic_exposure_valid_standard`, `test_demographic_exposure_no_vulnerable_groups`
  - Configurable D benchmark: `test_configurable_demographic_benchmark`
  - D bounds: `test_demographic_exposure_maximum_clamping`
  - Zero population: `test_demographic_exposure_zero_population`
  - V weighted calculation: `test_social_vulnerability_valid_standard`, `test_regional_profile_customization`
  - Road inversion: `test_road_connectivity_inversion_explicit`, `test_social_vulnerability_valid_standard`
  - Missing-data safety: `test_demographic_exposure_missing_and_unavailable`, `test_social_vulnerability_missing_and_insufficient`, `test_missing_data_safety_chain_to_m3_06`
  - M3-06 compatibility: `test_m3_06_d_contract_naming_preserved`, `test_integration_with_m3_06_risk_engine`
  - Deterministic behavior: `test_deterministic_reproducibility`
- **Scope Boundaries & Invariants Preserved:**
  - Status marked `COMMITTED`.
  - M3-10, M3-11, M3-12, M4 relocation, and frontend untouched.
  - Missing/unavailable data never coerced to zero.
  - Core numerical engine decoupled from LLMs and external network calls.
- **Dependencies & Downstream Readiness:**
  - Chunk M3-09 COMMITTED.
  - Prerequisite for M3-12 (Relocation Priority Scoring Backend) is now satisfied alongside committed M3-08.
  - Downstream chunks M3-10, M3-11, M3-12, M4, M5, M6 remain in their appropriate unstarted/blocked states.

---

## Chunk M3-10 Implementation Record

- **Status:** `COMMITTED`
- **Summary:**
  - Implemented and formalized the Permanent Red Zone Demarcation Engine for Member 3 (Risk / GIS / Data) per project lead approval (**Option 1 Formalization**).
  - Evaluates settlement/location-level geophysical observations and multi-hazard risk indicators to demarcate **analytical candidate / proposed** Permanent Red Zones without replacing or recomputing the M3-06 composite risk engine.
  - **Formalized Geophysical Triggers (Option 1):**
    ```text
    active_subsidence == True
    OR
    (
        slope_deg >= regional_profile.min_slope_deg
        AND
        historical_landslide_count >= regional_profile.min_historical_landslides
    )
    ```
    - Loaded dynamically from `RegionProfile.red_zone_thresholds.permanent_criteria`.
    - Profile criteria: Himalayan Pilot (`slope >= 35.0°`, `historical_landslides >= 1`), Riverine Template (`slope >= 15.0°`, `historical_landslides >= 0`), Coastal Template (`slope >= 10.0°`, `historical_landslides >= 0`).
  - **Relationship to Upstream M3-07 Composite Risk Classification:**
    - Upstream `CRITICAL` risk ($Risk \ge 85.0$) corroborates candidate permanent red zones.
    - `SAFE` or `MODERATE` combined with steep slope **without active subsidence** is explicitly designated as `MONITOR` status rather than a proposed permanent red zone.
    - Confirmed active subsidence triggers candidate status regardless of composite risk score due to immediate physical ground instability and fissure hazard.
  - **Spatial Representation & Geometry Normalization:**
    - Output geometries strictly normalized to valid Shapely `MultiPolygon` in **EPSG:4326 (SRID 4326)**, matching the `RedZone.geometry` database column type.
    - Polygonal inputs (`Polygon`, `MultiPolygon`, GeoJSON dict) are normalized directly and topology-repaired via `shapely.make_valid`.
    - Point-based village locations are converted into spatial perimeters using a **geodesic circular buffer** projected through metric azimuthal equidistant projection (`pyproj.CRS("+proj=aeqd ...")`) based on the profile's configured `hazard_buffer_m` (500.0 m in Himalayan pilot). Arbitrary degree-based buffers are strictly forbidden.
    - Ellipsoidal geodesic area is computed in square kilometers using WGS84 ellipsoid parameters (`pyproj.Geod(ellps="WGS84")`).
  - **Overlapping Zones & Dissolution:**
    - Continuous overlapping candidate perimeters are dissolved using graph-based spatial intersection and Shapely `unary_union`.
    - Dissolved candidates retain full auditability and provenance without loss: contributing village IDs (`contributing_village_ids`), individual trigger audits (`trigger_audits`), and source provenance records (`source_village_provenance`).
  - **Safety-Critical Missing Data Safety Rule:**
    - Missing or unavailable required geophysical indicators (`slope_deg`, `historical_landslide_count`, or `active_subsidence`) are **never defaulted to safe or 0**.
    - Strict return of `RedZoneStatus.INSUFFICIENT_DATA` with `is_candidate = False`, `geometry = None`, and explicit audit enumeration of `missing_indicators`.
    - Input domain validation strictly rejects `NaN`, $\pm\infty$, negative slopes, slopes $> 90^\circ$, or negative landslide counts (`InvalidGeophysicalDataError`).
  - **Governance Invariants:**
    - Output represents `PROPOSED` / candidate zones only.
    - Candidates strictly enforce `is_active = False`, `declared_by_officer_id = None`, and `declared_at = None`. Pydantic validators strictly raise errors if an algorithmic output attempts to set these officer-declaration fields.
    - Statutory legal declaration belongs exclusively to the downstream officer review workflow (Chunk M6-08).
  - **Review Finding Correction (DangerLevel Invariant & Dissolve Fallback Removal):**
    - Corrected unapproved trigger-based `DangerLevel` assignments (`landslide-only -> CRITICAL`, `subsidence -> UNINHABITABLE`, `MONITOR -> VERY_HIGH`).
    - Removed unapproved `or DangerLevel.UNINHABITABLE` fallback from `dissolve_overlapping_candidates` in `geometry.py`.
    - Dissolve strictly adheres to resolution order: 1) explicit caller `default_danger_level`, 2) constituent proposed candidate `danger_level`, 3) raise explicit `RedZoneConfigError` if neither is provided.
    - Engine strictly assigns profile-configured `default_danger_level` (from `profile.red_zone_thresholds.permanent_criteria.default_danger_level`) for `PROPOSED` candidates, and `danger_level = None` for non-candidate observations (`MONITOR`, `INSUFFICIENT_DATA`, `NOT_DEMARCATED`).
- **Files Created:**
  - `backend/app/core/risk/red_zone/__init__.py` (Package exports)
  - `backend/app/core/risk/red_zone/contracts.py` (Data contracts, schemas, enums, Pydantic validators)
  - `backend/app/core/risk/red_zone/errors.py` (Domain exception hierarchy)
  - `backend/app/core/risk/red_zone/geometry.py` (GIS geodesic buffering, MultiPolygon normalization, dissolve engine)
  - `backend/app/core/risk/red_zone/engine.py` (PermanentRedZoneEngine core candidate demarcation coordinator)
  - `backend/app/core/risk/red_zone/README.md` (Technical documentation, Option 1 rules, governance boundaries)
  - `backend/tests/test_permanent_red_zones.py` (43 unit and regression tests covering all 15 specification categories and danger-level invariants)
- **Files Modified:**
  - `backend/app/core/risk/__init__.py` (Re-exported M3-10 red zone engine and contracts)
  - `PROJECT_STATE.md` (Updated registry status to AWAITING_REVIEW, recorded implementation details and test metrics)
- **Files Removed:** None
- **Commands Executed & Results:**
  - `wsl -e docker exec rakshakgis-backend pytest tests/test_permanent_red_zones.py -v` -> Exited 0, 43 passed in 1.80s (100%)
  - `wsl -e docker exec rakshakgis-backend pytest tests/test_risk_normalization.py tests/test_risk_computation.py tests/test_risk_classification.py tests/test_risk_explainability.py tests/test_vulnerability_scoring.py tests/test_profiles.py tests/test_permanent_red_zones.py -v` -> Exited 0, 161 passed in 2.69s (100% risk subsystem pass)
  - `wsl -e docker exec rakshakgis-backend pytest tests -v` -> Exited 0, 327 passed, 4 warnings in 9.09s (100% full backend regression pass)
- **Test Coverage Mapping (All 15 Required Categories + Invariants):**
  1. Active subsidence triggers candidate: `test_active_subsidence_triggers_candidate`
  2. Slope + historical landslide thresholds trigger candidate: `test_slope_and_historical_landslides_trigger_candidate`, `test_compound_danger_when_both_triggers_active`
  3. Values exactly at thresholds: `test_values_exactly_at_thresholds_trigger_candidate`
  4. Values below thresholds do not trigger: `test_values_below_thresholds_do_not_trigger`
  5. CRITICAL risk corroborates candidate: `test_critical_risk_corroborates_candidate`, `test_critical_risk_with_subsidence`
  6. SAFE/MODERATE + steep slope without subsidence becomes MONITOR: `test_safe_or_moderate_with_steep_slope_becomes_monitor`, `test_safe_or_moderate_with_active_subsidence_still_triggers_candidate`
  7. Missing slope yields INSUFFICIENT_DATA: `test_missing_slope_yields_insufficient_data`, `test_strict_mode_raises_on_missing_slope`
  8. Missing landslide count yields INSUFFICIENT_DATA: `test_missing_landslide_count_yields_insufficient_data`
  9. Missing subsidence not converted to false/safe: `test_missing_subsidence_yields_insufficient_data`
  10. Point input produces valid MultiPolygon via configured 500m buffer: `test_point_input_produces_valid_multipolygon`, `test_create_geodesic_buffer_directly`
  11. Polygon/MultiPolygon normalized correctly: `test_polygon_input_normalized_to_multipolygon`, `test_normalize_to_multipolygon_handles_geojson_dict`
  12. Overlapping candidates dissolve without losing provenance: `test_overlapping_candidates_dissolve_preserving_provenance`, `test_non_overlapping_candidates_remain_separate`
  13. Output remains EPSG:4326 / SRID 4326: `test_geometry_srid_is_4326`
  14. Candidate output enforces governance invariants: `test_governance_invariants_candidate_not_officer_declared`, `test_governance_validation_rejects_active_flag`, `test_governance_validation_rejects_officer_declaration`
  15. Deterministic repeated inputs produce identical result: `test_strict_determinism_across_repeated_evaluations`
  16. Multi-region profile threshold tests: `test_riverine_template_thresholds`, `test_coastal_template_thresholds`
  17. Input validation & error cases: `test_invalid_negative_slope`, `test_invalid_slope_exceeding_90`, `test_invalid_negative_landslides`, `test_invalid_nan_slope`, `test_invalid_buffer_distance_raises`, `test_invalid_latitude_for_geodesic_buffer`
  18. DangerLevel contract and configuration invariants: `test_no_unapproved_danger_level_mappings_across_triggers`, `test_danger_level_strictly_respects_custom_configured_profile`, `test_monitor_status_has_no_danger_level_assigned`, `test_dissolved_candidates_preserve_configured_danger_level_without_trigger_selection`, `test_dissolve_rejects_missing_danger_level_when_neither_source_available`, `test_dissolve_single_candidate_rejects_missing_danger_level_when_neither_source_available`, `test_dissolve_adheres_to_strict_resolution_order`
- **Scope Boundaries & Invariants Preserved:**
  - Status marked `AWAITING_REVIEW` (not marked VERIFIED or COMMITTED).
  - Dynamic Red Zones (M3-11) and Relocation Priority (M3-12) left completely untouched.
  - Officer legal declaration workflow remains in M6-08.
  - Zero LLM usage; 100% deterministic algorithms.

---

## Chunk M3-11 Implementation Record

- **Status:** `COMMITTED`
- **Architectural & Formalization Decisions:**
  - **Dynamic Red Zone Demarcation Subsystem:**
    - Established `DynamicRedZoneEngine` in `backend/app/core/risk/red_zone/dynamic_engine.py` representing temporary, event-driven hazard demarcation separately from M3-10 permanent geophysical red zones.
    - Explicit 3-state evaluation model: `NO_TRIGGER`, `TRIGGERED`, `INSUFFICIENT_DATA` (represented by typed `DynamicTriggerStatus` enum).
    - Missing or unavailable observations strictly yield `INSUFFICIENT_DATA` (never coerced to safe or 0.0). In strict mode (`strict=True`), raises `InsufficientGeophysicalDataError`.
    - **Threshold-Unavailable Semantic Correction:** If an observation exists but its required dynamic threshold is unavailable/unconfigured in the regional profile (e.g. unconfigured `water_level_m_above_danger`, `debris_volume_cu_m`, or other absent thresholds), the engine cannot evaluate trigger status and strictly returns `DynamicTriggerStatus.INSUFFICIENT_DATA` with `danger_level = None`, `is_candidate = False`, and an explicit audit/explainability note identifying the missing threshold configuration. An unconfigured threshold is NEVER treated as `NO_TRIGGER`, `0`, `SAFE`, a fabricated/default threshold, or any danger level. In strict mode, raises `InsufficientGeophysicalDataError`.
    - `NO_TRIGGER` strictly means the trigger was evaluated against an available threshold and did not fire (`value < threshold`).
    - Input values of `NaN`, $\pm\infty$, or values violating physical domains strictly raise `InvalidGeophysicalDataError`.
  - **Profile-Driven Regional Trigger Resolution:**
    - Engine contains zero hardcoded regional threshold constants. Thresholds strictly resolve from `RegionProfile` (`red_zone_thresholds.dynamic_triggers` and `site_capacity_assumptions.hazard_buffer_m`).
    - Tested across Himalayan Pilot (64.5 mm rain, 6.0 MMI seismic, 25.0° slope, 500m buffer), Coastal Template (80.0 mm rain, 1500m buffer), and Riverine Template (75.0 mm rain, 1000m buffer).
    - Demonstrated that changing profile thresholds changes dynamic trigger decisions without modifying engine code.
  - **Supported Dynamic Indicators:**
    - 24h rainfall precipitation (`rainfall_24h_mm`).
    - Seismic intensity (`seismic_intensity_mmi`).
    - Terrain slope angle (`slope_deg`).
    - Hydrological flood water level above danger (`water_level_m_above_danger`).
    - Landslide debris volume (`debris_volume_cu_m`).
    - Compound triggers (e.g. concurrent heavy rainfall exceedance on steep slope).
  - **Deterministic Boundary Behavior:**
    - Aligns with IMD standard (`is_heavy_rain >= 64.5 mm`).
    - Explicit, typed `ComparisonOperator` (`>=`, `>`, `<`, `<=`, `==`) with boundary tests covering `value < T`, `value == T`, `value > T`.
  - **Spatial Geometry & Overlap Dissolution:**
    - Point-based sensor and settlement observations buffered via metric geodesic circular buffer (`create_geodesic_buffer`).
    - Polygon observations normalized to valid `MultiPolygon` in EPSG:4326 (SRID 4326).
    - Missing location data safely produces `geometry = None` without fabricating polygons.
    - Multiple overlapping dynamic candidates deterministically dissolved via `shapely.ops.unary_union`, preserving all contributing observation IDs, village IDs, and source provenance records.
  - **Strict Governance & DangerLevel Invariants:**
    - Output envelopes are candidate proposals only (`is_temporary = True`, `is_candidate = True` iff `TRIGGERED`, `is_active = False`, `declared_by_officer_id = None`, `declared_at = None`).
    - Candidate outputs strictly assign profile `default_danger_level` when `TRIGGERED`; `danger_level = None` when `NO_TRIGGER` or `INSUFFICIENT_DATA`. Never invents or escalates danger levels.
- **Files Created:**
  - `backend/app/core/risk/red_zone/dynamic_contracts.py` (Typed schemas, enums, `DynamicThresholdConfig`, `DynamicHazardObservation`, `DynamicRedZoneCandidate`, `DynamicRedZoneExplainability`)
  - `backend/app/core/risk/red_zone/dynamic_engine.py` (Core `DynamicRedZoneEngine` candidate evaluation coordinator and overlap dissolution)
  - `backend/tests/test_dynamic_red_zones.py` (38 unit, boundary, and threshold-unavailable regression tests covering all 15 required categories)
- **Files Modified:**
  - `backend/app/core/risk/red_zone/__init__.py` (Re-exported dynamic red zone engine and contracts)
  - `backend/app/core/risk/red_zone/README.md` (Updated documentation detailing permanent vs dynamic separation, profile resolution, indicators, threshold-unavailable semantics, missing data policy, and governance boundaries)
  - `PROJECT_STATE.md` (Updated registry status to AWAITING_REVIEW, documented implementation details, semantic correction, and test metrics)
- **Files Removed:** None
- **Commands Executed & Results:**
  - `wsl -e docker exec rakshakgis-backend pytest tests/test_dynamic_red_zones.py -v` -> Exited 0, 38 passed in 2.72s (100%)
  - `wsl -e docker exec rakshakgis-backend pytest tests/test_permanent_red_zones.py -v` -> Exited 0, 43 passed in 2.50s (100% M3-10 regression pass)
  - `wsl -e docker exec rakshakgis-backend pytest tests -v` -> Exited 0, 365 passed, 4 warnings in 14.53s (100% full backend regression pass)
- **Scope Boundaries & Invariants Preserved:**
  - Status marked `AWAITING_REVIEW` (not marked VERIFIED or COMMITTED).
  - Relocation Priority Scoring (M3-12) left completely untouched.
  - Scenario simulator integration (M4-06) and real-time alerts UI (M6-05) left completely untouched.
  - Officer legal declaration workflow remains in M6-08.
  - Zero LLM usage; 100% deterministic algorithms.

---

## Chunk M3-12 Implementation Record

- **Status:** `COMMITTED`
- **Architectural & Formalization Decisions:**
  - **Relocation Priority Scoring Subsystem:**
    - Established `RelocationPriorityEngine` in `backend/app/core/risk/relocation_priority/engine.py` evaluating settlement relocation urgency across 5 authoritative factors.
    - Authoritative Formula:
      $$\text{Relocation Priority} = 0.40 \times \text{Risk} + 0.25 \times \text{Exposure} + 0.20 \times \text{Vulnerability} + 0.10 \times \text{Historical Impact} + 0.05 \times \text{Accessibility}$$
    - Weights and band cutoffs resolve dynamically from `RegionProfile` (`relocation_priority_parameters.weights` and `relocation_priority_parameters.cutoffs`) with zero hardcoded numerical constants in calculation logic.
  - **Authoritative Priority Bands:**
    - `[80.0, 100.0]` -> `IMMEDIATE`
    - `[60.0, 80.0)`  -> `SHORT_TERM`
    - `[40.0, 60.0)`  -> `MEDIUM_TERM`
    - `[0.0, 40.0)`   -> `MONITOR`
  - **Factor Normalization & Range Guards:**
    - All 5 factors normalized to $[0.0, 100.0]$.
    - Mathematical score clamped deterministically to $[0.0, 100.0]$.
    - Negative values ($< 0.0$), values $> 100.0$, `NaN`, $\pm\infty$, and boolean types strictly raise `InvalidPriorityDataError`.
  - **Safety-Critical Missing Data Semantics:**
    - If any required factor is missing or unavailable, the engine strictly returns `RelocationPriorityStatus.INSUFFICIENT_DATA` with `priority_score = None`, `priority_band = None`, and `missing_factors` populated with the missing factor names.
    - Missing factor data is **never** assumed safe, never defaulted to 0, and never silently classified as `MONITOR`.
    - In strict mode (`strict=True`), missing factor data raises `InsufficientPriorityDataError`.
  - **Explainability & Auditability:**
    - Full factor breakdown with normalized score, weight, weighted contribution ($w_i \times v_i$), percentage share ($\frac{w_i \times v_i}{\text{score}} \times 100\%$), symbol, display name, and descriptive audit narrative.
    - Identification of primary urgency driver and its contribution.
    - Audit trail includes formula string, decision reason, profile metadata, and clamping status.
  - **Upstream Contract Consumption & Provenance:**
    - Consumes `CompositeRiskResult` (M3-06), `DemographicExposureResult` (M3-09), and `SocialVulnerabilityResult` (M3-09) directly or via numeric/dictionary inputs.
    - Aggregates provider provenance records across all input sources.
    - Incomplete or failed upstream calculations (`status != COMPUTED` or `status != SCORED`) are safely treated as missing data (`INSUFFICIENT_DATA`).
  - **Strict Governance Invariants:**
    - Relocation priority scores represent decision-support recommendations for District Officer and Rehabilitation Committee review.
    - `is_automatic_evacuation = False` strictly enforced (Pydantic model validator prevents setting `is_automatic_evacuation=True`).
    - Proposal only: `is_actionable_proposal = True` when scored, `False` when insufficient data.
    - Explicit governance notice embedded in both result envelope and explainability record.
    - 100% deterministic, zero LLM dependencies.
- **Files Created:**
  - `backend/app/core/risk/relocation_priority/__init__.py` (Package exports)
  - `backend/app/core/risk/relocation_priority/contracts.py` (Typed schemas, enums, `RelocationPriorityWeightsConfig`, `PriorityScoreBandsConfig`, `RelocationPriorityInput`, `PriorityFactorDetail`, `RelocationPriorityExplainability`, `RelocationPriorityResult`)
  - `backend/app/core/risk/relocation_priority/engine.py` (Core `RelocationPriorityEngine` evaluation coordinator, factor coercion, clamping, band classification, and batch evaluation)
  - `backend/app/core/risk/relocation_priority/errors.py` (Domain exception hierarchy: `RelocationPriorityError`, `InvalidPriorityDataError`, `InsufficientPriorityDataError`, `PriorityConfigError`)
  - `backend/app/core/risk/relocation_priority/README.md` (Subsystem documentation, mathematical formula, priority bands, explainability breakdown, governance boundaries)
  - `backend/tests/test_relocation_priority.py` (47 unit, boundary, and regression tests covering all 21 required test categories including zero-score behavior and hand-calculated formula verification)
- **Files Modified:**
  - `backend/app/core/risk/__init__.py` (Re-exported relocation priority engine, contracts, and exceptions)
  - `backend/app/core/risk/relocation_priority/engine.py` (Refined zero-score explainability: primary_driver is None when all contributions are 0; honest 0.0% contribution percentages without division-by-zero)
  - `PROJECT_STATE.md` (Updated registry status to AWAITING_REVIEW, documented implementation details, and updated test metrics)
- **Files Removed:** None
- **Commands Executed & Results:**
  - `wsl -e docker exec rakshakgis-backend pytest tests/test_relocation_priority.py -v` -> Exited 0, 47 passed in 2.36s (100%)
  - `wsl -e docker exec rakshakgis-backend pytest tests -v` -> Exited 0, 412 passed, 4 warnings in 14.99s (100% full backend regression pass)
- **Scope Boundaries & Invariants Preserved:**
  - Status marked `COMMITTED` following independent review verification.
  - Candidate relocation matching and capacity assignment (M4-04) left completely untouched.
  - Relocation routing and evacuation route analysis (M4-05) left completely untouched.
  - Officer approval and relocation workflow left completely untouched.
  - Zero LLM usage; 100% deterministic algorithms.

---

## Chunk M3-13 Implementation Record

- **Status:** `COMMITTED` (Commit: `a14d46b`)
- **Files Created:**
  - `backend/app/core/telemetry/__init__.py` (Subpackage re-exports for telemetry and freshness subsystem)
  - `backend/app/core/telemetry/contracts.py` (Contracts: FreshnessStatus, FreshnessThresholds, FreshnessEvaluation, SourceTelemetrySummary, IngestionRunSummary, TelemetryOverview)
  - `backend/app/core/telemetry/errors.py` (TelemetryError, DataSourceNotFoundError, InvalidTimestampError, TelemetryConfigError)
  - `backend/app/core/telemetry/evaluator.py` (Deterministic freshness evaluation engine: clock-skew guards, negative age clamping, provider availability gates, category thresholds)
  - `backend/app/core/telemetry/service.py` (TelemetryService: provider registry auto-sync, database DataSource and DataIngestionRun management, secret sanitization, health probes)
  - `backend/app/core/telemetry/README.md` (Operational architecture, freshness invariants, state machine, and configuration documentation)
  - `backend/app/schemas/telemetry.py` (Pydantic API models: FreshnessEvaluationRead, DataSourceTelemetryRead, DataSourceDetailRead, DataIngestionRunRead, TelemetryOverviewRead)
  - `backend/app/api/v1/telemetry.py` (FastAPI router: GET /overview, GET /sources, GET /sources/{id}, GET /sources/{id}/runs, POST /sources/{id}/probe)
  - `backend/tests/test_telemetry.py` (19 automated unit and API integration tests covering all 16 prompt requirements)
- **Files Modified:**
  - `backend/app/api/routes.py` (Registered telemetry_router under /telemetry prefix)
  - `PROJECT_STATE.md` (Updated registry status to COMMITTED, documented implementation details, and updated test metrics)
- **Files Removed:** None
- **Database / Migration Changes:** None (Reused existing `data_sources` and `data_ingestion_runs` tables created in initial migration)
- **Commands Executed & Results:**
  - `wsl -e docker exec rakshakgis-backend pytest tests/test_telemetry.py -v` -> Exited 0, 19 passed, 2 warnings in 1.40s (100%)
  - `wsl -e docker exec rakshakgis-backend pytest tests -v` -> Exited 0, 431 passed, 4 warnings in 17.07s (100% full backend regression pass)
- **Scope Boundaries & Invariants Preserved:**
  - Telemetry layer strictly decoupled from numerical risk engines, Red Zone demarcation, and relocation algorithms.
  - Zero secrets or credentials leaked in logs or API responses (sanitization patterns scrub Bearer tokens, passwords, API keys).
  - Conservative freshness rules: missing timestamps -> UNKNOWN (never fresh); future timestamps beyond 60s tolerance -> CLOCK_SKEW; unavailable providers -> UNAVAILABLE; failed ingestion -> not fresh.
  - Synthetic/demo provenance explicitly maintained (`is_synthetic = True`, disclaimer preserved).
  - Zero LLMs, zero random heuristics.

---

## Chunk M4-04 Implementation Record

- **Status:** `COMMITTED` (Commit: `b4e984ebc6a567e149881079d36c2580525ab72f`)
- **Files Created:**
  - `backend/app/core/relocation/matching/__init__.py` (Subpackage re-exports: `RelocationMatchingEngine`, contracts, error hierarchy, ranking utilities)
  - `backend/app/core/relocation/matching/contracts.py` (Domain models: `AssignmentStatus`, `RejectionReasonCode` formalizing `LOW_SUITABILITY` for sites passing hard constraints but with overall score $< 40.0$, `SITE_UNAVAILABLE`, `MatchingAlgorithmType`, `VillageDemandInput`, `MatchingSiteCandidate`, `CandidateEvaluationAudit`, `VillageAssignmentResult`, `RelocationMatchingResult`)
  - `backend/app/core/relocation/matching/errors.py` (Exception hierarchy: `RelocationMatchingError`, `InvalidMatchingInputError`, `MatchingConfigurationError`, `SiteCapacityExhaustedError`)
  - `backend/app/core/relocation/matching/ranking.py` (Deterministic scoring: Haversine great-circle distance $R = 6371.009\text{ km}$, exact linear proximity $\max(0.0, 100.0 - 2.0 \cdot d_{\text{km}})$ clamped to $[0, 100]$, exact rank score $0.70 \cdot \text{suitability} + 0.30 \cdot \text{proximity}$ with missing-coordinate fallback $\text{rank\_score} = \text{suitability}$, exact deterministic tie-break tuple $(-\text{rank\_score}, -\text{suitability\_score}, \text{distance\_km}, \text{str}(\text{site\_id}))$)
  - `backend/app/core/relocation/matching/engine.py` (Deterministic greedy matching engine implementing 6-step flow: priority ordering, demand validation, M4-02 & M4-03 constraint filtering, ranking, capacity reservation, unassigned fallback)
  - `backend/app/core/relocation/matching/README.md` (Operational architecture, exact ranking formula, Haversine distance, pure evaluation vs persistence separation, explainability, rejection taxonomy, future OR-Tools boundary)
  - `backend/app/schemas/relocation.py` (Pydantic API schemas: `RelocationMatchingRequest`, `RelocationAssignmentCreate`, `RelocationAssignmentBatchCreate`, `RelocationAssignmentRead`)
  - `backend/app/api/v1/relocation.py` (FastAPI router: `POST /match` pure evaluation with zero DB mutations, `POST /assignments` & `/batch` persistence, `GET /assignments` with authentication via `get_current_user`, filtering, deterministic ordering by `(assigned_at.desc(), id.asc())`, and pagination, `GET /assignments/{id}`)
  - `backend/tests/test_m4_04_matching.py` (28 automated unit and API integration tests covering all 27 requirements including 50-run repeated determinism, pure evaluation zero-mutation verification, exact linear proximity, exact tie-breaking, micro rank score floating point precision, positive capacity below 20 safety validation, and GET filtering/pagination)
- **Files Modified:**
  - `backend/app/api/routes.py` (Registered `relocation_router` under `/relocation` prefix)
  - `PROJECT_STATE.md` (Maintained status as AWAITING_REVIEW, documented correction pass details, and updated test metrics)
- **Files Removed:** None
- **Database / Migration Changes:** None (Reused existing `relocation_assignments` table created in initial migration M2-03)
- **Commands Executed & Results:**
  - `docker exec rakshakgis-backend pytest tests/test_m4_04_matching.py -v` -> Exited 0, 28 passed, 2 warnings in 1.79s (100%)
  - `docker exec rakshakgis-backend pytest tests/test_m4_03_capacity.py tests/test_site_suitability.py tests/test_sites.py -v` -> Exited 0, 50 passed, 3 warnings in 6.34s (100%)
  - `docker exec rakshakgis-backend pytest tests -v` -> Exited 0, 459 passed, 4 warnings in 26.97s (100% full backend regression pass)
  - `git diff --check` -> Exited 0 (Clean)
- **Scope Boundaries & Invariants Preserved:**
  - Deterministic greedy algorithm: no OR-Tools, ILP, ML, LLMs, or randomized assignment.
  - Strict descending priority ordering of villages with deterministic tie-breaking (village ID).
  - Validation of non-negative, finite household demand; zero silent invention.
  - Strict integration with M4-02 site suitability hard safety constraints and M4-03 carrying capacity weakest-link model.
  - Critical capacity dimensions missing or unknown are never treated as unlimited; rejected with `UNKNOWN_CAPACITY`.
  - Dynamic capacity reservation tracked across allocations without negative remainder or unintended DB mutations.
  - Clear separation between matching recommendation calculation (`POST /api/v1/relocation/match`) and assignment persistence (`POST /api/v1/relocation/assignments`).
  - Explainability contract populated for all evaluated sites per village including rejection reason codes and capacity margins.
  - Evacuation routing (M4-05) and scenario simulation (M4-06) left completely untouched.

---

## Chunk M4-05 Implementation Record

- **Status:** `COMMITTED` (Commit: `93e62e6392e0903aefc034a9cd13d4ad18e0c1ec`)
- **Scope:** Evacuation & Access Routing Engine (decision-support routing subsystem between village origins and assigned candidate relocation sites)
- **Files Created:**
  - `backend/app/core/relocation/routing/__init__.py` (Subpackage exports: `EvacuationRoutingEngine`, `HazardAwareRouteEvaluator`, `BaseRoadNetworkProvider`, `SyntheticHimalayanRoadProvider`, `RoadNetwork`, contracts, errors)
  - `backend/app/core/relocation/routing/contracts.py` (Domain models: `RouteStatus`, `SegmentHazardStatus`, `RouteType`, `HazardExposureDetail`, `RouteSegment`, `RouteExplainability`, `RouteResult`, `EvacuationRoutingResult`, `RouteQuery`)
  - `backend/app/core/relocation/routing/errors.py` (Exception hierarchy: `RoutingError`, `InvalidRouteInputError`, `InsufficientRoutingDataError`, `NoFeasibleRouteError`, `RouteBlockedError`)
  - `backend/app/core/relocation/routing/network.py` (Spatial network graph: `RoadNode`, `RoadSegmentEdge`, `RoadNetwork` with deterministic adjacency and Haversine snapping, `BaseRoadNetworkProvider`, `SyntheticHimalayanRoadProvider` featuring Valley Highway NH-7 corridor and Upper Ridge Bypass)
  - `backend/app/core/relocation/routing/hazards.py` (`HazardAwareRouteEvaluator`: dynamic buffer proximity, severity-based penalty multipliers, hard cut-off blockage detection for critical highway obstructions, and missing-hazard data safety tracking)
  - `backend/app/core/relocation/routing/engine.py` (`EvacuationRoutingEngine`: deterministic Dijkstra shortest-path with exact tuple tie-breaking `(round(cost, 6), hop_count, str(node_id))`, hard blocked segment omission, edge-penalty diversion for distinct alternative route discovery, continuous LineString coordinate assembly, and comprehensive explainability generation)
  - `backend/app/core/relocation/routing/README.md` (Subsystem documentation: architecture, cost formulations, hazard penalties, tie-breaking, missing data policy, explainability contract, demo data, and future OSM/routing provider replacement)
  - `backend/app/schemas/routing.py` (Pydantic schemas: `GeoJSONLineString`, `RouteGenerateRequest`, `RouteCreate`, `RouteRead`)
  - `backend/app/api/v1/routing.py` (FastAPI router: `POST /generate` pure calculation with zero DB mutation, `POST /` explicit persistence for `ADMIN`/`DISTRICT_OFFICER`, `GET /` list with filtering & pagination, `GET /{id}` retrieval)
  - `backend/tests/test_m4_05_routing.py` (35 automated tests covering validation, basic routing, hazard avoidance, missing data invariants, alternative routes, M4-04 integration, 50-run determinism, and API endpoints)
- **Files Modified:**
  - `backend/app/api/routes.py` (Registered `routing_router` under `/routes` prefix)
  - `PROJECT_STATE.md` (Updated Chunk M4-05 status to `AWAITING_REVIEW`, added Implementation Record, and refreshed test metrics)
- **Files Removed:** None
- **Database / Migration Changes:** None (Reused existing `routes` table created in initial migration M2-03)
- **Commands Executed & Results:**
  - `docker exec rakshakgis-backend pytest tests/test_m4_05_routing.py -v` -> Exited 0, 35 passed, 3 warnings in 4.49s (100%)
  - `docker exec rakshakgis-backend pytest tests/test_m4_04_matching.py tests/test_m4_03_capacity.py tests/test_site_suitability.py tests/test_sites.py -v` -> Exited 0, 78 passed, 3 warnings in 7.27s (100% M4 regression pass)
  - `docker exec rakshakgis-backend pytest tests -v` -> Exited 0, 494 passed, 5 warnings in 46.17s (100% full backend regression pass)
  - `git diff --check` -> Exited 0 (Clean)
- **Scope Boundaries & Invariants Preserved:**
  - Decision-support tool only; not an autonomous evacuation dispatcher or statutory evacuation order.
  - Hard safety constraint: strictly omit `BLOCKED` hazard road segments from the primary safe route.
  - Dynamic hazard penalties for caution/hazardous segments (`PENALIZED`).
  - Strict missing-data safety: "Unknown is NOT safe" (missing network -> `INSUFFICIENT_DATA`, missing speed -> `estimated_time_minutes = None`, missing hazard data tracked in explainability uncertainty notes).
  - Deterministic tie-breaking: `(round(cost, 6), segment_count, str(node_id))` across graph traversal.
  - Alternative route generation via deterministic edge-penalty diversion; report `NO_FEASIBLE_ALTERNATIVE` if only a single physical corridor exists or alternatives are blocked.
  - Pure calculation vs persistence boundary: `POST /api/v1/routes/generate` never mutates the database.

---

## Chunk M4-06 Implementation Record

- **Status:** `COMMITTED` (Commit: `feat(m4): integrate scenario simulator pipeline`)
- **Scope:** Scenario Simulator Integration Backend (orchestrates 7 existing domain engines into a deterministic what-if simulation pipeline with baseline isolation, explicit input modifications, before-vs-after comparisons, explainability, and analytical decision-support provenance)
- **Files Created:**
  - `backend/app/core/scenarios/__init__.py` (Subpackage re-exports: `ScenarioSimulatorEngine`, `ScenarioComparator`, contracts, errors, definitions, inputs)
  - `backend/app/core/scenarios/contracts.py` (Domain models: `ScenarioType`, `ScenarioRunStatus`, `ScenarioParameters`, `VillageSimulationInput`, `SiteSimulationInput`, stage results for all 7 engines, `ScenarioComparison`, `ScenarioSimulationOutput`)
  - `backend/app/core/scenarios/errors.py` (Exception hierarchy: `ScenarioError`, `InvalidScenarioParameterError`, `UnknownScenarioTypeError`, `ScenarioExecutionError`, `InsufficientScenarioDataError`)
  - `backend/app/core/scenarios/definitions.py` (Canonical scenario definitions and default parameter registry: `NORMAL`, `EXTREME_RAINFALL` with 1.40x multiplier, `FLASH_FLOOD` with +35 flood exposure and region-agnostic parameters, `CAPACITY_CRISIS` with 50% capacity reduction)
  - `backend/app/core/scenarios/inputs.py` (Isolated in-memory input modification functions: `apply_scenario_modifications` deep copying objects with zero baseline mutation)
  - `backend/app/core/scenarios/comparison.py` (`ScenarioComparator`: exact numeric deltas for risk, red zones, relocation priority, carrying capacity, matching reallocations/unassigned, and routing diversions)
  - `backend/app/core/scenarios/engine.py` (`ScenarioSimulatorEngine`: orchestrates all 7 domain engines across baseline and scenario pipelines, with stage failure trapping and provenance marking)
  - `backend/app/core/scenarios/README.md` (Subsystem documentation: architecture, execution pipeline, canonical scenarios, input modifications, comparison semantics, provenance, zero duplicate logic, and determinism)
  - `backend/app/schemas/scenarios.py` (Pydantic API schemas: `ScenarioDefinitionRead`, `ScenarioCreate`, `ScenarioRead`, `ScenarioRunRequest`, `ScenarioRunRecordRead`)
  - `backend/app/api/v1/scenarios.py` (FastAPI router: `GET /` list scenarios, `POST /` create custom scenario for `ADMIN`/`DISTRICT_OFFICER`, `GET /{id}`, `POST /run` pure simulation with optional persistence, `GET /runs/{id}`)
  - `backend/tests/test_m4_06_scenarios.py` (31 automated unit, integration, and API tests covering all 48 test cases including 20-run determinism, baseline isolation, real engine propagation, error handling, region-agnostic checks, and synthetic Himalayan pilot demonstration)
- **Files Modified:**
  - `backend/app/api/routes.py` (Registered `scenarios_router` under `/scenarios` prefix)
  - `backend/app/core/profiles/models.py` (Added `flood_prone_corridor_segments` to `ScenarioBounds`)
  - `backend/app/core/profiles/himalayan.py` (Configured `flood_prone_corridor_segments=["SEG-VALLEY-02"]` on `HIMALAYAN_PILOT_PROFILE`)
  - `backend/app/core/relocation/routing/network.py` (Added `get_default_road_network_provider()`)
  - `backend/app/core/relocation/routing/__init__.py` (Exported `get_default_road_network_provider`)
  - `PROJECT_STATE.md` (Updated Chunk M4-06 status to `COMMITTED`, added Implementation Record, and refreshed test metrics)
- **Files Removed:** None
- **Database / Migration Changes:** None (Reused existing `scenarios` and `scenario_runs` tables created in initial migration M2-03)
- **Commands Executed & Results:**
  - `docker exec rakshakgis-backend pytest tests/test_m4_06_scenarios.py -v` -> Exited 0, 31 passed, 3 warnings in 7.96s (100%)
  - `docker exec rakshakgis-backend pytest tests/test_m4_05_routing.py tests/test_m4_04_matching.py tests/test_m4_03_capacity.py tests/test_site_suitability.py tests/test_sites.py -v` -> Exited 0, 113 passed, 4 warnings in 7.25s (100% M4 regression pass)
  - `docker exec rakshakgis-backend pytest tests -v` -> Exited 0, 525 passed, 6 warnings in 29.02s (100% full backend regression pass)
  - `git diff --check` -> Exited 0 (Clean)
- **Scope Boundaries & Invariants Preserved:**
  - Zero duplicate numerical logic: orchestrates existing M3/M4 domain services (`MultiHazardRiskEngine`, `RiskClassificationEngine`, `DynamicRedZoneEngine`, `RelocationPriorityEngine`, `SiteSuitabilityEngine`, `CarryingCapacityEngine`, `RelocationMatchingEngine`, `EvacuationRoutingEngine`).
  - Strict baseline isolation: in-memory deep copy of simulation inputs; zero silent mutation of database records (`villages`, `candidate_sites`, `relocation_assignments`, `routes`).
  - Deterministic evaluation: zero random numbers, zero runtime clock inputs in formulas; verified by 20 repeated runs across core scenarios.
  - Decision-support boundary: simulation outputs tagged with `SIMULATION` provenance and explicit governance notice; not official government forecasts or evacuation orders.

---

## Known Issues

1. **Untracked Host Virtual Environment:** `backend/venv/` exists locally on Windows host and is properly ignored by `.gitignore`. The Docker service isolates this via an anonymous volume (`/app/venv`).
2. **Frontend Foundation Established:** `frontend/` scaffolded with Next.js 14 App Router, TypeScript, Tailwind CSS, UI primitives, command center shell, and Vitest testing suite in Chunk M5-01. Backend API client and authentication UI scheduled for M5-02 and M5-03.

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
- Chunk M4-02 established multi-criteria site suitability engine (`app.core.relocation.suitability`) evaluating 9 criteria (30/20/10/10/10/5/5/5/5), pre-scoring hard constraint gates (slope, buffer, capacity), weighted water availability scoring (10%), structured explainability breakdown, and API endpoints (`/api/v1/sites/evaluate`, `/api/v1/sites/{id}/evaluate`, `/api/v1/sites/{id}/suitability`) with strict region profile validation.
- Chunk M4-03 established carrying capacity & infrastructure sizing engine (`app.core.relocation.capacity`) implementing authoritative weakest-link formula $\min(\text{housing}, \text{water}, \text{sanitation}, \text{healthcare}, \text{shelter})$, negative margin preservation, deterministic limiting factor identification, unknown capacity safety invariants, and API endpoints (`/api/v1/sites/capacity/evaluate`, `/api/v1/sites/{id}/capacity/evaluate`, `/api/v1/sites/{id}/capacity`).
- Chunk M3-01 established typed, immutable regional configuration system (`app.core.profiles`) with deterministic validation, registry resolver, Himalayan pilot profile, and future Riverine/Coastal templates.
- Chunk M3-02 established deterministic synthetic Himalayan pilot dataset (40 villages, 12 candidate relocation sites, 30 hazard events, seed 26191) with GeoJSON fixtures and Pydantic loader schemas.
- Chunk M3-03 established provider-adapter abstraction layer (`app.data.providers`) with typed contracts, exception hierarchy, registry, and deterministic mock adapters consuming M3-02 fixtures.
- Chunk M3-04 established data validation and ingestion pipeline (`app.data.ingestion`) with multi-stage validators, intra-batch deduplication, canonicalization, and deterministic `IngestionResult` envelopes.
- Chunk M3-05 established risk normalization engine (`app.core.risk.normalization`) transforming heterogeneous hazard observations to comparable 0.0 - 100.0 factors with M3-01 profile thresholds, clamping tracking, explainability metadata, and safety-critical missing/unknown handling.
- Chunk M3-06 established multi-hazard risk computation engine (`app.core.risk.computation`) implementing $Risk = 0.30H + 0.20F + 0.15R + 0.15S + 0.10D + 0.10V$, weighted explainability breakdown, strict $[0.0, 100.0]$ bounds, and safe missing-factor handling.
- Chunk M3-07 established risk classification and grading engine (`app.core.risk.classification`) evaluating authoritative risk bands (SAFE, MODERATE, HIGH, VERY_HIGH, CRITICAL) with explicit boundary transitions, explainability metadata, and strict rejection of invalid scores.
- Chunk M3-08 established risk explainability & factor contribution engine (`app.core.risk.explainability`) evaluating 6-factor decompositions ($w_i \times v_i$), percentage shares, deterministic contribution rankings, primary risk driver identification, M3-07 classification integration, and human-readable audit narratives with strict missing-data safety invariants.
- Chunk M5-01 established frontend application foundation (Next.js 14 App Router, React 18, TypeScript, Tailwind CSS), design system tokens aligning with backend Risk Bands and Relocation Priority Cutoffs, WCAG 2.1 AA accessible UI primitives (Button, Badge, RiskBadge, RelocationBadge, Card, MetricCard, Alert, StatusIndicator), command center operational layout shell (CommandHeader, Sidebar, StatusBar, AppLayout), and automated test suite (29 Vitest tests passing, 0 lint errors, production build verified).
- Chunk M3-09 established vulnerability & exposure scoring engine (`app.core.risk.vulnerability`) implementing demographic exposure with vulnerable group weightings ($P_{\text{eff}} = P + (m_E-1)E + (m_C-1)C + (m_{Dis}-1)D_{is}$) benchmarked to regional capacity, 4-dimensional social vulnerability aggregation (social, economic, structural, access isolation), conversion to M3-06 `FactorInput` and M3-05 `NormalizedFactorResult`, and strict missing-data safety invariants. Formalized under project-approved Option 1.
- Chunk M3-10 established permanent red zone demarcation engine (`app.core.risk.red_zone`) implementing Option 1 formalization: geophysical trigger (`active_subsidence == True` or compound `slope >= min_slope` & `landslides >= min_landslides`), M3-07 CRITICAL risk corroboration and SAFE/MODERATE + steep slope MONITOR designation, geodesic circular buffering for point villages via configured `hazard_buffer_m`, overlap dissolution with full provenance preservation, safety-critical missing data policy (never assumed safe), and strict governance invariants (`is_active = False`, `declared_by_officer_id = None`).
- Chunk M3-11 established dynamic red zone & threshold trigger engine (`app.core.risk.red_zone.dynamic_engine`) implementing real-time event-driven hazard demarcation (`rainfall_24h_mm`, `seismic_intensity_mmi`, `slope_deg`, `water_level_m_above_danger`, `debris_volume_cu_m`, compound triggers) strictly resolved from regional profiles with zero hardcoded constants, explicit 3-state evaluation (`NO_TRIGGER`, `TRIGGERED`, `INSUFFICIENT_DATA`), threshold-unavailable INSUFFICIENT_DATA safety semantics, geodesic circular buffering, overlap dissolution with provenance preservation, safety-critical missing data rejection, and governance invariants (`is_active = False`, analytical proposals only).
- Chunk M3-12 established relocation priority scoring engine (`app.core.risk.relocation_priority.engine`) implementing 5-factor priority formula $0.40R + 0.25E + 0.20V + 0.10H + 0.05A$ normalized to $[0.0, 100.0]$, profile-driven weights and band cutoffs (IMMEDIATE, SHORT-TERM, MEDIUM-TERM, MONITOR), full explainability factor breakdown with percentage contributions, upstream result envelope consumption (`CompositeRiskResult`, `DemographicExposureResult`, `SocialVulnerabilityResult`), strict missing data safety semantics (`INSUFFICIENT_DATA`), and strict governance invariants (`is_automatic_evacuation = False`, analytical proposal only).
- Chunk M3-13 established data source freshness & telemetry backend (`app.core.telemetry`) providing deterministic 5-state freshness evaluation (`FRESH`, `STALE`, `UNAVAILABLE`, `CLOCK_SKEW`, `UNKNOWN`), category-specific default freshness thresholds (Rainfall 1h, Flood 1h, Landslide 24h, Sensors 1h, Population 7d, Fallback 24h) and custom overrides, provider health integration with M3-03 `BaseDataProvider` and `ProviderRegistry`, automatic synchronization to PostgreSQL `DataSource` and `DataIngestionRun` tables, secret scrubbing from diagnostic logs, and REST API endpoints under `/api/v1/telemetry`.
- Chunk M4-04 established relocation matching & assignment engine (`app.core.relocation.matching`) implementing deterministic greedy village-to-site matching with descending priority processing, dynamic carrying capacity reservation across sequential assignments, M4-02 hard safety constraint gating, M4-03 weakest-link capacity enforcement, distance/suitability ranking, rejection audits, and REST API endpoints under `/api/v1/relocation` (`POST /match`, `POST /assignments`, `POST /assignments/batch`, `GET /assignments`, `GET /assignments/{id}`).
- Chunk M4-05 established evacuation & access routing engine (`app.core.relocation.routing`) implementing deterministic Dijkstra routing with exact tuple tie-breaking, hard safety blockage omission for cut-off road corridors, dynamic hazard proximity penalties, continuous LineString coordinate assembly, edge-penalty diversion for distinct alternative route discovery, explainability synthesis, and REST API endpoints under `/api/v1/routes` (`POST /generate` pure evaluation with zero DB mutations, `POST /` explicit persistence, `GET /` filtering & pagination, `GET /{id}`).
- Chunk M4-06 established scenario simulator integration backend (`app.core.scenarios`) orchestrating the 7 backend engines into an isolated what-if simulation pipeline supporting NORMAL, EXTREME_RAINFALL, FLASH_FLOOD, and CAPACITY_CRISIS with before-vs-after deltas, REST API endpoints under `/api/v1/scenarios` (`GET /`, `POST /`, `GET /{id}`, `POST /run`, `GET /runs/{id}`), and zero baseline mutation.
- Automated tests verified: 525 backend tests passed in container (100% clean); 29 frontend tests passed in Vitest.

---

## Last Updated

- **Timestamp:** 2026-09-06 03:45:00 IST
- **Updated By:** M4 (Scenario Simulator Integration Backend — Chunk M4-06 Committed)
- **Status Summary:** Chunk M4-06 COMMITTED; Chunk M4-05 COMMITTED; Chunk M4-04 COMMITTED; Chunk M4-03 COMMITTED; Chunk M4-02 COMMITTED; Chunk M4-01 COMMITTED; Chunk M3-13 COMMITTED; Chunk M3-12 COMMITTED; Chunk M3-11 COMMITTED; Chunk M3-10 COMMITTED; Chunk M3-09 COMMITTED; Chunk M3-08 COMMITTED; Chunk M5-01 VERIFIED; 31 focused M4-06 tests passed (48 test cases); 113 M4 regression tests passed; 525 total backend regression tests verified passing in container (100% clean); 29 frontend tests passed in Vitest. Next eligible chunks: M5-02, M5-03, M6-01, M6-04.
