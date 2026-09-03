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

> **Important Note on Implementation Status:**
> The architecture diagram above outlines the planned complete system design per the authoritative specification. Currently, only the **Repository & Docker Foundation (Chunk M1-01)** is established. Core backend routes, database schemas, risk engines, and frontend interfaces are scheduled for subsequent implementation chunks.

---

## Current Development Status

- **Current Milestone:** M1 — Platform & DevOps Foundation
- **Current Chunk:** `M1-01` (Repository & Docker Foundation) — *In Progress / Awaiting Review*
- **Completed Milestones:** `M1-00` (Repository Audit & State Initialization — `COMMITTED`)
- **Next Eligible Chunk:** `M2-01` (FastAPI Foundation & Core App Setup)

For granular task statuses and dependency tracking, refer to [`PROJECT_STATE.md`](PROJECT_STATE.md).

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

## Intended Data Modes

RakshakGIS supports three operational data modes configured via `DATA_MODE` in `.env`:

1. **`demo` (Default for Development & Evaluation):**
   Uses pre-packaged synthetic datasets and deterministic mock adapters. Does **not** require external API credentials or active internet telemetry.
2. **`live` (Operational Monitoring):**
   Connects to real-time external data providers (IMD rainfall, GSI slope instability, telemetry sensors) via provider adapters.
3. **`simulation` (Scenario Exploration):**
   Allows disaster management officers to modify hazard parameters (e.g. simulated extreme rainfall, slope failure) and re-execute backend computational risk models deterministically without mock random numbers.

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
