# Multi-Criteria Site Suitability Engine (M4-02)

## Overview

The **Multi-Criteria Site Suitability Engine** evaluates candidate relocation sites using deterministic, transparent, and auditable scoring rules across 9 authoritative criteria, preceded by strict hard safety and capacity constraint gates.

## Core Architectural Invariants

1. **Pre-Evaluation Hard Constraints**:
   Hard constraints are checked **before** weighted scoring:
   - **Hazard Slope Safety**: Slope must not exceed the regional threshold (e.g. 15.0° in Himalayan terrain). Unknown slope is strictly rejected.
   - **Hazard Buffer Distance**: Sites inside the mandatory hazard runout buffer (e.g. < 500m) are disqualified.
   - **Known Usable Capacity**: Sites with missing, zero, or negative capacity are disqualified. Missing capacity is **never** silently treated as unlimited.
   - *Water Availability* is evaluated as an authoritative 10% weighted criterion, rather than an unconfigured hard exclusion gate.


2. **Strict Override Invariant**:
   A site that fails any hard constraint is permanently marked `is_eligible=False` with decision `INELIGIBLE`. A high weighted score on other criteria **cannot** override a hard constraint failure.

3. **Authoritative 9 Criteria & Weights (Sum strictly to 100%)**:
   - **Hazard Safety**: 30% (`0.30`)
   - **Capacity**: 20% (`0.20`)
   - **Road Access**: 10% (`0.10`)
   - **Water Availability**: 10% (`0.10`)
   - **Healthcare Access**: 10% (`0.10`)
   - **School Access**: 5% (`0.05`)
   - **Emergency Services**: 5% (`0.05`)
   - **Livelihood Access**: 5% (`0.05`)
   - **Expansion Potential**: 5% (`0.05`)
   Total: 100% (`1.00`).

4. **Zero LLMs / Deterministic Math**:
   Pure numerical and algorithmic evaluation. No LLMs are used for numerical calculations.

5. **Region-Agnostic Core**:
   Thresholds and weights are configuration-driven via `SuitabilityWeightsConfig` and `SuitabilityThresholdsConfig`, sourceable from regional profiles (`RegionProfile`).

## Categorical Decisions

- `SUITABLE`: Passed all hard constraints, overall score $\ge 65.0$, and capacity $\ge 20$ households.
- `CONSTRAINED`: Passed hard constraints, but either score is between $[40.0, 65.0)$ or capacity is a bottleneck ($< 20$ households).
- `UNSUITABLE`: Passed hard constraints, but overall score $< 40.0$.
- `INELIGIBLE`: Failed one or more mandatory hard constraints.
