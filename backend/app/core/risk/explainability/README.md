# Risk Explainability & Factor Contribution Engine (Chunk M3-08)

## 1. Purpose of the Engine
The Risk Explainability & Factor Contribution Engine provides a deterministic, auditable, and structured explanation of an already-computed multi-hazard composite risk assessment.

```
raw observation (M3-04)
        ↓
factor normalization [0.0, 100.0] (M3-05)
        ↓
multi-hazard composite risk engine [0.0, 100.0] (M3-06)
        ↓
risk classification & grading (M3-07)
        ↓
risk explainability & factor contribution (M3-08)
        ↓
auditable explanation envelope:
- normalized factor values (H, F, R, S, D, V)
- weighted contributions (w_i * v_i)
- percentage shares of total risk
- ranked factors & dominant driver
- integrated risk band
- deterministic human-readable narrative & audit trail
```

---

## 2. Authoritative Formula & Contribution Semantics

The composite risk score follows the authoritative specification:

$$\text{Risk} = 0.30H + 0.20F + 0.15R + 0.15S + 0.10D + 0.10V$$

For each factor $i \in \{H, F, R, S, D, V\}$:
- **Normalized Value ($v_i$):** Dimensionless factor score on $[0.0, 100.0]$.
- **Configured Weight ($w_i$):** Relative importance coefficient ($\sum w_i = 1.00$).
- **Weighted Contribution ($c_i$):**
  $$c_i = w_i \times v_i$$
- **Contribution Percentage ($p_i$):**
  $$p_i = \left(\frac{c_i}{\text{Risk}}\right) \times 100\% \quad (\text{for } \text{Risk} > 0)$$
  Represents the proportional share of total disaster risk driven by factor $i$.
- **Dominant Factor:** The factor with the highest weighted contribution $c_i$. In the event of ties, canonical factor order ($H \to F \to R \to S \to D \to V$) breaks ties deterministically.

---

## 3. Factor Metadata

| Symbol | Factor Identifier | Display Name | Authoritative Weight | Description |
| :---: | :--- | :--- | :---: | :--- |
| **$H$** | `hazard_severity` | Hazard Severity | **$0.30$** | Landslide and slope instability severity |
| **$F$** | `flood_exposure` | Flood Exposure | **$0.20$** | Hydrological flood and inundation exposure |
| **$R$** | `rainfall_intensity` | Rainfall Intensity | **$0.15$** | 24-hour precipitation exceedance factor |
| **$S$** | `slope_landslide_susceptibility` | Slope / Landslide Susceptibility | **$0.15$** | Geophysical slope gradient and seismic susceptibility |
| **$D$** | `infrastructure_vulnerability` | Infrastructure Vulnerability | **$0.10$** | Physical infrastructure damage vulnerability and demographic exposure |
| **$V$** | `social_vulnerability` | Social Vulnerability | **$0.10$** | Socioeconomic sensitivity and vulnerable demographic share |

---

## 4. Safety-Critical Missing Data Policy

> [!CAUTION]
> **Missing or unmonitored factors are NEVER assumed to be zero.**
>
> Coercing missing sensor readings or survey data to zero would dangerously obscure real hazard vulnerability in neglected or isolated villages.

When upstream status is `INSUFFICIENT_FACTORS`:
- `is_computable = False`
- `score = None` (strictly enforced by Pydantic model validator)
- `ranked_contributions = []`
- `dominant_factor = None`
- `missing_factors` explicitly lists all unmonitored or missing factors.
- `narrative_explanation` documents the incomplete status and lists the missing factors with safety disclaimers.

---

## 5. Risk Classification Integration (M3-07)

M3-08 integrates seamlessly with Chunk M3-07 (`RiskClassificationEngine`):
- Accepts pre-computed `RiskClassificationResult` envelopes, validating mathematical consistency ($|\text{classification.score} - \text{composite.score}| < 10^{-4}$).
- Optionally invokes `RiskClassificationEngine` automatically when an unclassified `CompositeRiskResult` is passed.
- Supports operating without classification if classification is intentionally omitted.
- Never recalculates risk bands or duplicates cutoff logic.

---

## 6. Determinism & Traceability

- Pure, reproducible computations with zero random seeds, zero external API calls, and zero timestamps in calculation logic.
- Human-readable narrative generated deterministically via templates, completely independent of LLMs.
- Canonical factor ordering preserved across all outputs.
- Configuration provenance recorded via `RegionProfile` metadata.

---

## 7. Critical Scope Boundaries

> [!IMPORTANT]
> **M3-08 is strictly an explainability layer.**
>
> The following features belong to later chunks and are NOT implemented here:
> - Demographic & social vulnerability scoring engine $\to$ **M3-09**
> - Permanent Red Zone demarcation $\to$ **M3-10**
> - Dynamic Red Zone threshold triggers $\to$ **M3-11**
> - Relocation priority scoring backend $\to$ **M3-12**
> - Site suitability evaluation & routing $\to$ **M4**
> - LLM-generated risk calculation or text generation
