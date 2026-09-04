# Risk Normalization Engine (Chunk M3-05)

## 1. Purpose of Normalization
The Risk Normalization Engine transforms validated, heterogeneous hazard and exposure observations (e.g., rainfall in mm/24h, flood water levels in meters above danger mark, landslide debris volumes in m³, seismic MMI intensity, and discrete severity categories) into comparable, normalized factor values on a standardized **0.0 — 100.0** scale.

This bridges the gap between raw data ingestion and downstream risk synthesis:
```
validated observation (M3-04)
        ↓
hazard-specific normalization (M3-05)
        ↓
normalized factor [0.0, 100.0] (M3-05)
        ↓
multi-hazard risk computation (M3-06)
```

## 2. Critical Scope Boundary
> [!IMPORTANT]
> **M3-05 DOES NOT calculate final composite risk scores.**
> 
> The composite formula:
> $$\text{Risk} = 0.30H + 0.20F + 0.15R + 0.15S + 0.10D + 0.10V$$
> and multi-hazard weighted aggregation are strictly deferred to **M3-06**.
> 
> Risk classification bands (`SAFE`, `MODERATE`, `HIGH`, `VERY_HIGH`, `CRITICAL`) are deferred to **M3-07**.
> Red Zone demarcation is deferred to **M3-10 / M3-11**.
> Relocation priority is deferred to **M3-12**.
> Demographic exposure and social vulnerability scoring ($D$ and $V$) are deferred to **M3-09**.

## 3. Supported Normalization Methods

### A. Linear Range Normalization (`NormalizationMethod.LINEAR`)
Maps a continuous domain `[min_value, max_value]` linearly to `[0.0, 100.0]`:
$$\text{Normalized} = \frac{\text{value} - \text{min\_value}}{\text{max\_value} - \text{min\_value}} \times 100.0$$
- $\text{value} \le \text{min\_value} \implies 0.0$ (clamped if enabled)
- $\text{value} \ge \text{max\_value} \implies 100.0$ (clamped if enabled)
- Strictly rejects $\text{max\_value} \le \text{min\_value}$ with `NormalizationConfigError`.

### B. Threshold-Based Piecewise Linear Interpolation (`NormalizationMethod.THRESHOLD_PIECEWISE`)
Interpolates continuous values across domain thresholds defined by the active regional profile.
For Himalayan rainfall:
- $0.0\text{ mm} \to 0.0$
- Heavy rainfall threshold ($64.5\text{ mm}$) $\to 50.0$
- Very heavy rainfall threshold ($115.5\text{ mm}$) $\to 80.0$
- Extreme rainfall benchmark ($204.4\text{ mm}$) $\to 100.0$

Interpolation is continuous, strictly monotonic, and deterministic.

### C. Categorical Severity Normalization (`NormalizationMethod.CATEGORICAL_SEVERITY`)
Deterministically maps discrete severity labels using `CategoricalSeverityPolicy`:
- `low` $\to 20.0$
- `moderate` $\to 40.0$
- `high` $\to 65.0$
- `very_high` $\to 85.0$
- `critical` $\to 100.0$

Unsupported categories are rejected with `InvalidInputError` or reported in typed `INVALID` results.

## 4. Configuration-Driven Parameters (M3-01 Reuse)
The normalization engine design is **region-agnostic**. All regional thresholds and scenario parameters are retrieved from the active `RegionProfile` (defined in `app.core.profiles`):
- `hazard_parameters.thresholds.rainfall_heavy_24h_mm` ($64.5\text{ mm}$)
- `hazard_parameters.thresholds.rainfall_very_heavy_24h_mm` ($115.5\text{ mm}$)
- `hazard_parameters.thresholds.slope_warning_deg` ($25.0^\circ$)
- `hazard_parameters.thresholds.slope_critical_deg` ($35.0^\circ$)
- `hazard_parameters.thresholds.seismic_critical_mmi` ($7.0$)
- `scenario_bounds.min_seismic_intensity_mmi` ($1.0$)
- `scenario_bounds.max_seismic_intensity_mmi` ($10.0$)

No regional thresholds are hardcoded as unexplained literals in normalization algorithms.

## 5. Safety-Critical Missing / Unknown Value Handling
> [!CAUTION]
> **Missing or unavailable data NEVER evaluates to 0.0.**
> 
> Converting missing observations to zero would dangerously misrepresent an unmonitored or sensor-failed village as "safe".

When an observation is missing, null, or unmonitored:
- Returns `NormalizationResult` with `status = NormalizationStatus.UNAVAILABLE`
- `normalized_value = None` (strictly enforced by Pydantic validators)
- `is_unknown_or_unavailable = True`
- `diagnostic_message` documents the exact data gap.

## 6. Clamping Behavior and Auditability
Inputs exceeding configured boundaries clamp to $0.0$ or $100.0$:
- `was_clamped = True`
- `clamping_reason` explains the boundary breach (e.g. `"Observation (125.0) exceeds maximum bound (100.0); clamped to 100.0."`).
- The original raw value is preserved in `raw_input_value`.

## 7. Explainability Metadata (`NormalizationExplainability`)
Downstream modules (M3-06 and M3-08) receive structured metadata:
- Normalization method used
- Parameters applied (min/max, benchmarks, policies)
- Thresholds applied (IMD heavy, very heavy)
- Input domain range
- Clamping reason (if clamped)
- Source record identity and provider provenance

## 8. Numerical Invariants
- Deterministic, pure mathematical functions: identical inputs produce identical outputs.
- Monotonic: higher hazard intensity produces higher or equal factor scores.
- Free of system time or network dependencies.
- Rejects `NaN` and $\pm\infty$ with `InvalidInputError`.
- Guaranteed $0.0 \le \text{normalized\_value} \le 100.0$.
