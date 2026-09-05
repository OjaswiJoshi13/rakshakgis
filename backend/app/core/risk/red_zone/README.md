# Red Zone Demarcation Subsystem (Chunks M3-10 & M3-11)

## 1. Subsystem Purpose & Architecture

The **Red Zone Demarcation Subsystem** provides deterministic, profile-driven geospatial hazard perimeter demarcation for RakshakGIS across two complementary operational regimes:

1. **Permanent Red Zones (Chunk M3-10):** Evaluates long-term, irreversible geophysical ground instability (active tectonic subsidence, extreme slope combined with chronic landslide history). Identifies candidate perimeters for potential climate-resilient relocation planning.
2. **Dynamic Red Zones & Threshold Triggers (Chunk M3-11):** Evaluates real-time, event-driven hazard observations (24h rainfall precipitation, seismic tremors, hydrological flood water level, active landslide debris) against configured regional profile trigger thresholds. Identifies temporary exclusion candidates for early warning and acute disaster response.

> [!IMPORTANT]
> **Governance Invariant: Analytical Proposals Only**
> Output perimeters from both M3-10 and M3-11 represent `PROPOSED` candidate exclusion zones (`is_candidate = True` when triggered, `is_active = False`, `declared_by_officer_id = None`). They do **not** constitute official statutory zoning, property condemnation, or legal evacuation orders. Official declaration remains strictly subject to administrative review and authorization by the competent disaster management officer (Chunk M6-08 workflow).

---

## 2. Semantic Separation: Permanent vs. Dynamic Red Zones

| Attribute | Permanent Red Zones (M3-10) | Dynamic Red Zones (M3-11) |
| :--- | :--- | :--- |
| **Operational Horizon** | Long-term / Permanent | Temporary / Event-Driven |
| **Physical Driver** | Irreversible ground movement, chronic slope instability | Weather extremes, seismic shocks, flash floods |
| **Result Model** | `PermanentRedZoneCandidate` | `DynamicRedZoneCandidate` (`is_temporary = True`) |
| **Status Enum** | `RedZoneStatus` (`PROPOSED`, `NOT_DEMARCATED`, `MONITOR`, `INSUFFICIENT_DATA`) | `DynamicTriggerStatus` (`TRIGGERED`, `NO_TRIGGER`, `INSUFFICIENT_DATA`) |
| **Profile Source** | `red_zone_thresholds.permanent_criteria` | `red_zone_thresholds.dynamic_triggers` |
| **Risk Integration** | Corroborated by M3-07 composite `CRITICAL` risk; `MONITOR` override for safe/moderate | Immediate threshold exceedance; compound rainfall-slope evaluation |
| **Downstream Impact** | Relocation Priority Scoring (M3-12) & Relocation Planning (M4) | Real-Time Alerts (M6-05) & Evacuation Routing (M4-05) |

---

## 3. Dynamic Threshold Triggers (Chunk M3-11)

### A. Supported Dynamic Indicators
The dynamic engine evaluates incoming telemetry observations across the project's upstream contracts:
- **24h Rainfall Precipitation:** Evaluated against `rainfall_trigger_24h_mm` (e.g. 64.5 mm in Himalayan pilot based on IMD Heavy Rainfall classification; 80.0 mm in Coastal; 75.0 mm in Riverine).
- **Seismic Intensity:** Evaluated against `seismic_trigger_mmi` (e.g. 6.0 MMI in Himalayan / Coastal profiles).
- **Slope Angle:** Evaluated against `slope_trigger_min_deg` (e.g. 25.0° in Himalayan, 3.0° in Coastal, 5.0° in Riverine).
- **Hydrological Water Level:** Evaluated against `water_level_trigger_m_above_danger` when configured.
- **Landslide Debris Volume:** Evaluated against `landslide_debris_volume_trigger_m3` when configured.
- **Compound Rainfall-Slope Trigger:** Evaluated when concurrent heavy rainfall breaches the rainfall threshold on a terrain with slope exceeding `slope_trigger_min_deg`.

### B. Profile-Driven Resolution (Zero Hardcoded Constants)
The engine contains zero hardcoded regional constants (no hardcoded `64.5`, `115.5`, `35.0`, or `500.0`). All thresholds are resolved dynamically from `DynamicThresholdConfig.from_profile(profile)`. Changing the configured profile values directly alters trigger decisions without code modification.

### C. Boundary Equality & Operator Semantics
- IMD meteorological standards define Heavy Rainfall as $\ge 64.5\text{ mm}$ (`NormalizedRainfallRecord.is_heavy_rain: bool = False # >= 64.5 mm`).
- The engine uses typed `ComparisonOperator` (`GREATER_THAN_OR_EQUAL` by default, with support for `>`, `<`, `<=`, `==`).
- Boundary conditions are deterministically evaluated when an active threshold is configured:
  - $\text{value} < \text{threshold} \implies \text{NO\_TRIGGER}$ (`NO_TRIGGER` strictly means the trigger was evaluated against an available threshold and did not fire).
  - $\text{value} == \text{threshold} \implies \text{TRIGGERED}$ (under default $\ge$)
  - $\text{value} > \text{threshold} \implies \text{TRIGGERED}$
- If an observation exists but its required dynamic threshold is unavailable/unconfigured (e.g., unconfigured `water_level_m_above_danger` or `debris_volume_cu_m`), the engine strictly returns `DynamicTriggerStatus.INSUFFICIENT_DATA`.

---

## 4. Permanent Red Zone Demarcation (Chunk M3-10)

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

Regional thresholds from `RegionProfile` (`red_zone_thresholds.permanent_criteria`):
- **Himalayan Pilot Profile:** `min_slope_deg = 35.0°`, `min_historical_landslides = 1`, `active_subsidence_triggers_permanent = True`.
- **Riverine Template Profile:** `min_slope_deg = 15.0°`, `min_historical_landslides = 0`, `active_subsidence_triggers_permanent = True`.
- **Coastal Template Profile:** `min_slope_deg = 10.0°`, `min_historical_landslides = 0`, `active_subsidence_triggers_permanent = True`.

### B. Relationship to M3-07 Composite Risk Classification
1. **CRITICAL Corroboration:** If composite risk is `CRITICAL` ($Risk \ge 85.0$), it corroborates the permanent red-zone candidate.
2. **Monitoring Override:** If a settlement exhibits steep slope ($\ge 35.0^\circ$) and landslide history, but is classified under `SAFE` or `MODERATE` composite risk **without active subsidence**, it is designated for `MONITOR` status rather than permanent exclusion zoning.
3. **Active Subsidence Priority:** Confirmed active subsidence triggers candidate status regardless of composite risk score due to immediate physical ground rupture threat.

---

## 5. Spatial Geometry & Overlap Dissolution

- **Polygonal Inputs (Polygon / MultiPolygon):** Normalized directly to a valid `MultiPolygon` in EPSG:4326 (SRID 4326) via Shapely.
- **Point-Based Sensor / Village Inputs:** Centered at `(lon, lat)`, a true **geodesic circular buffer** is computed using `pyproj` Azimuthal Equidistant projection based on the regional profile's configured hazard buffer:
  $$\text{buffer\_radius} = \text{profile.site\_capacity\_assumptions.hazard\_buffer\_m} \quad (\text{500.0 m for Himalayan Pilot})$$
- **Geodesic Area Calculation:** Calculated ellipsoidal geodesic area in square kilometers ($\text{km}^2$) using WGS84 ellipsoid parameters.
- **Spatial Dissolution:** When multiple candidates overlap geographically, they are dissolved via `shapely.ops.unary_union`. The resulting candidate retains complete deduplicated lists of:
  - `contributing_observation_ids`
  - `contributing_village_ids`
  - `source_provenance`
  - `trigger_evaluations`
  - `is_dissolved = True` and `dissolved_count = N`
- **Strict DangerLevel Invariant:** The dissolution engine never invents or escalates danger levels (e.g. no automatic escalation to `CRITICAL` or `UNINHABITABLE` solely due to multiple triggers).

---

## 6. Safety-Critical Missing Data & Threshold Invariants

> [!CAUTION]
> **Missing hazard data or unavailable threshold configurations are NEVER assumed safe or defaulted to 0.0.**

- **Trigger Evaluation Semantics:**
  - `NO_TRIGGER` strictly means the trigger was evaluated against an available threshold and did not fire.
  - `INSUFFICIENT_DATA` includes both missing observation values and cases where the required threshold configuration is unavailable.
- **Missing / Unavailable Observations:** If any required hazard observation is missing, null, or marked unavailable (`is_available = False`), the engine strictly returns `DynamicTriggerStatus.INSUFFICIENT_DATA` with `is_candidate = False`, `geometry = None`, and an explicit audit trail enumerating `missing_indicators`.
- **Unavailable / Unconfigured Dynamic Thresholds:** If an observation exists but the corresponding trigger threshold is unavailable or unconfigured in the regional profile (such as `water_level_m_above_danger` or `debris_volume_cu_m` when no threshold is configured), the engine cannot evaluate whether the observation triggers the hazard. It strictly returns `DynamicTriggerStatus.INSUFFICIENT_DATA` with `danger_level = None`, `is_candidate = False`, and an explicit audit note identifying the missing threshold configuration. An absent threshold is NEVER treated as `NO_TRIGGER`, `0`, `SAFE`, a fabricated/default threshold, or any danger level.
- In strict mode (`strict=True`), missing required data or unconfigured dynamic thresholds raise `InsufficientGeophysicalDataError`.
- Values of `NaN`, $\pm\infty$, or values outside physical domains (e.g. slope $> 90^\circ$, negative rainfall) raise `InvalidGeophysicalDataError`.

---

## 7. Critical Scope Boundaries

- **Relocation Priority Scoring Backend:** Multi-hazard village relocation ranking $\to$ **M3-12**
- **Real-Time Alerts & Warning UI:** Frontend dashboard notifications $\to$ **M6-05**
- **Officer Review & Action Sign-Off:** Administrative sign-off workflow $\to$ **M6-08**
- **Zero LLMs:** Numerical and geospatial evaluations are 100% deterministic algorithms.
