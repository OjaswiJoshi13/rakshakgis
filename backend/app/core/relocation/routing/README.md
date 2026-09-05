# Evacuation & Access Routing Engine (Chunk M4-05)

## Architectural Purpose
The Evacuation & Access Routing Engine provides deterministic, transparent, and hazard-aware routing connecting vulnerable or relocating villages to their assigned safe relocation sites.

> [!NOTE]
> **Planning & Decision Support Notice:**
> This subsystem is an analytical decision-support tool developed for the SIH Problem Statement 26191 pilot. It does NOT constitute an automated emergency dispatch service, autonomous vehicle controller, or statutory evacuation mandate. All proposed evacuation corridors require administrative validation and physical verification by the District Disaster Management Authority (DDMA) and public works engineers.

---

## Subsystem Architecture

```
           Relocation Assignment / Coordinate Query
                              ↓
                  [Origin Village & Target Site]
                              ↓
              [BaseRoadNetworkProvider Boundary]
             (SyntheticHimalayanRoadProvider / OSM)
                              ↓
               [HazardAwareRouteEvaluator]
          (Landslide / Flood / Extreme Rainfall Buffers)
                              ↓
               [EvacuationRoutingEngine]
       (Deterministic Dijkstra Graph Optimization)
         - Segment Exclusions (BLOCKED)
         - Dynamic Risk Costs (PENALIZED)
         - Exact Tie-Breaking Key: (cost, hops, node_id)
                              ↓
          [Primary Route + Feasible Alternative]
            (Deterministic Edge-Penalty Diversion)
                              ↓
         [Road Geometry, Distance, Time, Explainability]
                              ↓
                    [REST API Interfaces]
             POST /api/v1/routes/generate (Pure)
             POST /api/v1/routes (Persistence)
             GET  /api/v1/routes/{id} (Inspection)
```

---

## Core Components

1. **`contracts.py`**:
   - `RouteQuery`: Validated input schema with strict geographic coordinate bounds ($[-180, 180]$, $[-90, 90]$) and non-negative parameters.
   - `RouteSegment`: Directed edge metadata including distance, speed, road classification, hazard exposures, and blockage reasons.
   - `RouteResult`: Evaluated primary or alternative route with continuous LineString geometry, physical distance, estimated time, and complete explainability.
   - `EvacuationRoutingResult`: Aggregate container bundling primary and alternative evacuation corridors with statutory disclaimers.

2. **`network.py`**:
   - `RoadNetwork`: In-memory spatial adjacency graph of nodes and directed edges.
   - `RoadNode`: Graph vertex with (lon, lat) WGS84 coordinates.
   - `RoadSegmentEdge`: Graph edge with verified physical LineString geometry and road attributes.
   - `BaseRoadNetworkProvider`: Abstract provider interface decoupling the routing core from the data origin.
   - `SyntheticHimalayanRoadProvider`: Deterministic synthetic road network modeling the Joshimath-Pipalkoti pilot corridor.

3. **`hazards.py`**:
   - `HazardAwareRouteEvaluator`: Spatial intersection engine querying active hazard events against road segments.
   - Evaluates geodesic buffer distances (e.g. 800m critical buffer, 1200m high buffer) and classifies segments as `NORMAL`, `PENALIZED`, or `BLOCKED`.

4. **`engine.py`**:
   - `EvacuationRoutingEngine`: Orchestrates network retrieval, nearest-node snapping, Dijkstra shortest-path solving, alternative generation, and explainability synthesis.

---

## Routing Algorithm & Cost Formulation

### Graph Optimization
Routing uses a deterministic **Dijkstra shortest-path algorithm** with exact tuple ordering in the priority queue:
$$\text{Priority Key} = \left(\text{round}(\text{effective\_cost}, 6), \text{segment\_count}, \text{str}(\text{node\_id})\right)$$

- **`effective_cost`**: Sum of physical distance, hazard penalties, and optional diversion penalties.
- **`segment_count`**: Prefers routes with fewer turn/hop complexities in case of tied effective costs.
- **`str(node_id)`**: Lexicographically stable node identifier ensuring zero dependency on arbitrary hash table ordering.

### Cost Function
$$\text{effective\_edge\_cost} = \text{distance\_km} + \text{hazard\_penalty} + \text{diversion\_cost}$$

- **Normal Segments (`NORMAL`):** $\text{hazard\_penalty} = 0.0$
- **Penalized Segments (`PENALIZED`):** $\text{hazard\_penalty} = \text{distance\_km} \times \text{penalty\_multiplier}$
  - `high` hazard: $+150\%$ distance penalty
  - `moderate` hazard: $+60\%$ distance penalty
  - `low` hazard: $+20\%$ distance penalty
- **Blocked Segments (`BLOCKED`):** Hard exclusion from the search graph. The engine will never traverse a blocked segment during primary safe route optimization.

---

## Alternative Route Generation

When `require_alternative = True`:
1. The segments composing the primary route are identified.
2. A deterministic diversion penalty ($+50.0\text{ km}$) is applied to those segments.
3. Dijkstra's algorithm is re-run on the penalized graph while still strictly excluding all `BLOCKED` hazard links.
4. The resulting secondary path is evaluated for genuine distinctness:
   - If overlap exceeds $85\%$, or if only a single physical corridor exists in the network, the engine returns `alternative_route = None` with the explicit explanation `NO_FEASIBLE_ALTERNATIVE`.
   - If a genuinely independent corridor exists (e.g. Upper Ridge Bypass vs Valley Highway), the secondary route is returned as `RouteType.ALTERNATIVE`.

---

## Distance & Travel Time Semantics

- **Road Distance:** Calculated strictly by summing the physical lengths of the traversed road segments. Straight-line Haversine distance is **never** presented as road distance.
- **Estimated Travel Time:** Derived from segment distances and functional road class design speeds ($\text{time} = \sum \frac{\text{dist}_i}{\text{speed}_i} \times 60$).
  - If speed or travel time attributes are missing or unmeasured for any segment, `estimated_time_minutes` is returned as `None` with an explanatory uncertainty note. Travel time is **never** fabricated.

---

## Safety-Critical Missing-Data Policy

> **Invariant: Unknown is NOT equivalent to safe.**

1. **Missing Road Network:** If no road graph covers the area or coordinates are beyond 15 km from the nearest node, returns `INSUFFICIENT_DATA`.
2. **Missing Hazard Data:** If hazard event observations are absent, the route is marked with an explicit uncertainty disclaimer in `explainability.uncertainty_notes`. It is never silently claimed to be hazard-free.
3. **Missing Speed Data:** Emits `estimated_time_minutes = None` rather than assuming default speeds silently.

---

## Synthetic Demonstration Dataset

The `SyntheticHimalayanRoadProvider` models the Joshimath-Pipalkoti corridor with two distinct routes:
1. **Valley Highway (NH-7 riverside):** Shorter physical distance (~18.7 km), but runs adjacent to active landslide cut-off `HIM-EVT-001`.
2. **Upper Ridge Bypass Road:** Longer physical distance (~21.2 km), but located on a high geological terrace completely free of river runout hazards.

**Demonstration Behavior:**
- Under normal conditions, the valley highway has the lower cost.
- Under active hazard `HIM-EVT-001`, the valley segment is designated `BLOCKED`, and the routing engine automatically and deterministically diverts the safe primary evacuation route to the Upper Ridge Bypass.
