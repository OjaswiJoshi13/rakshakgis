# Relocation Priority Scoring Backend (Chunk M3-12)

## 1. Overview

The **Relocation Priority Scoring Engine** evaluates multi-hazard relocation urgency across human settlements based on evidence-backed geophysical, demographic, social, historical, and access risk factors.

It serves as the analytical bridge connecting upstream risk models (**M3-06** Multi-Hazard Risk, **M3-08** Explainability, **M3-09** Exposure & Vulnerability) with downstream rehabilitation planning (**M4-04** Relocation Matching & Assignment).

---

## 2. Authoritative Relocation Priority Formula

$$\text{Relocation Priority} = 0.40 \times \text{Risk} + 0.25 \times \text{Exposure} + 0.20 \times \text{Vulnerability} + 0.10 \times \text{Historical Impact} + 0.05 \times \text{Accessibility}$$

All five factors must be normalized on a $[0.0, 100.0]$ scale. The final score is deterministically clamped to $[0.0, 100.0]$.

### Factor Definitions & Weights

| Factor | Symbol | Weight | Normalized Domain | Description | Upstream Origin |
| --- | :---: | :---: | :---: | --- | --- |
| **Risk** | $R$ | `0.40` | $0.0 - 100.0$ | Multi-hazard composite risk score | **M3-06** (`CompositeRiskResult`) |
| **Exposure** | $E$ | `0.25` | $0.0 - 100.0$ | Demographic exposure and high-risk sensitive population density | **M3-09** (`DemographicExposureResult`) |
| **Vulnerability** | $V$ | `0.20` | $0.0 - 100.0$ | Social and socioeconomic vulnerability index | **M3-09** (`SocialVulnerabilityResult`) |
| **Historical Impact** | $H$ | `0.10` | $0.0 - 100.0$ | Past disaster event frequency and historical landslide scar counts | **M3-02 / M3-04** Synthetic telemetry & field logs |
| **Accessibility** | $A$ | `0.05` | $0.0 - 100.0$ | Physical access isolation, evacuation difficulty, and winter cutoff vulnerability | **M3-02 / M3-09** Road connectivity & evacuation chokepoints |

$$\sum_{i=1}^5 w_i = 0.40 + 0.25 + 0.20 + 0.10 + 0.05 = 1.00$$

---

## 3. Authoritative Priority Bands & Boundary Semantics

Scores are mapped into four authoritative Relocation Priority Bands:

| Priority Band | Score Interval | Interval Notation | Action Horizon | Description |
| --- | :---: | :---: | --- | --- |
| **IMMEDIATE** | $80.0 - 100.0$ | $[80.0, 100.0]$ | Urgent action ($0-3$ months) | Acute danger and exposure requiring immediate phased relocation |
| **SHORT-TERM** | $60.0 - 79.99$ | $[60.0, 80.0)$ | Short-term ($3-12$ months) | High multi-hazard vulnerability designated for prompt planned rehabilitation |
| **MEDIUM-TERM** | $40.0 - 59.99$ | $[40.0, 60.0)$ | Medium-term ($1-3$ years) | Moderate risk requiring mitigation, structural retrofitting, or planned relocation |
| **MONITOR** | $0.0 - 39.99$ | $[0.0, 40.0)$ | Routine monitoring | Safe / low-risk conditions requiring routine observational surveillance |

### Boundary Transition Semantics
- Exact `80.0` is `IMMEDIATE`.
- Exact `60.0` is `SHORT-TERM`.
- Exact `40.0` is `MEDIUM-TERM`.
- `39.99` is `MONITOR`.
- Scores outside $[0.0, 100.0]$, NaN, or infinite values raise `InvalidPriorityDataError`.

---

## 4. Profile-Driven Regional Configuration

The engine contains zero hardcoded weights or cutoffs in its calculation logic:
- Weights resolve from `profile.relocation_priority_parameters.weights`
- Cutoffs resolve from `profile.relocation_priority_parameters.cutoffs`
- Instantiated via `RelocationPriorityEngine.from_profile(profile)`.

---

## 5. Safety-Critical Missing Data Invariants

> [!CAUTION]
> **Missing factor data is NEVER assumed safe, defaulted to 0.0, or silently classified as MONITOR.**

1. **Incomplete Data Policy:** If any factor is missing, null, or uncomputed, the engine strictly returns:
   - `status = RelocationPriorityStatus.INSUFFICIENT_DATA`
   - `priority_score = None`
   - `priority_band = None`
   - `missing_factors = [...]` (enumerating missing fields)
   - `is_actionable_proposal = False`
2. **Strict Mode:** When `strict=True`, missing factors immediately raise `InsufficientPriorityDataError`.
3. **Invalid Values:** Values outside $[0.0, 100.0]$, NaN, or $\pm\infty$ raise `InvalidPriorityDataError`.

---

## 6. Explainability & Provenance

Every evaluation produces a structured `RelocationPriorityExplainability` envelope containing:
- **Formula Derivation:** Explicit mathematical representation.
- **Factor Breakdown:** List of `PriorityFactorDetail` records providing factor weight, normalized score, weighted contribution ($w_i \times v_i$), and percentage share.
- **Primary Driver:** Identification of the dominant factor providing the largest point contribution.
- **Audit Narrative:** Human-readable narrative detailing justification for District Officer review.
- **Provenance Preservation:** Full provenance records from contributing upstream models are retained.

---

## 7. Critical Scope & Governance Boundaries

> [!IMPORTANT]
> **Decision Support Only:**
> The relocation priority score is an advisory decision-support recommendation for District Officers and Rehabilitation Committees.
> It strictly enforces `is_automatic_evacuation = False` and does NOT issue legal orders, evacuation mandates, or candidate site allocations.

- **Downstream Matching:** Village-to-site matching and capacity sizing $\to$ **M4-04**
- **Evacuation Routing:** Multi-modal access and evacuation route planning $\to$ **M4-05**
- **Officer Review & Sign-Off Workflow:** Administrative approval $\to$ **M6-08**
- **Zero LLMs:** Calculations are 100% deterministic mathematical algorithms.
