# RakshakGIS Synthetic Himalayan Pilot Dataset (Chunk M3-02)

Deterministic, explicitly labeled synthetic demonstration dataset for the Uttarakhand Himalayan pilot region (`himalayan_pilot` / Chamoli District).

> [!IMPORTANT]
> **DEMONSTRATION / SYNTHETIC DATASET NOTICE**
> All records in this dataset are synthetic demonstrations created for SIH Problem Statement 26191. They do NOT contain real personal data (PII) and are NOT official Government of Uttarakhand, Survey of India, or Census statutory data.

---

## 1. Dataset Overview & Counts

| Entity Type | Count | Format | Primary File |
| :--- | :--- | :--- | :--- |
| **Villages** | **40** | GeoJSON (FeatureCollection) | `fixtures/villages.geojson` |
| **Candidate Relocation Sites** | **12** | GeoJSON (FeatureCollection) | `fixtures/candidate_sites.geojson` |
| **Hazard Events** | **30** | Structured JSON | `fixtures/hazard_events.json` |
| **Dataset Metadata** | **1** | JSON | `fixtures/himalayan_pilot_metadata.json` |

- **Seed**: `26191` (Fixed pseudo-random seed from SIH Problem Statement ID).
- **Pilot Region Profile ID**: `himalayan_pilot` (From M3-01 `RegionProfileRegistry`).
- **Administrative Extent**: Chamoli District, Uttarakhand (`CHAMOLI_01`), spanning 4 blocks:
  - `joshimath`: 15 high-altitude settlements (subsidence zones, steep slopes, rockfall chutes).
  - `dasholi`: 13 mid-elevation settlements (Gopeshwar/Pipalkoti valley benches).
  - `karnaprayag`: 7 confluence basin settlements (river terraces, lower slope risk).
  - `ghat`: 5 remote valley settlements (Nandakini valley, cloudburst runoff zones).

---

## 2. Schema Summary

### A. Villages (`villages.geojson`)
- **Geometry**: `Point` `[longitude, latitude]` in WGS84 (`EPSG:4326`).
- **Properties**:
  - `id`: Unique identifier (`HIM-VILL-001` through `HIM-VILL-040`).
  - `name`: Settlement name (e.g. Sunil, Ravigram, Manohar Bagh).
  - `region_code`: `uttarakhand_himalayan`, `district_code`: `chamoli`, `block_code`: block ID.
  - `population`: Integer count (190 to 920).
  - `households`: Non-negative integer count.
  - `demographics`: `elderly_count`, `children_count`, `disabled_count`, `livestock_count`.
  - `vulnerability`: Normalized indices (0.0 to 1.0) for social, economic, structural, road connectivity, poverty, and kuccha housing.
  - `infrastructure`: Boolean flags for primary school, health subcenter, piped water, electricity, and telecom coverage.
  - `accessibility`: Distance to motorable road, road type (`paved`, `unpaved`, `footpath`), evacuation condition, winter cutoff flag.
  - `hazards`: Elevation, slope angle (deg), historical landslide count, active subsidence flag, distance to river, soil type, geological formation.
  - `provenance`: `is_synthetic: true`, `data_source: "DEMO_SYNTHETIC_GENERATOR"`, disclaimer notice.

### B. Candidate Relocation Sites (`candidate_sites.geojson`)
- **Geometry**: `Polygon` (closed ring of 5 vertices forming bounding boundary) in WGS84.
- **Properties**:
  - `id`: Unique identifier (`HIM-SITE-001` through `HIM-SITE-012`).
  - `name`: Site name (e.g., Gauchar Aerodrome Terrace Flat, Pipalkoti North Plateau).
  - `site_type`: `government_revenue_land`, `panchayat_land`, `plateau_terrace`, `inter_mountain_basin`.
  - `status`: `proposed`, `approved`.
  - `suitability`:
    - `area_sq_m`: Surface area (9,500 m² to 85,000 m²).
    - `terrain_slope_deg`: Slope angle (5.8° to 24.0°).
    - `hazard_buffer_distance_m`: Buffer from active hazard runouts (220 m to 1,400 m).
    - `road_width_m`, `distance_to_highway_km`, `all_weather_access`.
    - `water_supply_lpd_per_capita` (35.0 to 90.0 LPD), `water_source_distance_m`, `perennial_water_source`.
    - Distances to healthcare, primary school, emergency services, and agricultural land.
    - `suitability_category`: `suitable` (7 sites), `rejected` (4 sites), `constrained` (1 site).
  - `capacity`: `max_households`, `max_population`, `available_households`, `available_population`, `sanitation_units`.
  - `provenance`: Synthetic provenance metadata and disclaimer.

#### Deliberate Rejection & Constraint Cases (For M4 Suitability Testing)
- **`HIM-SITE-008` (Joshimath Upper Escarpment)**: Slope violation (`19.5°` > `15.0°` safe relocation limit).
- **`HIM-SITE-009` (Marwari Ridge Slope)**: Severe slope & rockfall violation (`24.0°` > `15.0°`).
- **`HIM-SITE-010` (Helang Nala Confluence)**: Hazard buffer violation (`220.0 m` < `500.0 m` mandatory exclusion buffer).
- **`HIM-SITE-011` (Tangani Dry Hill Crest)**: Water deficit (`35.0 LPD` < `70.0 LPD` minimum standard).
- **`HIM-SITE-012` (Batula Pocket Terrace)**: Carrying capacity bottleneck (`18 households` max capacity).

### C. Hazard Events (`hazard_events.json`)
- 30 point-in-time incidents covering:
  - 10 Landslides (debris slumps, fissures, rockfalls with volumes and road blockages).
  - 8 Extreme / Heavy Rainfall readings (exceeding IMD 64.5 mm and 115.5 mm thresholds).
  - 6 Seismic Shocks (Zone V fault slip events, MMI 5.5 to 7.2).
  - 6 Flash Flood / River Inundation events (torrential runoff along Alaknanda / Dhauliganga tributaries).

---

## 3. Python API & Usage

```python
from app.data.synthetic import (
    load_himalayan_pilot_dataset,
    get_synthetic_villages_geojson,
    get_synthetic_candidate_sites_geojson,
    get_synthetic_hazard_events,
    get_dataset_metadata,
)

# Load complete strongly typed and validated dataset
dataset = load_himalayan_pilot_dataset()
print(f"Loaded {len(dataset.villages.features)} villages")
print(f"Loaded {len(dataset.candidate_sites.features)} candidate sites")
print(f"Loaded {len(dataset.hazard_events)} hazard events")

# Direct GeoJSON dictionary access
villages_geojson = get_synthetic_villages_geojson()
sites_geojson = get_synthetic_candidate_sites_geojson()
```

---

## 4. Regeneration and Determinism Verification

Regenerate and serialize fixtures deterministically from the CLI:

```bash
docker exec rakshakgis-backend python -m app.data.synthetic.generator
```

Run dataset validation and quality tests:

```bash
docker exec rakshakgis-backend pytest tests/test_synthetic_data.py -v
```

---

## 5. Downstream Consumers

- **M3-03 (Provider Interfaces & Mock Adapters)**: Mock adapters ingest synthetic streams.
- **M3-04 (Data Validation & Ingestion Pipelines)**: Populates database tables from fixtures.
- **M3-05 to M3-12 (Risk & Red Zone Engines)**: Computes risk scores and red zone triggers on the 40 villages.
- **M4-01 to M4-06 (Candidate Sites & Relocation Engines)**: Evaluates suitability and carries out capacity matching on the 12 candidate sites.
