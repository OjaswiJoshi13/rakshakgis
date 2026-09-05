# Scenario Simulator Integration Backend (Chunk M4-06)

## 1. Overview

The **Scenario Simulator Engine** (`app.core.scenarios`) provides deterministic, explainable what-if simulation capabilities for RakshakGIS. It coordinates the 7 core domain computational engines to evaluate how climate shocks, hazard escalations, and resource constraints propagate across disaster risk management and relocation planning.

```text
Scenario definition & parameters
               ↓
    Baseline Inputs (Villages & Sites)
               ↓
    In-Memory Input Modifications (Isolated)
               ↓
Stage 1: Multi-Hazard Risk Recalculation (M3-06 & M3-07)
               ↓
Stage 2: Dynamic Red Zone Demarcation (M3-11)
               ↓
Stage 3: Relocation Priority Urgency Scoring (M3-12)
               ↓
Stage 4: Candidate Site Multi-Criteria Suitability (M4-02)
               ↓
Stage 5: Carrying Capacity & Infrastructure Deficit Sizing (M4-03)
               ↓
Stage 6: Village → Site Relocation Matching (M4-04)
               ↓
Stage 7: Evacuation & Access Routing (M4-05)
               ↓
    Before vs After Comparison Engine
               ↓
    ScenarioSimulationOutput (Deltas + Provenance + Audit)
```

---

## 2. Core Principles & Governance Invariants

1. **Zero Duplicate Numerical Logic**: The simulator does NOT define new risk formulas, suitability weights, capacity formulas, matching algorithms, or routing cost functions. It orchestrates the existing single source of truth for each domain.
2. **Strict Baseline Isolation**: Simulations operate on in-memory deep copies. Running a scenario will never silently mutate baseline database entities (`villages`, `candidate_sites`, `relocation_assignments`, or `routes`).
3. **100% Deterministic Execution**: Given identical inputs and parameters, simulations produce identical numerical scores, band classifications, assignments, and routes. Randomness, runtime timestamps as math inputs, and unordered dict/set iteration are strictly prohibited.
4. **Decision Support Only**: Simulation outcomes are analytical what-if assessments for district officers and disaster managers. They do not constitute statutory evacuation orders or official government forecasts.

---

## 3. Supported Canonical Scenarios

| Scenario Type | Primary Input Modification | Expected Downstream Consequence |
|---|---|---|
| `NORMAL` | Multiplier = 1.0; no alterations | Baseline verification; proves reproducibility. |
| `EXTREME_RAINFALL` | Rainfall intensity multiplied by 1.40 (+40%) | Increases village rainfall risk factor; breaches dynamic rainfall triggers ($64.5\text{ mm}/24\text{h}$); escalates relocation priorities to IMMEDIATE. |
| `FLASH_FLOOD` | Flood hazard factor increased (+35 points); critical severity on river corridor | Severely increases risk for river valley settlements; activates flood hazard blockage on profile-configured low-lying valley highway corridors, forcing evacuation traffic onto alternate bypass routes. |
| `CAPACITY_CRISIS` | Candidate site infrastructure capacity reduced by 50% | Slashes effective carrying capacity in M4-03; triggers capacity exhaustion in M4-04 matching, causing subsequent villages to divert or become `UNASSIGNED`. |

---

## 4. Pipeline Stages & Engine Integration

1. **Risk Engine** (`app.core.risk.computation.MultiHazardRiskEngine` & `RiskClassificationEngine`):
   Evaluates 6 weighted factors ($\text{Hazard} \times 0.30 + \text{Flood} \times 0.20 + \text{Rainfall} \times 0.15 + \text{Slope} \times 0.15 + \text{Infra} \times 0.10 + \text{Social} \times 0.10$).
2. **Dynamic Red Zone Engine** (`app.core.risk.red_zone.dynamic_engine.DynamicRedZoneEngine`):
   Compares simulated telemetry against regional profile thresholds (e.g. $64.5\text{ mm}/24\text{h}$ rainfall).
3. **Relocation Priority Engine** (`app.core.risk.relocation_priority.RelocationPriorityEngine`):
   Computes urgency score ($0.40R + 0.25E + 0.20V + 0.10H + 0.05A$) and maps to IMMEDIATE, SHORT_TERM, MEDIUM_TERM, or MONITOR.
4. **Site Suitability Engine** (`app.core.relocation.suitability.SiteSuitabilityEngine`):
   Evaluates 9 weighted criteria with slope, buffer, and capacity hard safety constraint gates.
5. **Carrying Capacity Engine** (`app.core.relocation.capacity.CarryingCapacityEngine`):
   Evaluates weakest-link capacity $\min(\text{housing}, \text{water}, \text{sanitation}, \text{healthcare}, \text{shelter})$.
6. **Relocation Matching Engine** (`app.core.relocation.matching.RelocationMatchingEngine`):
   Greedy deterministic allocation in descending priority order with dynamic capacity reservation.
7. **Evacuation Routing Engine** (`app.core.relocation.routing.EvacuationRoutingEngine`):
   Deterministic Dijkstra routing avoiding severed corridors and penalizing hazard buffer proximity.

---

## 5. API Endpoints

- `GET /api/v1/scenarios`: Returns catalog of canonical and persisted scenarios.
- `POST /api/v1/scenarios`: Create custom scenario definition (`ADMIN` or `DISTRICT_OFFICER`).
- `GET /api/v1/scenarios/{id}`: Retrieve scenario definition by ID.
- `POST /api/v1/scenarios/run`: Execute scenario simulation. Supports `persist: bool = False` (pure calculation) or `persist: bool = True` (stores run record).
- `GET /api/v1/scenarios/runs/{id}`: Retrieve persisted scenario run record.
