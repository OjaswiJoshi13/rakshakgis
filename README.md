# RakshakGIS

> **SIH Problem Statement 26191** — AI-powered GIS platform for multi-hazard disaster risk assessment, dynamic Red Zone demarcation, village vulnerability profiling, and climate-resilient relocation planning.

---

## Overview

**RakshakGIS** is designed to provide actionable intelligence for disaster management authorities and district administration officers. It combines geospatial data analysis, deterministic multi-hazard risk modeling, vulnerability indices, and constrained relocation site suitability to support critical decision-making before, during, and after disasters.

---

## Architecture Overview

The system is structured across four primary layers:

```text
┌────────────────────────────────────────────────────────┐
│                   Frontend Layer                       │
│    Next.js / MapLibre GL GIS Canvas / Ops Dashboard    │
└───────────────────────────┬────────────────────────────┘
                            │ REST / GeoJSON
                            ▼
┌────────────────────────────────────────────────────────┐
│               Backend API & Core Engines               │
│          FastAPI (Python 3.11) + Pydantic              │
│  ┌──────────────────┐ ┌──────────────────────────────┐ │
│  │   Risk Engine    │ │  Relocation & Routing Engine │ │
│  └──────────────────┘ └──────────────────────────────┘ │
│  ┌──────────────────┐ ┌──────────────────────────────┐ │
│  │ Red Zone Engine  │ │ Adapters & Ingestion Pipeline│ │
│  └──────────────────┘ └──────────────────────────────┘ │
└───────────────────────────┬────────────────────────────┘
                            │ SQLAlchemy / GeoAlchemy2
                            ▼
┌────────────────────────────────────────────────────────┐
│               Spatial Database Engine                  │
│       PostgreSQL 16 + PostGIS 3.4 Spatial Database     │
└────────────────────────────────────────────────────────┘
```

> **System Readiness Status:**
> The complete end-to-end platform is implemented, integrated, and validated across all tiers: PostgreSQL 16 + PostGIS 3.4 spatial database, FastAPI computational engines, live telemetry provider adapters, interactive MapLibre GIS canvas, and Next.js operations dashboard.

---

## Current Development Status

- **Status:** Full Platform Implementation & Authoritative Data Pipeline Complete
- **Milestones Completed:**
  - `M1` through `M6` (Core Foundation, Risk, Vulnerability, Relocation, Routing, GIS Canvas, Operational Workflows)
  - `INT-01`, `INT-02`, `INT-03` (Integration, SIH Flow Validation, Automated Quality Gates)
  - `DATA-01` (Real-World Dataset Inventory & Manifest Distribution)
  - `DATA-02` (Database Ingestion, Authoritative Adapters & Backend REST Endpoints)
  - `INT-04` (End-to-End Real Data Integration, GIS Search, Governance Persistence & Pipeline Hardening)

For granular task statuses and formal audit records, refer to [`PROJECT_STATE.md`](PROJECT_STATE.md).

---

## System Requirements

To run and develop RakshakGIS locally, the following tools are required:

| Tool | Recommended Version | Purpose |
| --- | --- | --- |
| **Git** | 2.40+ | Version control & synchronization |
| **Docker Desktop / Engine** | 24.0+ (Docker 29+) | Containerized services |
| **Docker Compose** | v2.20+ (Compose v5+) | Multi-container orchestration |
| **Python** *(optional for host dev)* | 3.11.x | Local virtual environment & script execution |
| **Node.js & npm** *(for frontend)* | Node v20+ / v22+, npm 10+ | Frontend development (when implemented) |

---

## Quickstart & Local Setup

### 1. Clone the Repository

```bash
git clone https://github.com/OjaswiJoshi13/rakshakgis.git
cd rakshakgis
```

### 2. Configure Environment Variables

Copy the example configuration to `.env`:

**Linux / macOS / Git Bash:**
```bash
cp .env.example .env
```

**Windows (PowerShell):**
```powershell
Copy-Item .env.example .env
```

> **Security Reminder:** Never commit `.env` or any real API keys, passwords, or credentials into version control. `.env` is ignored by `.gitignore`.

### 3. Build and Start Services via Docker Compose

```bash
docker compose up --build -d
```

Check the status of running services:
```bash
docker compose ps
```

View real-time service logs:
```bash
docker compose logs -f
```

---

## Development Commands

| Action | Command |
| --- | --- |
| **Validate Compose Config** | `docker compose config` |
| **Build Images** | `docker compose build` |
| **Start Services (Detached)** | `docker compose up -d` |
| **Start with Rebuild** | `docker compose up --build -d` |
| **Stop Services** | `docker compose down` |
| **Stop and Remove Volumes** | `docker compose down -v` *(Caution: resets database)* |
| **View Service Status** | `docker compose ps` |
| **View Logs (All Services)** | `docker compose logs -f` |
| **View Database Logs** | `docker compose logs -f db` |
| **View Backend Logs** | `docker compose logs -f backend` |

---

## Repository Structure

```text
rakshakgis/
├── .env.example          # Template for local environment variables
├── .gitignore            # Git exclusion rules for secrets, caches, and builds
├── docker-compose.yml    # Docker Compose definition (PostGIS db + backend)
├── PROJECT_STATE.md      # Authoritative project progress and chunk registry
├── README.md             # Project documentation and developer setup guide
├── requirements.txt      # Python dependencies with geospatial pins
├── backend/              # FastAPI application core
│   ├── Dockerfile        # Python 3.11 container definition with GDAL/GEOS/PROJ
│   ├── app/              # Application source code
│   │   ├── adapters/     # External data providers (IMD, telemetry, GeoServer)
│   │   ├── api/          # FastAPI routers and route handlers
│   │   ├── core/         # Settings, database session, security
│   │   ├── models/       # SQLAlchemy / GeoAlchemy2 spatial models
│   │   ├── schemas/      # Pydantic data validation schemas
│   │   └── services/     # Computational engines (Risk, Red Zone, Relocation)
│   └── tests/            # Automated test suite (pytest)
├── frontend/             # Next.js / React user interface (to be scaffolded in M5-01)
├── data/                 # Regional profiles, synthetic demo data, schemas
├── docs/                 # Architecture specifications and technical documentation
└── scripts/              # Utility scripts for data generation and database setup
```

---

## Data Architecture & Bootstrap Workflow

RakshakGIS operates under four strictly isolated data modes configured via `DATA_MODE` in `.env`:

1. **`demo` (SIH Presentation & Offline Development):**
   Uses pre-packaged deterministic datasets (`app/data/synthetic/`). Zero external network dependencies.
2. **`full_data` (Authoritative Planning & Analysis):**
   Powered by PostgreSQL/PostGIS database populated from Census 2011, LGD administrative hierarchy, Survey of India village boundaries, and NCS seismology catalogs. **Missing data is explicit (`DATA_UNAVAILABLE`)**; calculations never assume missing values are zero or synthetic.
3. **`live` (Operational Multi-Hazard Monitoring):**
   Connects to real-time external providers:
   - **Open-Meteo**: Live precipitation and rainfall forecasts (CC-BY 4.0; *not labelled as IMD*).
   - **Central Water Commission (CWC) Flood AFF**: Live river gauge levels, danger thresholds, and flood forecasts.
   - **USGS Real-time Earthquakes**: Live seismic hazard observations for India bounding box.
4. **`simulation` (Dynamic What-If Analysis):**
   Modifies hazard/rainfall/road blockage parameters and reruns the real backend computational risk, Red Zone, priority, and matching engines deterministically.

### Teammate Data Bootstrap (Reproducible Setup)

To bootstrap the local data environment on a fresh clone without manual hunting:

```bash
# 1. Start backing PostgreSQL / PostGIS container
docker compose up -d db

# 2. Run data directory bootstrap & register manifests
python scripts/setup_data.py

# 3. Verify local dataset checksums against verified SHA-256 manifest
python scripts/verify_data.py --quick

# 4. Ingest authoritative data (Census 2011, LGD, Survey of India, NCS) into PostGIS
python scripts/ingest_all.py

# 5. Run full 22-step Golden SIH demo flow verification
python scripts/validate_golden_sih_flow.py
```

### Data Attribution & Licensing

- **Census 2011 & LGD**: Government Open Data License - India (GODL-India).
- **Survey of India**: Department of Science & Technology, Government of India.
- **National Centre for Seismology (NCS)**: Ministry of Earth Sciences, Government of India.
- **OpenStreetMap**: © OpenStreetMap contributors, licensed under the Open Database License (ODbL) 1.0.
- **Open-Meteo**: Weather data licensed under CC-BY 4.0.
- **Copernicus DEM (GLO-30)**: Manifests tracked; DEM rasters deferred due to automated 403. Physical slope/elevation explicitly reported as unavailable in `full_data` mode.
- **Bhuvan / GSI Landslide**: Official portal UI only; machine-readable endpoints not fabricated.

---

## Team Collaboration Workflow

All team members follow strict Git synchronization practices to prevent merge conflicts:

### 1. Synchronize Before Starting Work

```bash
git status
git fetch origin
git pull --rebase origin main
```

### 2. Implementation Rules

- Verify dependencies in [`PROJECT_STATE.md`](PROJECT_STATE.md) before starting any chunk.
- Stage only modified files explicitly (`git add <file>`), never `git add .`.
- **Never force-push (`git push --force`) to `main`.**
- If an ambiguous semantic merge conflict occurs during rebase, stop and report immediately.
