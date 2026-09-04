# Multi-Hazard Risk Computation Engine (Chunk M3-06)

## 1. Purpose of the Engine
The Multi-Hazard Risk Computation Engine evaluates the composite disaster risk score for geographic entities (e.g. villages, blocks) by synthesizing six normalized factor values on a common `[0.0, 100.0]` scale.

```
raw / provider observation (M3-04)
        ↓
hazard-specific factor normalization (M3-05)
        ↓
normalized factor values [0.0, 100.0]
        ↓
multi-hazard composite risk engine (M3-06)
        ↓
composite risk score [0.0, 100.0]
        ↓
risk classification & grading (M3-07)
```

## 2. Authoritative Formula and Weights
The composite risk score is evaluated strictly according to the domain specification:

$$\text{Risk} = 0.30H + 0.20F + 0.15R + 0.15S + 0.10D + 0.10V$$

Where:
| Symbol | Factor Name | Authoritative Weight | Description |
| :---: | :--- | :---: | :--- |
| **$H$** | `hazard_severity` | **$0.30$** | Landslide and slope instability severity |
| **$F$** | `flood_exposure` | **$0.20$** | Hydrological flood / flash flood factor |
| **$R$** | `rainfall_intensity` | **$0.15$** | 24h precipitation exceedance factor |
| **$S$** | `slope_landslide_susceptibility` | **$0.15$** | Geophysical slope and seismic intensity |
| **$D$** | `infrastructure_vulnerability` | **$0.10$** | Physical infrastructure damage / disaster vulnerability |
| **$V$** | `social_vulnerability` | **$0.10$** | Demographic and socioeconomic vulnerability |

- The weights sum strictly to $1.00$ ($0.30 + 0.20 + 0.15 + 0.15 + 0.10 + 0.10 = 1.00$).
- The final score is guaranteed to lie within $[0.0, 100.0]$.

## 3. Safety-Critical Missing / Unknown Factor Handling
> [!CAUTION]
> **Missing or unmonitored factors NEVER evaluate to 0.0.**
> 
> Silently converting missing observations to zero would dangerously under-report risk in areas with sensor failures or incomplete monitoring.

When any of the six required factors is missing or unavailable:
- `status = RiskComputationStatus.INSUFFICIENT_FACTORS`
- `score = None` (strictly enforced by Pydantic model validators)
- `missing_factors` enumerates the missing factors.
- `diagnostic_message` documents the missing data.

## 4. Input Validation and Numerical Invariants
- **Domain Validity:** Normalized factor values must be finite numbers in $[0.0, 100.0]$.
- **Rejection of Malformed Data:** `NaN`, $\pm\infty$, and numbers outside $[0.0, 100.0]$ produce `status = RiskComputationStatus.INVALID_INPUT` with `score = None` (or raise `InvalidFactorValueError`).
- **Determinism:** Pure mathematical calculations with zero random numbers, zero system time dependencies, and zero network calls.
- **Safety Clamping:** Total composite score is clamped to $[0.0, 100.0]$ as an invariant.

## 5. Explainability and Auditability
Every computed result generates a `CompositeRiskExplainability` record:
- Formula derivation string: `"Risk = 0.30*H + 0.20*F + 0.15*R + 0.15*S + 0.10*D + 0.10*V"`
- Weighted factor contribution breakdown: $\text{contribution}_i = w_i \times v_i$
- Exact normalized factor values used: $\{H, F, R, S, D, V\}$
- Weights used: $\{w_H, w_F, w_R, w_S, w_D, w_V\}$
- Human-readable mathematical audit trail explaining the exact summation.

## 6. Critical Scope Boundaries
> [!IMPORTANT]
> **M3-06 is the mathematical computation engine only.**
> 
> The following features belong to later chunks and are NOT implemented here:
> - Risk classification bands (`SAFE`, `MODERATE`, `HIGH`, `VERY_HIGH`, `CRITICAL`) $\to$ **M3-07**
> - Red Zone demarcation $\to$ **M3-10 / M3-11**
> - Relocation priority scoring $\to$ **M3-12**
> - Multi-criteria site suitability $\to$ **M4-02**
> - Village-site matching and routing $\to$ **M4-04 / M4-05**
> - LLM-generated natural language risk interpretations
