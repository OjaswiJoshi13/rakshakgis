# Risk Classification & Grading Engine (Chunk M3-07)

## 1. Purpose of the Engine
The Risk Classification & Grading Engine assigns an authoritative categorical risk band to the continuous composite risk score ($0.0 \le \text{Risk} \le 100.0$) evaluated upstream by Chunk M3-06.

```
raw observation (M3-04)
        ↓
normalization [0.0, 100.0] (M3-05)
        ↓
composite risk computation [0.0, 100.0] (M3-06)
        ↓
risk classification & grading (M3-07)
        ↓
authoritative risk band (SAFE, MODERATE, HIGH, VERY_HIGH, CRITICAL)
```

## 2. Authoritative Risk Bands & Cutoffs
The classification intervals are defined strictly by the platform domain specification:

| Risk Band | Interval Notation | Condition | Description |
| :--- | :---: | :---: | :--- |
| **SAFE** | $[0.0, 25.0)$ | $0.0 \le \text{score} < 25.0$ | Low disaster risk; standard routine monitoring |
| **MODERATE** | $[25.0, 50.0)$ | $25.0 \le \text{score} < 50.0$ | Elevated hazard potential; heightened watch |
| **HIGH** | $[50.0, 70.0)$ | $50.0 \le \text{score} < 70.0$ | High vulnerability and hazard overlap; mitigation alerts |
| **VERY_HIGH** | $[70.0, 85.0)$ | $70.0 \le \text{score} < 85.0$ | Severe disaster threat; evacuation preparedness |
| **CRITICAL** | $[85.0, 100.0]$ | $85.0 \le \text{score} \le 100.0$ | Imminent disaster risk / Red Zone candidate consideration |

## 3. Explicit Boundary Behavior
All boundary transitions are strictly defined and tested:
- **$0.0$** $\to$ `SAFE`
- **$25.0$** $\to$ `MODERATE` (inclusive lower bound)
- **$50.0$** $\to$ `HIGH` (inclusive lower bound)
- **$70.0$** $\to$ `VERY_HIGH` (inclusive lower bound)
- **$85.0$** $\to$ `CRITICAL` (inclusive lower bound)
- **$100.0$** $\to$ `CRITICAL` (inclusive upper bound)

Values just below boundaries map strictly to the lower tier (e.g. $24.999 \to \text{SAFE}$, $49.999 \to \text{MODERATE}$, $69.999 \to \text{HIGH}$, $84.999 \to \text{VERY\_HIGH}$).

## 4. Safety-Critical Input Validation
> [!CAUTION]
> **Invalid scores are strictly rejected and NEVER clamped.**
> 
> Silently clamping scores (e.g., coercing $-5 \to 0$ or $120 \to 100$) would mask fatal corruption in upstream pipelines or data adapters.

The engine raises `InvalidRiskScoreError` upon encountering:
- Out-of-bounds scores: $\text{score} < 0.0$ or $\text{score} > 100.0$
- Non-finite values: `NaN`, $+\infty$, $-\infty$
- Null / non-numeric types
- Incomplete `CompositeRiskResult` objects (`status != COMPUTED` or `score is None`)

## 5. Explainability Metadata
Each `RiskClassificationResult` includes a `RiskClassificationExplainability` model with:
- Selected `band` (`RiskBand` enum) and uppercase `band_name`
- Exact `score` preserved without truncation
- Applied `interval_notation` (e.g. `"[25.0, 50.0)"`)
- Boundary values (`lower_bound`, `upper_bound`) and inclusivity flags (`lower_inclusive`, `upper_inclusive`)
- Human-readable `audit_trail`

## 6. Critical Scope Boundaries
> [!IMPORTANT]
> **M3-07 is strictly a classification layer.**
> 
> The following features belong to later chunks and are NOT implemented here:
> - Risk explainability factor contribution decomposition $\to$ **M3-08**
> - Demographic & social vulnerability scoring $\to$ **M3-09**
> - Permanent Red Zone demarcation $\to$ **M3-10**
> - Dynamic Red Zone triggers $\to$ **M3-11**
> - Relocation priority scoring $\to$ **M3-12**
> - Candidate site suitability & relocation matching $\to$ **M4**
