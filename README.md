<div align="center">

# 🛡️ RakshakGIS

### Intelligent Identification of Hazard-Based Red Zones, Carrying Capacity Assessment, and Relocation Planning

<br/>

![Smart India Hackathon 2026](https://img.shields.io/badge/Smart%20India%20Hackathon-2026-1E40AF?style=flat-square)
![Problem Statement](https://img.shields.io/badge/Problem%20Statement-SIH26191-0F766E?style=flat-square)
![Team](https://img.shields.io/badge/Team-EndgameX-7C3AED?style=flat-square)
![Team ID](https://img.shields.io/badge/Team%20ID-148879-B45309?style=flat-square)
![Theme](https://img.shields.io/badge/Theme-Disaster%20Management-DC2626?style=flat-square)

<br/>

[![Live Demo](https://img.shields.io/badge/Live%20Demo-Open%20RakshakGIS-2ea44f?style=for-the-badge&logo=googlechrome&logoColor=white)](http://65.2.84.177)
[![Demo Video](https://img.shields.io/badge/YouTube-Watch%20Demo-red?style=for-the-badge&logo=youtube&logoColor=white)](https://youtu.be/_ubteCFdp9c)

<br/>

*An explainable geospatial decision-support platform for assessing multi-hazard risk, identifying vulnerable settlements, evaluating relocation capacity, and planning safer evacuation routes.*

<br/>

[Overview](#-overview) · [Features](#-key-features) · [Architecture](#-system-architecture) · [Workflows](#-core-workflows) · [Methodology](#-risk-assessment-methodology) · [Roadmap](#-aiml-roadmap) · [Stack](#-technology-stack) · [Quick Start](#-quick-start) · [Data](#-data-sources--attribution) · [Status](#-project-status)

</div>

---

## 📖 Overview

Disaster response teams often work with fragmented hazard data, uncertain evacuation routes, and limited information about relocation-site capacity. RakshakGIS brings these workflows together in one platform, helping authorities assess settlement-level risk, visualize Red Zones, compare potential relocation sites, and review evacuation corridors.

> [!IMPORTANT]
> **Human oversight:** RakshakGIS provides analytical recommendations, not autonomous emergency dispatch. Authorized officials must review and approve Red Zone boundaries, relocation assignments, and evacuation routes.

---

## ✨ Key Features

| | Feature | Description |
|:-:|---|---|
| 🌪️ | **Multi-hazard risk assessment** | Explainable composite risk scoring across hazard severity, flood risk, rainfall, terrain, service access, and social vulnerability. |
| 🟥 | **Dynamic and permanent Red Zones** | Distinguishes persistent susceptibility from acute conditions and threshold breaches. |
| 🏘️ | **Village vulnerability profiles** | Uses demographic and socioeconomic indicators to understand population exposure. |
| 🏥 | **Relocation capacity assessment** | Evaluates site safety and the limiting capacity of essential services such as housing, water, sanitation, healthcare, and shelter. |
| 🧭 | **Risk-aware evacuation routing** | Uses Dijkstra's algorithm to find routes while accounting for hazard exposure and road restrictions. |
| 🧪 | **Scenario simulation** | Tests hypothetical changes—such as increased rainfall—without modifying baseline records. |
| 📋 | **Auditable decisions** | Includes role-based access, decision logs, and explicit handling of unavailable data. |

---

## 🏗️ System Architecture

The platform follows a clear flow: external datasets are validated and processed by backend services, persisted in a spatial database, and exposed through the API to the interactive map and dashboard.

```mermaid
%%{init: {'theme':'base','flowchart':{'curve':'linear','nodeSpacing':28,'rankSpacing':56,'padding':16},'themeVariables':{'fontFamily':'Inter, Segoe UI, Helvetica, Arial, sans-serif','fontSize':'14px','lineColor':'#475569'}}}%%
flowchart TB
    subgraph INPUTS["DATA SOURCES"]
        direction LR
        weather["<b>Weather</b><br/>Open-Meteo"]
        flood["<b>Flood Gauges</b><br/>CWC"]
        seismic["<b>Seismic Feeds</b><br/>USGS / NCS"]
        geo["<b>Boundaries & Demographics</b><br/>SOI / Census / LGD"]
        roads["<b>Road Network</b><br/>OpenStreetMap"]
    end

    subgraph PLATFORM["RAKSHAKGIS PLATFORM"]
        direction TB
        ingest["<b>Data Validation & Ingestion</b>"]
        subgraph SERVICES["FASTAPI SERVICES"]
            direction LR
            risk["Risk & Red Zone Engine"]
            relocate["Relocation & Capacity Engine"]
            routing["Hazard-Aware Routing"]
            simulate["Scenario Simulator"]
            auth["Authentication & Audit"]
        end
        api["<b>REST API</b><br/>JSON / GeoJSON"]
    end

    db[("<b>PostgreSQL + PostGIS</b><br/>Spatial Data Store")]

    subgraph CLIENT["USER INTERFACE"]
        direction LR
        dashboard["Operations Dashboard"]
        map["MapLibre Interactive Map"]
    end

    officials(["<b>Disaster Management Officials</b>"])

    INPUTS --> ingest
    ingest --> db
    db <--> SERVICES
    SERVICES --> api
    auth --> api
    api <--> CLIENT
    CLIENT --> officials

    classDef source fill:#F8FAFC,stroke:#94A3B8,stroke-width:1.5px,color:#0F172A
    classDef pipeline fill:#EEF2FF,stroke:#4F46E5,stroke-width:1.5px,color:#312E81
    classDef service fill:#ECFEFF,stroke:#0891B2,stroke-width:1.5px,color:#164E63
    classDef store fill:#FFFBEB,stroke:#D97706,stroke-width:1.5px,color:#78350F
    classDef ui fill:#F0F9FF,stroke:#0284C7,stroke-width:1.5px,color:#0C4A6E
    classDef actor fill:#0F172A,stroke:#0F172A,stroke-width:1.5px,color:#F8FAFC

    class weather,flood,seismic,geo,roads source
    class ingest,api pipeline
    class risk,relocate,routing,simulate,auth service
    class db store
    class dashboard,map ui
    class officials actor

    style INPUTS fill:#FFFFFF,stroke:#CBD5E1,stroke-width:1.5px,stroke-dasharray:4 4,color:#475569
    style PLATFORM fill:#F5F3FF,stroke:#C7D2FE,stroke-width:1.5px,color:#3730A3
    style SERVICES fill:#FFFFFF,stroke:#A5F3FC,stroke-width:1.5px,color:#0E7490
    style CLIENT fill:#FFFFFF,stroke:#BAE6FD,stroke-width:1.5px,stroke-dasharray:4 4,color:#0369A1
    linkStyle default stroke:#475569,stroke-width:1.5px
```

---

## 🔄 Core Workflows

### 1️⃣ Risk Assessment & Red Zone Identification

```mermaid
%%{init: {'theme':'base','flowchart':{'curve':'linear','nodeSpacing':36,'rankSpacing':44,'padding':14},'themeVariables':{'fontFamily':'Inter, Segoe UI, Helvetica, Arial, sans-serif','fontSize':'14px','lineColor':'#475569'}}}%%
flowchart TD
    A(["<b>Select village or area</b>"]) --> B["Collect available hazard,<br/>terrain, access and vulnerability data"]
    B --> C{"Are required inputs available?"}
    C -- No --> D["Mark result as<br/><b>INSUFFICIENT_DATA</b>"]
    C -- Yes --> E["Normalize factors and<br/>calculate composite risk"]
    E --> F["Assign risk band"]
    F --> G["Generate or update<br/>Red Zone layers"]
    D --> H["Display result with<br/>data-status explanation"]
    G --> I["Show map, score and<br/>factor-level explanation"]
    H --> J(["<b>Officer review</b>"])
    I --> J

    classDef start fill:#1E3A8A,stroke:#1E3A8A,stroke-width:1.5px,color:#FFFFFF
    classDef step fill:#FFFFFF,stroke:#64748B,stroke-width:1.5px,color:#0F172A
    classDef decision fill:#FFFBEB,stroke:#D97706,stroke-width:2px,color:#78350F
    classDef neg fill:#FEF2F2,stroke:#DC2626,stroke-width:1.5px,color:#7F1D1D
    classDef pos fill:#F0FDF4,stroke:#16A34A,stroke-width:1.5px,color:#14532D
    classDef review fill:#0F172A,stroke:#0F172A,stroke-width:1.5px,color:#F8FAFC

    class A start
    class B,E,F step
    class C decision
    class D,H neg
    class G,I pos
    class J review

    linkStyle default stroke:#475569,stroke-width:1.5px
    linkStyle 2 stroke:#DC2626,stroke-width:2px
    linkStyle 3 stroke:#16A34A,stroke-width:2px
```

### 2️⃣ Relocation & Evacuation Planning

```mermaid
%%{init: {'theme':'base','flowchart':{'curve':'linear','nodeSpacing':36,'rankSpacing':44,'padding':14},'themeVariables':{'fontFamily':'Inter, Segoe UI, Helvetica, Arial, sans-serif','fontSize':'14px','lineColor':'#475569'}}}%%
flowchart TD
    A(["<b>Identify affected population</b>"]) --> B["Find candidate relocation sites"]
    B --> C["Check hazard and terrain safety"]
    C --> D{"Does the site pass<br/>safety constraints?"}
    D -- No --> E["Exclude site"]
    D -- Yes --> F["Assess capacity and<br/>essential services"]
    F --> G{"Is capacity sufficient?"}
    G -- No --> E
    G -- Yes --> H["Evaluate road access<br/>and route risk"]
    H --> I["Present feasible sites<br/>and evacuation corridors"]
    I --> J(["<b>Officer review and approval</b>"])
    E -.-> B

    classDef start fill:#1E3A8A,stroke:#1E3A8A,stroke-width:1.5px,color:#FFFFFF
    classDef step fill:#FFFFFF,stroke:#64748B,stroke-width:1.5px,color:#0F172A
    classDef decision fill:#FFFBEB,stroke:#D97706,stroke-width:2px,color:#78350F
    classDef neg fill:#FEF2F2,stroke:#DC2626,stroke-width:1.5px,color:#7F1D1D
    classDef pos fill:#F0FDF4,stroke:#16A34A,stroke-width:1.5px,color:#14532D
    classDef review fill:#0F172A,stroke:#0F172A,stroke-width:1.5px,color:#F8FAFC

    class A start
    class B,C,F,H step
    class D,G decision
    class E neg
    class I pos
    class J review

    linkStyle default stroke:#475569,stroke-width:1.5px
    linkStyle 3,6 stroke:#DC2626,stroke-width:2px
    linkStyle 4,7 stroke:#16A34A,stroke-width:2px
    linkStyle 10 stroke:#94A3B8,stroke-width:1.5px
```

<sub>**Legend:** 🟦 start · ⬜ process step · 🟨 decision · 🟥 exclusion / insufficient data · 🟩 outcome · ⬛ human review</sub>

---

## 📐 Risk Assessment Methodology

The current deterministic model uses the following weighted formulation:

$$
\text{Risk Score} = 0.30H + 0.20F + 0.15R + 0.15S + 0.10D + 0.10V
$$

| Factor | Weight | Share | Meaning |
|:-:|--:|:--|---|
| `H` | 30% | `██████` | Hazard severity |
| `F` | 20% | `████` | Flood risk |
| `R` | 15% | `███` | Rainfall |
| `S` | 15% | `███` | Slope and landslide susceptibility |
| `D` | 10% | `██` | Distance to essential services |
| `V` | 10% | `██` | Social vulnerability |

The factors are combined into a score from 0 to 100 and mapped to risk bands. If required inputs are missing, the system reports `INSUFFICIENT_DATA` rather than silently treating missing values as zero. Refer to the implementation for the exact normalization and band thresholds.

---

## 🤖 AI/ML Roadmap

A CNN-LSTM model is planned for a future research phase: CNN layers would extract spatial patterns, while LSTM layers would model temporal dependencies in rainfall and river-gauge data.

> [!NOTE]
> **The current live decision loop uses deterministic calculations; CNN-LSTM forecasting is not represented as a deployed feature.**

---

## 🧰 Technology Stack

| Layer | Technologies |
|---|---|
| 🖥️ **Frontend** | `Next.js 14` · `TypeScript` · `Tailwind CSS` · `MapLibre GL JS` · `Recharts` |
| ⚙️ **Backend** | `FastAPI` · `Python 3.11` · `Pydantic` · `SQLAlchemy` · `GeoAlchemy2` · `Shapely` · `PyProj` |
| 🗄️ **Database / GIS** | `PostgreSQL 16` · `PostGIS 3.4` |
| ☁️ **Infrastructure** | `Docker Compose` · `AWS EC2` · `Terraform` |
| 🧪 **Testing** | `Vitest` · `Pytest` |

---

## 🌐 Live Demo & Video

| | Resource | Link |
|:-:|---|---|
| 🚀 | **Deployed application** | [http://65.2.84.177](http://65.2.84.177) |
| 🎬 | **Project walkthrough** | [Watch on YouTube](https://youtu.be/_ubteCFdp9c) |

---

## ⚡ Quick Start

```bash
git clone https://github.com/OjaswiJoshi13/rakshakgis.git
cd rakshakgis
cp .env.example .env
docker compose up --build -d
```

Check service status and the backend health endpoint:

```bash
docker compose ps
curl http://localhost:8000/health
```

| Service | URL |
|---|---|
| 🖥️ Frontend | `http://localhost:3000` |
| 📚 API documentation | `http://localhost:8000/docs` |

For full data ingestion and end-to-end validation, see `docs/DEPLOYMENT.md`.

---

## 🗂️ Data Sources & Attribution

| Source | Data | License / Note |
|---|---|---|
| **Census of India (2011) and LGD** | Demographics and administrative data | Government Open Data License – India (GODL-India) |
| **Survey of India** | Administrative boundaries | Refer to the applicable Government of India terms |
| **National Centre for Seismology (NCS)** | Seismic catalogs | — |
| **Open-Meteo** | Meteorological data | CC BY 4.0; it is an open provider, not IMD |
| **Central Water Commission (CWC)** | River-gauge information and danger levels | — |
| **USGS Earthquakes** | Seismic event feeds | Public domain |
| **OpenStreetMap** | Road-network data | ODbL 1.0; attribution is required |

---

## 🚦 Project Status

The repository's `PROJECT_STATE.md` is the source of truth for milestone status.

| Status | Milestones |
|:-:|---|
| ✅ **Completed** | Core risk, Red Zone, relocation, routing, dashboard, integration, and cloud-deployment milestones |
| 🗓️ **Planned** | CNN-LSTM forecasting and multi-state expansion |
| ⏸️ **Deferred** | Copernicus DEM raster downloads |

> [!WARNING]
> Elevation data must be treated as unavailable where it has not been ingested.

---

## 👥 Team & License

<div align="center">

**EndgameX** · SIH 2026 · `SIH26191` · Team ID `148879`

</div>

The software is proprietary to Team EndgameX pending formal license assignment. External datasets remain subject to their respective licenses.
