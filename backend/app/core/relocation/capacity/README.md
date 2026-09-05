# Carrying Capacity & Infrastructure Sizing Engine (Chunk M4-03)

## Architectural Purpose
The Carrying Capacity & Infrastructure Sizing Engine provides deterministic, explainable, and region-agnostic calculations to determine:
> *"How many incoming households can this relocation site safely accommodate, based on its effective capacity and critical infrastructure?"*

## Authoritative Effective-Capacity Rule
Effective carrying capacity is governed by the strict weakest-link bottleneck principle:
$$\text{effective\_capacity} = \min(\text{housing}, \text{water}, \text{sanitation}, \text{healthcare}, \text{shelter})$$

- **No Averaging / No Summing:** Critical dimensions cannot compensate for deficits in others.
- **Safety Invariant on Unknown Data:** Unknown critical capacity dimensions are **never** treated as unlimited. Any missing critical dimension yields an indeterminate/infeasible result.

## Incoming and Available Capacity
$$\text{available\_capacity} = \text{effective\_capacity} - \text{current\_occupancy}$$
$$\text{capacity\_margin} = \text{available\_capacity} - \text{incoming\_households}$$

- **Feasibility:** Feasible if and only if $\text{available\_capacity} > 0$ and $\text{capacity\_margin} \ge 0$, with no critical deficits.
- **Negative Margin Preservation:** Deficits are strictly preserved as negative numbers (never clamped to zero) for explainability and downstream relocation optimization (M4-04).

## Limiting Factor Identification
All critical infrastructure dimensions whose capacity equals $\text{effective\_capacity}$ are reported deterministically as limiting factors (sorted alphabetically in case of ties).

## Infrastructure Sizing Across Critical Dimensions
1. **Housing / Habitation:** Existing household capacity vs. incoming household demand; physical land area ($\text{sq.m}$) sized against regional `land_area_sq_m_per_household`.
2. **Water Availability:** Existing household water capacity vs. incoming household demand; physical water sized against regional `water_supply_lpd_per_capita` (70.0 LPD baseline).
3. **Sanitation Facilities:** Existing household sanitation vs. incoming household demand; toilet units sized against `households_per_sanitation_unit` (4.0 hh/unit).
4. **Healthcare Access:** Existing healthcare coverage capacity vs. incoming household demand.
5. **Emergency Shelter:** Existing emergency shelter capacity vs. incoming household demand.

## Regional Configuration
Default planning parameters are sourced dynamically from `RegionProfile` (`SiteCapacityAssumptions`). Explicit invalid profiles raise `UnknownRegionProfileError` (HTTP 404) without silent fallback.
