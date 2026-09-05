# Relocation Matching & Assignment Engine (Chunk M4-04)

## Architectural Purpose
The Relocation Matching & Assignment Engine provides deterministic, transparent, and explainable allocation of displaced and highly vulnerable village populations to safe, viable candidate relocation sites.

> [!NOTE]
> **Planning Standard Notice:** This engine implements a deterministic greedy assignment algorithm developed as an MVP decision-support tool. It is NOT an officially mandated statutory government optimization methodology, nor does it constitute an automated legal eviction or relocation mandate. All proposed assignments require formal administrative review and sign-off by the District Magistrate and Rehabilitation Committee.

---

## Conceptual Workflow

The matching engine implements an exact 6-step deterministic allocation flow:

### Step A — Order Villages by Relocation Priority
Villages are processed sequentially in descending order of their M3-12 Relocation Priority Score:
$$\text{Priority} = 0.40 \times \text{Risk} + 0.25 \times \text{Exposure} + 0.20 \times \text{Vulnerability} + 0.10 \times \text{Historical Impact} + 0.05 \times \text{Accessibility}$$
- **Deterministic Tie-Breaking:** In the event of identical priority scores, ties are broken deterministically by ascending string representation of `village_id`.
- **Randomness:** Zero random ordering or non-deterministic shuffling is permitted.

### Step B — Determine Incoming Demand
For each village, household demand $D$ is extracted from official demographic enumeration or relocation priority assessments. Inputs are strictly validated:
- Must be non-negative ($D \ge 0$).
- Must be finite (rejection of $\text{NaN}$ and $\pm\infty$).

### Step C — Evaluate Candidate Sites
Every candidate site is evaluated for the current village against authoritative safety and capacity gates:
1. **Registry Availability:** The site must not be marked `rejected` or `inactive`.
2. **M4-02 Hard Safety Constraints:** The site must pass all hard topographical safety constraints (`hazard_slope` $\le 15.0^\circ$, `hazard_buffer` $\ge 500.0\text{ m}$, known `usable_capacity` $> 0$). Rejection code: `UNSAFE_SITE`.
3. **M4-02 Suitability Decision:** The site must not be classified as `UNSUITABLE` (overall score $\ge 40.0$). Rejection code: `LOW_SUITABILITY`.
4. **M4-03 Unknown Data Safety:** All 5 critical carrying capacity dimensions (housing, water, sanitation, healthcare, shelter) must be known. Unknown capacity is **never** treated as unlimited. Rejection code: `UNKNOWN_CAPACITY`.
5. **M4-03 Dynamic Capacity Sufficiency:** Current available capacity $C_{\text{avail}}$ must be greater than or equal to village demand $D$. Rejection code: `INSUFFICIENT_CAPACITY`.

### Step D — Deterministic Ranking of Feasible Sites
Feasible sites are ranked using a composite score prioritizing site suitability while rewarding spatial proximity:
$$\text{proximity\_score} = \max(0.0, 100.0 - 2.0 \times \text{distance\_km})$$
$$\text{rank\_score} = 0.70 \times \text{suitability\_score} + 0.30 \times \text{proximity\_score}$$
*(If spatial coordinates are unavailable, $\text{rank\_score} = \text{suitability\_score}$).*

- **Distance Calculation:** Haversine great-circle formula using mean Earth radius $R = 6371.009\text{ km}$ between village and site coordinates (WGS84).
- **Linear Attenuation:** At $0\text{ km}$, $\text{proximity\_score} = 100.0$; at $10\text{ km}$, $\text{proximity\_score} = 80.0$; at $50\text{ km}$ and beyond, $\text{proximity\_score} = 0.0$. Negative distances are strictly invalid.
- **Deterministic Sort Key:**
$$\left(-\text{rank\_score}, -\text{suitability\_score}, \text{distance\_km}, \text{str}(\text{site\_id})\right)$$

### Step E — Capacity Reservation
When a village is allocated to site $S$:
$$\text{available\_capacity\_after} = \text{available\_capacity\_before} - D$$
- The updated remaining capacity is immediately reflected for subsequent villages.
- Capacity is strictly guarded: $\text{available\_capacity\_after} \ge 0$.
- Evaluation is pure: dynamic capacity tracking is in-memory and does not mutate database tables unless an explicit assignment commit API is invoked.

### Step F — UNASSIGNED Handling
If no candidate site satisfies all constraints for a village:
- The village is designated as `UNASSIGNED`.
- Village priority is preserved.
- Structured rejection reasons and codes (`UNSAFE_SITE`, `LOW_SUITABILITY`, `INSUFFICIENT_CAPACITY`, `UNKNOWN_CAPACITY`, `SITE_UNAVAILABLE`, `NO_FEASIBLE_SITE`) are attached for every candidate site evaluated.

---

## Evaluation vs. Persistence Architecture

The subsystem strictly decouples pure algorithmic calculation from transactional database state mutations:
1. **Pure Matching Calculation (`POST /api/v1/relocation/match`):**
   - Purely analytical computation;
   - Generates deterministic recommendations and complete explainability payloads;
   - Zero database mutations: no rows inserted, no capacities altered, no side effects.
2. **Explicit Assignment Persistence (`POST /api/v1/relocation/assignments` & `/batch`):**
   - Authorized officers (`ADMIN`, `DISTRICT_OFFICER`) persist reviewed assignments to `relocation_assignments`;
   - Optional transactional deduction of physical site capacities (`commit_site_capacity=True`);
   - Enforces referential integrity with `villages` and `candidate_sites`.
3. **Assignment Inspection (`GET /api/v1/relocation/assignments` & `/{id}`):**
   - Authenticated, paginated query endpoint supporting filtering by `village_id`, `candidate_site_id`, and `status`.

---

## Explainability Architecture

Every matching run produces an exhaustive decision trail for officer review:
- **Village Record:** `village_id`, `village_name`, `priority_score`, `priority_band`, `incoming_households`.
- **Assignment Outcome:** `status` (`assigned` or `unassigned`), `assigned_site_id`, `assigned_site_name`.
- **Numerical Accounting:** `available_capacity_before`, `available_capacity_after`, `rank_score`, `suitability_score`, `distance_km`, `proximity_score`.
- **Candidate Site Rejection Audit:** List of all evaluated sites with `is_feasible`, `rejection_code`, `rejection_reasons`, and `capacity_margin`.
- **Unassigned Narrative:** If unassigned, clear structured reasons detailing why every candidate site was rejected.
- **Statutory Notice:** Explicit governance disclaimer attached to every result envelope.

---

## Rejection Reason Taxonomy
| Rejection Code | Trigger Condition |
|---|---|
| `UNSAFE_SITE` | Failed M4-02 hard safety constraint (slope $\le 15^\circ$, buffer $\ge 500\text{ m}$, known usable capacity $> 0$ households). |
| `LOW_SUITABILITY` | Site passes hard safety constraints, but overall M4-02 suitability score is below acceptable threshold ($< 40.0$). |
| `INSUFFICIENT_CAPACITY` | Available site capacity remaining $< D$ (exhausted or deficit). |
| `UNKNOWN_CAPACITY` | Site has missing or unmeasured critical capacity dimensions; never assumed unlimited. |
| `SITE_UNAVAILABLE` | Site is designated as `rejected` or `inactive` in the registry. |
| `NO_FEASIBLE_SITE` | Village-level failure when all candidate sites fail one or more constraints. |

---

## Future Optimization Solver Replacement Boundary
The greedy matching engine is decoupled behind the standard interface:
```python
class RelocationMatchingEngine:
    def match(
        self, villages: List[VillageDemandInput], sites: List[MatchingSiteCandidate]
    ) -> RelocationMatchingResult:
        ...
```
In future iterations (e.g. post-SIH), this interface can be backed by an integer linear programming (ILP) or constraint programming solver (such as Google OR-Tools) to optimize global multi-village assignments, without modifying data transfer contracts, schema envelopes, or REST API endpoints.
