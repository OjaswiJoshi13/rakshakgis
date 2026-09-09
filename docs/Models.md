# Disaster-Aware Relocation & Dynamic Routing

## Overview

In a natural disaster such as a flood, identifying a safe relocation destination is only one part of the problem.

A village may have a nearby safe village or shelter, but the connecting roads may be:

* Flooded
* Destroyed
* Blocked by debris
* Damaged due to landslides
* Cut off because of a collapsed bridge
* Unsafe for vehicles

Therefore, a conventional shortest-path navigation system is not sufficient.

The system must determine:

> **What is the safest feasible way to relocate people to a safe destination given the current disaster conditions and infrastructure damage?**

This module combines **GIS, hazard information, infrastructure-damage assessment, and dynamic routing** to provide disaster-aware evacuation and relocation decisions.

---

# 1. Problem Statement

Consider the following situation:

```text
Village A 🚨
     |
     | Road destroyed ❌
     |
     |
Village B 🏠
```

Village B is the only nearby safe relocation destination, but the road connecting Village A and Village B is destroyed.

A conventional routing system would simply return:

```text
NO ROUTE FOUND
```

That is not sufficient during an emergency.

The system should instead determine whether:

1. Another road exists.
2. A pedestrian path exists.
3. A boat-based evacuation route is possible.
4. An alternative access route can be established.
5. Emergency road restoration is possible.
6. Air evacuation or emergency rescue is required.

---

# 2. Core Concept

The system should move beyond:

> **Shortest path**

and instead solve:

> **Safest feasible evacuation path under changing disaster conditions.**

The routing engine should consider:

* Distance
* Flood depth
* Road condition
* Bridge condition
* Landslide risk
* Terrain
* Road accessibility
* Vehicle accessibility
* Population density
* Destination safety
* Current and predicted hazard conditions

---

# 3. Overall Architecture

```text
                    NATURAL DISASTER
                           |
                           v
                 Hazard Detection /
                    Prediction
                           |
             +-------------+-------------+
             |                           |
             v                           v
       Hazard Information        Infrastructure Data
       Flood extent              Road network
       Rainfall                  Bridges
       Water level               Footpaths
       Landslide                  Shelters
             |                           |
             +-------------+-------------+
                           |
                           v
                  Infrastructure
                  Damage Analysis
                           |
                           v
                    Dynamic GIS
                    Road Network
                           |
                           v
                   Route Availability
                           |
                 +---------+---------+
                 |                   |
                YES                  NO
                 |                   |
                 v                   v
          Safe Route Found     Alternative Access
                 |                   |
                 |           +-------+-------+-------+
                 |           |       |       |       |
                 |           v       v       v       v
                 |         Walk    Boat    Air    Repair
                 |           |       |       |       |
                 +-----------+-------+-------+-------+
                             |
                             v
                     Best Feasible
                     Evacuation Plan
                             |
                             v
                         ALERT / ACTION
```

---

# 4. Role of GIS

GIS is the foundation of the relocation system.

The geographical environment is represented as multiple layers.

## Road Network

Contains:

* Roads
* Road segments
* Intersections
* Bridges
* Tunnels
* Access points

Each road segment can have attributes such as:

```text
road_id
length
road_type
surface
status
flood_depth
damage_level
vehicle_access
risk_score
```

Example:

```text
Road 101
Length: 4.2 km
Status: BLOCKED
Flood depth: 1.4 m
Vehicle access: NO
Risk: HIGH
```

---

# 5. Dynamic Road Graph

The road network can be represented as a graph.

```text
        B
       / \
      /   \
     A     C
      \   /
       \ /
        D
```

Where:

* Nodes = villages, intersections, shelters, bridges, etc.
* Edges = roads or paths

Each edge receives a dynamic cost.

For example:

```text
Road A-B
Distance = 5 km
Risk = Low

Road B-C
Distance = 3 km
Risk = High

Road A-D
Distance = 8 km
Risk = Low
```

The routing engine can then choose the safest feasible route instead of blindly selecting the shortest one.

---

# 6. Risk-Aware Routing

A simple routing cost can be represented as:

```text
Cost = Distance + λ × Risk
```

Where:

* `Distance` = physical distance or travel time
* `Risk` = disaster-related danger
* `λ` = importance assigned to safety

The actual implementation can use a more sophisticated weighted cost.

For example:

```text
Cost =
    Travel Time
    + Flood Risk
    + Road Damage
    + Bridge Risk
    + Terrain Risk
    + Population Exposure
```

This allows the system to prefer a longer but safer route.

### Example

```text
Route 1
Distance = 10 km
Risk = Very High

Route 2
Distance = 15 km
Risk = Low
```

A normal navigation application might select Route 1.

A disaster evacuation system should generally prefer:

```text
Route 2 → Safer
```

provided it is actually feasible.

---

# 7. Routing Algorithms

## A*

A* is suitable for normal GIS-based route calculation.

It efficiently searches for a path by combining:

```text
Actual cost
+
Estimated remaining cost
```

It is useful when:

* The road network is known.
* A destination is known.
* We need an efficient path calculation.

---

## Dijkstra

Dijkstra's algorithm can also be used.

It finds the lowest-cost path through the graph.

It is simpler conceptually but can explore more nodes than A*.

---

## D* / D* Lite

D* is particularly interesting for disaster scenarios.

Disaster environments are dynamic.

For example:

```text
10:00

A ─── B ─── C
    OPEN
```

Later:

```text
10:20

A ─── B ❌ ─── C
       FLOOD
```

The road network has changed.

Instead of treating the environment as static, a dynamic routing algorithm can update the route when edge costs or connectivity change.

---

# 8. Detecting Damaged Roads

The routing system needs reliable information about road conditions.

Possible data sources include:

### Satellite imagery

Before/after imagery can identify:

* Flooded roads
* Collapsed bridges
* Landslides
* Debris
* Infrastructure destruction

A computer-vision model such as a CNN-based segmentation/detection model can help identify damage.

```text
Satellite Image
       |
       v
Computer Vision Model
       |
       v
Infrastructure Damage
       |
       v
Road = BLOCKED
```

---

# 9. Other Sources of Road Information

AI-based detection does not have to be the only source.

Road status can also come from:

* Government disaster-management agencies
* Emergency responders
* Police
* Local authorities
* IoT sensors
* Drones
* Crowdsourced reports
* Traffic/infrastructure APIs
* Manual operator updates

The system can combine these sources to determine the current road condition.

---

# 10. Road Status

Rather than simply using:

```text
OPEN / CLOSED
```

roads can have multiple states:

```text
OPEN
CAUTION
FLOODED
DAMAGED
BLOCKED
BRIDGE_FAILURE
UNKNOWN
```

This gives the routing engine more information.

For example:

```text
Road A → OPEN
Road B → CAUTION
Road C → FLOODED
Road D → BLOCKED
```

---

# 11. When No Road Exists

This is one of the most important parts of the system.

Suppose:

```text
                 Safe Village B
                      🏠
                      |
                Road destroyed
                      ❌
                      |
                 Village A
                    🚨
```

If every vehicle-accessible route is blocked, the system must **not invent a route**.

Instead, it should enter an **Alternative Access Mode**.

---

# 12. Alternative Access Modes

## 12.1 Pedestrian Evacuation

A vehicle road may be unusable while a footpath or trail remains accessible.

The system can check:

```text
Road network
+
Footpath network
+
Terrain
```

and determine whether people can safely walk to the destination.

Example:

```text
Village A
   |
   | Road ❌
   |
   +-------- Footpath --------+
                              |
                              v
                          Village B
```

---

## 12.2 Boat Evacuation

During severe flooding, water may make conventional roads unusable.

If conditions permit, the system can evaluate a water-based route.

```text
Village A 🚨
      |
      | Boat
      v
 ~~~~~~~~~~~~~
 ~ FLOODED ~~~
 ~~~~~~~~~~~~~
      |
      v
Village B 🏠
```

This should only be recommended when appropriate safety and operational data indicate that water transport is feasible.

---

## 12.3 Air Evacuation

If all ground and water routes are unavailable, the system can escalate the situation.

It can identify possible:

* Helicopter landing zones
* Open fields
* Emergency helipads
* Suitable staging areas

The result could be:

```text
GROUND ACCESS → BLOCKED
WATER ACCESS → UNAVAILABLE
AIR ACCESS → POSSIBLE

ACTION:
REQUEST EMERGENCY AIR EVACUATION
```

---

# 13. Emergency Road Restoration

Sometimes the destination is inaccessible because of a **single critical obstruction**.

Example:

```text
Village A
   |
   |
Bridge ❌
   |
   |
Village B
```

Instead of searching endlessly for another route, the system can identify:

> "The only connectivity failure is Bridge X."

Authorities can then prioritize:

* Bridge repair
* Debris removal
* Temporary bridge installation
* Emergency road clearance
* Rescue vehicle access

This makes the system useful not only for navigation but also for **disaster-response planning**.

---

# 14. Multi-Modal Evacuation

The system should ideally support multiple modes.

```text
                 Destination
                     |
             Is road available?
                /          \
              YES           NO
               |             |
        Vehicle Route    Check alternatives
                             |
             +---------------+---------------+
             |               |               |
          Walking          Boat            Air
             |               |               |
             +---------------+---------------+
                             |
                             v
                     Feasibility Check
                             |
                             v
                    Best Available Option
```

---

# 15. Hazard Prediction vs Routing

It is important to separate **hazard prediction** from **route planning**.

For example:

### Hazard prediction

Predict:

> "Flood intensity is likely to increase over the next 30–60 minutes."

This can use ML models such as:

* CNN
* LSTM
* CNN + LSTM
* Other spatiotemporal models

### Routing

Determine:

> "Given the current/predicted hazard and road conditions, how should people evacuate?"

This is primarily:

* GIS
* Graph algorithms
* Risk modelling
* Constraint-based routing

Therefore:

```text
ML
 ↓
Predict hazard / detect damage
 ↓
GIS
 ↓
Update environment
 ↓
Routing algorithm
 ↓
Evacuation plan
```

---

# 16. Where CNN + LSTM Fits

CNN + LSTM is useful when the problem contains both **spatial and temporal information**.

For example, rainfall:

```text
Rainfall Map t1
      ↓
     CNN
      ↓
Spatial features
      ↓
Rainfall Map t2
      ↓
     CNN
      ↓
Spatial features
      ↓
       ...
      ↓
     LSTM
      ↓
Temporal evolution
      ↓
Future rainfall / anomaly
```

CNN handles spatial patterns.

LSTM handles temporal patterns.

The output can then influence the GIS routing layer.

---

# 17. Other Natural Hazards

The architecture should not assume that every hazard requires CNN + LSTM.

A useful rule is:

```text
Spatial data
     ↓
    CNN

Time-series data
     ↓
    LSTM

Spatial + temporal data
     ↓
 CNN + LSTM
```

Examples:

| Hazard                           | Possible model                          |
| -------------------------------- | --------------------------------------- |
| Extreme rainfall                 | CNN + LSTM                              |
| Flood                            | CNN + LSTM / other spatiotemporal model |
| Wildfire                         | CNN + LSTM                              |
| Cyclone                          | CNN + LSTM                              |
| Earthquake signals               | 1D CNN / LSTM                           |
| Landslide susceptibility         | CNN                                     |
| River-level prediction           | LSTM                                    |
| Satellite-based damage detection | CNN                                     |

The exact architecture should ultimately be selected based on the available data and validation performance.

---

# 18. Complete Disaster Relocation Workflow

```text
                 DISASTER OCCURS
                       |
                       v
              Hazard Detection
                       |
                       v
              Hazard Assessment
                       |
                       v
            Identify affected areas
                       |
                       v
             Identify safe villages
              / shelters / hospitals
                       |
                       v
               Build road graph
                       |
                       v
             Check road conditions
                       |
            +----------+----------+
            |                     |
         Route exists         No route
            |                     |
            v                     v
      Risk-aware routing     Alternative access
            |                     |
            |          +----------+----------+
            |          |          |          |
            |        Walk       Boat       Air
            |          |          |          |
            |          +----------+----------+
            |                     |
            |                     v
            |              Feasibility check
            |                     |
            +----------+----------+
                       |
                       v
              Safest feasible plan
                       |
                       v
                Emergency Alert
                       |
                       v
             Continuous Monitoring
                       |
                       v
             Recalculate if needed
```

---

# 19. Dynamic Re-Routing

The system should continuously monitor changing conditions.

For example:

```text
10:00
Route A → SAFE

10:15
Flood level rising

10:20
Route A → HIGH RISK

10:25
Route A → BLOCKED

10:25
      ↓
Recalculate
      ↓
Route B → SAFE
```

Therefore, the system is not:

> "Calculate route once."

It is:

> **"Continuously maintain the safest feasible evacuation plan as the disaster evolves."**

---

# 20. Example Scenario

### Initial state

```text
Village A 🚨
     |
     | 5 km
     |
Village B 🏠
```

Village B is the nearest safe relocation destination.

### Disaster occurs

The connecting road becomes flooded.

```text
Village A 🚨
     |
     X
  FLOODED
     |
Village B 🏠
```

The routing engine checks alternative roads.

No vehicle route exists.

### Next step

The system checks:

```text
Footpath → Available
Boat route → Unsafe
Helicopter landing zone → Available
```

Depending on the actual conditions, it may recommend pedestrian evacuation or escalate to emergency air evacuation.

If **no feasible access mode exists**, the system reports:

```text
DESTINATION: Village B
GROUND ACCESS: BLOCKED
ALTERNATIVE ACCESS: UNAVAILABLE

ACTION:
REQUEST EMERGENCY RESCUE /
PRIORITIZE ROAD RESTORATION
```

This is preferable to generating a dangerous or fictional route.

---

# 21. Key Design Principle

The system should always follow:

```text
SAFETY
   ↓
FEASIBILITY
   ↓
TIME
   ↓
DISTANCE
```

Rather than:

```text
Shortest distance
       ↓
Ignore disaster conditions
```

In disaster management, the shortest route is not necessarily the best route.

The **best route is the safest route that is actually feasible under the current conditions**.

---

# 22. Recommended Technology Stack

A practical implementation could use:

### GIS

* PostGIS
* GeoServer
* OpenStreetMap
* GeoPandas

### Routing

* A*
* Dijkstra
* D* Lite for dynamic environments
* OSRM / GraphHopper / custom routing

### AI / Computer Vision

* CNN-based models
* Segmentation models
* Object detection
* CNN + LSTM for spatiotemporal prediction

### Backend

* Python
* FastAPI
* PostgreSQL/PostGIS

### Frontend

* React
* Leaflet / MapLibre / Mapbox-compatible mapping

### Data

* Satellite imagery
* Weather/rainfall data
* River/water-level data
* Road network
* Elevation/DEM
* Infrastructure information
* Government/emergency reports

---

# 23. Final Architecture for RakshakGIS

The complete concept can be summarized as:

```text
             ┌──────────────────────┐
             │   HAZARD PREDICTION  │
             │ CNN / LSTM / Hybrid   │
             └──────────┬───────────┘
                        ↓
                Hazard Risk Map
                        ↓
             ┌──────────────────────┐
             │ DAMAGE / ACCESS      │
             │ ASSESSMENT           │
             └──────────┬───────────┘
                        ↓
                 Road Conditions
                        ↓
             ┌──────────────────────┐
             │       GIS            │
             │ Dynamic Road Graph   │
             └──────────┬───────────┘
                        ↓
              ┌───────────────────┐
              │ ROUTE AVAILABLE?  │
              └─────────┬─────────┘
                   YES /   \ NO
                      /     \
                     ↓       ↓
             Safe Routing   Alternative
                  A*        Access
                            |
                   +--------+--------+
                   |        |        |
                 Walk     Boat      Air
                   |        |        |
                   +--------+--------+
                            |
                            ↓
                    Feasibility Check
                            |
                            ↓
                  SAFEST RESPONSE PLAN
                            |
                            ↓
                     ALERT / EVACUATE
                            |
                            ↓
                     CONTINUOUS UPDATE
                            |
                            └────→ Re-route
```

## Core takeaway

**CNN/LSTM predicts and understands the hazard.**

**Computer vision/GIS determines the state of the physical environment.**

**Graph-based routing determines how to move through that environment.**

**Alternative-access logic handles situations where normal roads no longer provide connectivity.**

Together, these components turn the system from a simple map/navigation application into a **dynamic disaster-aware evacuation and relocation platform**.
