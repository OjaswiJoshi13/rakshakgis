# Permanent Red Zone Demarcation Engine (Chunk M3-10)

## 1. Purpose & Scope

The **Permanent Red Zone Demarcation Engine** evaluates settlement-level geophysical and multi-hazard risk indicators to demarcate **candidate / proposed** Permanent Red Zones in RakshakGIS.

A Permanent Red Zone designates an area characterized by irreversible ground instability or extreme recurrent geophysical hazard risk where long-term habitation is fundamentally unsafe and climate-resilient relocation is indicated.

> [!IMPORTANT]
> **Governance Invariant: Analytical Proposals Only**
> Output perimeters represent `PROPOSED` candidate exclusion zones. They do **not** constitute official statutory zoning, property condemnation, or legal evacuation orders. Official declaration remains strictly subject to administrative review and authorization by the competent disaster management officer (Chunk M6-08 workflow).

---

## 2. Formalized Demarcation Rules (Option 1)

### A. Geophysical Hard Triggers
A location breaches permanent red zone criteria when:
```text
active_subsidence == True
OR
(
    slope_deg >= regional_profile.min_slope_deg
    AND
    historical_landslide_count >= regional_profile.min_historical_landslides
)
```

Regional thresholds are configuration-driven via `RegionProfile` (`red_zone_thresholds.permanent_criteria`):
- **Himalayan Pilot Profile:** `min_slope_deg = 35.0°`, `min_historical_landslides = 1`, `active_subsidence_triggers_permanent = True`.
- **Riverine Template Profile:** `min_slope_deg = 15.0°`, `min_historical_landslides = 0`, `active_subsidence_triggers_permanent = True`.
- **Coastal Template Profile:** `min_slope_deg = 10.0°`, `min_historical_landslides = 0`, `active_subsidence_triggers_permanent = True`.

### B. Relationship to M3-07 Composite Risk Classification
When upstream M3-07 risk classification results are supplied:
1. **CRITICAL Corroboration:** If composite risk is `CRITICAL` ($Risk \ge 85.0$), it corroborates the permanent red-zone candidate.
2. **Monitoring Override:** If a settlement exhibits steep slope ($\ge 35.0^\circ$) and landslide history, but is classified under `SAFE` or `MODERATE` composite risk **without active subsidence**, it is designated for `MONITOR` status rather than permanent exclusion zoning.
3. **Active Subsidence Priority:** Confirmed active subsidence triggers candidate status regardless of composite risk score due to immediate physical ground rupture threat.

---

## 3. Spatial Geometry & Representation

The database model (`RedZone.geometry`) mandates `Geometry("MULTIPOLYGON", srid=4326)`.

The engine handles spatial representations as follows:
- **Polygonal Inputs (Polygon / MultiPolygon):** Normalized directly to a valid `MultiPolygon` in EPSG:4326 (SRID 4326) using Shapely.
- **Point-Based Village Inputs:** Centered at `(longitude, latitude)`, a true **geodesic circular buffer** is computed using metric projection (`pyproj` Azimuthal Equidistant) based on the regional profile's configured hazard buffer:
  $$\text{buffer\_radius} = \text{profile.site\_capacity\_assumptions.hazard\_buffer\_m} \quad (\text{default } 500.0\text{ m for Himalayan Pilot})$$
- **Geodesic Area Calculation:** Calculated ellipsoidal geodesic area in square kilometers ($\text{km}^2$) using WGS84 ellipsoid parameters.

---

## 4. Overlap Resolution & Dissolution

When multiple candidate perimeters overlap (e.g. contiguous hazard zones across adjacent settlements):
1. Overlapping geometries are dissolved into unified contiguous perimeters via `shapely.ops.unary_union`.
2. **Provenance & Source Preservation:** The dissolved candidate retains:
   - Complete list of contributing village/settlement IDs (`source_village_ids`).
   - Source provenance records (`source_provenance`).
   - Contributing candidate zone IDs and settlement names.
   - `is_dissolved = True` and `dissolved_zone_count = N`.

---

## 5. Safety-Critical Missing Data Invariants

> [!CAUTION]
> **Missing hazard data is NEVER assumed safe.**

- If any required geophysical indicator (`slope_deg`, `historical_landslide_count`, or `active_subsidence`) is missing or null, the settlement is **not** demarcated as safe.
- The engine strictly returns `RedZoneStatus.INSUFFICIENT_DATA` with `is_candidate = False`, `geometry = None`, and an explicit audit trail enumerating `missing_indicators` for geotechnical field inspection.
- Values of `NaN`, $\pm\infty$, or negative landslide counts raise `InvalidGeophysicalDataError`.

---

## 6. Critical Scope Boundaries

- **Dynamic Sensor-Triggered Red Zones:** Real-time rainfall/seismic triggers $\to$ **M3-11**
- **Relocation Priority Scoring:** Multi-hazard village relocation ranking $\to$ **M3-12**
- **Officer Review & Action Sign-Off:** Administrative sign-off workflow $\to$ **M6-08**
- **Zero LLMs:** Numerical and geospatial evaluations are 100% deterministic algorithms.
