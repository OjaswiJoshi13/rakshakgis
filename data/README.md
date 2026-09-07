# RakshakGIS Data Repository & Distribution Guide

This directory contains the data architecture, machine-readable manifests, ingestion targets, and bootstrap scripts for the **RakshakGIS** disaster decision-support platform.

---

## 1. Directory Structure

```
data/
├── raw/                      # Raw authoritative datasets (git-ignored, local-only)
│   ├── census/               # Census 2011 Primary Census Abstract (PCA)
│   ├── lgd/                  # Local Government Directory (States, Districts, Sub-districts, Villages)
│   ├── ncs/                  # National Centre for Seismology earthquake catalog
│   ├── osm/                  # OpenStreetMap India PBF extract (1.7 GB)
│   ├── survey_of_india/      # Survey of India administrative boundary ZIP shapefiles (27 states)
│   └── copernicus/           # Copernicus GLO-30 DEM manifest catalogues
├── processed/                # Extracted geometries, parquet, and intermediate ingestion artifacts
├── manifests/                # Machine-readable registries & verified SHA-256 checksums (committed)
│   ├── dataset_manifest.json # Complete metadata, provenance, licensing, and acquisition instructions
│   └── raw_files_checksums.json # Verified SHA-256 byte fingerprints for all raw inputs
├── demo/                     # Deterministic demo fixtures for isolated SIH presentations
└── README.md                 # This documentation
```

---

## 2. Operational Data Modes

RakshakGIS operates under three strictly isolated data modes configured via `DATA_MODE`:

| Mode | Intended Usage | Data Source | Missing Data Behavior |
| :--- | :--- | :--- | :--- |
| **`demo`** | Hackathon/SIH presentations, offline dev | Deterministic fixtures in `app/data/synthetic/` | Zero external network calls; fully synthetic |
| **`full_data`** | Authority disaster planners, GIS analysts | PostgreSQL/PostGIS ingested from Census, LGD, SoI, OSM, NCS | **Explicit `DATA_UNAVAILABLE`**. Never silently falls back to synthetic or zero. |
| **`live`** | Active emergency response monitoring | Live external API feeds (Open-Meteo, CWC Flood, USGS) + Ingested DB | Live observations with freshness timestamps; explicit provider error handling |

---

## 3. Dataset Catalog & Provenance

All 40 registered datasets are tracked with verified byte counts and SHA-256 checksums in `data/manifests/dataset_manifest.json`.

### A. Static National Datasets (Raw Ingestion)

1. **Census of India 2011 (Village PCA)**
   - *File*: `data/raw/census/2011-IndiaStateDistSbDistVill-0000.xlsx` (318 MB)
   - *Provider*: Office of the Registrar General & Census Commissioner, India (ORGI)
   - *Coverage*: All India States, Districts, Sub-districts, Villages.
   - *Fields*: Total population, households, SC/ST, child population (0-6), literacy, workers.
   - *License*: Government Open Data License - India (GODL-India).

2. **Local Government Directory (LGD) 2026**
   - *Files*: `data/raw/lgd/All_Stateof_India_*.xlsx`, `All_Districtof_India_*.xlsx`, `All_Sub_Districtof_India_*.xlsx`, `All_Villagesof_India_*.xlsx`
   - *Provider*: Ministry of Panchayati Raj (MoPR), Government of India
   - *Target*: Administrative hierarchy (`regions`, `districts`, `blocks`, `villages`).
   - *License*: GODL-India.

3. **National Centre for Seismology (NCS) Catalog**
   - *File*: `data/raw/ncs/Official Website of National Center of Seismology.xlsx`
   - *Provider*: National Centre for Seismology, Ministry of Earth Sciences (MoES)
   - *Target*: `hazard_observations`, `disaster_events` (Magnitude, depth, origin time, coordinates).
   - *License*: GODL-India.

4. **OpenStreetMap India Road Network**
   - *File*: `data/raw/osm/india-260906.osm.pbf` (1.7 GB)
   - *Provider*: OpenStreetMap Contributors / Geofabrik GmbH
   - *Target*: Real evacuation road network, edge traversal costs, bridge constraints.
   - *License*: Open Database License (ODbL) 1.0 — © OpenStreetMap contributors.

5. **Survey of India Village Boundaries**
   - *Files*: `data/raw/survey_of_india/<STATE>.zip` (27 state shapefile archives)
   - *Provider*: Survey of India (SoI), Department of Science & Technology
   - *Target*: `villages.boundary` (MultiPolygon geometry, SRID 4326).
   - *License*: Survey of India National Map Policy.

### B. Deferred Datasets

- **Copernicus DEM (GLO-30)**: Direct raster tile downloads require authentication / encountered HTTP 403 on automated mirrors. The tile catalog and download manifests (`india_dem_catalogue_2024.csv`) are recorded. In `full_data` mode, elevation and slope are reported as `DATA_UNAVAILABLE` rather than fabricating values.
- **Bhuvan / GSI Landslide**: GSI National Landslide Susceptibility Mapping is available via Bhuvan portal UI only. No public unauthenticated machine-readable REST/WFS endpoint exists. Reported as manual portal only.

### C. Live Authoritative Providers

- **Open-Meteo Weather & Precipitation**:
  - *Endpoint*: `https://api.open-meteo.com/v1/forecast`
  - *Usage*: Real-time rainfall and rolling precipitation for dynamic risk adjustment.
  - *Attribution*: Open-Meteo (CC-BY 4.0). *Do NOT label as IMD.*
- **Central Water Commission (CWC) Flood AFF**:
  - *Endpoint*: `https://aff.india-water.gov.in/textdata/Floodday_table_view_header.txt`
  - *Usage*: River station danger level, warning level, HFL, and daily flood stage forecasts.
- **USGS Real-time Earthquakes**:
  - *Endpoint*: `https://earthquake.usgs.gov/fdsnws/event/1/query`
  - *Usage*: Real-time seismic hazard alerts for India bounding box.

---

## 4. Teammate Bootstrap Workflow

To set up your local development environment with data on a fresh git clone:

```bash
# 1. Clone repository and start backing services
git clone <repo-url>
cd rakshakgis
docker compose up -d postgres

# 2. Run data environment bootstrap
python scripts/setup_data.py

# 3. Verify existing files and checksums
python scripts/verify_data.py --quick

# 4. Ingest authoritative data into PostgreSQL/PostGIS
python scripts/ingest_all.py

# 5. (Alternative for demo/presentation testing)
python scripts/seed_demo.py
```

---

## 5. Security & Git Hygiene

- Large raw binary datasets (`*.pbf`, `*.zip`, `*.xlsx`) are **NEVER committed to Git**.
- Only manifests (`data/manifests/*.json`), bootstrap scripts (`scripts/*.py`), and documentation are version-controlled.
- No API keys or credentials exist in raw datasets or code.
